from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "essay" / "optimized_experimental_database_with_supplementary_expanded160_union_evidence_aware_llm_qc_enriched.csv"
DEFAULT_OUTPUT = ROOT / "essay" / "optimized_experimental_database_with_supplementary_expanded160_union_evidence_aware_fulltext_pro_completed.csv"
DEFAULT_SUMMARY = ROOT / "essay" / "optimized_experimental_database_with_supplementary_expanded160_union_evidence_aware_fulltext_pro_completed_summary.json"
DEFAULT_CACHE = ROOT / "essay" / "fulltext_pro_field_completion_cache.jsonl"
DEFAULT_API_TXT = ROOT / "API.txt"

UNKNOWN_VALUES = {"", "unknown", "none", "null", "nan", "n/a", "na", "not specified", "not available"}
MODEL = "deepseek-v4-pro"
API_BASE = "https://api.deepseek.com/v1/chat/completions"

LABEL_FIELDS = ["canonical_product", "product_family", "canonical_host", "host_group"]
TARGET_FIELDS = [
    "enzyme_name",
    "enzyme_mutant",
    "enzyme_source_species",
    "expression_host",
    "substrate_name",
    "main_product_name",
    "reaction_system_type",
    "is_whole_cell",
    "llps_component",
    "llps_state",
    "llps_trigger",
    "reaction_temperature",
    "reaction_ph",
    "reaction_time",
    "buffer_type",
    "substrate_concentration",
    "cofactor",
    "cofactor_concentration",
    "cosubstrate",
    "cell_density_od600",
]

PRODUCT_FAMILIES = {
    "flavonoid",
    "isoflavonoid",
    "terpenoid",
    "isoprenoid",
    "stilbene",
    "phenylpropanoid",
    "prenylflavonoid",
    "natural_product",
    "llps_system",
    "other",
}
HOST_GROUPS = {"yeast", "bacteria", "cyanobacteria", "plant", "mammalian", "cell_free", "other"}
PROJECT_TERMS = [
    "titer", "titre", "yield", "production", "produced", "activity", "conversion",
    "specific activity", "kcat", "km", "enzyme", "mutant", "substrate", "host",
    "strain", "Saccharomyces", "yeast", "Escherichia", "Yarrowia", "Bacillus",
    "flavonoid", "isoflavonoid", "terpenoid", "isoprenoid", "glabridin",
    "naringenin", "liquiritigenin", "lycopene", "astaxanthin", "carotene",
    "phase separation", "LLPS", "condensate", "droplet", "puncta", "foci",
    "temperature", "pH", "OD600", "medium", "supplementary", "table",
]


def compact(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def is_unknown(value: Any) -> bool:
    return compact(value).lower() in UNKNOWN_VALUES


def read_deepseek_key(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    match = re.search(r"DEEPSEEK_API_KEY\s*=\s*['\"]([^'\"]+)['\"]", text)
    return match.group(1).strip() if match else ""


def safe_path(path_text: str) -> Path:
    p = Path(compact(path_text))
    if not p.is_absolute():
        p = ROOT / p
    return p


def load_text_manifests(root: Path) -> dict[str, list[str]]:
    doi_to_files: dict[str, list[str]] = {}
    for manifest in (root / "essay").rglob("*manifest*.csv"):
        try:
            with manifest.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames or "doi" not in reader.fieldnames or "text_file" not in reader.fieldnames:
                    continue
                for row in reader:
                    doi = compact(row.get("doi", "")).lower()
                    text_file = compact(row.get("text_file", ""))
                    status = compact(row.get("status", "")).lower()
                    if not doi or not text_file or status not in {"cached", "downloaded"}:
                        continue
                    path = safe_path(text_file)
                    if path.exists():
                        doi_to_files.setdefault(doi, [])
                        if str(path) not in doi_to_files[doi]:
                            doi_to_files[doi].append(str(path))
        except Exception:
            continue
    for doi, files in doi_to_files.items():
        files.sort(key=lambda p: ("supplementary" not in p.lower(), len(p)))
    return doi_to_files


def words(text: str) -> set[str]:
    stop = {
        "the", "and", "for", "with", "from", "that", "this", "were", "was", "are", "into",
        "after", "before", "using", "table", "figure", "showed", "shown", "than", "then",
        "also", "only", "when", "where", "which", "their", "there", "these", "those",
    }
    return {w for w in re.findall(r"[A-Za-z0-9_.+-]+", text.lower()) if len(w) > 3 and w not in stop}


def split_chunks(text: str, target: int = 1800) -> list[str]:
    text = re.sub(r"\s+", " ", text or " ").strip()
    if not text:
        return []
    pieces = re.split(r"(?<=[.!?。])\s+(?=[A-Z0-9(])", text)
    chunks: list[str] = []
    buf = ""
    for piece in pieces:
        if len(buf) + len(piece) > target and buf:
            chunks.append(buf.strip())
            buf = piece
        else:
            buf = (buf + " " + piece).strip()
    if buf:
        chunks.append(buf.strip())
    return chunks


def row_needs_completion(row: dict[str, str]) -> bool:
    if row_missing_label(row):
        return True
    for field in TARGET_FIELDS:
        best_value = row.get(f"best_{field}_value") if f"best_{field}_value" in row else ""
        if is_unknown(best_value) and is_unknown(row.get(f"{field}_value")) and is_unknown(row.get(f"{field}_norm_value")):
            return True
    return False


def row_missing_label(row: dict[str, str]) -> bool:
    return row_missing_product_label(row) or row_missing_host_label(row)


def row_missing_product_label(row: dict[str, str]) -> bool:
    product = row.get("best_canonical_product") if "best_canonical_product" in row else row.get("final_canonical_product")
    family = row.get("best_product_family") if "best_product_family" in row else row.get("final_product_family")
    return is_unknown(product) or is_unknown(family)


def row_missing_host_label(row: dict[str, str]) -> bool:
    host = row.get("best_canonical_host") if "best_canonical_host" in row else row.get("final_canonical_host")
    group = row.get("best_host_group") if "best_host_group" in row else row.get("final_host_group")
    return is_unknown(host) or is_unknown(group)


def row_priority(row: dict[str, str]) -> tuple[int, int, str]:
    tier_rank = {"core": 0, "llps_core": 0, "silver": 1, "review": 2}
    clean_rank = {"A_complete": 0, "A_llps": 0, "B_product_condition": 1, "C_partial_context": 2, "C_llps_candidate": 2, "D_result_only": 3}
    return (
        0 if row_missing_product_label(row) else 1,
        0 if row_missing_host_label(row) else 1,
        tier_rank.get(compact(row.get("database_tier")), 5),
        clean_rank.get(compact(row.get("clean_level")), 5),
        compact(row.get("optimized_record_id")),
    )


def row_attempted(row: dict[str, str]) -> bool:
    return not is_unknown(row.get("fulltext_pro_status"))


def row_matches_mode(row: dict[str, str], mode: str, only_unattempted: bool) -> bool:
    if only_unattempted and row_attempted(row):
        return False
    if mode == "retry_errors":
        return compact(row.get("fulltext_pro_status")).lower() == "error" and row_needs_completion(row)
    if mode == "missing_labels":
        return row_missing_label(row)
    if mode == "missing_products":
        return row_missing_product_label(row)
    if mode == "missing_hosts":
        return row_missing_host_label(row)
    if mode == "all_missing_fields":
        return row_needs_completion(row)
    raise ValueError(f"Unsupported mode: {mode}")


def build_row_batches(rows: list[dict[str, str]], text_map: dict[str, list[str]], rows_per_batch: int, limit: int, mode: str, only_unattempted: bool = True, offset: int = 0) -> list[dict[str, Any]]:
    by_doi: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        doi = compact(row.get("doi", "")).lower()
        if doi and doi in text_map and row_matches_mode(row, mode, only_unattempted):
            by_doi.setdefault(doi, []).append(row)

    batches: list[dict[str, Any]] = []
    for doi, items in by_doi.items():
        items.sort(key=row_priority)
        for batch_i in range(0, len(items), rows_per_batch):
            selected = items[batch_i:batch_i + rows_per_batch]
            key_basis = doi + "|" + "|".join(compact(r.get("optimized_record_id")) for r in selected)
            batches.append({
                "batch_key": hashlib.sha1(key_basis.encode("utf-8", errors="ignore")).hexdigest()[:18],
                "doi": doi,
                "title": compact(selected[0].get("title_clean") or selected[0].get("title")),
                "rows": selected,
                "text_files": text_map[doi],
            })
    batches.sort(key=lambda b: (row_priority(b["rows"][0]), b["doi"], b["batch_key"]))
    if offset > 0:
        batches = batches[offset:]
    return batches[:limit] if limit > 0 else batches


def query_for_rows(rows: list[dict[str, str]]) -> str:
    parts = []
    for row in rows:
        parts.extend([
            compact(row.get("title_clean") or row.get("title")),
            compact(row.get("primary_result_metric")),
            compact(row.get("primary_result_value")),
            compact(row.get("primary_result_unit")),
            compact(row.get("primary_result_evidence")),
            compact(row.get("final_canonical_product")),
            compact(row.get("final_canonical_host")),
            compact(row.get("main_product_name_evidence")),
            compact(row.get("expression_host_evidence")),
            compact(row.get("enzyme_name_evidence")),
            compact(row.get("substrate_name_evidence")),
        ])
    return " ".join(x for x in parts if x and x.lower() not in UNKNOWN_VALUES)


def retrieve_context(batch: dict[str, Any], *, max_files: int, max_chars_per_file: int, max_context_chars: int) -> tuple[str, list[str], int]:
    query = query_for_rows(batch["rows"])
    qwords = words(query)
    rows = batch["rows"]
    scored: list[tuple[int, str, str]] = []
    used_files: list[str] = []
    total_read = 0

    for file_path in batch["text_files"][:max_files]:
        path = Path(file_path)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[:max_chars_per_file]
        except Exception:
            continue
        if not text.strip():
            continue
        used_files.append(str(path))
        total_read += len(text)
        source_label = "SI/data" if "supplementary" in str(path).lower() else "fulltext"
        first = compact(text[:2500])
        if first:
            scored.append((15, source_label, first))
        chunks = split_chunks(text)
        for chunk in chunks:
            low = chunk.lower()
            score = 0
            score += len(qwords & words(chunk)) * 3
            for row in rows:
                value = compact(row.get("primary_result_value"))
                unit = compact(row.get("primary_result_unit")).lower()
                ev = compact(row.get("primary_result_evidence"))
                if value and value.lower() in low:
                    score += 40
                if unit and unit in low:
                    score += 10
                ev_words = words(ev)
                score += len(ev_words & words(chunk)) * 5
            for term in PROJECT_TERMS:
                if term.lower() in low:
                    score += 4
            if score > 10:
                scored.append((score, source_label, chunk[:2400]))

    scored.sort(key=lambda x: x[0], reverse=True)
    contexts: list[str] = []
    seen: set[str] = set()
    for score, source, chunk in scored:
        key = chunk[:180]
        if key in seen:
            continue
        seen.add(key)
        contexts.append(f"[{source}; score={score}]\n{chunk}")
        if sum(len(c) for c in contexts) >= max_context_chars:
            break
    return "\n\n".join(contexts)[:max_context_chars], used_files, total_read


def row_payload(row: dict[str, str]) -> str:
    current = {
        "record_id": compact(row.get("optimized_record_id")),
        "clean_level": compact(row.get("clean_level")),
        "database_tier": compact(row.get("database_tier")),
        "primary_result_metric": compact(row.get("primary_result_metric")),
        "primary_result_value": compact(row.get("primary_result_value")),
        "primary_result_unit": compact(row.get("primary_result_unit")),
        "primary_result_evidence": compact(row.get("primary_result_evidence"))[:1000],
        "current_canonical_product": compact(row.get("final_canonical_product")),
        "current_product_family": compact(row.get("final_product_family")),
        "current_canonical_host": compact(row.get("final_canonical_host")),
        "current_host_group": compact(row.get("final_host_group")),
    }
    for field in TARGET_FIELDS:
        current[field] = compact(row.get(f"{field}_value") or row.get(f"{field}_norm_value"))
        ev = compact(row.get(f"{field}_evidence"))
        if ev:
            current[f"{field}_evidence"] = ev[:350]
    return json.dumps(current, ensure_ascii=False)


def build_prompt(batch: dict[str, Any], context: str, strategy_note: str = "") -> str:
    rows_json = "\n".join(row_payload(row) for row in batch["rows"])
    target_fields = ", ".join(TARGET_FIELDS)
    return f"""
You are a highly conservative scientific database curator.

Goal: complete missing row-level fields for extracted experimental records using full article and supplementary/data contexts.
Accuracy is more important than filling every cell. Fill a field only when the supplied context directly supports it.

Return strict JSON only:
{{
  "updates": [
    {{
      "record_id": "exact input record_id",
      "confidence": 0.0,
      "evidence_summary": "short quote/paraphrase from supplied context",
      "canonical_product": null,
      "product_family": null,
      "canonical_host": null,
      "host_group": null,
      "fields": {{
        "field_name": {{"value": null, "unit": null, "evidence": null}}
      }}
    }}
  ]
}}

Allowed product_family values: {", ".join(sorted(PRODUCT_FAMILIES))}.
Allowed host_group values: {", ".join(sorted(HOST_GROUPS))}.
Allowed row fields: {target_fields}.

Rules:
- Do not infer from DOI alone. Use only title/current row evidence/fulltext/SI context below.
- Keep null for unsupported fields.
- If the context identifies article-level product or host and the row result clearly belongs to that article system, you may fill the row label.
- If an article reports multiple products, hosts, strains, mutants, substrates, or conditions, fill only the value connected to the row's numeric result/evidence.
- Do not overwrite a precise current value with a broader value.
- Use glabridin_titer/glabridin_yield in current rows as generic titer/yield columns; the true product name belongs in main_product_name/canonical_product.
- Confidence >= 0.80 means directly supported and safe to use. Confidence < 0.80 will be kept only as review evidence, not best-field fill.
- Evidence should be short and must come from the provided context.
{strategy_note}

DOI: {batch["doi"]}
Title: {batch["title"]}

Rows needing completion, one JSON object per line:
{rows_json}

Retrieved fulltext/SI contexts:
{context}
""".strip()


def parse_json_object(text: str) -> dict[str, Any]:
    text = compact(text)
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise


def call_llm(api_key: str, prompt: str, model: str, api_base: str, retries: int) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return JSON only. Be conservative and evidence-grounded."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    last_error = ""
    for attempt in range(max(1, retries)):
        try:
            resp = requests.post(api_base, headers=headers, json=payload, timeout=180)
            if resp.status_code == 429:
                time.sleep(min(90, 5 * (2 ** attempt)))
                continue
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return parse_json_object(content)
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < retries - 1:
                time.sleep(min(60, 3 * (2 ** attempt)))
    return {"error": last_error}


def load_cache(path: Path) -> dict[str, dict[str, Any]]:
    cache: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return cache
    transient_markers = ("SSLError", "Timeout", "ConnectionError", "429", "Max retries exceeded")
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            error = compact((obj.get("result") or {}).get("error"))
            if error and any(marker in error for marker in transient_markers):
                continue
            key = obj.get("cache_key")
            if key:
                cache[key] = obj
    return cache


def append_cache(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def process_batch(batch: dict[str, Any], args: argparse.Namespace, api_key: str, cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    context, files, total_read = retrieve_context(
        batch,
        max_files=args.max_text_files,
        max_chars_per_file=args.max_chars_per_file,
        max_context_chars=args.max_context_chars,
    )
    record_ids = [compact(r.get("optimized_record_id")) for r in batch["rows"]]
    cache_basis = json.dumps({
        "batch_key": batch["batch_key"],
        "model": args.model,
        "retry_tag": args.retry_tag,
        "strategy_note": args.strategy_note,
        "record_ids": record_ids,
        "context_hash": hashlib.sha1(context.encode("utf-8", errors="ignore")).hexdigest(),
    }, ensure_ascii=False, sort_keys=True)
    cache_key = hashlib.sha1(cache_basis.encode("utf-8", errors="ignore")).hexdigest()
    if cache_key in cache:
        result = cache[cache_key]["result"]
        cached = True
    elif not context.strip():
        result = {"error": "no_fulltext_or_si_context"}
        cached = False
    else:
        result = call_llm(api_key, build_prompt(batch, context, args.strategy_note), args.model, args.api_base, args.retries)
        append_cache(args.cache, {
            "cache_key": cache_key,
            "batch_key": batch["batch_key"],
            "doi": batch["doi"],
            "record_ids": record_ids,
            "model": args.model,
            "retry_tag": args.retry_tag,
            "strategy_note": args.strategy_note,
            "result": result,
            "context_files": files,
            "context_chars": len(context),
            "ts": time.time(),
        })
        cached = False
    return {
        "batch_key": batch["batch_key"],
        "doi": batch["doi"],
        "record_ids": record_ids,
        "result": result,
        "context_files": files,
        "context_chars": len(context),
        "total_read_chars": total_read,
        "cached": cached,
    }


def update_field(row: dict[str, str], field: str, value: Any, unit: Any, evidence: Any, confidence: float, source: str) -> None:
    if is_unknown(value):
        return
    row[f"fulltext_pro_{field}_value"] = compact(value)
    row[f"fulltext_pro_{field}_unit"] = "" if is_unknown(unit) else compact(unit)
    row[f"fulltext_pro_{field}_evidence"] = compact(evidence)[:700]
    if confidence >= 0.80 and is_unknown(row.get(f"{field}_value")) and is_unknown(row.get(f"{field}_norm_value")):
        row[f"best_{field}_value"] = compact(value)
        row[f"best_{field}_unit"] = "" if is_unknown(unit) else compact(unit)
        row[f"best_{field}_evidence"] = compact(evidence)[:700]
        row[f"best_{field}_source"] = source


def apply_result(rows_by_id: dict[str, dict[str, str]], batch_result: dict[str, Any]) -> None:
    result = batch_result["result"]
    if result.get("error"):
        for rid in batch_result["record_ids"]:
            row = rows_by_id.get(rid)
            if row:
                row["fulltext_pro_status"] = "error"
                row["fulltext_pro_reason"] = compact(result.get("error"))[:500]
                row["fulltext_pro_batch_key"] = batch_result["batch_key"]
        return

    updates = result.get("updates") or []
    seen: set[str] = set()
    for update in updates:
        rid = compact(update.get("record_id"))
        if not rid or rid not in rows_by_id:
            continue
        seen.add(rid)
        row = rows_by_id[rid]
        try:
            confidence = float(update.get("confidence") or 0)
        except (TypeError, ValueError):
            confidence = 0.0
        row["fulltext_pro_status"] = "accepted" if confidence >= 0.80 else "low_confidence"
        row["fulltext_pro_confidence"] = f"{confidence:.2f}"
        row["fulltext_pro_evidence_summary"] = compact(update.get("evidence_summary"))[:700]
        row["fulltext_pro_raw_json"] = json.dumps(update, ensure_ascii=False)
        row["fulltext_pro_batch_key"] = batch_result["batch_key"]
        row["fulltext_pro_context_files"] = ";".join(batch_result["context_files"][:8])
        row["fulltext_pro_context_chars"] = str(batch_result["context_chars"])
        row["fulltext_pro_completed_at"] = datetime.now().isoformat(timespec="seconds")

        for label in LABEL_FIELDS:
            value = update.get(label)
            if is_unknown(value):
                continue
            if label == "product_family" and compact(value) not in PRODUCT_FAMILIES:
                value = "other"
            if label == "host_group" and compact(value) not in HOST_GROUPS:
                value = "other"
            row[f"fulltext_pro_{label}"] = compact(value)
            final_col = f"final_{label}"
            best_col = f"best_{label}"
            if confidence >= 0.80 and is_unknown(row.get(final_col)):
                row[best_col] = compact(value)
                row[f"{best_col}_source"] = "fulltext_pro"

        fields = update.get("fields") or {}
        if isinstance(fields, dict):
            for field, payload in fields.items():
                if field not in TARGET_FIELDS or not isinstance(payload, dict):
                    continue
                update_field(
                    row,
                    field,
                    payload.get("value"),
                    payload.get("unit"),
                    payload.get("evidence"),
                    confidence,
                    "fulltext_pro",
                )

    for rid in batch_result["record_ids"]:
        if rid not in seen:
            row = rows_by_id.get(rid)
            if row and not row.get("fulltext_pro_status"):
                row["fulltext_pro_status"] = "no_update"
                row["fulltext_pro_batch_key"] = batch_result["batch_key"]
                row["fulltext_pro_context_chars"] = str(batch_result["context_chars"])


def initialize_best_columns(row: dict[str, str]) -> None:
    for label in LABEL_FIELDS:
        final_col = f"final_{label}"
        best_col = f"best_{label}"
        if not is_unknown(row.get(best_col)):
            row.setdefault(f"{best_col}_source", row.get(f"{best_col}_source", "previous_fulltext_pro"))
            continue
        row[best_col] = compact(row.get(final_col)) if not is_unknown(row.get(final_col)) else "unknown"
        row[f"{best_col}_source"] = "existing_or_prior_qc" if not is_unknown(row.get(final_col)) else "unresolved"
    for field in TARGET_FIELDS:
        if not is_unknown(row.get(f"best_{field}_value")):
            row.setdefault(f"best_{field}_source", row.get(f"best_{field}_source", "previous_fulltext_pro"))
            continue
        value = compact(row.get(f"{field}_value") or row.get(f"{field}_norm_value"))
        unit = compact(row.get(f"{field}_unit") or row.get(f"{field}_norm_unit"))
        evidence = compact(row.get(f"{field}_evidence"))
        row[f"best_{field}_value"] = value if not is_unknown(value) else ""
        row[f"best_{field}_unit"] = unit if not is_unknown(unit) else ""
        row[f"best_{field}_evidence"] = evidence
        row[f"best_{field}_source"] = "existing" if not is_unknown(value) else "unresolved"


def summarize(rows: list[dict[str, str]], text_map: dict[str, list[str]], batches: list[dict[str, Any]]) -> dict[str, Any]:
    def count_unknown(field: str) -> int:
        return sum(1 for row in rows if is_unknown(row.get(field)))

    def counts(field: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for row in rows:
            value = compact(row.get(field)) or "unknown"
            out[value] = out.get(value, 0) + 1
        return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0]))[:30])

    field_before_after = {}
    for field in TARGET_FIELDS:
        before = sum(1 for row in rows if is_unknown(row.get(f"{field}_value")) and is_unknown(row.get(f"{field}_norm_value")))
        after = sum(1 for row in rows if is_unknown(row.get(f"best_{field}_value")))
        field_before_after[field] = {"missing_before": before, "missing_after": after, "filled_by_pro": before - after}

    needed_rows = [row for row in rows if row_needs_completion(row)]
    return {
        "rows": len(rows),
        "text_mapped_dois": len(text_map),
        "batches_built": len(batches),
        "rows_still_needing_by_original_logic": len(needed_rows),
        "labels": {
            "final_product_family_unknown_before_fulltext": count_unknown("final_product_family"),
            "best_product_family_unknown_after_fulltext": count_unknown("best_product_family"),
            "final_host_group_unknown_before_fulltext": count_unknown("final_host_group"),
            "best_host_group_unknown_after_fulltext": count_unknown("best_host_group"),
            "final_canonical_product_unknown_before_fulltext": count_unknown("final_canonical_product"),
            "best_canonical_product_unknown_after_fulltext": count_unknown("best_canonical_product"),
            "final_canonical_host_unknown_before_fulltext": count_unknown("final_canonical_host"),
            "best_canonical_host_unknown_after_fulltext": count_unknown("best_canonical_host"),
        },
        "target_field_missing_before_after": field_before_after,
        "fulltext_pro_status_counts": counts("fulltext_pro_status"),
        "best_product_family_counts": counts("best_product_family"),
        "best_host_group_counts": counts("best_host_group"),
    }


def write_outputs(rows: list[dict[str, str]], fields: list[str], output: Path, summary: Path, cache_path: Path, text_map: dict[str, list[str]], batches: list[dict[str, Any]], start: float, checkpoint_done: int, checkpoint_total: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    summary_obj = summarize(rows, text_map, batches)
    summary_obj["output"] = str(output)
    summary_obj["cache"] = str(cache_path)
    summary_obj["elapsed_sec"] = round(time.time() - start, 1)
    summary_obj["checkpoint_done_batches"] = checkpoint_done
    summary_obj["checkpoint_total_batches"] = checkpoint_total
    summary.write_text(json.dumps(summary_obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--api-txt", type=Path, default=DEFAULT_API_TXT)
    parser.add_argument("--api-base", default=API_BASE)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--batch-offset", type=int, default=0)
    parser.add_argument("--rows-per-batch", type=int, default=12)
    parser.add_argument("--mode", choices=["missing_labels", "missing_products", "missing_hosts", "all_missing_fields", "retry_errors"], default="missing_labels")
    parser.add_argument("--max-text-files", type=int, default=8)
    parser.add_argument("--max-chars-per-file", type=int, default=260000)
    parser.add_argument("--max-context-chars", type=int, default=42000)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--checkpoint-every", type=int, default=20)
    parser.add_argument("--include-attempted", action="store_true", help="Also include rows that already have a fulltext_pro_status.")
    parser.add_argument("--retry-tag", default="", help="Change this to force a new LLM pass for the same batch/context.")
    parser.add_argument("--strategy-note", default="", help="Extra instruction appended to the prompt for looped retries.")
    args = parser.parse_args()

    api_key = read_deepseek_key(args.api_txt)
    if not api_key:
        print("DeepSeek key missing", file=sys.stderr)
        return 2

    with args.input.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = [dict(row) for row in reader]
        base_fields = list(reader.fieldnames or [])

    for row in rows:
        initialize_best_columns(row)

    text_map = load_text_manifests(ROOT)
    batches = build_row_batches(
        rows,
        text_map,
        max(1, args.rows_per_batch),
        args.limit,
        args.mode,
        only_unattempted=not args.include_attempted,
        offset=max(0, args.batch_offset),
    )
    cache = load_cache(args.cache)
    rows_by_id = {compact(row.get("optimized_record_id")): row for row in rows if compact(row.get("optimized_record_id"))}

    extra_fields = [
        "fulltext_pro_status", "fulltext_pro_confidence", "fulltext_pro_evidence_summary",
        "fulltext_pro_raw_json", "fulltext_pro_batch_key", "fulltext_pro_context_files",
        "fulltext_pro_context_chars", "fulltext_pro_completed_at", "fulltext_pro_reason",
    ]
    for label in LABEL_FIELDS:
        extra_fields.extend([f"fulltext_pro_{label}", f"best_{label}", f"best_{label}_source"])
    for field in TARGET_FIELDS:
        extra_fields.extend([
            f"fulltext_pro_{field}_value", f"fulltext_pro_{field}_unit", f"fulltext_pro_{field}_evidence",
            f"best_{field}_value", f"best_{field}_unit", f"best_{field}_evidence", f"best_{field}_source",
        ])

    fields = base_fields + [field for field in extra_fields if field not in base_fields]

    print(f"rows={len(rows)} mapped_dois={len(text_map)} batches={len(batches)} mode={args.mode} model={args.model}", flush=True)
    start = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futures = [ex.submit(process_batch, batch, args, api_key, cache) for batch in batches]
        for future in as_completed(futures):
            result = future.result()
            apply_result(rows_by_id, result)
            done += 1
            if done % 20 == 0 or done == len(futures):
                print(f"fulltext_pro_batches_done={done}/{len(futures)} elapsed_sec={time.time()-start:.1f}", flush=True)
            if args.checkpoint_every > 0 and (done % args.checkpoint_every == 0 or done == len(futures)):
                write_outputs(rows, fields, args.output, args.summary, args.cache, text_map, batches, start, done, len(futures))

    write_outputs(rows, fields, args.output, args.summary, args.cache, text_map, batches, start, done, len(futures))
    summary = summarize(rows, text_map, batches)
    print(json.dumps(summary["labels"], ensure_ascii=False), flush=True)
    print(f"Wrote: {args.output}", flush=True)
    print(f"Wrote: {args.summary}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

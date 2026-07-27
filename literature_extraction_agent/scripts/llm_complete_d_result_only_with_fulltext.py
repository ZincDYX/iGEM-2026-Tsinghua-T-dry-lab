from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from CatalystOptimizationSystem.core.constraints import compute_confidence
from CatalystOptimizationSystem.core.extractor import (
    _append_rows,
    _as_records,
    _dedupe_records,
    _existing_article_keys,
    _flatten_record_rows,
    _normalize_records,
    _output_columns,
    _status_row,
    call_llm_openai,
    load_icl_examples,
    parse_metrics_json,
)
from CatalystOptimizationSystem.core.icl_selector import select_icl_examples
from CatalystOptimizationSystem.core.schema_config import load_schema, schema_constraints, schema_metric_names, schema_prompt
from CatalystOptimizationSystem.utils.config import DEFAULT_ICL_BANK, DEFAULT_LLM_BASE, DEFAULT_LLM_MODEL, DEFAULT_SCHEMA_JSON


DEFAULT_INPUT = ROOT / "essay" / "aggregated_clean_experimental_database.csv"
DEFAULT_OUT = ROOT / "essay" / "llm_completed_d_result_only_fulltext.csv"
DEFAULT_API_TXT = ROOT / "API.txt"

RESULT_PRIORITY = {
    "glabridin_titer": 0,
    "glabridin_yield": 1,
    "substrate_conversion": 2,
    "enzyme_activity": 3,
    "specific_activity": 3,
    "relative_activity": 4,
    "kcat": 5,
    "km": 5,
    "critical_phase_concentration": 6,
    "llps_state": 6,
}
PROJECT_TERMS = {
    "glabridin": 10,
    "isoflavonoid": 8,
    "flavonoid": 7,
    "naringenin": 7,
    "liquiritigenin": 7,
    "yeast": 7,
    "saccharomyces": 7,
    "yarrowia": 5,
    "pichia": 5,
    "metabolic engineering": 7,
    "heterologous": 5,
    "biosynthesis": 5,
    "phase separation": 8,
    "condensate": 8,
    "droplet": 5,
    "titer": 3,
    "yield": 2,
    "activity": 2,
}


def read_deepseek_key(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    match = re.search(r"DEEPSEEK_API_KEY\s*=\s*['\"]([^'\"]+)['\"]", text)
    return match.group(1).strip() if match else ""


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def safe_console(text: str, limit: int = 90) -> str:
    return str(text or "")[:limit].encode("gbk", errors="replace").decode("gbk")


def metric_value(row: dict[str, str], metric: str) -> tuple[str, str, str]:
    return norm(row.get(f"{metric}_value", "")), norm(row.get(f"{metric}_unit", "")), norm(row.get(f"{metric}_evidence", ""))


def row_priority(row: dict[str, str]) -> tuple[int, int, str]:
    metric = norm(row.get("primary_result_metric", ""))
    try:
        score = -int(float(row.get("source_scores", "").split(";")[0].strip() or 0))
    except Exception:
        score = 0
    return RESULT_PRIORITY.get(metric, 99), score, row.get("aggregate_record_id", "")


def project_score(rows: list[dict[str, str]]) -> int:
    text = "\n".join([rows[0].get("title", "")] + [r.get("primary_result_evidence", "") for r in rows]).lower()
    score = 0
    for term, weight in PROJECT_TERMS.items():
        score += weight * min(4, text.count(term))
    return score


def load_text_manifest() -> dict[str, str]:
    doi_to_text: dict[str, str] = {}
    for manifest in (ROOT / "essay").glob("pdf_text_cache*_manifest.csv"):
        try:
            with manifest.open("r", encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    doi = norm(row.get("doi", "")).lower()
                    text_file = norm(row.get("text_file", ""))
                    if row.get("status") == "cached" and doi and text_file and doi not in doi_to_text:
                        doi_to_text[doi] = text_file
        except Exception:
            continue
    return doi_to_text


def words(text: str) -> set[str]:
    stop = {
        "the", "and", "for", "with", "from", "that", "this", "were", "was", "are", "into",
        "after", "before", "table", "figure", "using", "showed", "shown", "production",
    }
    return {w for w in re.findall(r"[A-Za-z0-9α-ωΑ-ΩβγδμµΩ]+", text.lower()) if len(w) > 3 and w not in stop}


def split_context_units(text: str) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    contexts: list[str] = []
    for paragraph in paragraphs:
        one = re.sub(r"\s+", " ", paragraph).strip()
        if len(one) <= 1800:
            contexts.append(one)
            continue
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(])", one)
        buf = ""
        for sentence in sentences:
            if len(buf) + len(sentence) > 1800:
                if buf:
                    contexts.append(buf.strip())
                buf = sentence
            else:
                buf = (buf + " " + sentence).strip()
        if buf:
            contexts.append(buf.strip())
    return contexts


def best_fulltext_contexts(text: str, evidence: str, value: str, unit: str, *, max_contexts: int = 3) -> list[str]:
    contexts = split_context_units(text)
    evidence_words = words(evidence)
    val = norm(value)
    unit_low = norm(unit).lower()
    scored: list[tuple[int, int, str]] = []
    for i, ctx in enumerate(contexts):
        low = ctx.lower()
        score = 0
        overlap = len(evidence_words & words(ctx))
        score += overlap * 5
        if val and val.lower() in low:
            score += 25
        if unit_low and unit_low in low:
            score += 10
        for term in PROJECT_TERMS:
            if term in low:
                score += 2
        if any(x in low for x in ["titer", "titre", "yield", "activity", "conversion", "produced", "reached", "achieved"]):
            score += 8
        if score > 0:
            start = max(0, i - 1)
            end = min(len(contexts), i + 2)
            merged = " ".join(contexts[start:end])
            scored.append((score, i, merged[:3500]))
    scored.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    out: list[str] = []
    seen: set[str] = set()
    for _, _, ctx in scored:
        key = ctx[:200]
        if key in seen:
            continue
        seen.add(key)
        out.append(ctx)
        if len(out) >= max_contexts:
            break
    return out


def build_groups(input_csv: Path, doi_to_text: dict[str, str], *, max_rows_per_doi: int, min_project_score: int) -> list[dict[str, Any]]:
    by_doi: dict[str, list[dict[str, str]]] = {}
    with input_csv.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("clean_level") != "D_result_only":
                continue
            doi = norm(row.get("doi", "")).lower()
            if not doi or doi not in doi_to_text:
                continue
            by_doi.setdefault(doi, []).append(row)

    groups: list[dict[str, Any]] = []
    for doi, rows in by_doi.items():
        rows.sort(key=row_priority)
        selected = rows[:max_rows_per_doi]
        score = project_score(selected)
        if score < min_project_score:
            continue
        groups.append({
            "doi": doi,
            "title": norm(selected[0].get("title", "")),
            "rows": selected,
            "text_file": doi_to_text[doi],
            "project_score": score,
        })
    groups.sort(key=lambda g: (-g["project_score"], g["doi"]))
    return groups


def evidence_payload(group: dict[str, Any]) -> str:
    text_file = Path(group["text_file"])
    if not text_file.is_absolute():
        text_file = ROOT / text_file
    try:
        fulltext = text_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        fulltext = ""
    lines = [
        f"Article DOI: {group['doi']}",
        f"Article title: {group.get('title', '')}",
        "",
        "The rows below were previously classified as D_result_only because they had numeric results but insufficient local context.",
        "Use the longer full-text contexts to recover product, host/strain, substrate, reaction system, conditions, and true result type when explicitly supported.",
        "Output only strict experimental records. If the longer context still does not identify at least a result plus product/host/system context, return {\"records\": []}.",
        "Do not invent values. Keep null for unknown fields. For non-glabridin products, store the real product name in main_product_name and use glabridin_titer/glabridin_yield as generic product titer/yield fields.",
        "If one evidence sentence reports multiple products with different titers, create separate records for each product-result pair.",
        "",
        "D_result_only candidates with longer contexts:",
    ]
    for i, row in enumerate(group["rows"], start=1):
        metric = norm(row.get("primary_result_metric", ""))
        value = norm(row.get("primary_result_value", ""))
        unit = norm(row.get("primary_result_unit", ""))
        evidence = norm(row.get("primary_result_evidence", ""))
        contexts = best_fulltext_contexts(fulltext, evidence, value, unit)
        lines.append(
            f"[{i}] id={row.get('aggregate_record_id')} metric={metric} "
            f"value={value} unit={unit} local_evidence={evidence[:900]}"
        )
        for j, ctx in enumerate(contexts, start=1):
            lines.append(f"  longer_context_{j}: {ctx}")
    return "\n".join(lines)[:30000]


def build_prompt(examples: list[dict[str, Any]], payload: str, metrics: list[str], schema: dict[str, Any]) -> str:
    parts = [
        "You are a strict scientific data curator completing weak high-recall extraction rows using full-text context.",
        "Return JSON only as {\"records\": [<record>, ...]}.",
        "Each record must use flat JSON keys exactly matching the requested metric names.",
        "Each metric value must be an object: {\"value\": <string_or_number|null>, \"unit\": <string|null>, \"evidence\": <string|null>}.",
        "A valid record corresponds to one product/result under one host/system/condition context.",
        "Reject method-only, medium-addition, scale-bar, reference, and unrelated biomedical values.",
        "Requested metrics: " + ", ".join(metrics),
    ]
    schema_instructions = schema_prompt(schema, metrics)
    if schema_instructions:
        parts.append(schema_instructions)
    if examples:
        parts.append("Relevant few-shot examples:")
        for ex in examples[:3]:
            inst = norm(ex.get("instruction", ""))
            if inst:
                parts.append("Instruction:\n" + inst)
            parts.append("Context:\n" + str(ex.get("context", ""))[:1600])
            parts.append("Expected JSON:\n" + json.dumps({"records": [ex.get("output", {})]}, ensure_ascii=False))
    parts.append("Input:\n" + payload)
    return "\n\n".join(parts)


def process_group(
    group: dict[str, Any],
    *,
    metrics: list[str],
    examples: list[dict[str, Any]],
    schema: dict[str, Any],
    constraints: dict[str, Any],
    llm_api_key: str,
    llm_base: str,
    llm_model: str,
    icl_top_k: int,
) -> list[dict[str, Any]]:
    doi = group["doi"]
    title = group.get("title", "")
    payload = evidence_payload(group)
    selected_examples = select_icl_examples(examples, payload, metrics, domain=schema.get("domain"), k=int(icl_top_k or 3))
    try:
        if not llm_api_key:
            return [_status_row(pii=None, doi=doi, title=title, keyword="llm_complete_d_result_only_fulltext", schema=schema, selected_examples=selected_examples, status="llm_key_missing", error="llm key missing", text_chars=len(payload), chunk_count=1, processed_chunks=0)]
        prompt = build_prompt(selected_examples, payload, metrics, schema)
        parsed = parse_metrics_json(call_llm_openai(llm_api_key, llm_base, llm_model, prompt))
        records = _dedupe_records(_as_records(parsed, metrics), metrics)
        if not records:
            return [_status_row(pii=None, doi=doi, title=title, keyword="llm_complete_d_result_only_fulltext", schema=schema, selected_examples=selected_examples, status="no_records", error="LLM returned no supported records from D_result_only context", text_chars=len(payload), chunk_count=1, processed_chunks=1)]
        norm_maps, metric_vios, cross_vios = _normalize_records(records, metrics, constraints, schema)
        confidence = compute_confidence(metric_vios, cross_vios, 0)
        rows = _flatten_record_rows(
            records=records,
            norm_maps=norm_maps,
            metrics=metrics,
            pii=None,
            doi=doi,
            title=title,
            keyword="llm_complete_d_result_only_fulltext",
            schema=schema,
            selected_examples=selected_examples,
            corrected_rounds=0,
            confidence=confidence,
            text_chars=len(payload),
            chunk_count=1,
            processed_chunks=1,
        )
        source_ids = ";".join(row.get("aggregate_record_id", "") for row in group["rows"])
        for row in rows:
            row["source_d_result_record_ids"] = source_ids
            row["source_d_result_count"] = len(group["rows"])
            row["normalization_source"] = "llm_complete_d_result_only_fulltext"
            row["project_score"] = group.get("project_score", 0)
            row["source_text_file"] = group.get("text_file", "")
        return rows
    except Exception as exc:
        return [_status_row(pii=None, doi=doi, title=title, keyword="llm_complete_d_result_only_fulltext", schema=schema, selected_examples=selected_examples, status="error", error=f"{type(exc).__name__}: {exc}", text_chars=len(payload), chunk_count=1, processed_chunks=0)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--schema", type=Path, default=ROOT / DEFAULT_SCHEMA_JSON)
    parser.add_argument("--icl-bank", type=Path, default=ROOT / DEFAULT_ICL_BANK)
    parser.add_argument("--api-txt", type=Path, default=DEFAULT_API_TXT)
    parser.add_argument("--llm-key", default="")
    parser.add_argument("--llm-base", default=DEFAULT_LLM_BASE)
    parser.add_argument("--llm-model", default=DEFAULT_LLM_MODEL)
    parser.add_argument("--icl-top-k", type=int, default=3)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--max-rows-per-doi", type=int, default=8)
    parser.add_argument("--min-project-score", type=int, default=0)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    schema = load_schema(str(args.schema))
    metrics = schema_metric_names(schema)
    constraints = schema_constraints(schema)
    examples = load_icl_examples(str(args.icl_bank))
    llm_key = args.llm_key or read_deepseek_key(args.api_txt)
    doi_to_text = load_text_manifest()
    groups = build_groups(args.input, doi_to_text, max_rows_per_doi=max(1, args.max_rows_per_doi), min_project_score=args.min_project_score)
    done = set() if args.no_resume else _existing_article_keys(str(args.out))
    groups = [g for g in groups if f"doi:{g['doi'].lower().strip()}" not in done]
    if args.limit > 0:
        groups = groups[: args.limit]

    columns = _output_columns(metrics) + [
        "source_d_result_record_ids",
        "source_d_result_count",
        "normalization_source",
        "project_score",
        "source_text_file",
    ]
    lock = threading.Lock()
    written = 0
    start = time.time()
    with ThreadPoolExecutor(max_workers=max(1, int(args.workers or 1))) as pool:
        futures = [
            pool.submit(
                process_group,
                group,
                metrics=metrics,
                examples=examples,
                schema=schema,
                constraints=constraints,
                llm_api_key=llm_key,
                llm_base=args.llm_base,
                llm_model=args.llm_model,
                icl_top_k=args.icl_top_k,
            )
            for group in groups
        ]
        for i, future in enumerate(as_completed(futures), start=1):
            out_rows = future.result()
            _append_rows(str(args.out), out_rows, columns, lock)
            written += len(out_rows)
            first = out_rows[0] if out_rows else {}
            print(f"processed={i}/{len(futures)} rows={len(out_rows)} status={first.get('extraction_status')} title={safe_console(first.get('title', ''))}", flush=True)
    print(f"done groups={len(groups)} written_rows={written} elapsed_sec={time.time()-start:.1f} out={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests


UNKNOWN_VALUES = {"", "unknown", "none", "null", "nan", "n/a", "na", "not specified"}
PRODUCT_FAMILY_NORMALIZATION = {
    "alkaloid": "other",
    "polyketide": "other",
    "pterocarpanoid": "isoflavonoid",
    "pterocarpan": "isoflavonoid",
}
HOST_GROUP_NORMALIZATION = {
    "microbial": "other",
    "microorganisms": "other",
    "microorganism": "other",
    "fungal": "other",
    "fungi": "other",
}


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = DEFAULT_ROOT / "essay" / "optimized_experimental_database_with_supplementary_expanded160_union_evidence_aware.csv"
DEFAULT_OUTPUT = DEFAULT_ROOT / "essay" / "optimized_experimental_database_with_supplementary_expanded160_union_evidence_aware_llm_qc_enriched.csv"
DEFAULT_SUMMARY = DEFAULT_ROOT / "essay" / "optimized_experimental_database_with_supplementary_expanded160_union_evidence_aware_llm_qc_enriched_summary.json"
DEFAULT_CACHE = DEFAULT_ROOT / "essay" / "llm_qc_broad_database_cache.jsonl"
DEFAULT_API_TXT = DEFAULT_ROOT / "API.txt"


PRODUCT_PATTERNS: list[tuple[str, str, list[str]]] = [
    ("glabridin", "isoflavonoid", [r"\bglabridin\b"]),
    ("liquiritigenin", "flavonoid", [r"\bliquiritigenin\b"]),
    ("naringenin", "flavonoid", [r"\bnaringenin\b"]),
    ("pinocembrin", "flavonoid", [r"\bpinocembrin\b"]),
    ("apigenin", "flavonoid", [r"\bapigenin\b"]),
    ("eriodictyol", "flavonoid", [r"\beriodictyol\b"]),
    ("kaempferol", "flavonoid", [r"\bkaempferol\b"]),
    ("quercetin", "flavonoid", [r"\bquercetin\b"]),
    ("taxifolin", "flavonoid", [r"\btaxifolin\b", r"\bdihydroquercetin\b"]),
    ("anthocyanin", "flavonoid", [r"\banthocyanin(?:s)?\b"]),
    ("flavonoid", "flavonoid", [r"\bflavonoid(?:s)?\b", r"\bchalcone(?:s)?\b", r"\bflavanone(?:s)?\b"]),
    ("daidzein", "isoflavonoid", [r"\bdaidzein\b"]),
    ("genistein", "isoflavonoid", [r"\bgenistein\b"]),
    ("glycitein", "isoflavonoid", [r"\bglycitein\b"]),
    ("isoflavonoid", "isoflavonoid", [r"\bisoflavonoid(?:s)?\b", r"\bisoflavone(?:s)?\b"]),
    ("resveratrol", "stilbene", [r"\bresveratrol\b", r"\bstilbene(?:s)?\b"]),
    ("phloretin", "phenylpropanoid", [r"\bphloretin\b"]),
    ("xanthohumol", "prenylflavonoid", [r"\bxanthohumol\b"]),
    ("lycopene", "isoprenoid", [r"\blycopene\b"]),
    ("astaxanthin", "isoprenoid", [r"\bastaxanthin\b"]),
    ("beta-carotene", "isoprenoid", [r"\b(?:beta|β)-carotene\b", r"\bcarotene\b"]),
    ("carotenoid", "isoprenoid", [r"\bcarotenoid(?:s)?\b"]),
    ("squalene", "isoprenoid", [r"\bsqualene\b"]),
    ("limonene", "terpenoid", [r"\blimonene\b"]),
    ("taxadiene", "terpenoid", [r"\btaxadiene\b"]),
    ("amorpha-4,11-diene", "terpenoid", [r"\bamorpha-?4,?11-?diene\b", r"\bartemisinic\b"]),
    ("farnesene", "terpenoid", [r"\bfarnesene\b"]),
    ("isoprene", "isoprenoid", [r"\bisoprene\b"]),
    ("nootkatone", "terpenoid", [r"\bnootkatone\b"]),
    ("valencene", "terpenoid", [r"\bvalencene\b"]),
    ("patchoulol", "terpenoid", [r"\bpatchoulol\b"]),
    ("geraniol", "terpenoid", [r"\bgeraniol\b"]),
    ("linalool", "terpenoid", [r"\blinalool\b"]),
    ("terpenoid", "terpenoid", [r"\bterpenoid(?:s)?\b", r"\bterpene(?:s)?\b"]),
    ("isoprenoid", "isoprenoid", [r"\bisoprenoid(?:s)?\b"]),
    ("natural product", "natural_product", [r"\bnatural product(?:s)?\b", r"\bspecialized metabolite(?:s)?\b"]),
    ("LLPS/condensate system", "llps_system", [r"\bphase separation\b", r"\bLLPS\b", r"\bcondensate(?:s)?\b", r"\bdroplet(?:s)?\b", r"\bpuncta\b", r"\bfoci\b", r"\bgranule(?:s)?\b", r"\bmembraneless organelle(?:s)?\b"]),
]


HOST_PATTERNS: list[tuple[str, str, list[str]]] = [
    ("Saccharomyces cerevisiae", "yeast", [r"\bSaccharomyces cerevisiae\b", r"\bS\. cerevisiae\b", r"\byeast\b"]),
    ("Yarrowia lipolytica", "yeast", [r"\bYarrowia lipolytica\b", r"\bY\. lipolytica\b"]),
    ("Pichia/Komagataella/Ogataea yeast", "yeast", [r"\bPichia pastoris\b", r"\bKomagataella phaffii\b", r"\bOgataea\b"]),
    ("Escherichia coli", "bacteria", [r"\bEscherichia coli\b", r"\bE\. coli\b"]),
    ("Bacillus subtilis", "bacteria", [r"\bBacillus subtilis\b", r"\bB\. subtilis\b"]),
    ("Bacillus", "bacteria", [r"\bBacillus\b"]),
    ("Streptomyces", "bacteria", [r"\bStreptomyces\b"]),
    ("Corynebacterium glutamicum", "bacteria", [r"\bCorynebacterium glutamicum\b", r"\bC\. glutamicum\b"]),
    ("Pseudomonas putida", "bacteria", [r"\bPseudomonas putida\b", r"\bP\. putida\b"]),
    ("Synechocystis sp. PCC 6803", "cyanobacteria", [r"\bSynechocystis\b", r"\bPCC 6803\b"]),
    ("Nicotiana benthamiana", "plant", [r"\bNicotiana benthamiana\b", r"\bN\. benthamiana\b"]),
    ("Arabidopsis thaliana", "plant", [r"\bArabidopsis thaliana\b", r"\bA\. thaliana\b"]),
    ("Glycine max", "plant", [r"\bGlycine max\b", r"\bsoybean\b"]),
    ("plant", "plant", [r"\bplant cell(?:s)?\b", r"\bplant\b"]),
    ("mammalian cell", "mammalian", [r"\bHEK293\b", r"\bCHO\b", r"\bmammalian cell(?:s)?\b"]),
]


CONTEXT_FIELDS = [
    "doi", "title", "title_clean", "source_keywords", "source_article_keys",
    "primary_result_evidence", "main_product_name_evidence", "expression_host_evidence",
    "enzyme_name_evidence", "substrate_name_evidence", "reaction_system_type_evidence",
    "llps_state_evidence", "primary_result_metric", "structured_metric",
]


def compact(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_label(value: Any, mapping: dict[str, str]) -> str:
    value = compact(value).replace("β", "beta")
    if value == "尾-carotene":
        value = "beta-carotene"
    return mapping.get(value.lower(), value)


def is_unknown(value: Any) -> bool:
    return compact(value).lower() in UNKNOWN_VALUES


def read_deepseek_key(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    match = re.search(r"DEEPSEEK_API_KEY\s*=\s*['\"]([^'\"]+)['\"]", text)
    return match.group(1).strip() if match else ""


def row_context(row: dict[str, str], max_chars: int = 5000) -> str:
    parts: list[str] = []
    for field in CONTEXT_FIELDS:
        value = compact(row.get(field, ""))
        if value and value.lower() not in UNKNOWN_VALUES:
            parts.append(f"{field}: {value}")
    for key, value in row.items():
        if key.endswith("_evidence") and key not in CONTEXT_FIELDS:
            value = compact(value)
            if value and value.lower() not in UNKNOWN_VALUES:
                parts.append(f"{key}: {value}")
    return "\n".join(parts)[:max_chars]


def first_match(text: str, patterns: list[tuple[str, str, list[str]]]) -> tuple[str, str] | None:
    for canonical, group, regexes in patterns:
        for pattern in regexes:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return canonical, group
    return None


def rule_enrich_row(row: dict[str, str]) -> dict[str, str]:
    out = dict(row)
    context = row_context(row)
    product = compact(row.get("canonical_product", ""))
    family = compact(row.get("product_family", ""))
    host = compact(row.get("canonical_host", ""))
    host_group = compact(row.get("host_group", ""))

    if is_unknown(product) or is_unknown(family):
        match = first_match(context, PRODUCT_PATTERNS)
        if match:
            inferred_product, inferred_family = match
            if is_unknown(product):
                product = inferred_product
            if is_unknown(family):
                family = inferred_family
            out["product_inference_source"] = "rule_context"
        else:
            out["product_inference_source"] = "existing" if not is_unknown(product) or not is_unknown(family) else "unresolved"
    else:
        out["product_inference_source"] = "existing"

    if is_unknown(host) or is_unknown(host_group):
        match = first_match(context, HOST_PATTERNS)
        if match:
            inferred_host, inferred_group = match
            if is_unknown(host):
                host = inferred_host
            if is_unknown(host_group):
                host_group = inferred_group
            out["host_inference_source"] = "rule_context"
        else:
            out["host_inference_source"] = "existing" if not is_unknown(host) or not is_unknown(host_group) else "unresolved"
    else:
        out["host_inference_source"] = "existing"

    out["final_canonical_product"] = normalize_label(product, {}) if not is_unknown(product) else "unknown"
    out["final_product_family"] = normalize_label(family, PRODUCT_FAMILY_NORMALIZATION) if not is_unknown(family) else "unknown"
    out["final_canonical_host"] = host if not is_unknown(host) else "unknown"
    out["final_host_group"] = normalize_label(host_group, HOST_GROUP_NORMALIZATION) if not is_unknown(host_group) else "unknown"
    out["llm_qc_status"] = "not_requested"
    out["llm_qc_confidence"] = ""
    out["llm_qc_reason"] = ""
    out["llm_qc_raw_json"] = ""
    out["needs_human_review"] = "true" if ("D_result_only" in compact(row.get("clean_level", "")) and (is_unknown(product) or is_unknown(host))) else "false"
    return out


def load_cache(path: Path) -> dict[str, dict[str, Any]]:
    cache: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return cache
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = obj.get("cache_key")
            if key:
                cache[key] = obj
    return cache


def append_cache(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def group_key(row: dict[str, str]) -> str:
    doi = compact(row.get("doi", "")).lower()
    title = compact(row.get("title_clean") or row.get("title", "")).lower()
    if doi:
        return f"doi:{doi}"
    digest = hashlib.sha1(title.encode("utf-8", errors="ignore")).hexdigest()[:16]
    return f"title:{digest}"


def build_groups(rows: list[dict[str, str]], limit: int) -> list[dict[str, Any]]:
    by_key: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        needs_product = is_unknown(row.get("final_product_family")) or is_unknown(row.get("final_canonical_product"))
        needs_host = is_unknown(row.get("final_host_group")) or is_unknown(row.get("final_canonical_host"))
        context = row_context(row)
        if (needs_product or needs_host) and len(context) >= 120:
            by_key.setdefault(group_key(row), []).append(row)

    groups: list[dict[str, Any]] = []
    for key, items in by_key.items():
        title = compact(items[0].get("title_clean") or items[0].get("title", ""))
        doi = compact(items[0].get("doi", ""))
        sample = sorted(items, key=lambda r: (compact(r.get("clean_level")) == "D_result_only", -len(row_context(r))))[:8]
        context = "\n\n".join(f"[row {i + 1}]\n{row_context(r, 1600)}" for i, r in enumerate(sample))
        score = sum(1 for r in items if compact(r.get("clean_level")) != "D_result_only") * 3 + len(items)
        groups.append({"key": key, "doi": doi, "title": title, "rows": items, "context": context[:9000], "score": score})
    groups.sort(key=lambda g: (-g["score"], g["key"]))
    return groups[:limit] if limit > 0 else groups


def llm_prompt(group: dict[str, Any]) -> str:
    return f"""
You are a careful scientific database curator for LLPS/enzyme/metabolic-engineering literature.

Infer missing article-level labels only from the provided title and evidence snippets.
Do not invent labels. If the evidence is insufficient or the article appears to contain multiple unrelated systems, return null for that field.

Allowed product_family values:
flavonoid, isoflavonoid, terpenoid, isoprenoid, stilbene, phenylpropanoid, prenylflavonoid, natural_product, llps_system, other.

Allowed host_group values:
yeast, bacteria, cyanobacteria, plant, mammalian, cell_free, other.

Return strict JSON only:
{{
  "canonical_product": string|null,
  "product_family": string|null,
  "canonical_host": string|null,
  "host_group": string|null,
  "confidence": number,
  "reason": string
}}

Rules:
- Use a concise product name such as naringenin, glabridin, lycopene, LLPS/condensate system, or null.
- Use a concise canonical host such as Saccharomyces cerevisiae, Escherichia coli, Yarrowia lipolytica, or null.
- confidence must be 0.0 to 1.0.
- Use confidence >= 0.70 only when the label is directly supported by title/evidence.
- If only "yeast" is stated, canonical_host may be "yeast" and host_group "yeast".
- If only LLPS/condensate terms are explicit and no product is explicit, canonical_product may be "LLPS/condensate system" and product_family "llps_system".

Article key: {group["key"]}
DOI: {group.get("doi", "")}
Title: {group.get("title", "")}

Evidence snippets:
{group["context"]}
""".strip()


def call_llm(api_key: str, prompt: str, model: str, api_base: str, retries: int = 5) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return JSON only. Do not include markdown fences."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    last_error = ""
    for attempt in range(retries):
        try:
            resp = requests.post(api_base, headers=headers, json=payload, timeout=90)
            if resp.status_code == 429:
                time.sleep(min(60, 2 ** attempt * 3))
                continue
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as exc:
            last_error = str(exc)
            if attempt == retries - 1:
                break
            time.sleep(min(45, 2 ** attempt * 2))
    return {"error": last_error}


def apply_llm_result(row: dict[str, str], result: dict[str, Any]) -> None:
    if result.get("error"):
        row["llm_qc_status"] = "error"
        row["llm_qc_reason"] = compact(result.get("error"))[:500]
        return

    try:
        confidence = float(result.get("confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0.0

    row["llm_qc_status"] = "accepted" if confidence >= 0.70 else "low_confidence"
    row["llm_qc_confidence"] = f"{confidence:.2f}"
    row["llm_qc_reason"] = compact(result.get("reason", ""))[:500]
    row["llm_qc_raw_json"] = json.dumps(result, ensure_ascii=False)

    if confidence < 0.70:
        row["needs_human_review"] = "true"
        return

    if is_unknown(row.get("final_canonical_product")) and not is_unknown(result.get("canonical_product")):
        row["final_canonical_product"] = normalize_label(result.get("canonical_product"), {})
        row["product_inference_source"] = "llm_article_context"
    if is_unknown(row.get("final_product_family")) and not is_unknown(result.get("product_family")):
        row["final_product_family"] = normalize_label(result.get("product_family"), PRODUCT_FAMILY_NORMALIZATION)
        row["product_inference_source"] = "llm_article_context"
    if is_unknown(row.get("final_canonical_host")) and not is_unknown(result.get("canonical_host")):
        row["final_canonical_host"] = compact(result.get("canonical_host"))
        row["host_inference_source"] = "llm_article_context"
    if is_unknown(row.get("final_host_group")) and not is_unknown(result.get("host_group")):
        row["final_host_group"] = normalize_label(result.get("host_group"), HOST_GROUP_NORMALIZATION)
        row["host_inference_source"] = "llm_article_context"
    if compact(row.get("clean_level")) == "D_result_only":
        row["needs_human_review"] = "true"


def summarize(rows: list[dict[str, str]], input_rows: list[dict[str, str]]) -> dict[str, Any]:
    def counts(field: str, data: list[dict[str, str]]) -> dict[str, int]:
        out: dict[str, int] = {}
        for row in data:
            value = compact(row.get(field, "")) or "unknown"
            out[value] = out.get(value, 0) + 1
        return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0]))[:30])

    return {
        "rows": len(rows),
        "before": {
            "product_family_unknown": sum(1 for r in input_rows if is_unknown(r.get("product_family"))),
            "host_group_unknown": sum(1 for r in input_rows if is_unknown(r.get("host_group"))),
            "canonical_product_unknown": sum(1 for r in input_rows if is_unknown(r.get("canonical_product"))),
            "canonical_host_unknown": sum(1 for r in input_rows if is_unknown(r.get("canonical_host"))),
        },
        "after": {
            "final_product_family_unknown": sum(1 for r in rows if is_unknown(r.get("final_product_family"))),
            "final_host_group_unknown": sum(1 for r in rows if is_unknown(r.get("final_host_group"))),
            "final_canonical_product_unknown": sum(1 for r in rows if is_unknown(r.get("final_canonical_product"))),
            "final_canonical_host_unknown": sum(1 for r in rows if is_unknown(r.get("final_canonical_host"))),
        },
        "final_product_family_counts": counts("final_product_family", rows),
        "final_host_group_counts": counts("final_host_group", rows),
        "final_canonical_product_counts": counts("final_canonical_product", rows),
        "final_canonical_host_counts": counts("final_canonical_host", rows),
        "product_inference_source_counts": counts("product_inference_source", rows),
        "host_inference_source_counts": counts("host_inference_source", rows),
        "llm_qc_status_counts": counts("llm_qc_status", rows),
        "needs_human_review_counts": counts("needs_human_review", rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--api-txt", type=Path, default=DEFAULT_API_TXT)
    parser.add_argument("--llm-limit", type=int, default=0, help="0 disables LLM; positive value is max article groups.")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--api-base", default="https://api.deepseek.com/v1/chat/completions")
    parser.add_argument("--model", default="deepseek-chat")
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        input_rows = [dict(row) for row in reader]
        base_fields = list(reader.fieldnames or [])

    rows = [rule_enrich_row(row) for row in input_rows]

    if args.llm_limit > 0:
        api_key = read_deepseek_key(args.api_txt)
        if not api_key:
            print("DeepSeek API key not found; writing rule-enriched output only.", file=sys.stderr)
        else:
            groups = build_groups(rows, args.llm_limit)
            cache = load_cache(args.cache)
            print(f"LLM groups selected: {len(groups)}")

            def resolve(group: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
                cache_key = hashlib.sha1((group["key"] + "\n" + group["context"]).encode("utf-8", errors="ignore")).hexdigest()
                if cache_key in cache:
                    result = cache[cache_key].get("result", {})
                    return group, result
                result = call_llm(api_key, llm_prompt(group), args.model, args.api_base)
                append_cache(args.cache, {"cache_key": cache_key, "group_key": group["key"], "result": result, "ts": time.time()})
                return group, result

            done = 0
            with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
                futures = [ex.submit(resolve, group) for group in groups]
                for future in as_completed(futures):
                    group, result = future.result()
                    for row in group["rows"]:
                        apply_llm_result(row, result)
                    done += 1
                    if done % 25 == 0 or done == len(groups):
                        print(f"LLM QC groups done: {done}/{len(groups)}")

    extra_fields = [
        "final_canonical_product", "final_product_family", "final_canonical_host", "final_host_group",
        "product_inference_source", "host_inference_source",
        "llm_qc_status", "llm_qc_confidence", "llm_qc_reason", "llm_qc_raw_json", "needs_human_review",
    ]
    fields = base_fields + [field for field in extra_fields if field not in base_fields]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    summary = summarize(rows, input_rows)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary["before"], ensure_ascii=False))
    print(json.dumps(summary["after"], ensure_ascii=False))
    print(f"Wrote: {args.output}")
    print(f"Wrote: {args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

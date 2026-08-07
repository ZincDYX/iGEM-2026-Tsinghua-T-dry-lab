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


DEFAULT_INPUT = ROOT / "essay" / "rule_c_fulltext_context.csv"
DEFAULT_OUT = ROOT / "essay" / "llm_upgraded_rule_c_with_context.csv"
DEFAULT_API_TXT = ROOT / "API.txt"


PROJECT_TERMS = {
    "glabridin": 10,
    "isoflavonoid": 8,
    "flavonoid": 7,
    "naringenin": 7,
    "taxifolin": 6,
    "quercetin": 5,
    "kaempferol": 5,
    "yeast": 7,
    "saccharomyces": 7,
    "yarrowia": 5,
    "metabolic engineering": 7,
    "heterologous": 5,
    "biosynthesis": 5,
    "isoprenoid": 5,
    "terpene": 4,
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


def safe_console(text: str, limit: int = 90) -> str:
    return str(text or "")[:limit].encode("gbk", errors="replace").decode("gbk")


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def metric_value(row: dict[str, str], metric: str) -> tuple[str, str, str]:
    return (
        compact(row.get(f"{metric}_value", "")),
        compact(row.get(f"{metric}_unit", "")),
        compact(row.get(f"{metric}_evidence", "")),
    )


def project_score(row: dict[str, str]) -> int:
    text = (row.get("title", "") + "\n" + row.get("fulltext_context", "")).lower()
    return sum(weight * min(5, text.count(term)) for term, weight in PROJECT_TERMS.items())


def read_rows(input_csv: Path, *, min_project_score: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with input_csv.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            score = project_score(row)
            row["context_project_score"] = str(score)
            if score < min_project_score:
                continue
            rows.append(row)
    rows.sort(key=lambda r: (-int(r.get("context_project_score", "0") or 0), r.get("doi", ""), r.get("rule_strict_id", "")))
    return rows


def payload(row: dict[str, str]) -> str:
    metric = compact(row.get("structured_metric", ""))
    value, unit, evidence = metric_value(row, metric)
    return "\n".join([
        f"Article DOI: {compact(row.get('doi', ''))}",
        f"Article title: {compact(row.get('title', ''))}",
        f"Original RULE_C tier: {compact(row.get('rule_strict_tier', ''))}",
        f"Structured metric hint: {metric}",
        f"Auto value/unit hint: {value} {unit}".strip(),
        f"Current product hint: {compact(row.get('main_product_name_value', ''))}",
        f"Current host hint: {compact(row.get('expression_host_value', ''))}",
        f"Current system hint: {compact(row.get('reaction_system_type_value', ''))}",
        f"Original evidence snippet: {evidence}",
        "",
        "Full-text context around the evidence:",
        compact(row.get("fulltext_context", ""))[:7000],
    ])


def build_prompt(examples: list[dict[str, Any]], row_payload: str, metrics: list[str], schema: dict[str, Any]) -> str:
    parts = [
        "You are a strict scientific data curator.",
        "Upgrade or reject a RULE_C candidate using the longer full-text context.",
        "Return JSON only as {\"records\": [<record>, ...]}.",
        "Output one or more records only if the context supports a real experimental record.",
        "A valid record may have null enzyme or substrate, but it must have explicit product or LLPS component/system and an explicit reported result value.",
        "Use the full-text context to correct broken auto value/unit hints, e.g. recover '120.3 ± 2.4 mg/L' or '10.3 mg L-1'.",
        "Discard substrate/feed/additive/media concentrations unless they are clearly the measured product titer/yield/activity/conversion/kinetic/LLPS result.",
        "For non-glabridin products, keep the real product name in main_product_name; use glabridin_titer/glabridin_yield as generic product titer/yield fields.",
        "Each metric value must be an object: {\"value\": <string_or_number|null>, \"unit\": <string|null>, \"evidence\": <string|null>}.",
        "Use null when a field is not supported. Do not hallucinate.",
        "Requested metrics: " + ", ".join(metrics),
    ]
    sp = schema_prompt(schema, metrics)
    if sp:
        parts.append(sp)
    if examples:
        parts.append("Relevant few-shot examples:")
        for ex in examples[:3]:
            inst = compact(ex.get("instruction", ""))
            if inst:
                parts.append("Instruction:\n" + inst)
            parts.append("Context:\n" + str(ex.get("context", "")))
            parts.append("Expected JSON:\n" + json.dumps({"records": [ex.get("output", {})]}, ensure_ascii=False))
    parts.append("Candidate and full-text context:\n" + row_payload)
    return "\n\n".join(parts)


def process_row(
    row: dict[str, str],
    *,
    metrics: list[str],
    examples: list[dict[str, Any]],
    schema: dict[str, Any],
    constraints: dict[str, Any],
    llm_key: str,
    llm_base: str,
    llm_model: str,
    icl_top_k: int,
) -> list[dict[str, Any]]:
    doi = compact(row.get("doi", ""))
    title = compact(row.get("title", ""))
    text = payload(row)
    selected_examples = select_icl_examples(examples, text, metrics, domain=schema.get("domain"), k=int(icl_top_k or 3))
    try:
        if not llm_key:
            return [_status_row(pii=None, doi=doi, title=title, keyword="llm_upgrade_rule_c_fulltext_context", schema=schema, selected_examples=selected_examples, status="llm_key_missing", error="llm key missing", text_chars=len(text), chunk_count=1, processed_chunks=0)]
        prompt = build_prompt(selected_examples, text, metrics, schema)
        parsed = parse_metrics_json(call_llm_openai(llm_key, llm_base, llm_model, prompt))
        records = _dedupe_records(_as_records(parsed, metrics), metrics)
        if not records:
            return [_status_row(pii=None, doi=doi, title=title, keyword="llm_upgrade_rule_c_fulltext_context", schema=schema, selected_examples=selected_examples, status="no_records", error="RULE_C not supported after fulltext context QC", text_chars=len(text), chunk_count=1, processed_chunks=1)]
        norm_maps, metric_vios, cross_vios = _normalize_records(records, metrics, constraints, schema)
        confidence = compute_confidence(metric_vios, cross_vios, 0)
        rows = _flatten_record_rows(
            records=records,
            norm_maps=norm_maps,
            metrics=metrics,
            pii=None,
            doi=doi,
            title=title,
            keyword="llm_upgrade_rule_c_fulltext_context",
            schema=schema,
            selected_examples=selected_examples,
            corrected_rounds=0,
            confidence=confidence,
            text_chars=len(text),
            chunk_count=1,
            processed_chunks=1,
        )
        for out in rows:
            out["source_rule_strict_id"] = row.get("rule_strict_id", "")
            out["source_rule_strict_tier"] = row.get("rule_strict_tier", "")
            out["source_structured_metric"] = row.get("structured_metric", "")
            out["source_clean_record_id"] = row.get("source_clean_record_id", "")
            out["context_location_method"] = row.get("context_location_method", "")
            out["context_match_score"] = row.get("context_match_score", "")
            out["context_project_score"] = row.get("context_project_score", "")
            out["normalization_source"] = "llm_upgrade_rule_c_fulltext_context"
        return rows
    except Exception as exc:
        return [_status_row(pii=None, doi=doi, title=title, keyword="llm_upgrade_rule_c_fulltext_context", schema=schema, selected_examples=selected_examples, status="error", error=f"{type(exc).__name__}: {exc}", text_chars=len(text), chunk_count=1, processed_chunks=0)]


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
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--min-project-score", type=int, default=10)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    schema = load_schema(str(args.schema))
    metrics = schema_metric_names(schema)
    constraints = schema_constraints(schema)
    examples = load_icl_examples(str(args.icl_bank))
    llm_key = args.llm_key or read_deepseek_key(args.api_txt)
    rows = read_rows(args.input, min_project_score=args.min_project_score)
    done = set() if args.no_resume else _existing_article_keys(str(args.out))
    # article_key is row-specific in this script after writing, but _existing_article_keys is DOI-level.
    # Keep resume conservative by skipping already processed DOI groups.
    rows = [r for r in rows if f"doi:{compact(r.get('doi','')).lower()}" not in done]
    if args.limit > 0:
        rows = rows[: args.limit]

    columns = _output_columns(metrics) + [
        "source_rule_strict_id",
        "source_rule_strict_tier",
        "source_structured_metric",
        "source_clean_record_id",
        "context_location_method",
        "context_match_score",
        "context_project_score",
        "normalization_source",
    ]
    lock = threading.Lock()
    written = 0
    start = time.time()
    with ThreadPoolExecutor(max_workers=max(1, int(args.workers or 1))) as pool:
        futures = [
            pool.submit(
                process_row,
                row,
                metrics=metrics,
                examples=examples,
                schema=schema,
                constraints=constraints,
                llm_key=llm_key,
                llm_base=args.llm_base,
                llm_model=args.llm_model,
                icl_top_k=args.icl_top_k,
            )
            for row in rows
        ]
        for i, future in enumerate(as_completed(futures), start=1):
            out_rows = future.result()
            # Make article_key row-specific so multiple RULE_C rows from the same DOI can be resumed later if needed.
            for out in out_rows:
                rid = out.get("source_rule_strict_id")
                if rid and out.get("article_key", "").startswith("doi:"):
                    out["article_key"] = out["article_key"] + "#rule_c:" + str(rid)
            _append_rows(str(args.out), out_rows, columns, lock)
            written += len(out_rows)
            first = out_rows[0] if out_rows else {}
            print(f"processed={i}/{len(futures)} rows={len(out_rows)} status={first.get('extraction_status')} title={safe_console(first.get('title', ''))}")
    print(f"done rows={len(rows)} written_rows={written} elapsed_sec={time.time()-start:.1f} out={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

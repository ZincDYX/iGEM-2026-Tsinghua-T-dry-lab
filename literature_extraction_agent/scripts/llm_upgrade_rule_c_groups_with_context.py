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
DEFAULT_OUT = ROOT / "essay" / "llm_upgraded_rule_c_groups_with_context.csv"
DEFAULT_API_TXT = ROOT / "API.txt"

PROJECT_TERMS = {
    "glabridin": 10, "isoflavonoid": 8, "flavonoid": 7, "naringenin": 7,
    "taxifolin": 6, "quercetin": 5, "kaempferol": 5, "yeast": 7,
    "saccharomyces": 7, "yarrowia": 5, "metabolic engineering": 7,
    "heterologous": 5, "biosynthesis": 5, "isoprenoid": 5, "terpene": 4,
    "phase separation": 8, "condensate": 8, "droplet": 5, "titer": 3,
    "yield": 2, "activity": 2,
}
METRIC_ORDER = {
    "glabridin_titer": 0, "glabridin_yield": 1, "substrate_conversion": 2,
    "enzyme_activity": 3, "specific_activity": 3, "relative_activity": 4,
    "kcat": 5, "km": 5, "critical_phase_concentration": 6, "llps_state": 6,
}


def read_deepseek_key(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    match = re.search(r"DEEPSEEK_API_KEY\s*=\s*['\"]([^'\"]+)['\"]", text)
    return match.group(1).strip() if match else ""


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def safe_console(text: str, limit: int = 90) -> str:
    return str(text or "")[:limit].encode("gbk", errors="replace").decode("gbk")


def metric_value(row: dict[str, str], metric: str) -> tuple[str, str, str]:
    return (
        compact(row.get(f"{metric}_value", "")),
        compact(row.get(f"{metric}_unit", "")),
        compact(row.get(f"{metric}_evidence", "")),
    )


def project_score_text(text: str) -> int:
    low = text.lower()
    return sum(weight * min(5, low.count(term)) for term, weight in PROJECT_TERMS.items())


def row_sort_key(row: dict[str, str]) -> tuple[int, int, str]:
    metric = compact(row.get("structured_metric", ""))
    try:
        source_score = -int(float(row.get("source_score", "0") or 0))
    except ValueError:
        source_score = 0
    return METRIC_ORDER.get(metric, 99), source_score, row.get("rule_strict_id", "")


def build_groups(input_csv: Path, *, min_project_score: int, max_rows: int) -> list[dict[str, Any]]:
    by_doi: dict[str, list[dict[str, str]]] = {}
    with input_csv.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            doi = compact(row.get("doi", "")).lower()
            if doi:
                by_doi.setdefault(doi, []).append(row)

    groups: list[dict[str, Any]] = []
    for doi, rows in by_doi.items():
        text = "\n".join([rows[0].get("title", "")] + [r.get("fulltext_context", "")[:3000] for r in rows[:20]])
        pscore = project_score_text(text)
        if pscore < min_project_score:
            continue
        rows.sort(key=row_sort_key)
        selected = rows[:max_rows]
        groups.append({
            "doi": doi,
            "title": compact(selected[0].get("title", "")),
            "rows": selected,
            "project_score": pscore,
            "source_ids": [r.get("rule_strict_id", "") for r in selected],
        })
    groups.sort(key=lambda g: (-g["project_score"], g["doi"]))
    return groups


def evidence_payload(group: dict[str, Any]) -> str:
    lines = [
        f"Article DOI: {group['doi']}",
        f"Article title: {group.get('title', '')}",
        "These are RULE_C candidate records with longer full-text context. They are incomplete or uncertain.",
        "Merge evidence across rows from the same article. Keep only true experimental records.",
        "A valid record can have null enzyme/substrate, but must have a supported product or LLPS component/system and an explicit result value.",
        "Correct broken auto values/units from the full-text context. Discard substrate/feed/additive/media concentrations.",
        "",
        "RULE_C candidates:",
    ]
    for i, row in enumerate(group["rows"], start=1):
        metric = compact(row.get("structured_metric", ""))
        value, unit, evidence = metric_value(row, metric)
        lines.append(
            f"[{i}] id={row.get('rule_strict_id')} tier={row.get('rule_strict_tier')} "
            f"metric={metric} hint_value={value} hint_unit={unit} "
            f"product_hint={compact(row.get('main_product_name_value', ''))} "
            f"host_hint={compact(row.get('expression_host_value', ''))} "
            f"context_method={row.get('context_location_method')} match={row.get('context_match_score')}\n"
            f"evidence={evidence}\n"
            f"context={compact(row.get('fulltext_context', ''))[:2600]}"
        )
    return "\n\n".join(lines)


def build_prompt(examples: list[dict[str, Any]], payload: str, metrics: list[str], schema: dict[str, Any]) -> str:
    parts = [
        "You are a strict scientific data curator.",
        "Upgrade RULE_C candidates using full-text context and output strict normalized experimental records.",
        "Return JSON only as {\"records\": [<record>, ...]}.",
        "Do not output a record unless product/host/system or LLPS component and a measured result are supported by evidence.",
        "For review tables, output records only when product/host/result are explicit; set data_source_type to table or text as supported.",
        "For non-glabridin products, keep the real product in main_product_name and use glabridin_titer/glabridin_yield as generic product result fields.",
        "Each metric value is {\"value\": <string_or_number|null>, \"unit\": <string|null>, \"evidence\": <string|null>}. Use null for unsupported fields.",
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
    parts.append("Input:\n" + payload)
    return "\n\n".join(parts)


def process_group(group: dict[str, Any], *, metrics: list[str], examples: list[dict[str, Any]], schema: dict[str, Any], constraints: dict[str, Any], llm_key: str, llm_base: str, llm_model: str, icl_top_k: int) -> list[dict[str, Any]]:
    doi = group["doi"]
    title = group.get("title", "")
    text = evidence_payload(group)
    selected_examples = select_icl_examples(examples, text, metrics, domain=schema.get("domain"), k=int(icl_top_k or 3))
    try:
        if not llm_key:
            return [_status_row(pii=None, doi=doi, title=title, keyword="llm_upgrade_rule_c_group_fulltext_context", schema=schema, selected_examples=selected_examples, status="llm_key_missing", error="llm key missing", text_chars=len(text), chunk_count=1, processed_chunks=0)]
        prompt = build_prompt(selected_examples, text, metrics, schema)
        parsed = parse_metrics_json(call_llm_openai(llm_key, llm_base, llm_model, prompt))
        records = _dedupe_records(_as_records(parsed, metrics), metrics)
        if not records:
            return [_status_row(pii=None, doi=doi, title=title, keyword="llm_upgrade_rule_c_group_fulltext_context", schema=schema, selected_examples=selected_examples, status="no_records", error="RULE_C group not supported after fulltext context QC", text_chars=len(text), chunk_count=1, processed_chunks=1)]
        norm_maps, metric_vios, cross_vios = _normalize_records(records, metrics, constraints, schema)
        confidence = compute_confidence(metric_vios, cross_vios, 0)
        rows = _flatten_record_rows(
            records=records, norm_maps=norm_maps, metrics=metrics, pii=None, doi=doi,
            title=title, keyword="llm_upgrade_rule_c_group_fulltext_context",
            schema=schema, selected_examples=selected_examples, corrected_rounds=0,
            confidence=confidence, text_chars=len(text), chunk_count=1, processed_chunks=1,
        )
        source_ids = ",".join(group.get("source_ids") or [])
        for out in rows:
            out["source_rule_strict_ids"] = source_ids
            out["source_rule_c_count"] = len(group.get("rows") or [])
            out["context_project_score"] = group.get("project_score", 0)
            out["normalization_source"] = "llm_upgrade_rule_c_group_fulltext_context"
        return rows
    except Exception as exc:
        return [_status_row(pii=None, doi=doi, title=title, keyword="llm_upgrade_rule_c_group_fulltext_context", schema=schema, selected_examples=selected_examples, status="error", error=f"{type(exc).__name__}: {exc}", text_chars=len(text), chunk_count=1, processed_chunks=0)]


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
    parser.add_argument("--max-rows-per-doi", type=int, default=18)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    schema = load_schema(str(args.schema))
    metrics = schema_metric_names(schema)
    constraints = schema_constraints(schema)
    examples = load_icl_examples(str(args.icl_bank))
    llm_key = args.llm_key or read_deepseek_key(args.api_txt)
    groups = build_groups(args.input, min_project_score=args.min_project_score, max_rows=max(3, args.max_rows_per_doi))
    done = set() if args.no_resume else _existing_article_keys(str(args.out))
    groups = [g for g in groups if f"doi:{g['doi'].lower().strip()}" not in done]
    if args.limit > 0:
        groups = groups[: args.limit]

    columns = _output_columns(metrics) + [
        "source_rule_strict_ids", "source_rule_c_count", "context_project_score", "normalization_source"
    ]
    lock = threading.Lock()
    written = 0
    start = time.time()
    with ThreadPoolExecutor(max_workers=max(1, int(args.workers or 1))) as pool:
        futures = [
            pool.submit(process_group, g, metrics=metrics, examples=examples, schema=schema, constraints=constraints, llm_key=llm_key, llm_base=args.llm_base, llm_model=args.llm_model, icl_top_k=args.icl_top_k)
            for g in groups
        ]
        for i, future in enumerate(as_completed(futures), start=1):
            out_rows = future.result()
            _append_rows(str(args.out), out_rows, columns, lock)
            written += len(out_rows)
            first = out_rows[0] if out_rows else {}
            print(f"processed={i}/{len(futures)} rows={len(out_rows)} status={first.get('extraction_status')} title={safe_console(first.get('title', ''))}")
    print(f"done groups={len(groups)} written_rows={written} elapsed_sec={time.time()-start:.1f} out={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

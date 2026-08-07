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


DEFAULT_INPUT = ROOT / "essay" / "final_structured_database_high_recall.csv"
DEFAULT_OUT = ROOT / "essay" / "llm_qc_normalized_from_high_recall_structured.csv"
DEFAULT_API_TXT = ROOT / "API.txt"

KEY_STRUCTURED_METRICS = {
    "glabridin_titer", "glabridin_yield", "substrate_conversion",
    "enzyme_activity", "specific_activity", "relative_activity",
    "kcat", "km", "critical_phase_concentration", "llps_state",
    "cell_density_od600", "reaction_system_type",
}
CONDITION_STRUCTURED_METRICS = {
    "reaction_time", "reaction_temperature", "reaction_ph",
    "substrate_concentration", "cofactor_concentration",
    "llps_salt_concentration",
}
METRIC_PRIORITY = {
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
    "cell_density_od600": 7,
    "reaction_system_type": 8,
    "reaction_time": 9,
    "reaction_temperature": 10,
    "reaction_ph": 11,
    "substrate_concentration": 12,
}
PROJECT_TERMS = {
    "glabridin": 10,
    "isoflavonoid": 8,
    "flavonoid": 7,
    "naringenin": 7,
    "liquiritigenin": 7,
    "taxifolin": 6,
    "quercetin": 5,
    "kaempferol": 5,
    "yeast": 7,
    "saccharomyces": 7,
    "yarrowia": 5,
    "metabolic engineering": 7,
    "heterologous": 5,
    "biosynthesis": 5,
    "natural product": 5,
    "isoprenoid": 5,
    "terpene": 4,
    "terpenoid": 4,
    "phase separation": 8,
    "condensate": 8,
    "droplet": 5,
    "channeling": 6,
    "scaffold": 4,
    "titer": 3,
    "yield": 2,
    "activity": 2,
}
NEGATIVE_TERMS = {
    "editorial": 12,
    "ruminant": 8,
    "goat": 8,
    "rabbit": 8,
    "obesity": 10,
    "neuropathic pain": 10,
    "rheumatoid arthritis": 8,
    "alcohol consumption": 8,
}


def read_deepseek_key(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    match = re.search(r"DEEPSEEK_API_KEY\s*=\s*['\"]([^'\"]+)['\"]", text)
    return match.group(1).strip() if match else ""


def safe_console(text: str, limit: int = 90) -> str:
    return str(text or "")[:limit].encode("gbk", errors="replace").decode("gbk")


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def field_value(row: dict[str, str], metric: str, suffix: str) -> str:
    return compact(row.get(f"{metric}_{suffix}", ""))


def row_main_value(row: dict[str, str]) -> tuple[str, str, str]:
    metric = compact(row.get("structured_metric", ""))
    return field_value(row, metric, "value"), field_value(row, metric, "unit"), field_value(row, metric, "evidence")


def row_priority(row: dict[str, str]) -> tuple[int, int]:
    metric = compact(row.get("structured_metric", ""))
    try:
        score = -int(float(row.get("source_score", "0") or 0))
    except ValueError:
        score = 0
    return METRIC_PRIORITY.get(metric, 99), score


def project_score_for(rows: list[dict[str, str]]) -> int:
    text = "\n".join(
        [compact(rows[0].get("title", ""))] +
        [row_main_value(r)[2] for r in rows[:40]]
    ).lower()
    score = 0
    for term, weight in PROJECT_TERMS.items():
        score += weight * min(5, text.count(term))
    for term, weight in NEGATIVE_TERMS.items():
        if term in text:
            score -= weight
    return score


def build_article_groups(input_csv: Path, *, max_rows: int, include_conditions: int) -> list[dict[str, Any]]:
    by_doi: dict[str, list[dict[str, str]]] = {}
    with input_csv.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("extraction_status") != "ok":
                continue
            doi = compact(row.get("doi", "")).lower()
            metric = compact(row.get("structured_metric", ""))
            if not doi or not metric:
                continue
            by_doi.setdefault(doi, []).append(row)

    groups: list[dict[str, Any]] = []
    for doi, rows in by_doi.items():
        key_rows = [r for r in rows if compact(r.get("structured_metric", "")) in KEY_STRUCTURED_METRICS]
        if not key_rows:
            continue
        condition_rows = [r for r in rows if compact(r.get("structured_metric", "")) in CONDITION_STRUCTURED_METRICS]
        key_rows.sort(key=row_priority)
        condition_rows.sort(key=row_priority)
        selected = key_rows[:max_rows]
        selected_ids = {r.get("source_clean_record_id") or r.get("article_key") for r in selected}
        for row in condition_rows[:include_conditions]:
            if len(selected) >= max_rows:
                break
            rid = row.get("source_clean_record_id") or row.get("article_key")
            if rid not in selected_ids:
                selected.append(row)
                selected_ids.add(rid)
        selected.sort(key=row_priority)
        score = project_score_for(selected)
        groups.append({
            "doi": doi,
            "title": compact(selected[0].get("title", "")),
            "rows": selected,
            "key_count": len(key_rows),
            "project_score": score,
            "source_ids": [r.get("source_clean_record_id") or r.get("article_key") for r in selected],
        })
    groups.sort(key=lambda g: (-g["project_score"], -g["key_count"], g["doi"]))
    return groups


def evidence_payload(group: dict[str, Any]) -> str:
    lines = [
        f"Article DOI: {group['doi']}",
        f"Article title: {group.get('title', '')}",
        "",
        "The rows below are high-recall structured records automatically mapped from mined PDF evidence.",
        "They may contain duplicated, fragmented, or method-only entries. Perform strict quality control.",
        "Your task: merge rows that describe the same experiment, discard irrelevant or unsupported rows, and output only true experimental records.",
        "A strict record corresponds to one enzyme/mutant/host/substrate/product/system/condition/result combination.",
        "Use the evidence snippets only. Do not invent missing enzyme, product, host, substrate, LLPS state, or result values.",
        "The auto-mapped value/unit fields may be wrong or fragmented. Treat them as hints. The original evidence text is authoritative.",
        "If evidence contains a complete result such as '120.3 ± 2.4 mg/L', '10.3 mg L-1', or multiple product titers listed in order, extract the correct main value and unit from the evidence rather than copying a broken hint.",
        "Do not return no_records when product, host/system, and a numeric result are explicit, even if enzyme or substrate is missing; put missing fields as null.",
        "For non-glabridin products, keep the real product name in main_product_name; use glabridin_titer/glabridin_yield as generic product titer/yield fields.",
        "Discard rows that only report a method condition without a linked result unless the condition is required to interpret a reported result in the same evidence set.",
        "If the article is a review, extract table-like reported experimental values only when host/product/result are explicit; otherwise return no records.",
        "",
        "Candidate high-recall structured rows:",
    ]
    for i, row in enumerate(group["rows"], start=1):
        metric = compact(row.get("structured_metric", ""))
        value, unit, evidence = row_main_value(row)
        product = field_value(row, "main_product_name", "value")
        host = field_value(row, "expression_host", "value")
        system = field_value(row, "reaction_system_type", "value")
        lines.append(
            f"[{i}] id={row.get('source_clean_record_id') or row.get('article_key')} "
            f"metric={metric} value={value} unit={unit} product={product} host={host} "
            f"system={system} quality={row.get('quality_label')} score={row.get('source_score')} "
            f"evidence={compact(evidence)[:900]}"
        )
    return "\n".join(lines)


def build_prompt(examples: list[dict[str, Any]], payload: str, metrics: list[str], schema: dict[str, Any]) -> str:
    parts = [
        "You are a strict scientific data curator.",
        "Quality-control high-recall structured extraction rows and convert them into strict normalized experimental records.",
        "Return JSON only as {\"records\": [<record>, ...]}.",
        "Each record must use flat JSON keys exactly matching the requested metric names.",
        "Each metric value must be an object: {\"value\": <string_or_number|null>, \"unit\": <string|null>, \"evidence\": <string|null>}.",
        "Never hallucinate. Use null for fields not directly supported by the evidence.",
        "Auto-mapped candidate values may be wrong. Prefer the complete numeric expression in the evidence snippet and correct obvious parsing errors.",
        "A record may still be valid when enzyme_name or substrate_name is null, if product/host/system and a reported titer, yield, activity, conversion, kinetic value, or LLPS quantity are explicit.",
        "Requested metrics: " + ", ".join(metrics),
    ]
    sp = schema_prompt(schema, metrics)
    if sp:
        parts.append(sp)
    if examples:
        instructions = []
        for ex in examples[:3]:
            inst = compact(ex.get("instruction", ""))
            if inst and inst not in instructions:
                instructions.append(inst)
        if instructions:
            parts.append("Relevant ICL task instructions:\n" + "\n".join(f"- {inst}" for inst in instructions))
        parts.append("Relevant few-shot examples:")
        for ex in examples[:3]:
            inst = compact(ex.get("instruction", ""))
            if inst:
                parts.append("Instruction:\n" + inst)
            parts.append("Context:\n" + str(ex.get("context", "")))
            parts.append("Expected JSON:\n" + json.dumps({"records": [ex.get("output", {})]}, ensure_ascii=False))
    parts.append("Input rows:\n" + payload)
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
    selected_examples = select_icl_examples(
        examples,
        payload,
        metrics,
        domain=schema.get("domain"),
        k=int(icl_top_k or 3),
    )
    try:
        if not llm_api_key:
            return [_status_row(pii=None, doi=doi, title=title, keyword="llm_qc_high_recall_structured", schema=schema, selected_examples=selected_examples, status="llm_key_missing", error="llm key missing", text_chars=len(payload), chunk_count=1, processed_chunks=0)]
        prompt = build_prompt(selected_examples, payload, metrics, schema)
        parsed = parse_metrics_json(call_llm_openai(llm_api_key, llm_base, llm_model, prompt))
        records = _dedupe_records(_as_records(parsed, metrics), metrics)
        if not records:
            return [_status_row(pii=None, doi=doi, title=title, keyword="llm_qc_high_recall_structured", schema=schema, selected_examples=selected_examples, status="no_records", error="LLM QC returned no strict records", text_chars=len(payload), chunk_count=1, processed_chunks=1)]
        norm_maps, metric_vios, cross_vios = _normalize_records(records, metrics, constraints, schema)
        confidence = compute_confidence(metric_vios, cross_vios, 0)
        rows = _flatten_record_rows(
            records=records,
            norm_maps=norm_maps,
            metrics=metrics,
            pii=None,
            doi=doi,
            title=title,
            keyword="llm_qc_high_recall_structured",
            schema=schema,
            selected_examples=selected_examples,
            corrected_rounds=0,
            confidence=confidence,
            text_chars=len(payload),
            chunk_count=1,
            processed_chunks=1,
        )
        source_ids = ",".join(group.get("source_ids") or [])
        for row in rows:
            row["source_high_recall_record_ids"] = source_ids
            row["source_high_recall_count"] = len(group.get("rows") or [])
            row["normalization_source"] = "llm_qc_high_recall_structured"
            row["project_score"] = group.get("project_score", 0)
        return rows
    except Exception as exc:
        return [_status_row(pii=None, doi=doi, title=title, keyword="llm_qc_high_recall_structured", schema=schema, selected_examples=selected_examples, status="error", error=f"{type(exc).__name__}: {exc}", text_chars=len(payload), chunk_count=1, processed_chunks=0)]


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
    parser.add_argument("--max-rows", type=int, default=24)
    parser.add_argument("--include-conditions", type=int, default=8)
    parser.add_argument("--min-project-score", type=int, default=0)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    schema = load_schema(str(args.schema))
    metrics = schema_metric_names(schema)
    constraints = schema_constraints(schema)
    examples = load_icl_examples(str(args.icl_bank))
    llm_key = args.llm_key or read_deepseek_key(args.api_txt)
    groups = build_article_groups(args.input, max_rows=max(4, args.max_rows), include_conditions=max(0, args.include_conditions))
    groups = [g for g in groups if int(g.get("project_score", 0)) >= args.min_project_score]
    done = set() if args.no_resume else _existing_article_keys(str(args.out))
    groups = [g for g in groups if f"doi:{g['doi'].lower().strip()}" not in done]
    if args.limit > 0:
        groups = groups[: args.limit]

    columns = _output_columns(metrics) + [
        "source_high_recall_record_ids",
        "source_high_recall_count",
        "normalization_source",
        "project_score",
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
            print(f"processed={i}/{len(futures)} rows={len(out_rows)} status={first.get('extraction_status')} title={safe_console(first.get('title', ''))}")
    print(f"done groups={len(groups)} written_rows={written} elapsed_sec={time.time()-start:.1f} out={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

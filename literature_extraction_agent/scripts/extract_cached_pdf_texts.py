from __future__ import annotations

import argparse
import csv
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
    build_prompt,
    call_llm_openai,
    chunk_text,
    load_icl_examples,
    parse_metrics_json,
)
from CatalystOptimizationSystem.core.icl_selector import select_icl_examples
from CatalystOptimizationSystem.core.schema_config import load_schema, schema_constraints, schema_metric_names
from CatalystOptimizationSystem.utils.config import DEFAULT_ICL_BANK, DEFAULT_LLM_BASE, DEFAULT_LLM_MODEL, DEFAULT_SCHEMA_JSON


DEFAULT_TEXT_MANIFEST = ROOT / "essay" / "pdf_text_cache_20000_direct_manifest.csv"
DEFAULT_OUT = ROOT / "essay" / "pdf_extraction_20000_direct.csv"
DEFAULT_API_TXT = ROOT / "API.txt"


def read_deepseek_key(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"DEEPSEEK_API_KEY\s*=\s*['\"]([^'\"]+)['\"]", text)
    return match.group(1).strip() if match else ""


def safe_console(text: str, limit: int = 80) -> str:
    text = str(text or "")[:limit]
    return text.encode("gbk", errors="replace").decode("gbk")


def process_text_row(
    row: dict[str, str],
    *,
    metrics: list[str],
    examples: list[dict[str, Any]],
    schema: dict[str, Any] | None,
    constraints: dict[str, Any],
    llm_api_key: str,
    llm_base: str,
    llm_model: str,
    icl_top_k: int,
    chunk_chars: int,
    chunk_overlap: int,
    max_chunks: int,
) -> list[dict[str, Any]]:
    doi = row.get("doi", "")
    title = row.get("title", "")
    keyword = "local_pdf_20000_direct"
    pii = None
    text_file = row.get("text_file", "")
    selected_examples: list[dict[str, Any]] = []
    try:
        text = Path(text_file).read_text(encoding="utf-8", errors="ignore")
        if not text.strip():
            return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, status="empty_text", error="cached PDF text is empty")]
        chunks = chunk_text(text, max_chars=chunk_chars, overlap=chunk_overlap, max_chunks=max_chunks)
        if not chunks:
            return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, status="empty_text", error="chunking returned empty", text_chars=len(text))]
        if not llm_api_key:
            return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, status="llm_key_missing", error="DeepSeek key not found", text_chars=len(text), chunk_count=len(chunks))]

        records: list[dict[str, Any]] = []
        selected_by_id: dict[str, dict[str, Any]] = {}
        corrected_rounds = 0
        processed_chunks = 0
        for chunk_index, chunk in enumerate(chunks, start=1):
            chunk_examples = select_icl_examples(
                examples,
                chunk,
                metrics,
                domain=(schema or {}).get("domain"),
                k=int(icl_top_k or 3),
            )
            for example in chunk_examples:
                selected_by_id[str(example.get("id", ""))] = example
            prompt = build_prompt(chunk_examples, chunk, metrics, schema=schema)
            parsed = parse_metrics_json(call_llm_openai(llm_api_key, llm_base, llm_model, prompt))
            chunk_records = _as_records(parsed, metrics)
            processed_chunks += 1
            if not chunk_records:
                continue

            norm_maps, metric_vios, cross_vios = _normalize_records(chunk_records, metrics, constraints, schema)
            if metric_vios or cross_vios:
                err_text = "\n".join(metric_vios + cross_vios)[:1500]
                corr_prompt = prompt + "\n\nThe previous extraction violated validation rules:\n" + err_text + "\nReturn corrected JSON only in the same {\"records\": [...]} format."
                parsed2 = parse_metrics_json(call_llm_openai(llm_api_key, llm_base, llm_model, corr_prompt))
                records2 = _as_records(parsed2, metrics)
                if records2:
                    chunk_records = records2
                    corrected_rounds += 1
            records.extend(chunk_records)

        selected_examples = list(selected_by_id.values())
        records = _dedupe_records(records, metrics)
        if not records:
            return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, selected_examples=selected_examples, status="no_records", error="LLM returned no records", text_chars=len(text), chunk_count=len(chunks), processed_chunks=processed_chunks)]

        norm_maps, metric_vios, cross_vios = _normalize_records(records, metrics, constraints, schema)
        confidence = compute_confidence(metric_vios, cross_vios, corrected_rounds)
        return _flatten_record_rows(
            records=records,
            norm_maps=norm_maps,
            metrics=metrics,
            pii=pii,
            doi=doi,
            title=title,
            keyword=keyword,
            schema=schema,
            selected_examples=selected_examples,
            corrected_rounds=corrected_rounds,
            confidence=confidence,
            text_chars=len(text),
            chunk_count=len(chunks),
            processed_chunks=processed_chunks,
        )
    except Exception as exc:
        return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, selected_examples=selected_examples, status="error", error=f"{type(exc).__name__}: {exc}")]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-manifest", type=Path, default=DEFAULT_TEXT_MANIFEST)
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
    parser.add_argument("--chunk-chars", type=int, default=14000)
    parser.add_argument("--chunk-overlap", type=int, default=1000)
    parser.add_argument("--max-chunks", type=int, default=4)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    schema = load_schema(str(args.schema))
    metrics = schema_metric_names(schema)
    constraints = schema_constraints(schema)
    examples = load_icl_examples(str(args.icl_bank))
    llm_key = args.llm_key or read_deepseek_key(args.api_txt)

    with args.text_manifest.open("r", encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("status") == "cached" and r.get("text_file")]
    unique_rows: list[dict[str, str]] = []
    seen_inputs: set[str] = set()
    for row in rows:
        key = (row.get("doi") or row.get("file_path") or row.get("text_file") or "").lower().strip()
        if not key or key in seen_inputs:
            continue
        seen_inputs.add(key)
        unique_rows.append(row)
    rows = unique_rows

    done = set() if args.no_resume else _existing_article_keys(str(args.out))
    rows = [r for r in rows if f"doi:{r.get('doi','').lower().strip()}" not in done]
    if args.limit > 0:
        rows = rows[: args.limit]

    columns = _output_columns(metrics)
    lock = threading.Lock()
    max_workers = max(1, int(args.workers or 1))
    start = time.time()
    written = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [
            pool.submit(
                process_text_row,
                row,
                metrics=metrics,
                examples=examples,
                schema=schema,
                constraints=constraints,
                llm_api_key=llm_key,
                llm_base=args.llm_base,
                llm_model=args.llm_model,
                icl_top_k=args.icl_top_k,
                chunk_chars=args.chunk_chars,
                chunk_overlap=args.chunk_overlap,
                max_chunks=args.max_chunks,
            )
            for row in rows
        ]
        for i, future in enumerate(as_completed(futures), start=1):
            out_rows = future.result()
            _append_rows(str(args.out), out_rows, columns, lock)
            written += len(out_rows)
            first = out_rows[0] if out_rows else {}
            print(f"processed={i}/{len(futures)} rows={len(out_rows)} status={first.get('extraction_status')} title={safe_console(first.get('title', ''))}")
    print(f"done papers={len(rows)} written_rows={written} elapsed_sec={time.time()-start:.1f} out={args.out}")


if __name__ == "__main__":
    main()

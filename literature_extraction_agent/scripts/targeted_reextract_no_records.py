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
DEFAULT_RESOLVED = ROOT / "essay" / "pdf_extraction_20000_direct_resolved.csv"
DEFAULT_OUT = ROOT / "essay" / "pdf_extraction_20000_targeted_no_records.csv"
DEFAULT_API_TXT = ROOT / "API.txt"


SIGNAL_TERMS = {
    "strong_result": [
        "mg/l", "g/l", "mg l", "g l", "titer", "titre", "yield", "production",
        "produced", "conversion", "productivity", "specific activity", "u/mg",
        "kcat", "km", "vmax", "fold", "relative activity", "enzyme activity",
    ],
    "condition": [
        "ph ", "°c", "degc", "temperature", "substrate concentration",
        "incubated", "reaction mixture", "fermentation", "bioreactor",
        "shake flask", "od600", "iptg", "induction",
    ],
    "host_pathway": [
        "saccharomyces", "yeast", "e. coli", "escherichia", "bacillus",
        "pichia", "yarrowia", "streptomyces", "engineered", "heterologous",
        "strain", "plasmid", "pathway", "biosynthesis",
    ],
    "table_figure": [
        "table ", "fig.", "figure ", "supplementary table", "supplementary fig",
        "supplementary data", "dataset",
    ],
    "domain": [
        "flavonoid", "isoflavonoid", "glabridin", "naringenin", "terpene",
        "terpenoid", "isoprenoid", "carotenoid", "pterocarpan", "coumarin",
        "stilbene", "phase separation", "condensate", "droplet", "puncta",
        "foci", "inclusion body", "enzyme scaffold", "channeling",
    ],
}

REVIEW_TITLE_TERMS = [
    "review", "progress", "advances", "prospects", "perspective", "outlook",
    "status", "trends", "strategies", "frontiers", "recent advances",
]


def read_deepseek_key(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    match = re.search(r"DEEPSEEK_API_KEY\s*=\s*['\"]([^'\"]+)['\"]", text)
    return match.group(1).strip() if match else ""


def safe_console(text: str, limit: int = 80) -> str:
    return str(text or "")[:limit].encode("gbk", errors="replace").decode("gbk")


def chunk_score(text: str) -> int:
    low = text.lower()
    score = 0
    weights = {
        "strong_result": 5,
        "condition": 2,
        "host_pathway": 2,
        "table_figure": 3,
        "domain": 3,
    }
    for group, terms in SIGNAL_TERMS.items():
        for term in terms:
            if term in low:
                score += weights[group] * min(4, low.count(term))
    # Reward chunks that contain both numeric values and biological production terms.
    score += min(10, len(re.findall(r"\b\d+(?:\.\d+)?\s*(?:mg/l|g/l|mm|µm|um|%|fold|h|°c)\b", low)))
    return score


def select_target_chunks(text: str, *, chunk_chars: int, chunk_overlap: int, max_chunks: int) -> list[str]:
    chunks = chunk_text(text, max_chars=chunk_chars, overlap=chunk_overlap, max_chunks=10_000)
    scored = []
    for idx, chunk in enumerate(chunks):
        score = chunk_score(chunk)
        if score > 0:
            scored.append((score, idx, chunk))
    if not scored:
        return chunks[:max_chunks]
    scored.sort(key=lambda item: (-item[0], item[1]))
    chosen = sorted(scored[:max_chunks], key=lambda item: item[1])
    return [f"[Targeted chunk {idx + 1}; signal_score={score}]\n{chunk}" for score, idx, chunk in chosen]


def build_no_record_targets(resolved_csv: Path, text_manifest: Path, *, include_reviews: bool) -> list[dict[str, str]]:
    with resolved_csv.open("r", encoding="utf-8-sig", newline="") as f:
        resolved_rows = list(csv.DictReader(f))
    no_dois = {r.get("doi", "").lower().strip() for r in resolved_rows if r.get("extraction_status") == "no_records" and r.get("doi")}
    with text_manifest.open("r", encoding="utf-8-sig", newline="") as f:
        text_rows = [r for r in csv.DictReader(f) if r.get("status") == "cached" and r.get("text_file")]
    targets = []
    seen = set()
    for row in text_rows:
        doi = row.get("doi", "").lower().strip()
        if not doi or doi not in no_dois or doi in seen:
            continue
        seen.add(doi)
        title = (row.get("title") or "").lower()
        if not include_reviews and any(term in title for term in REVIEW_TITLE_TERMS):
            continue
        targets.append(row)
    return targets


def target_signal_score(row: dict[str, str]) -> int:
    try:
        text = Path(row.get("text_file", "")).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return 0
    chunks = chunk_text(text, max_chars=12000, overlap=1000, max_chunks=10_000)
    best = max((chunk_score(chunk) for chunk in chunks), default=0)
    title = (row.get("title") or "").lower()
    if any(term in title for term in ["biosynthesis", "metabolic engineering", "engineered", "heterologous", "enzyme", "activity", "production"]):
        best += 15
    if any(term in title for term in ["flavonoid", "isoprenoid", "terpene", "carotenoid", "yeast", "saccharomyces", "e. coli", "bacillus", "pichia", "yarrowia"]):
        best += 10
    return best


def process_target(
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
    keyword = "targeted_no_records_reextract"
    pii = None
    selected_examples: list[dict[str, Any]] = []
    try:
        text = Path(row.get("text_file", "")).read_text(encoding="utf-8", errors="ignore")
        chunks = select_target_chunks(text, chunk_chars=chunk_chars, chunk_overlap=chunk_overlap, max_chunks=max_chunks)
        if not chunks:
            return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, status="empty_text", error="targeted chunks empty", text_chars=len(text))]
        records: list[dict[str, Any]] = []
        selected_by_id: dict[str, dict[str, Any]] = {}
        corrected_rounds = 0
        processed_chunks = 0
        for chunk in chunks:
            chunk = (
                "The following excerpt was selected from later Results/Tables/Supplementary-like parts of a paper "
                "that was previously missed by front-of-PDF extraction. Extract concrete experimental records with numeric evidence only.\n\n"
                + chunk
            )
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
            return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, selected_examples=selected_examples, status="no_records", error="targeted re-extraction found no records", text_chars=len(text), chunk_count=len(chunks), processed_chunks=processed_chunks)]
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
    parser.add_argument("--resolved", type=Path, default=DEFAULT_RESOLVED)
    parser.add_argument("--text-manifest", type=Path, default=DEFAULT_TEXT_MANIFEST)
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
    parser.add_argument("--chunk-chars", type=int, default=12000)
    parser.add_argument("--chunk-overlap", type=int, default=1000)
    parser.add_argument("--max-chunks", type=int, default=4)
    parser.add_argument("--include-reviews", action="store_true")
    parser.add_argument("--no-sort-by-signal", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    schema = load_schema(str(args.schema))
    metrics = schema_metric_names(schema)
    constraints = schema_constraints(schema)
    examples = load_icl_examples(str(args.icl_bank))
    llm_key = args.llm_key or read_deepseek_key(args.api_txt)

    rows = build_no_record_targets(args.resolved, args.text_manifest, include_reviews=args.include_reviews)
    if not args.no_sort_by_signal:
        scored_rows = [(target_signal_score(row), row) for row in rows]
        scored_rows.sort(key=lambda item: item[0], reverse=True)
        rows = [row for score, row in scored_rows if score > 0]
    done = set() if args.no_resume else _existing_article_keys(str(args.out))
    rows = [r for r in rows if f"doi:{r.get('doi','').lower().strip()}" not in done]
    if args.limit > 0:
        rows = rows[: args.limit]

    columns = _output_columns(metrics)
    lock = threading.Lock()
    start = time.time()
    written = 0
    with ThreadPoolExecutor(max_workers=max(1, int(args.workers or 1))) as pool:
        futures = [
            pool.submit(
                process_target,
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

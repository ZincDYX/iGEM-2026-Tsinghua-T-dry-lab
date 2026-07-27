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


DEFAULT_AUGMENTED = ROOT / "essay" / "pdf_extraction_20000_direct_augmented_targeted.csv"
DEFAULT_TEXT_MANIFEST = ROOT / "essay" / "pdf_text_cache_20000_direct_manifest.csv"
DEFAULT_OUT = ROOT / "essay" / "pdf_extraction_20000_record_papers_expanded.csv"
DEFAULT_API_TXT = ROOT / "API.txt"


SIGNALS = [
    "mg/l", "g/l", "titer", "titre", "yield", "production", "produced",
    "conversion", "productivity", "specific activity", "enzyme activity",
    "u/mg", "kcat", "km", "vmax", "fold", "relative activity", "table ",
    "fig.", "figure ", "supplementary table", "saccharomyces", "yeast",
    "e. coli", "escherichia", "bacillus", "pichia", "yarrowia", "strain",
    "engineered", "heterologous", "fermentation", "bioreactor", "pathway",
    "flavonoid", "isoflavonoid", "terpene", "terpenoid", "isoprenoid",
    "carotenoid", "naringenin", "glabridin", "phase separation",
    "condensate", "droplet", "scaffold", "channeling",
]


def read_deepseek_key(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    match = re.search(r"DEEPSEEK_API_KEY\s*=\s*['\"]([^'\"]+)['\"]", text)
    return match.group(1).strip() if match else ""


def safe_console(text: str, limit: int = 80) -> str:
    return str(text or "")[:limit].encode("gbk", errors="replace").decode("gbk")


def score_chunk(chunk: str) -> int:
    low = chunk.lower()
    score = 0
    for term in SIGNALS:
        if term in low:
            score += min(5, low.count(term))
    score += min(20, len(re.findall(r"\b\d+(?:\.\d+)?\s*(?:mg/l|g/l|mm|µm|um|%|fold|h|°c)\b", low)))
    return score


def select_chunks(text: str, *, chunk_chars: int, chunk_overlap: int, max_chunks: int) -> list[str]:
    chunks = chunk_text(text, max_chars=chunk_chars, overlap=chunk_overlap, max_chunks=10_000)
    scored = [(score_chunk(chunk), idx, chunk) for idx, chunk in enumerate(chunks)]
    scored = [item for item in scored if item[0] > 0]
    if not scored:
        return chunks[:max_chunks]
    scored.sort(key=lambda item: (-item[0], item[1]))
    # Preserve local order after selecting high-signal chunks.
    selected = sorted(scored[:max_chunks], key=lambda item: item[1])
    return [f"[Expanded record-paper chunk {idx + 1}; signal_score={score}]\n{chunk}" for score, idx, chunk in selected]


def build_targets(augmented_csv: Path, text_manifest: Path) -> list[dict[str, str]]:
    with augmented_csv.open("r", encoding="utf-8-sig", newline="") as f:
        aug_rows = list(csv.DictReader(f))
    ok_dois = {r.get("doi", "").lower().strip() for r in aug_rows if r.get("extraction_status") == "ok" and r.get("doi")}
    with text_manifest.open("r", encoding="utf-8-sig", newline="") as f:
        text_rows = [r for r in csv.DictReader(f) if r.get("status") == "cached" and r.get("text_file")]
    out = []
    seen = set()
    for row in text_rows:
        doi = row.get("doi", "").lower().strip()
        if doi and doi in ok_dois and doi not in seen:
            seen.add(doi)
            out.append(row)
    return out


def process_row(row: dict[str, str], *, metrics: list[str], examples: list[dict[str, Any]],
                schema: dict[str, Any] | None, constraints: dict[str, Any], llm_api_key: str,
                llm_base: str, llm_model: str, icl_top_k: int, chunk_chars: int,
                chunk_overlap: int, max_chunks: int) -> list[dict[str, Any]]:
    doi = row.get("doi", "")
    title = row.get("title", "")
    keyword = "expanded_record_papers_reextract"
    pii = None
    selected_examples: list[dict[str, Any]] = []
    try:
        text = Path(row.get("text_file", "")).read_text(encoding="utf-8", errors="ignore")
        chunks = select_chunks(text, chunk_chars=chunk_chars, chunk_overlap=chunk_overlap, max_chunks=max_chunks)
        if not chunks:
            return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, status="empty_text", error="expanded chunks empty", text_chars=len(text))]
        records: list[dict[str, Any]] = []
        selected_by_id: dict[str, dict[str, Any]] = {}
        corrected_rounds = 0
        processed_chunks = 0
        for chunk in chunks:
            chunk = (
                "This paper already yielded at least one record in a previous conservative pass. "
                "Now extract additional concrete experimental records from this high-signal excerpt. "
                "Split every enzyme/mutant/strain/substrate/condition/result row into a separate record. "
                "Do not summarize multiple rows into one.\n\n" + chunk
            )
            chunk_examples = select_icl_examples(examples, chunk, metrics, domain=(schema or {}).get("domain"), k=int(icl_top_k or 3))
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
            return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, selected_examples=selected_examples, status="no_records", error="expanded re-extraction found no records", text_chars=len(text), chunk_count=len(chunks), processed_chunks=processed_chunks)]
        norm_maps, metric_vios, cross_vios = _normalize_records(records, metrics, constraints, schema)
        confidence = compute_confidence(metric_vios, cross_vios, corrected_rounds)
        return _flatten_record_rows(
            records=records, norm_maps=norm_maps, metrics=metrics, pii=pii, doi=doi,
            title=title, keyword=keyword, schema=schema, selected_examples=selected_examples,
            corrected_rounds=corrected_rounds, confidence=confidence, text_chars=len(text),
            chunk_count=len(chunks), processed_chunks=processed_chunks,
        )
    except Exception as exc:
        return [_status_row(pii=pii, doi=doi, title=title, keyword=keyword, schema=schema, selected_examples=selected_examples, status="error", error=f"{type(exc).__name__}: {exc}")]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--augmented", type=Path, default=DEFAULT_AUGMENTED)
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
    parser.add_argument("--max-chunks", type=int, default=8)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    schema = load_schema(str(args.schema))
    metrics = schema_metric_names(schema)
    constraints = schema_constraints(schema)
    examples = load_icl_examples(str(args.icl_bank))
    llm_key = args.llm_key or read_deepseek_key(args.api_txt)
    rows = build_targets(args.augmented, args.text_manifest)
    done = set() if args.no_resume else _existing_article_keys(str(args.out))
    rows = [r for r in rows if f"doi:{r.get('doi','').lower().strip()}" not in done]
    if args.limit > 0:
        rows = rows[: args.limit]

    columns = _output_columns(metrics)
    lock = threading.Lock()
    written = 0
    start = time.time()
    with ThreadPoolExecutor(max_workers=max(1, int(args.workers or 1))) as pool:
        futures = [
            pool.submit(
                process_row, row, metrics=metrics, examples=examples, schema=schema,
                constraints=constraints, llm_api_key=llm_key, llm_base=args.llm_base,
                llm_model=args.llm_model, icl_top_k=args.icl_top_k,
                chunk_chars=args.chunk_chars, chunk_overlap=args.chunk_overlap,
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

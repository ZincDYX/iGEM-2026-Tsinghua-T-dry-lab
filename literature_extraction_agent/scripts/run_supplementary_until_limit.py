from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ESSAY = ROOT / "essay"
SUP = ESSAY / "supplementary_current"


def run(cmd: list[str], label: str) -> None:
    print(f"\n=== {label} ===", flush=True)
    print(" ".join(str(x) for x in cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def write_excel_friendly() -> None:
    src = ESSAY / "optimized_core_experimental_database_with_supplementary.csv"
    out = ESSAY / "optimized_core_experimental_database_with_supplementary_excel_friendly.csv"
    cols = [
        "database_tier", "project_relevance_score", "aggregate_record_id", "doi", "title",
        "product_family", "canonical_host", "host_group",
        "primary_result_metric", "primary_result_value", "primary_result_unit",
        "primary_result_numeric", "primary_result_numeric_min", "primary_result_numeric_max",
        "primary_result_numeric_qualifier", "primary_result_numeric_normalized", "primary_result_unit_normalized",
        "clean_level", "aggregation_quality", "source_mode", "source_row_count",
        "enzyme_name_value", "enzyme_mutant_value", "enzyme_source_species_value",
        "expression_host_value", "product_name_value", "substrate_name_value",
        "reaction_system_type_value", "primary_result_evidence",
    ]
    rows: list[dict[str, str]] = []
    with src.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({col: row.get(col, "") for col in cols})
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"excel_friendly": str(out), "rows": len(rows), "cols": len(cols)}, ensure_ascii=False), flush=True)


def final_database_steps(py: str) -> None:
    run([
        py, "scripts/clean_numeric_evidence_database.py",
        "--input", "essay/supplementary_current/high_recall_numeric_evidence_supplementary_current.csv",
        "--out", "essay/supplementary_current/clean_numeric_evidence_supplementary_current.csv",
        "--excluded", "essay/supplementary_current/clean_numeric_evidence_supplementary_current_excluded.csv",
        "--summary", "essay/supplementary_current/clean_numeric_evidence_supplementary_current_summary.json",
    ], "clean SI/data numeric evidence")
    run([
        py, "scripts/build_high_recall_structured_database.py",
        "--input", "essay/supplementary_current/clean_numeric_evidence_supplementary_current.csv",
        "--out", "essay/supplementary_current/high_recall_structured_supplementary_current.csv",
        "--summary", "essay/supplementary_current/high_recall_structured_supplementary_current_summary.json",
        "--min-score", "8",
    ], "build structured SI/data database")
    run([
        py, "scripts/aggregate_structured_records.py",
        "--input", "essay/supplementary_current/high_recall_structured_supplementary_current.csv",
        "--out", "essay/supplementary_current/aggregated_supplementary_current_database.csv",
        "--long-out", "essay/supplementary_current/aggregated_supplementary_current_database_long.csv",
        "--excluded", "essay/supplementary_current/aggregated_supplementary_current_excluded.csv",
        "--summary", "essay/supplementary_current/aggregated_supplementary_current_summary.json",
    ], "aggregate SI/data structured records")
    run([
        py, "scripts/merge_aggregated_databases.py",
        "--inputs",
        "essay/aggregated_analysis_ready_database_with_d_completion.csv",
        "essay/supplementary_current/aggregated_supplementary_current_database.csv",
        "--out", "essay/aggregated_analysis_ready_database_with_supplementary.csv",
        "--summary", "essay/aggregated_analysis_ready_database_with_supplementary_summary.json",
    ], "merge SI/data records into analysis database")
    run([
        py, "scripts/optimize_experimental_database.py",
        "--input", "essay/aggregated_analysis_ready_database_with_supplementary.csv",
        "--out", "essay/optimized_experimental_database_with_supplementary.csv",
        "--core-out", "essay/optimized_core_experimental_database_with_supplementary.csv",
        "--review-out", "essay/optimized_review_queue_with_supplementary.csv",
        "--long-out", "essay/optimized_experimental_database_with_supplementary_long.csv",
        "--summary", "essay/optimized_experimental_database_with_supplementary_summary.json",
    ], "optimize final database")
    write_excel_friendly()


def run_limit(py: str, cache_py: str, limit: int, *, workers: int) -> None:
    run([
        py, "scripts/download_supplementary_for_current_database.py",
        "--input", "essay/final_structured_database_after_elsevier_pdf_expansion.csv",
        "--candidate-csv", "outputs/candidate_literature_50000_year_slices_full.csv",
        "--manifest", "essay/supplementary_current/supplementary_current_download_manifest.csv",
        "--summary", "essay/supplementary_current/supplementary_current_download_summary.json",
        "--out-dir", "essay/supplementary_current",
        "--workers", str(workers),
        "--max-urls-per-doi", "12",
        "--batch-dois", "50",
        "--limit-dois", str(limit),
    ], f"download SI/data through first {limit} DOI")
    run([
        cache_py, "scripts/cache_supplementary_texts.py",
        "--manifest", "essay/supplementary_current/supplementary_current_download_manifest.csv",
        "--cache-dir", "essay/supplementary_current/text_cache",
        "--out", "essay/supplementary_current/supplementary_current_text_manifest.csv",
        "--summary", "essay/supplementary_current/supplementary_current_text_summary.json",
        "--workers", "4",
        "--max-rows-per-table", "300",
        "--max-text-chars", "220000",
    ], f"cache newly downloaded SI/data text through first {limit} DOI")
    run([
        py, "scripts/mine_numeric_evidence_records.py",
        "--manifest", "essay/supplementary_current/supplementary_current_text_manifest.csv",
        "--out", "essay/supplementary_current/high_recall_numeric_evidence_supplementary_current.csv",
        "--summary", "essay/supplementary_current/high_recall_numeric_evidence_supplementary_current_summary.json",
        "--max-per-paper", "60",
        "--max-contexts-per-paper", "700",
        "--target-rows", "100000",
    ], f"mine numeric evidence through first {limit} DOI")


def parse_limits(text: str) -> list[int]:
    return [int(x.strip()) for x in text.split(",") if x.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limits", default="2500,3000,3500,4000,4500,5000,5275")
    parser.add_argument("--cache-python", required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--final-each-limit", action="store_true")
    args = parser.parse_args()

    py = sys.executable
    cache_py = str(Path(args.cache_python))
    for limit in parse_limits(args.limits):
        run_limit(py, cache_py, limit, workers=args.workers)
        if args.final_each_limit:
            final_database_steps(py)
    if not args.final_each_limit:
        final_database_steps(py)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

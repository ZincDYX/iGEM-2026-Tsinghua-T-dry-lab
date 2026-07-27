from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUTS = [
    ROOT / "essay" / "aggregated_analysis_ready_database_with_d_completion.csv",
    ROOT / "essay" / "supplementary_current" / "aggregated_supplementary_current_database.csv",
]
DEFAULT_OUT = ROOT / "essay" / "aggregated_analysis_ready_database_with_supplementary.csv"
DEFAULT_SUMMARY = ROOT / "essay" / "aggregated_analysis_ready_database_with_supplementary_summary.json"


def norm(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def record_key(row: dict[str, str]) -> str:
    parts = [
        norm(row.get("doi", "")),
        norm(row.get("title", ""))[:120],
        norm(row.get("primary_result_metric", "")),
        norm(row.get("primary_result_value", "")),
        norm(row.get("primary_result_unit", "")),
        norm(row.get("primary_result_evidence", ""))[:280],
    ]
    return hashlib.sha1("|".join(parts).encode("utf-8", errors="ignore")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()

    fieldnames: list[str] = []
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    source_counts: dict[str, int] = {}
    duplicates = 0
    for path in args.inputs:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for field in reader.fieldnames or []:
                if field not in fieldnames:
                    fieldnames.append(field)
            for row in reader:
                source_counts[str(path)] = source_counts.get(str(path), 0) + 1
                key = record_key(row)
                if key in seen:
                    duplicates += 1
                    continue
                seen.add(key)
                rows.append(row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    doi_set: set[str] = set()
    by_level: dict[str, int] = {}
    by_metric: dict[str, int] = {}
    for row in rows:
        doi = norm(row.get("doi", ""))
        if doi:
            doi_set.add(doi)
        by_level[row.get("clean_level", "")] = by_level.get(row.get("clean_level", ""), 0) + 1
        by_metric[row.get("primary_result_metric", "")] = by_metric.get(row.get("primary_result_metric", ""), 0) + 1

    summary = {
        "input_rows": source_counts,
        "merged_rows": len(rows),
        "duplicates_removed": duplicates,
        "unique_dois": len(doi_set),
        "by_clean_level": dict(sorted(by_level.items())),
        "by_primary_result_metric": dict(sorted(by_metric.items())),
        "output": str(args.out),
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

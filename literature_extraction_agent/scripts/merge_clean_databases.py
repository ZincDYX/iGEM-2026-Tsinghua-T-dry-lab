from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUTS = [
    ROOT / "essay" / "final_clean_database_10000.csv",
    ROOT / "essay" / "final_clean_database_remaining.csv",
]
DEFAULT_OUT = ROOT / "essay" / "final_clean_database_all_pdfs.csv"
DEFAULT_SUMMARY = ROOT / "essay" / "final_clean_database_all_pdfs_summary.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    fieldnames: list[str] = []
    seen: set[str] = set()
    duplicates = 0
    source_counts: dict[str, int] = {}
    for path in args.inputs:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for field in reader.fieldnames or []:
                if field not in fieldnames:
                    fieldnames.append(field)
            for row in reader:
                source_counts[str(path)] = source_counts.get(str(path), 0) + 1
                key = row.get("record_id") or "|".join([
                    row.get("doi", "").lower(),
                    row.get("metric_category", ""),
                    row.get("value", ""),
                    row.get("unit", ""),
                    row.get("evidence", "")[:220].lower(),
                ])
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

    by_metric: dict[str, int] = {}
    by_quality: dict[str, int] = {}
    doi_set: set[str] = set()
    for row in rows:
        by_metric[row.get("metric_category", "")] = by_metric.get(row.get("metric_category", ""), 0) + 1
        by_quality[row.get("quality_label", "")] = by_quality.get(row.get("quality_label", ""), 0) + 1
        doi = (row.get("doi") or "").strip().lower()
        if doi:
            doi_set.add(doi)

    summary = {
        "input_rows": source_counts,
        "merged_rows": len(rows),
        "duplicates_removed": duplicates,
        "unique_dois": len(doi_set),
        "by_metric_category": dict(sorted(by_metric.items())),
        "by_quality_label": dict(sorted(by_quality.items())),
        "output": str(args.out),
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

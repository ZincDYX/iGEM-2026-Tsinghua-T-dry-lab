from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ESSAY = ROOT / "essay"

DIRECT = ESSAY / "pdf_extraction_20000_direct_resolved.csv"
TARGETED = ESSAY / "pdf_extraction_20000_targeted_no_records.csv"
OUT = ESSAY / "pdf_extraction_20000_direct_augmented_targeted.csv"
PREVIEW = ESSAY / "pdf_extraction_20000_direct_augmented_targeted_records_preview.csv"
SUMMARY = ESSAY / "pdf_extraction_20000_direct_augmented_targeted_summary.json"


def doi_key(row: dict[str, str]) -> str:
    return (row.get("doi") or row.get("article_key") or "").strip().lower()


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), list(reader.fieldnames or [])


def write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    direct_rows, fieldnames = read_rows(DIRECT)
    targeted_rows, targeted_fields = read_rows(TARGETED)
    for field in targeted_fields:
        if field not in fieldnames:
            fieldnames.append(field)

    targeted_ok_dois = {
        doi_key(row)
        for row in targeted_rows
        if row.get("extraction_status") == "ok" and doi_key(row)
    }

    merged: list[dict[str, str]] = []
    for row in direct_rows:
        if doi_key(row) in targeted_ok_dois and row.get("extraction_status") == "no_records":
            continue
        merged.append(row)

    merged.extend(row for row in targeted_rows if row.get("extraction_status") == "ok")

    ok_rows = [row for row in merged if row.get("extraction_status") == "ok"]
    ok_dois = {doi_key(row) for row in ok_rows if doi_key(row)}
    all_dois = {doi_key(row) for row in merged if doi_key(row)}
    no_record_dois = {
        doi_key(row)
        for row in merged
        if row.get("extraction_status") == "no_records" and doi_key(row)
    } - ok_dois

    write_rows(OUT, merged, fieldnames)
    write_rows(PREVIEW, ok_rows, fieldnames)

    summary = {
        "direct_rows": len(direct_rows),
        "targeted_rows": len(targeted_rows),
        "targeted_ok_rows": len([r for r in targeted_rows if r.get("extraction_status") == "ok"]),
        "targeted_ok_dois": len(targeted_ok_dois),
        "augmented_rows": len(merged),
        "augmented_ok_rows": len(ok_rows),
        "augmented_unique_dois": len(all_dois),
        "augmented_ok_dois": len(ok_dois),
        "augmented_no_record_dois": len(no_record_dois),
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

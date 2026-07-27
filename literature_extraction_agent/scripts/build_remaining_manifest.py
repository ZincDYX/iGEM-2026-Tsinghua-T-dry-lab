from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "essay" / "pdf_text_cache_20000_direct_manifest.csv"
DEFAULT_CLEAN = ROOT / "essay" / "final_clean_database_10000.csv"
DEFAULT_OUT = ROOT / "essay" / "remaining_pdf_text_manifest_after_clean10000.csv"
DEFAULT_SUMMARY = ROOT / "essay" / "remaining_pdf_text_manifest_after_clean10000_summary.json"


def norm_doi(value: str) -> str:
    return (value or "").strip().lower()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--clean", type=Path, default=DEFAULT_CLEAN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()

    clean_dois: set[str] = set()
    with args.clean.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            doi = norm_doi(row.get("doi", ""))
            if doi:
                clean_dois.add(doi)

    remaining: list[dict[str, str]] = []
    manifest_dois: set[str] = set()
    remaining_dois: set[str] = set()
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        for row in reader:
            if row.get("status") != "cached":
                continue
            doi = norm_doi(row.get("doi", ""))
            if doi:
                manifest_dois.add(doi)
            if doi and doi in clean_dois:
                continue
            remaining.append(row)
            if doi:
                remaining_dois.add(doi)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(remaining)

    summary = {
        "cached_manifest_rows": len(manifest_dois),
        "clean_dois": len(clean_dois),
        "remaining_rows": len(remaining),
        "remaining_unique_dois": len(remaining_dois),
        "output": str(args.out),
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

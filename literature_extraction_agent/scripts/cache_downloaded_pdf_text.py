from __future__ import annotations

import argparse
import csv
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "essay" / "download_manifest_20000_direct.csv"
DEFAULT_CACHE_DIR = ROOT / "essay" / "text_cache_20000_direct"
DEFAULT_OUT = ROOT / "essay" / "pdf_text_cache_20000_direct_manifest.csv"


def safe_id(row: dict[str, str]) -> str:
    basis = row.get("file_path") or row.get("doi") or row.get("url") or row.get("title") or "pdf"
    digest = hashlib.sha1(basis.encode("utf-8", errors="ignore")).hexdigest()[:10]
    rank = row.get("rank") or row.get("candidate_id") or "0"
    return f"rank_{int(rank):04d}_{digest}"


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text.strip():
            parts.append(text.strip())
    return "\n\n".join(parts)


def existing_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return {r.get("file_path", "") for r in csv.DictReader(f) if r.get("status") == "cached"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    args.cache_dir.mkdir(parents=True, exist_ok=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    with args.manifest.open("r", encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("status") == "downloaded" and r.get("file_path")]
    done = existing_keys(args.out)
    unique_rows: list[dict[str, str]] = []
    seen_files: set[str] = set()
    for row in rows:
        file_path = row.get("file_path", "")
        if not file_path or file_path in done or file_path in seen_files:
            continue
        seen_files.add(file_path)
        unique_rows.append(row)
    rows = unique_rows
    if args.limit > 0:
        rows = rows[: args.limit]

    fields = [
        "rank",
        "candidate_id",
        "doi",
        "title",
        "file_path",
        "text_file",
        "status",
        "text_chars",
        "error",
    ]
    write_header = not args.out.exists() or args.out.stat().st_size == 0
    def run_row(row: dict[str, str]) -> dict[str, str]:
        out_row = {k: row.get(k, "") for k in fields}
        out_row["text_file"] = ""
        out_row["text_chars"] = "0"
        out_row["error"] = ""
        path = Path(row["file_path"])
        try:
            text = extract_pdf_text(path)
            text_path = args.cache_dir / f"{safe_id(row)}.txt"
            text_path.write_text(text, encoding="utf-8", errors="ignore")
            out_row["text_file"] = str(text_path)
            out_row["status"] = "cached" if text.strip() else "empty_text"
            out_row["text_chars"] = str(len(text))
        except Exception as exc:
            out_row["status"] = "error"
            out_row["error"] = f"{type(exc).__name__}: {exc}"
        return out_row

    max_workers = max(1, int(args.workers or 1))
    with args.out.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if write_header:
            writer.writeheader()
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(run_row, row) for row in rows]
            for i, future in enumerate(as_completed(futures), start=1):
                writer.writerow(future.result())
                f.flush()
                if i % 50 == 0:
                    print(f"cached_or_attempted={i} remaining={len(rows)-i}")
    print(f"done cached_attempts={len(rows)} manifest={args.out}")


if __name__ == "__main__":
    main()

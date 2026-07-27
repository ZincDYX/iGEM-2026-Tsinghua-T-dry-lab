from __future__ import annotations

import argparse
import csv
import hashlib
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

import requests


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "outputs" / "candidate_literature_50000_year_slices_full.csv"
DEFAULT_OUT_DIR = ROOT / "essay"
DEFAULT_MANIFEST = DEFAULT_OUT_DIR / "download_manifest_elsevier_article_api.csv"
DEFAULT_API_TXT = ROOT / "API.txt"


def read_elsevier_key(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    match = re.search(r"ELSEVIER_API_KEY\s*=\s*['\"]([^'\"]+)['\"]", text)
    return match.group(1).strip() if match else ""


def safe_name(text: str, limit: int = 120) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff.-]+", " ", text or "", flags=re.UNICODE).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:limit].strip(" .") or "untitled"


def split_article_urls(source_links: str) -> list[str]:
    urls: list[str] = []
    for part in re.split(r";\s*", source_links or ""):
        url = part.strip()
        if "/content/article/" in url and url not in urls:
            urls.append(url)
    return urls


def downloaded_dois(out_dir: Path, current_manifest: Path) -> set[str]:
    dois: set[str] = set()
    manifests = list(out_dir.glob("download*_manifest*.csv"))
    if current_manifest.exists() and current_manifest not in manifests:
        manifests.append(current_manifest)
    for manifest in manifests:
        try:
            with manifest.open("r", encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    if row.get("status") == "downloaded" and row.get("doi"):
                        dois.add(row["doi"].strip().lower())
        except Exception:
            continue
    return dois


def done_keys(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return {(r.get("doi", "").strip().lower(), r.get("url", "").strip()) for r in csv.DictReader(f)}


def iter_jobs(input_csv: Path) -> Iterable[dict[str, str]]:
    with input_csv.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            for url in split_article_urls(row.get("source_links", "")):
                job = dict(row)
                job["url"] = url
                yield job


def fetch_elsevier_pdf(api_key: str, url: str, timeout: int = 90) -> tuple[bytes | None, str, str]:
    try:
        resp = requests.get(
            url,
            headers={"X-ELS-APIKey": api_key, "Accept": "application/pdf"},
            params={"httpAccept": "application/pdf"},
            timeout=timeout,
            allow_redirects=True,
        )
        ctype = resp.headers.get("content-type", "")
        if resp.status_code != 200:
            return None, str(resp.status_code), ctype
        if not resp.content.startswith(b"%PDF"):
            return None, "not_pdf", ctype
        return resp.content, "downloaded", ctype
    except Exception as exc:
        return None, f"error:{type(exc).__name__}", ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--api-txt", type=Path, default=DEFAULT_API_TXT)
    parser.add_argument("--limit", type=int, default=0, help="0 means all remaining article API URLs")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--sleep", type=float, default=0.05)
    parser.add_argument("--include-existing-dois", action="store_true")
    args = parser.parse_args()

    api_key = read_elsevier_key(args.api_txt)
    if not api_key:
        raise SystemExit(f"Elsevier API key not found in {args.api_txt}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    completed = done_keys(args.manifest)
    skip_dois = set() if args.include_existing_dois else downloaded_dois(args.out_dir, args.manifest)

    jobs = []
    seen: set[tuple[str, str]] = set()
    for job in iter_jobs(args.input):
        doi = job.get("doi", "").strip().lower()
        url = job.get("url", "").strip()
        key = (doi, url)
        if key in seen or key in completed:
            continue
        if doi and doi in skip_dois:
            continue
        seen.add(key)
        jobs.append(job)
    if args.limit > 0:
        jobs = jobs[: args.limit]

    fields = [
        "rank", "candidate_id", "doi", "title", "url", "status",
        "content_type", "file_path", "bytes", "sha256",
    ]
    write_header = not args.manifest.exists() or args.manifest.stat().st_size == 0

    def run_job(index_and_job: tuple[int, dict[str, str]]) -> dict[str, str]:
        i, job = index_and_job
        rank = job.get("rank") or job.get("candidate_id") or str(i)
        doi = job.get("doi", "")
        url = job["url"]
        title = job.get("title", "")
        basis = doi or url
        digest = hashlib.sha1(basis.encode("utf-8", errors="ignore")).hexdigest()[:10]
        target = args.out_dir / f"elsevier_{int(rank):05d}_{digest}_{safe_name(title)}.pdf"
        content, status, ctype = fetch_elsevier_pdf(api_key, url)
        row = {
            "rank": rank,
            "candidate_id": job.get("candidate_id", ""),
            "doi": doi,
            "title": title,
            "url": url,
            "status": status,
            "content_type": ctype,
            "file_path": "",
            "bytes": "",
            "sha256": "",
        }
        if content is not None:
            target.write_bytes(content)
            row["file_path"] = str(target)
            row["bytes"] = str(len(content))
            row["sha256"] = hashlib.sha256(content).hexdigest()
        return row

    max_workers = max(1, int(args.workers or 1))
    with args.manifest.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if write_header:
            writer.writeheader()
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(run_job, pair) for pair in enumerate(jobs, start=1)]
            for i, future in enumerate(as_completed(futures), start=1):
                writer.writerow(future.result())
                f.flush()
                if i % 50 == 0:
                    print(f"processed={i} remaining={len(jobs)-i}", flush=True)
                if args.sleep:
                    time.sleep(max(0.0, args.sleep))
    print(f"done attempted={len(jobs)} manifest={args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

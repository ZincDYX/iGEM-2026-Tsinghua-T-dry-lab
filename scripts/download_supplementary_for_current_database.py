from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
ESSAY = ROOT / "essay"
OUT_DIR = ESSAY / "supplementary_current"
DEFAULT_INPUT = ESSAY / "final_structured_database_after_elsevier_pdf_expansion.csv"
DEFAULT_CANDIDATES = ROOT / "outputs" / "candidate_literature_50000_year_slices_full.csv"
DEFAULT_MANIFEST = OUT_DIR / "supplementary_current_download_manifest.csv"
DEFAULT_SUMMARY = OUT_DIR / "supplementary_current_download_summary.json"
DEFAULT_API_TXT = ROOT / "API.txt"

URL_RE = re.compile(r"https?://[^\s)\]}<>\"']+", re.I)
HREF_RE = re.compile(r"""(?:href|src)=["']([^"']+)["']""", re.I)
SUP_HINTS = [
    "supplement", "supporting", "additional", "appendix", "media", "mmc",
    "data availability", "dataset", "figshare", "zenodo", "dryad", "osf.io",
    "github", "repository", "source data", "raw data", "excel", "table s",
]
EXT_HINTS = [".xlsx", ".xls", ".csv", ".tsv", ".zip", ".docx", ".txt", ".pdf"]
PREFERRED_EXT = [".xlsx", ".xls", ".csv", ".tsv", ".zip"]


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def read_elsevier_key(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    match = re.search(r"ELSEVIER_API_KEY\s*=\s*['\"]([^'\"]+)['\"]", text)
    return match.group(1).strip() if match else ""


def clean_doi(value: str) -> str:
    doi = norm(value)
    if doi.lower().startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/") :]
    if doi.lower().startswith("doi:"):
        doi = doi[4:]
    return doi.lower().strip()


def safe_name(text: str, max_len: int = 95) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"[^A-Za-z0-9._ -]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len].strip(" ._-") or "supplementary"


def load_target_dois(path: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            doi = clean_doi(row.get("doi", ""))
            if not doi:
                continue
            if doi not in out:
                out[doi] = {"doi": doi, "title": norm(row.get("title", "")), "rank": row.get("rank", "") or row.get("candidate_id", "")}
    return out


def load_candidate_metadata(path: Path, target_dois: set[str]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            doi = clean_doi(row.get("doi", ""))
            if doi in target_dois and doi not in out:
                out[doi] = dict(row)
    return out


def load_text_files() -> dict[str, str]:
    out: dict[str, str] = {}
    for manifest in ESSAY.glob("pdf_text_cache*_manifest.csv"):
        try:
            with manifest.open("r", encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    doi = clean_doi(row.get("doi", ""))
                    text_file = norm(row.get("text_file", ""))
                    if row.get("status") == "cached" and doi and text_file and doi not in out:
                        out[doi] = text_file
        except Exception:
            continue
    return out


def done_keys(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return {(clean_doi(r.get("doi", "")), norm(r.get("url", ""))) for r in csv.DictReader(f)}


def load_done_dois(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {clean_doi(doi) for doi in data.get("done_dois", []) if clean_doi(doi)}
    except Exception:
        return set()


def save_done_dois(path: Path, done_dois: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "done_dois_count": len(done_dois),
        "done_dois": sorted(done_dois),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def add_url(urls: list[tuple[str, str]], url: str, source: str) -> None:
    url = norm(url).rstrip(".,;:)")
    if not url or not url.lower().startswith(("http://", "https://")):
        return
    low = url.lower()
    if not (any(h in low for h in SUP_HINTS) or any(ext in low for ext in EXT_HINTS)):
        return
    if url.lower().startswith("https://doi.org/"):
        return
    if not any(existing == url for existing, _ in urls):
        urls.append((url, source))


def links_from_text(text: str) -> list[tuple[str, str]]:
    urls: list[tuple[str, str]] = []
    for match in URL_RE.finditer(text):
        add_url(urls, match.group(0), "fulltext_url")
    return urls


def links_from_html(base_url: str, html: str, source: str) -> list[tuple[str, str]]:
    urls: list[tuple[str, str]] = []
    for match in HREF_RE.finditer(html):
        href = match.group(1)
        url = urljoin(base_url, href)
        low = url.lower()
        around = html[max(0, match.start() - 220) : match.end() + 220].lower()
        if any(h in low or h in around for h in SUP_HINTS) or any(ext in low for ext in EXT_HINTS):
            add_url(urls, url, source)
    return urls


def links_from_xml(base_url: str, xml: str) -> list[tuple[str, str]]:
    urls: list[tuple[str, str]] = []
    for match in HREF_RE.finditer(xml):
        add_url(urls, urljoin(base_url, match.group(1)), "elsevier_xml")
    for match in URL_RE.finditer(xml):
        add_url(urls, match.group(0), "elsevier_xml")
    # Elsevier XML sometimes stores attachment metadata without literal supplement in URL.
    for match in re.finditer(r"<ce:link[^>]+href=[\"']([^\"']+)[\"'][^>]*>", xml, flags=re.I):
        around = xml[max(0, match.start() - 300) : match.end() + 300].lower()
        if any(h in around for h in SUP_HINTS):
            add_url(urls, urljoin(base_url, match.group(1)), "elsevier_xml")
    return urls


def doi_landing_urls(doi: str) -> list[str]:
    urls = [f"https://doi.org/{doi}"]
    low = doi.lower()
    if low.startswith("10.1038/"):
        urls.append(f"https://www.nature.com/articles/{doi.split('/', 1)[1]}")
    if low.startswith(("10.1002/", "10.1111/")):
        urls.append(f"https://onlinelibrary.wiley.com/doi/full/{doi}")
    if low.startswith("10.1021/"):
        urls.append(f"https://pubs.acs.org/doi/full/{doi}")
    if low.startswith("10.1007/"):
        urls.append(f"https://link.springer.com/article/{doi}")
    if low.startswith("10.3389/"):
        urls.append(f"https://www.frontiersin.org/articles/{doi}/full")
    return urls


def extension_from_response(url: str, content_type: str) -> str:
    path = urlparse(url).path.lower()
    for ext in EXT_HINTS:
        if path.endswith(ext):
            return ext
    ctype = (content_type or "").lower()
    if "spreadsheet" in ctype or "excel" in ctype:
        return ".xlsx"
    if "zip" in ctype:
        return ".zip"
    if "csv" in ctype:
        return ".csv"
    if "tab-separated" in ctype:
        return ".tsv"
    if "word" in ctype:
        return ".docx"
    if "pdf" in ctype:
        return ".pdf"
    if "text" in ctype:
        return ".txt"
    return ".bin"


def looks_downloadable(content: bytes, ctype: str, url: str) -> bool:
    low = (ctype or "").lower()
    path = urlparse(url).path.lower()
    if content.startswith(b"%PDF") or content.startswith(b"PK\x03\x04"):
        return True
    if any(path.endswith(ext) for ext in EXT_HINTS):
        return "html" not in low and len(content) > 100
    return "csv" in low or "text/tab-separated" in low


def fetch_html(session: requests.Session, url: str, headers: dict[str, str]) -> str:
    try:
        resp = session.get(url, headers=headers, timeout=25, allow_redirects=True)
        if resp.status_code < 400 and "html" in resp.headers.get("content-type", "").lower():
            return resp.text
    except Exception:
        return ""
    return ""


def fetch_elsevier_xml(session: requests.Session, url: str, api_key: str) -> str:
    if not api_key:
        return ""
    try:
        resp = session.get(
            url,
            headers={"X-ELS-APIKey": api_key, "Accept": "application/xml"},
            params={"httpAccept": "application/xml"},
            timeout=35,
            allow_redirects=True,
        )
        if resp.status_code == 200 and "xml" in resp.headers.get("content-type", "").lower():
            return resp.text
    except Exception:
        return ""
    return ""


def candidate_urls_for(
    doi: str,
    title: str,
    candidate_row: dict[str, str] | None,
    text_file: str | None,
    session: requests.Session,
    headers: dict[str, str],
    elsevier_key: str,
) -> list[tuple[str, str]]:
    urls: list[tuple[str, str]] = []
    if text_file:
        path = Path(text_file)
        if not path.is_absolute():
            path = ROOT / path
        if path.exists():
            try:
                urls.extend(links_from_text(path.read_text(encoding="utf-8", errors="ignore")))
            except Exception:
                pass
    article_api_urls: list[str] = []
    if candidate_row:
        for part in re.split(r";\s*", candidate_row.get("source_links", "")):
            if "/content/article/" in part and part not in article_api_urls:
                article_api_urls.append(part.strip())
            add_url(urls, part.strip(), "source_links")
    for article_url in article_api_urls[:2]:
        xml = fetch_elsevier_xml(session, article_url, elsevier_key)
        if xml:
            urls.extend(links_from_xml(article_url, xml))
    for landing in doi_landing_urls(doi):
        html = fetch_html(session, landing, headers)
        if html:
            urls.extend(links_from_html(landing, html, "landing_html"))
    deduped: list[tuple[str, str]] = []
    for url, source in urls:
        if not any(u == url for u, _ in deduped):
            deduped.append((url, source))
    deduped.sort(key=lambda item: (not any(ext in item[0].lower() for ext in PREFERRED_EXT), item[0]))
    return deduped


def download_one(
    doi: str,
    title: str,
    rank: str,
    url: str,
    source: str,
    out_dir: Path,
    headers: dict[str, str],
) -> dict[str, str]:
    rec = {
        "rank": rank,
        "doi": doi,
        "title": title,
        "url": url,
        "source": source,
        "status": "failed",
        "http_status": "",
        "content_type": "",
        "file_path": "",
        "bytes": "",
        "sha256": "",
        "error": "",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=45, allow_redirects=True)
        rec["http_status"] = str(resp.status_code)
        rec["content_type"] = resp.headers.get("content-type", "")
        if resp.status_code >= 400:
            rec["error"] = f"http {resp.status_code}"
            return rec
        if not looks_downloadable(resp.content, rec["content_type"], resp.url):
            rec["error"] = f"not_downloadable:{rec['content_type']}"
            return rec
        ext = extension_from_response(resp.url, rec["content_type"])
        digest = hashlib.sha1((doi + url).encode("utf-8", errors="ignore")).hexdigest()[:10]
        file_path = out_dir / f"sup_{digest}_{safe_name(title)}{ext}"
        file_path.write_bytes(resp.content)
        rec["status"] = "downloaded"
        rec["file_path"] = str(file_path)
        rec["bytes"] = str(len(resp.content))
        rec["sha256"] = hashlib.sha256(resp.content).hexdigest()
    except Exception as exc:
        rec["error"] = f"{type(exc).__name__}: {exc}"
    return rec


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--candidate-csv", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--api-txt", type=Path, default=DEFAULT_API_TXT)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--limit-dois", type=int, default=0)
    parser.add_argument("--max-urls-per-doi", type=int, default=12)
    parser.add_argument("--batch-dois", type=int, default=50)
    parser.add_argument("--state", type=Path, default=None)
    parser.add_argument("--no-skip-done-dois", action="store_true")
    args = parser.parse_args()
    if args.state is None:
        args.state = args.manifest.with_name(args.manifest.stem + "_state.json")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    target = load_target_dois(args.input)
    if args.limit_dois > 0:
        target = dict(list(target.items())[: args.limit_dois])
    candidates = load_candidate_metadata(args.candidate_csv, set(target))
    text_files = load_text_files()
    elsevier_key = read_elsevier_key(args.api_txt)
    completed = done_keys(args.manifest)
    done_dois = set() if args.no_skip_done_dois else load_done_dois(args.state)
    headers = {
        "User-Agent": "Mozilla/5.0 LiteratureExtraction/1.0",
        "Accept": "text/html,application/pdf,application/octet-stream,*/*",
    }

    fields = ["rank", "doi", "title", "url", "source", "status", "http_status", "content_type", "file_path", "bytes", "sha256", "error"]
    write_header = not args.manifest.exists() or args.manifest.stat().st_size == 0
    jobs: list[tuple[str, str, str, str, str]] = []
    batch_dois: list[str] = []
    discovery_stats = {"target_dois": len(target), "done_dois_at_start": len(done_dois), "skipped_done_dois": 0, "dois_with_candidate_urls": 0, "candidate_urls": 0}
    session = requests.Session()
    jobs_total = 0
    with args.manifest.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if write_header:
            writer.writeheader()

        def flush_jobs(batch: list[tuple[str, str, str, str, str]]) -> None:
            nonlocal jobs_total
            if not batch:
                return
            jobs_total += len(batch)
            with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
                futures = [
                    pool.submit(download_one, doi, title, rank, url, source, args.out_dir, headers)
                    for doi, title, rank, url, source in batch
                ]
                for j, future in enumerate(as_completed(futures), start=1):
                    row = future.result()
                    writer.writerow(row)
                    f.flush()
                    completed.add((clean_doi(row.get("doi", "")), norm(row.get("url", ""))))
                    if j % 25 == 0 or j == len(batch):
                        print(f"batch_downloaded_or_attempted={j}/{len(batch)} total_jobs={jobs_total}", flush=True)

        batch_size = max(1, int(args.batch_dois or 1))
        for i, (doi, meta) in enumerate(target.items(), start=1):
            if doi in done_dois:
                discovery_stats["skipped_done_dois"] += 1
                continue
            urls = candidate_urls_for(
                doi,
                meta.get("title", ""),
                candidates.get(doi),
                text_files.get(doi),
                session,
                headers,
                elsevier_key,
            )
            if urls:
                discovery_stats["dois_with_candidate_urls"] += 1
            for url, source in urls[: max(1, args.max_urls_per_doi)]:
                if (doi, url) in completed:
                    continue
                jobs.append((doi, meta.get("title", ""), meta.get("rank", "") or str(i), url, source))
            discovery_stats["candidate_urls"] += len(urls)
            batch_dois.append(doi)
            if len(batch_dois) >= batch_size:
                print(f"discovered_dois={i}/{len(target)} pending_jobs={len(jobs)}", flush=True)
                flush_jobs(jobs)
                done_dois.update(batch_dois)
                save_done_dois(args.state, done_dois)
                jobs = []
                batch_dois = []
        if jobs or batch_dois:
            print(f"discovered_dois={len(target)}/{len(target)} pending_jobs={len(jobs)}", flush=True)
            flush_jobs(jobs)
            done_dois.update(batch_dois)
            save_done_dois(args.state, done_dois)

    final_rows = []
    if args.manifest.exists():
        with args.manifest.open("r", encoding="utf-8-sig", newline="") as f:
            final_rows = list(csv.DictReader(f))
    status_counts: dict[str, int] = {}
    ext_counts: dict[str, int] = {}
    for row in final_rows:
        status_counts[row.get("status", "")] = status_counts.get(row.get("status", ""), 0) + 1
        if row.get("status") == "downloaded":
            ext = Path(row.get("file_path", "")).suffix.lower()
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
    summary = {
        **discovery_stats,
        "new_jobs_this_run": jobs_total,
        "manifest_rows_total": len(final_rows),
        "status_counts": dict(sorted(status_counts.items())),
        "downloaded_by_extension": dict(sorted(ext_counts.items())),
        "manifest": str(args.manifest),
        "state": str(args.state),
        "done_dois_total": len(done_dois),
        "out_dir": str(args.out_dir),
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

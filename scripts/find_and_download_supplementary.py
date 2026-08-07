import csv
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


ROOT = Path.cwd()
ESSAY = ROOT / "essay"
TEXT_MANIFEST = ESSAY / "pdf_text_cache_all_manifest.csv"
SUP_DIR = ESSAY / "supplementary"
SUP_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = SUP_DIR / "supplementary_download_manifest.csv"
SUMMARY_JSON = SUP_DIR / "supplementary_download_summary.json"

URL_RE = re.compile(r"https?://[^\s)\]}>\"']+", re.I)
SUP_HINTS = [
    "supplement",
    "supporting",
    "additional",
    "data availability",
    "figshare",
    "zenodo",
    "dryad",
    "github",
    "osf.io",
    "repository",
    "dataset",
    "appendix",
    "media",
]
EXT_HINTS = [".pdf", ".xlsx", ".xls", ".csv", ".tsv", ".zip", ".docx", ".txt"]


def safe_name(text: str, max_len: int = 80) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    text = re.sub(r"[^A-Za-z0-9._ -]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len].strip(" ._-") or "supplementary"


def candidate_urls(text: str) -> list[str]:
    urls = []
    for match in URL_RE.finditer(text):
        url = match.group(0).rstrip(".,;:)")
        low = url.lower()
        if any(h in low for h in SUP_HINTS) or any(ext in low for ext in EXT_HINTS):
            if url not in urls:
                urls.append(url)
    return urls


def doi_landing_urls(doi: str) -> list[str]:
    if not doi:
        return []
    urls = [f"https://doi.org/{doi}"]
    low = doi.lower()
    if low.startswith("10.1038/"):
        article = doi.split("/", 1)[1]
        urls.append(f"https://www.nature.com/articles/{article}")
    if low.startswith("10.1002/") or low.startswith("10.1111/"):
        urls.append(f"https://onlinelibrary.wiley.com/doi/full/{doi}")
    if low.startswith("10.1021/"):
        urls.append(f"https://pubs.acs.org/doi/full/{doi}")
    if low.startswith("10.1007/"):
        urls.append(f"https://link.springer.com/article/{doi}")
    return urls


def links_from_html(base_url: str, html: str) -> list[str]:
    links = []
    for match in re.finditer(r"""href=["']([^"']+)["']""", html, flags=re.I):
        href = match.group(1)
        url = urljoin(base_url, href)
        low = url.lower()
        text_around = html[max(0, match.start() - 160) : match.end() + 160].lower()
        if any(h in low or h in text_around for h in SUP_HINTS) or any(ext in low for ext in EXT_HINTS):
            if url not in links:
                links.append(url)
    return links


def extension_from_response(url: str, content_type: str) -> str:
    path = urlparse(url).path.lower()
    for ext in [".pdf", ".xlsx", ".xls", ".csv", ".tsv", ".zip", ".docx", ".txt"]:
        if path.endswith(ext):
            return ext
    ctype = (content_type or "").lower()
    if "pdf" in ctype:
        return ".pdf"
    if "spreadsheet" in ctype or "excel" in ctype:
        return ".xlsx"
    if "zip" in ctype:
        return ".zip"
    if "csv" in ctype:
        return ".csv"
    if "word" in ctype:
        return ".docx"
    if "text" in ctype:
        return ".txt"
    return ".bin"


def looks_like_download(content: bytes, content_type: str, url: str) -> bool:
    low = (content_type or "").lower()
    path = urlparse(url).path.lower()
    if content.startswith(b"%PDF") or content.startswith(b"PK\x03\x04"):
        return True
    if any(path.endswith(ext) for ext in EXT_HINTS):
        return "html" not in low and len(content) > 100
    return False


def main() -> None:
    if not TEXT_MANIFEST.exists():
        raise SystemExit(f"missing {TEXT_MANIFEST}")
    rows = list(csv.DictReader(TEXT_MANIFEST.open("r", encoding="utf-8-sig", newline="")))
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LiteratureExtraction/1.0",
        "Accept": "text/html,application/pdf,application/octet-stream,*/*",
    }
    existing = set()
    if OUT_CSV.exists() and OUT_CSV.stat().st_size:
        with OUT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                existing.add((row.get("rank"), row.get("url")))

    fields = ["rank", "doi", "title", "url", "source", "status", "http_status", "content_type", "file_path", "bytes", "sha256", "error"]
    write_header = not OUT_CSV.exists() or OUT_CSV.stat().st_size == 0
    with OUT_CSV.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        for row in rows:
            if row.get("status") == "failed":
                continue
            rank = row.get("rank", "")
            doi = row.get("doi", "")
            title = row.get("title", "")
            text_path = Path(row.get("text_path", ""))
            urls = []
            if text_path.exists():
                text = text_path.read_text(encoding="utf-8", errors="ignore")
                urls.extend(candidate_urls(text))
            for landing in doi_landing_urls(doi):
                try:
                    resp = session.get(landing, headers=headers, timeout=25, allow_redirects=True)
                    if resp.status_code < 400 and "html" in resp.headers.get("Content-Type", "").lower():
                        urls.extend(links_from_html(resp.url, resp.text))
                except Exception:
                    pass
                time.sleep(0.1)
            deduped = []
            for url in urls:
                if url not in deduped:
                    deduped.append(url)
            for url in deduped[:20]:
                if (rank, url) in existing:
                    continue
                rec = {
                    "rank": rank,
                    "doi": doi,
                    "title": title,
                    "url": url,
                    "source": "text_or_landing",
                    "status": "failed",
                    "http_status": "",
                    "content_type": "",
                    "file_path": "",
                    "bytes": 0,
                    "sha256": "",
                    "error": "",
                }
                try:
                    resp = session.get(url, headers=headers, timeout=35, allow_redirects=True)
                    rec["http_status"] = resp.status_code
                    rec["content_type"] = resp.headers.get("Content-Type", "")
                    if resp.status_code >= 400:
                        rec["error"] = f"http {resp.status_code}"
                    elif not looks_like_download(resp.content, rec["content_type"], resp.url):
                        rec["error"] = f"not downloadable content-type={rec['content_type']}"
                    else:
                        ext = extension_from_response(resp.url, rec["content_type"])
                        digest = hashlib.sha1((doi + url).encode("utf-8", "ignore")).hexdigest()[:10]
                        filename = f"rank_{int(rank or 0):04d}_{digest}_{safe_name(title)}{ext}"
                        out_path = SUP_DIR / filename
                        out_path.write_bytes(resp.content)
                        rec["status"] = "downloaded"
                        rec["file_path"] = str(out_path)
                        rec["bytes"] = len(resp.content)
                        rec["sha256"] = hashlib.sha256(resp.content).hexdigest()
                except Exception as ex:
                    rec["error"] = f"{type(ex).__name__}: {ex}"
                writer.writerow(rec)
                f.flush()
                existing.add((rank, url))
                time.sleep(0.15)

    final_rows = list(csv.DictReader(OUT_CSV.open("r", encoding="utf-8-sig", newline=""))) if OUT_CSV.exists() else []
    summary = {
        "rows": len(final_rows),
        "downloaded": sum(1 for r in final_rows if r.get("status") == "downloaded"),
        "failed": sum(1 for r in final_rows if r.get("status") != "downloaded"),
        "manifest": str(OUT_CSV),
        "supplementary_dir": str(SUP_DIR),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
INPUT_CSV = OUT / "candidate_literature_20000.csv"
OUTPUT_CSV = OUT / "openalex_oa_links_20000.csv"
SUMMARY_JSON = OUT / "openalex_oa_links_20000_summary.json"


OPENALEX_URL = "https://api.openalex.org/works"
USER_AGENT = "CatalystOptimizationSystem/0.1 (literature extraction; mailto:example@example.com)"


def clean_doi(value: str) -> str:
    doi = (value or "").strip()
    if doi.lower().startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/") :]
    if doi.lower().startswith("doi:"):
        doi = doi[4:]
    return doi.strip().lower()


def load_candidates(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for i, row in enumerate(rows, start=1):
        row.setdefault("candidate_id", str(i))
        row["doi"] = clean_doi(row.get("doi", ""))
    return rows


def existing_done(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        done: set[str] = set()
        for row in csv.DictReader(f):
            doi = clean_doi(row.get("doi", ""))
            if doi and row.get("openalex_error") != "query_failed":
                done.add(doi)
        return done


def chunks(values: list[str], size: int) -> list[list[str]]:
    return [values[i : i + size] for i in range(0, len(values), size)]


def get_nested_text(obj: dict[str, Any] | None, key: str) -> str:
    if not isinstance(obj, dict):
        return ""
    value = obj.get(key)
    return "" if value is None else str(value)


def extract_openalex(work: dict[str, Any]) -> dict[str, str]:
    open_access = work.get("open_access") if isinstance(work.get("open_access"), dict) else {}
    primary = work.get("primary_location") if isinstance(work.get("primary_location"), dict) else {}
    best = work.get("best_oa_location") if isinstance(work.get("best_oa_location"), dict) else {}
    locations = work.get("locations") if isinstance(work.get("locations"), list) else []

    pdf_urls: list[str] = []
    landing_urls: list[str] = []

    for location in [primary, best, *locations]:
        if not isinstance(location, dict):
            continue
        pdf_url = get_nested_text(location, "pdf_url")
        landing = get_nested_text(location, "landing_page_url")
        if pdf_url and pdf_url not in pdf_urls:
            pdf_urls.append(pdf_url)
        if landing and landing not in landing_urls:
            landing_urls.append(landing)

    oa_url = get_nested_text(open_access, "oa_url")
    if oa_url and oa_url.lower().endswith(".pdf") and oa_url not in pdf_urls:
        pdf_urls.insert(0, oa_url)
    elif oa_url and oa_url not in landing_urls:
        landing_urls.insert(0, oa_url)

    return {
        "openalex_id": get_nested_text(work, "id"),
        "openalex_is_oa": str(open_access.get("is_oa", "")),
        "openalex_oa_status": get_nested_text(open_access, "oa_status"),
        "openalex_oa_url": oa_url,
        "openalex_best_pdf_url": pdf_urls[0] if pdf_urls else "",
        "openalex_best_landing_url": landing_urls[0] if landing_urls else "",
        "openalex_version": get_nested_text(best, "version"),
        "pdf_candidate_urls": "; ".join(pdf_urls),
        "fulltext_candidate_urls": "; ".join(landing_urls),
        "openalex_error": "",
    }


def query_batch(session: requests.Session, dois: list[str], retries: int = 4) -> dict[str, dict[str, str]]:
    if not dois:
        return {}
    doi_filter = "|".join(f"https://doi.org/{quote(doi, safe='')}" for doi in dois)
    params = {
        "filter": f"doi:{doi_filter}",
        "per-page": len(dois),
        "select": "id,doi,open_access,primary_location,best_oa_location,locations",
    }
    for attempt in range(retries):
        try:
            resp = session.get(OPENALEX_URL, params=params, timeout=45)
            if resp.status_code == 429:
                message = resp.text[:1000].replace("\n", " ")
                if "Insufficient budget" in message or "dailyRemainingUsd" in message:
                    raise RuntimeError(f"OpenAlex budget/rate limit exhausted: {message}")
                time.sleep(2 ** attempt)
                continue
            if resp.status_code in {429, 500, 502, 503, 504}:
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            data = resp.json()
            found: dict[str, dict[str, str]] = {}
            for work in data.get("results", []):
                doi = clean_doi(get_nested_text(work, "doi"))
                if doi:
                    found[doi] = extract_openalex(work)
            return found
        except RuntimeError:
            raise
        except Exception:
            if attempt == retries - 1:
                break
            time.sleep(2 ** attempt)
    return {doi: {"openalex_error": "query_failed"} for doi in dois}


def write_summary(
    path: Path,
    input_csv: Path,
    output_csv: Path,
    input_rows: int,
    doi_rows: int,
    output_rows: int,
    error_rows: int,
) -> None:
    pdf_rows = 0
    oa_rows = 0
    if output_csv.exists():
        with output_csv.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("pdf_candidate_urls"):
                    pdf_rows += 1
                if row.get("openalex_is_oa", "").lower() == "true":
                    oa_rows += 1
    summary = {
        "input_csv": str(input_csv),
        "output_csv": str(output_csv),
        "input_rows": input_rows,
        "doi_rows": doi_rows,
        "openalex_rows_written": output_rows,
        "pdf_candidate_rows": pdf_rows,
        "oa_rows": oa_rows,
        "error_rows": error_rows,
    }
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=INPUT_CSV)
    parser.add_argument("--output", type=Path, default=OUTPUT_CSV)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--limit", type=int, default=0, help="0 means all remaining DOI rows")
    parser.add_argument("--sleep", type=float, default=0.15)
    args = parser.parse_args()

    input_csv = args.input
    output_csv = args.output
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    candidates = load_candidates(input_csv)
    doi_to_candidate: dict[str, dict[str, str]] = {}
    for row in candidates:
        doi = row.get("doi", "")
        if doi and doi not in doi_to_candidate:
            doi_to_candidate[doi] = row

    done = existing_done(output_csv)
    remaining = [doi for doi in doi_to_candidate if doi not in done]
    if args.limit > 0:
        remaining = remaining[: args.limit]

    base_fields = list(candidates[0].keys()) if candidates else []
    extra_fields = [
        "openalex_id",
        "openalex_is_oa",
        "openalex_oa_status",
        "openalex_oa_url",
        "openalex_best_pdf_url",
        "openalex_best_landing_url",
        "openalex_version",
        "pdf_candidate_urls",
        "fulltext_candidate_urls",
        "openalex_error",
    ]
    fieldnames = [*base_fields, *[f for f in extra_fields if f not in base_fields]]

    write_header = not output_csv.exists() or output_csv.stat().st_size == 0
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    error_rows = 0
    with output_csv.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for batch_index, doi_batch in enumerate(chunks(remaining, max(1, args.batch_size)), start=1):
            try:
                found = query_batch(session, doi_batch)
            except RuntimeError as exc:
                status = {
                    "status": "stopped",
                    "reason": str(exc),
                    "already_written": len(existing_done(output_csv)),
                    "remaining_before_stop": len(remaining) - ((batch_index - 1) * args.batch_size),
                    "output_csv": str(output_csv),
                }
                stopped_path = output_csv.with_name(f"{output_csv.stem}_stopped.json")
                stopped_path.write_text(
                    json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                print(json.dumps(status, ensure_ascii=False, indent=2))
                return
            for doi in doi_batch:
                row = dict(doi_to_candidate[doi])
                info = found.get(doi, {"openalex_error": "not_found"})
                if info.get("openalex_error"):
                    error_rows += 1
                for key in extra_fields:
                    row[key] = info.get(key, "")
                writer.writerow(row)
            f.flush()
            if batch_index % 10 == 0:
                print(f"processed_batches={batch_index} processed_dois={batch_index * args.batch_size}")
            time.sleep(max(0.0, args.sleep))

    total_written = len(existing_done(output_csv))
    total_errors = 0
    with output_csv.open("r", encoding="utf-8-sig", newline="") as f:
        total_errors = sum(1 for row in csv.DictReader(f) if row.get("openalex_error"))
    summary_path = output_csv.with_name(f"{output_csv.stem}_summary.json")
    write_summary(summary_path, input_csv, output_csv, len(candidates), len(doi_to_candidate), total_written, total_errors)
    print(f"done openalex_rows_written={total_written} remaining={len(doi_to_candidate) - total_written}")
    print(f"summary={summary_path}")


if __name__ == "__main__":
    main()

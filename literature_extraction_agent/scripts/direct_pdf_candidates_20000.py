from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = ROOT / "outputs" / "candidate_literature_20000.csv"
OUTPUT_CSV = ROOT / "outputs" / "direct_pdf_candidates_20000.csv"
SUMMARY_JSON = ROOT / "outputs" / "direct_pdf_candidates_20000_summary.json"


def clean_doi(value: str) -> str:
    doi = (value or "").strip()
    if doi.lower().startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/") :]
    if doi.lower().startswith("doi:"):
        doi = doi[4:]
    return doi.strip().lower()


def add_unique(items: list[str], url: str) -> None:
    if url and url not in items:
        items.append(url)


def source_pdf_urls(source_links: str) -> list[str]:
    urls: list[str] = []
    for url in re.split(r";\s*", source_links or ""):
        u = url.strip()
        if not u:
            continue
        low = u.lower()
        if ".pdf" in low or "/pdf" in low or "pdfdirect" in low or "article-pdf" in low:
            add_unique(urls, u)
    return urls


def doi_pdf_urls(doi: str) -> list[str]:
    doi = clean_doi(doi)
    urls: list[str] = []
    if not doi:
        return urls

    if doi.startswith("10.1038/"):
        suffix = doi.split("/", 1)[1]
        add_unique(urls, f"https://www.nature.com/articles/{suffix}.pdf")
    if doi.startswith(("10.1007/", "10.1186/")):
        add_unique(urls, f"https://link.springer.com/content/pdf/{doi}.pdf")
    if doi.startswith(("10.1002/", "10.1111/")):
        add_unique(urls, f"https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}")
        add_unique(urls, f"https://onlinelibrary.wiley.com/doi/pdf/{doi}")
    if doi.startswith("10.1021/"):
        add_unique(urls, f"https://pubs.acs.org/doi/pdf/{doi}?ref=article_openPDF")
    if doi.startswith("10.3389/"):
        add_unique(urls, f"https://www.frontiersin.org/articles/{doi}/pdf")
    if doi.startswith("10.1371/"):
        add_unique(urls, f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable")
        add_unique(urls, f"https://journals.plos.org/plosbiology/article/file?id={doi}&type=printable")
        add_unique(urls, f"https://journals.plos.org/plosgenetics/article/file?id={doi}&type=printable")
    if doi.startswith("10.1073/"):
        add_unique(urls, f"https://www.pnas.org/doi/pdf/{doi}")
    if doi.startswith("10.1128/"):
        add_unique(urls, f"https://journals.asm.org/doi/pdf/{doi}")
    if doi.startswith("10.7554/"):
        suffix = doi.rsplit(".", 1)[-1]
        add_unique(urls, f"https://elifesciences.org/articles/{suffix}.pdf")
    if doi.startswith("10.3390/"):
        # MDPI DOI redirects carry the exact journal/volume/page PDF path, so direct DOI-derived
        # construction is intentionally omitted here to avoid thousands of dead URLs.
        pass

    return urls


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=INPUT_CSV)
    parser.add_argument("--output", type=Path, default=OUTPUT_CSV)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if args.limit > 0:
        rows = rows[: args.limit]

    base_fields = list(rows[0].keys()) if rows else []
    extra = ["pdf_candidate_urls", "fulltext_candidate_urls", "pdf_candidate_source"]
    fieldnames = [*base_fields, *[x for x in extra if x not in base_fields]]

    out_rows: list[dict[str, str]] = []
    source_counts: dict[str, int] = {}
    for row in rows:
        doi = clean_doi(row.get("doi", ""))
        row["doi"] = doi
        candidates = []
        sources = []
        direct = doi_pdf_urls(doi)
        if direct:
            candidates.extend(direct)
            sources.append("doi_rule")
        src = source_pdf_urls(row.get("source_links", ""))
        if src:
            for url in src:
                add_unique(candidates, url)
            sources.append("source_links")
        if not candidates:
            continue
        out = dict(row)
        out["pdf_candidate_urls"] = "; ".join(candidates)
        out["fulltext_candidate_urls"] = row.get("source_links", "")
        out["pdf_candidate_source"] = ";".join(sources)
        out_rows.append(out)
        for source in sources:
            source_counts[source] = source_counts.get(source, 0) + 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    summary = {
        "input_csv": str(args.input),
        "output_csv": str(args.output),
        "input_rows": len(rows),
        "rows_with_pdf_candidates": len(out_rows),
        "source_counts": source_counts,
    }
    summary_path = args.output.with_name(f"{args.output.stem}_summary.json")
    summary["summary_json"] = str(summary_path)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

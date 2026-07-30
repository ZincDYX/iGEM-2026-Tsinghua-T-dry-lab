from __future__ import annotations

import csv
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Protocol

import requests

from .elsevier import search_scopus


OPENALEX_WORKS_ENDPOINT = "https://api.openalex.org/works"
CROSSREF_WORKS_ENDPOINT = "https://api.crossref.org/works"


@dataclass(frozen=True)
class LiteratureSearchQuery:
    query: str
    max_results: int = 25
    from_year: int | None = None
    to_year: int | None = None
    mailto: str | None = None
    api_key_env: str | None = None


@dataclass(frozen=True)
class LiteratureSearchResult:
    provider: str
    article_id: str
    title: str = ""
    doi: str = ""
    pii: str = ""
    year: int | None = None
    journal: str = ""
    abstract: str = ""
    landing_url: str = ""
    open_access_url: str = ""
    score: float | None = None
    raw: dict[str, Any] | None = None


class LiteratureSource(Protocol):
    provider: str

    def search(self, query: LiteratureSearchQuery) -> list[LiteratureSearchResult]:
        ...


class OpenAlexSource:
    provider = "openalex"

    def search(self, query: LiteratureSearchQuery) -> list[LiteratureSearchResult]:
        params: dict[str, Any] = {"search": query.query, "per-page": min(query.max_results, 200)}
        filters = _year_filter(query.from_year, query.to_year, field="from_publication_date")
        if filters:
            params["filter"] = filters
        if query.mailto:
            params["mailto"] = query.mailto
        response = requests.get(OPENALEX_WORKS_ENDPOINT, params=params, timeout=45)
        response.raise_for_status()
        return [_openalex_result(item) for item in response.json().get("results", [])]


class CrossrefSource:
    provider = "crossref"

    def search(self, query: LiteratureSearchQuery) -> list[LiteratureSearchResult]:
        params: dict[str, Any] = {
            "query.bibliographic": query.query,
            "rows": min(query.max_results, 1000),
            "select": "DOI,title,container-title,published-print,published-online,published,URL,score,abstract",
        }
        filters = _crossref_year_filter(query.from_year, query.to_year)
        if filters:
            params["filter"] = filters
        if query.mailto:
            params["mailto"] = query.mailto
        headers = {"User-Agent": _user_agent(query.mailto)}
        response = requests.get(CROSSREF_WORKS_ENDPOINT, params=params, headers=headers, timeout=45)
        response.raise_for_status()
        items = response.json().get("message", {}).get("items", []) or []
        return [_crossref_result(item) for item in items]


class ElsevierScopusSource:
    provider = "elsevier_scopus"

    def search(self, query: LiteratureSearchQuery) -> list[LiteratureSearchResult]:
        env_name = query.api_key_env or "ELSEVIER_API_KEY"
        api_key = os.getenv(env_name)
        if not api_key:
            raise ValueError(f"Environment variable '{env_name}' is not set")
        entries = search_scopus(api_key=api_key, query=query.query, count=query.max_results)
        return [_elsevier_result(entry) for entry in entries]


def search_literature(
    *,
    providers: Iterable[str],
    query: LiteratureSearchQuery,
    deduplicate: bool = True,
) -> list[LiteratureSearchResult]:
    results: list[LiteratureSearchResult] = []
    for provider_name in providers:
        provider = create_source(provider_name)
        results.extend(provider.search(query))
    return deduplicate_results(results) if deduplicate else results


def create_source(provider: str) -> LiteratureSource:
    normalized = provider.strip().lower()
    if normalized == "openalex":
        return OpenAlexSource()
    if normalized == "crossref":
        return CrossrefSource()
    if normalized in {"elsevier", "elsevier_scopus", "scopus"}:
        return ElsevierScopusSource()
    raise ValueError(f"Unknown literature source provider: {provider}")


def deduplicate_results(results: Iterable[LiteratureSearchResult]) -> list[LiteratureSearchResult]:
    out: list[LiteratureSearchResult] = []
    seen: set[str] = set()
    for result in results:
        key = _dedupe_key(result)
        if key in seen:
            continue
        seen.add(key)
        out.append(result)
    return out


def write_search_manifest(path: Path, results: list[LiteratureSearchResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "article_id",
        "title",
        "doi",
        "pii",
        "year",
        "journal",
        "provider",
        "score",
        "landing_url",
        "open_access_url",
        "text_file",
        "rank",
        "source",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rank, result in enumerate(results, start=1):
            writer.writerow(
                {
                    "article_id": result.article_id,
                    "title": result.title,
                    "doi": result.doi,
                    "pii": result.pii,
                    "year": result.year or "",
                    "journal": result.journal,
                    "provider": result.provider,
                    "score": result.score if result.score is not None else "",
                    "landing_url": result.landing_url,
                    "open_access_url": result.open_access_url,
                    "text_file": "",
                    "rank": rank,
                    "source": result.provider,
                }
            )


def _openalex_result(item: dict[str, Any]) -> LiteratureSearchResult:
    doi = _strip_doi_url(item.get("doi", ""))
    title = _clean_text(item.get("title", ""))
    best_oa = item.get("best_oa_location") or {}
    primary_location = item.get("primary_location") or {}
    source = (primary_location.get("source") or {}) if isinstance(primary_location, dict) else {}
    return LiteratureSearchResult(
        provider="openalex",
        article_id=str(item.get("id") or _fallback_id("openalex", doi, title)),
        title=title,
        doi=doi,
        year=_safe_int(item.get("publication_year")),
        journal=_clean_text(source.get("display_name", "")),
        abstract=_abstract_from_inverted_index(item.get("abstract_inverted_index")),
        landing_url=str(item.get("id") or ""),
        open_access_url=str(best_oa.get("pdf_url") or best_oa.get("landing_page_url") or ""),
        score=_safe_float(item.get("relevance_score")),
        raw=item,
    )


def _crossref_result(item: dict[str, Any]) -> LiteratureSearchResult:
    title = _first_list_item(item.get("title"))
    journal = _first_list_item(item.get("container-title"))
    return LiteratureSearchResult(
        provider="crossref",
        article_id=_fallback_id("crossref", item.get("DOI", ""), title),
        title=_clean_text(title),
        doi=_clean_text(item.get("DOI", "")).lower(),
        year=_crossref_year(item),
        journal=_clean_text(journal),
        abstract=_clean_text(item.get("abstract", "")),
        landing_url=str(item.get("URL") or ""),
        score=_safe_float(item.get("score")),
        raw=item,
    )


def _elsevier_result(entry: dict[str, Any]) -> LiteratureSearchResult:
    title = _clean_text(entry.get("dc:title", ""))
    doi = _clean_text(entry.get("prism:doi", "")).lower()
    return LiteratureSearchResult(
        provider="elsevier_scopus",
        article_id=_fallback_id("elsevier_scopus", doi, title),
        title=title,
        doi=doi,
        pii=_clean_text(entry.get("pii", "")),
        year=_safe_int(str(entry.get("prism:coverDate", ""))[:4]),
        journal=_clean_text(entry.get("prism:publicationName", "")),
        landing_url=_clean_text(entry.get("prism:url", "")),
        score=_safe_float(entry.get("score")),
        raw=entry,
    )


def _year_filter(from_year: int | None, to_year: int | None, *, field: str) -> str:
    filters = []
    if from_year is not None:
        filters.append(f"{field}:{from_year}-01-01")
    if to_year is not None:
        filters.append(f"to_publication_date:{to_year}-12-31")
    return ",".join(filters)


def _crossref_year_filter(from_year: int | None, to_year: int | None) -> str:
    filters = []
    if from_year is not None:
        filters.append(f"from-pub-date:{from_year}-01-01")
    if to_year is not None:
        filters.append(f"until-pub-date:{to_year}-12-31")
    return ",".join(filters)


def _crossref_year(item: dict[str, Any]) -> int | None:
    for key in ("published-print", "published-online", "published"):
        parts = item.get(key, {}).get("date-parts", [])
        if parts and parts[0]:
            return _safe_int(parts[0][0])
    return None


def _abstract_from_inverted_index(index: Any) -> str:
    if not isinstance(index, dict):
        return ""
    positions: list[tuple[int, str]] = []
    for word, indexes in index.items():
        if isinstance(indexes, list):
            positions.extend((int(pos), str(word)) for pos in indexes if isinstance(pos, int))
    return " ".join(word for _pos, word in sorted(positions))


def _dedupe_key(result: LiteratureSearchResult) -> str:
    if result.doi:
        return f"doi:{result.doi.lower()}"
    title = _clean_text(result.title).lower()
    return "title:" + hashlib.sha1(title.encode("utf-8", errors="ignore")).hexdigest()


def _fallback_id(provider: str, doi: str, title: str) -> str:
    raw = "|".join([provider, _clean_text(doi).lower(), _clean_text(title).lower()])
    return provider + ":" + hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _strip_doi_url(value: str) -> str:
    value = _clean_text(value)
    return value.removeprefix("https://doi.org/").removeprefix("http://doi.org/").lower()


def _first_list_item(value: Any) -> str:
    if isinstance(value, list) and value:
        return str(value[0])
    return str(value or "")


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _user_agent(mailto: str | None) -> str:
    suffix = f" mailto:{mailto}" if mailto else ""
    return f"igem-drylab-2026/0.1{suffix}"

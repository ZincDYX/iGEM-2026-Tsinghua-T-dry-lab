from __future__ import annotations

from pathlib import Path

from igem_drylab.literature.sources import (
    LiteratureSearchQuery,
    deduplicate_results,
    search_literature,
    write_search_manifest,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_openalex_search_normalizes_and_writes_manifest(monkeypatch, tmp_path):
    def fake_get(url, params=None, headers=None, timeout=None):
        return FakeResponse(
            {
                "results": [
                    {
                        "id": "https://openalex.org/W1",
                        "doi": "https://doi.org/10.0000/glabridin",
                        "title": "Glabridin biosynthesis",
                        "publication_year": 2026,
                        "primary_location": {"source": {"display_name": "Example Journal"}},
                        "best_oa_location": {"pdf_url": "https://example.org/paper.pdf"},
                        "relevance_score": 12.5,
                    }
                ]
            }
        )

    monkeypatch.setattr("igem_drylab.literature.sources.requests.get", fake_get)
    results = search_literature(
        providers=["openalex"],
        query=LiteratureSearchQuery(query="glabridin", max_results=5),
    )
    manifest = tmp_path / "manifest.csv"
    write_search_manifest(manifest, results)

    assert len(results) == 1
    assert results[0].doi == "10.0000/glabridin"
    assert "Glabridin biosynthesis" in manifest.read_text(encoding="utf-8-sig")


def test_crossref_search_normalizes_result(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        return FakeResponse(
            {
                "message": {
                    "items": [
                        {
                            "DOI": "10.0000/crossref",
                            "title": ["Crossref glabridin record"],
                            "container-title": ["Journal"],
                            "published": {"date-parts": [[2025]]},
                            "URL": "https://doi.org/10.0000/crossref",
                            "score": 8.0,
                        }
                    ]
                }
            }
        )

    monkeypatch.setattr("igem_drylab.literature.sources.requests.get", fake_get)
    results = search_literature(
        providers=["crossref"],
        query=LiteratureSearchQuery(query="glabridin", max_results=5, mailto="team@example.org"),
    )

    assert len(results) == 1
    assert results[0].provider == "crossref"
    assert results[0].year == 2025


def test_deduplicate_results_prefers_first_provider(monkeypatch):
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append(url)
        if "openalex" in url:
            return FakeResponse({"results": [{"doi": "https://doi.org/10.0000/same", "title": "Same"}]})
        return FakeResponse({"message": {"items": [{"DOI": "10.0000/same", "title": ["Same"]}]}})

    monkeypatch.setattr("igem_drylab.literature.sources.requests.get", fake_get)
    results = search_literature(
        providers=["openalex", "crossref"],
        query=LiteratureSearchQuery(query="same", max_results=5),
    )

    assert len(calls) == 2
    assert len(deduplicate_results(results)) == 1
    assert results[0].provider == "openalex"

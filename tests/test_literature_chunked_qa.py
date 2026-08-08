from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from igem_drylab.literature.chunked import chunk_text, extract_records_chunked
from igem_drylab.literature.qa import answer_question, load_evidence_documents, search_evidence
from igem_drylab.literature.schema import load_schema


class FakeClient:
    def complete_json(self, prompt: str) -> dict[str, Any]:
        record = {
            "enzyme_name": {"value": "GgOC1", "unit": None, "evidence": "GgOC1 converted the substrate."},
            "substrate_name": {"value": "compound 11", "unit": None, "evidence": "compound 11"},
        }
        return {"records": [record]}


class RepairClient:
    def complete_json(self, prompt: str) -> dict[str, Any]:
        if "Repair this extraction" in prompt:
            return {"record": {"enzyme_name": {"value": "GgOC1", "unit": None, "evidence": "quoted"}}}
        return {"records": [{"enzyme_name": "GgOC1"}]}


def test_chunk_text_overlap_and_chunked_extraction_deduplicate():
    chunks = chunk_text("A" * 400 + ". " + "B" * 400, max_characters=500, overlap_characters=80)
    assert len(chunks) == 2
    schema = load_schema(Path("data/schemas/glabridin_enzyme_catalysis.schema.json"))
    results = extract_records_chunked(
        text="first paragraph\n\nsecond paragraph", schema=schema, examples=[], client=FakeClient(), source_id="10.1/demo",
        max_characters=200, overlap_characters=0,
    )
    assert len(results) == 1
    assert results[0].source_id == "10.1/demo"
    assert results[0].validation_status == "valid"


def test_chunked_extraction_repairs_only_when_explicitly_enabled():
    schema = load_schema(Path("data/schemas/glabridin_enzyme_catalysis.schema.json"))
    result = extract_records_chunked(
        text="A short paper.", schema=schema, examples=[], client=RepairClient(), max_characters=200,
        repair_invalid=True,
    )
    assert result[0].record["enzyme_name"]["value"] == "GgOC1"
    assert result[0].validation_status == "valid"


def test_local_qa_returns_doi_and_missing_database_is_structured(tmp_path):
    evidence = tmp_path / "evidence.jsonl"
    rows = [
        {"record_id": "a", "title": "Glabridin enzyme study", "doi": "10.1000/a", "evidence": "OC converts intermediate 11 to glabridin."},
        {"record_id": "b", "title": "Unrelated", "doi": "10.1000/b", "evidence": "A yeast growth curve."},
    ]
    evidence.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    hits = search_evidence("Which enzyme converts intermediate 11 to glabridin?", load_evidence_documents(evidence))
    assert hits[0]["doi"] == "10.1000/a"
    assert answer_question("glabridin enzyme", evidence)["status"] == "retrieved"
    assert answer_question("anything", tmp_path / "missing.jsonl")["status"] == "database_unavailable"

from __future__ import annotations

import json
from pathlib import Path

from igem_drylab.literature.qa import (
    EvidenceDocument,
    RankedEvidence,
    answer_question,
    bm25_search,
    deduplicate_sources,
    load_evidence_documents,
    mmr_select,
    retrieve_evidence,
    rrf_fuse,
)
from igem_drylab.literature.semantic import evidence_fingerprint, load_embedding_cache, write_embedding_cache


def _evidence_file(tmp_path: Path) -> Path:
    rows = [
        {"record_id": "dmt-km", "title": "DMT kinetics", "doi": "10.1000/dmt", "evidence": "Measured Km for DMT acting on compound 11 in yeast.", "fields": {"enzyme": "GgDMT1", "substrate": "11", "parameter_type": "Km", "host": "Saccharomyces cerevisiae"}},
        {"record_id": "dmt-repeat", "title": "DMT kinetics follow-up", "doi": "10.1000/dmt", "evidence": "Measured Km for DMT acting on compound 11 in yeast.", "fields": {"enzyme": "GgDMT1", "substrate": "11", "parameter_type": "Km"}},
        {"record_id": "oc-activity", "title": "OC activity", "doi": "10.1000/oc", "evidence": "OC activity produces intermediate 11.", "fields": {"enzyme": "GgOC1", "substrate": "10", "product": "11"}},
        {"record_id": "transferable", "title": "DMT activity in a transfer system", "doi": "10.1000/transfer", "evidence": "DMT activity was measured in a different host.", "fields": {"enzyme": "DMT", "parameter_type": "activity"}},
    ]
    path = tmp_path / "evidence.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    return path


class FakeSemanticBackend:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        if self.fail:
            raise RuntimeError("offline")
        if len(texts) == 1:
            return [[1.0, 0.0]]
        return [[1.0, 0.0] if "OC" in text else [0.5, 0.5] for text in texts]


class FakeChatClient:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.calls = 0

    def complete_json(self, prompt: str) -> dict[str, object]:
        self.calls += 1
        assert "Retrieved evidence is not a validated model parameter" in prompt
        return self.response


def test_bm25_exact_tokens_and_metadata_conditioning() -> None:
    documents = [
        EvidenceDocument("oc", "Activity assay", "10.1/oc", "Activity was measured.", fields={"enzyme": "GgOC1"}),
        EvidenceDocument("dmt", "Activity assay", "10.1/dmt", "Activity was measured.", fields={"enzyme": "GgDMT1"}),
    ]
    ranked = bm25_search("activity", documents, constraints={"enzyme": "DMT"})
    assert documents[ranked[0].index].record_id == "dmt"
    assert ranked[0].matched_metadata == ("enzyme",)


def test_semantic_disabled_or_failed_falls_back_to_bm25(tmp_path: Path) -> None:
    path = _evidence_file(tmp_path)
    disabled = answer_question("OC activity", path)
    failed = answer_question("OC activity", path, semantic_enabled=True, semantic_backend=FakeSemanticBackend(fail=True))
    assert disabled["status"] == failed["status"] == "retrieved"
    assert disabled["retrieval"]["semantic"] == "disabled"
    assert failed["retrieval"]["semantic"] == "unavailable"
    assert failed["sources"]


def test_rrf_deduplication_and_doi_diversity(tmp_path: Path) -> None:
    documents = load_evidence_documents(_evidence_file(tmp_path))
    lexical = [RankedEvidence(index=0, lexical_rank=2), RankedEvidence(index=2, lexical_rank=1)]
    semantic = [RankedEvidence(index=0, semantic_rank=1), RankedEvidence(index=3, semantic_rank=2)]
    fused = rrf_fuse(lexical, semantic)
    assert fused[0].index == 0
    deduplicated = deduplicate_sources([RankedEvidence(index=0, rrf_score=.3), RankedEvidence(index=1, rrf_score=.2), RankedEvidence(index=2, rrf_score=.1)], documents)
    assert [documents[item.index].record_id for item in deduplicated] == ["dmt-km", "oc-activity"]


def test_mmr_prefers_a_relevant_non_duplicate_second_source(tmp_path: Path) -> None:
    documents = load_evidence_documents(_evidence_file(tmp_path))
    candidates = [RankedEvidence(index=0, rrf_score=.3), RankedEvidence(index=1, rrf_score=.28), RankedEvidence(index=2, rrf_score=.22)]
    selected = mmr_select(candidates, documents, top_k=2)
    assert [item.index for item in selected] == [0, 2]


def test_retrieve_only_never_calls_chat_and_synthesis_calls_once(tmp_path: Path) -> None:
    path = _evidence_file(tmp_path)
    client = FakeChatClient({"answer": "OC activity is directly reported [oc-activity].", "claims": [{"claim": "OC activity is reported.", "evidence_ids": ["oc-activity"], "type": "direct_report"}], "limitations": [], "suggested_next_steps": [], "selected_evidence_ids": ["oc-activity"]})
    retrieve_only = answer_question("OC activity", path, chat_client=client)
    synthesized = answer_question("OC activity", path, mode="synthesize", chat_client=client)
    assert retrieve_only["mode"] == "retrieve_only"
    assert client.calls == 1
    assert synthesized["status"] == "retrieved"
    assert synthesized["claims"][0]["evidence_ids"] == ["oc-activity"]


def test_invalid_synthesis_falls_back_to_retrieval_results(tmp_path: Path) -> None:
    path = _evidence_file(tmp_path)
    result = answer_question("OC activity", path, mode="synthesize", chat_client=FakeChatClient({"claims": []}))
    assert result["ok"] is True
    assert result["status"] == "synthesis_error"
    assert result["sources"]


def test_retrieve_evidence_records_semantic_route_and_constraints(tmp_path: Path) -> None:
    path = _evidence_file(tmp_path)
    sources, analysis, retrieval = retrieve_evidence("DMT compound 11 Km yeast", load_evidence_documents(path), semantic_enabled=True, semantic_backend=FakeSemanticBackend(), evidence_path=path)
    assert sources and sources[0]["retrieval"]["lexical_rank"] is not None
    assert analysis["constraints"]["enzyme"] == "DMT"
    assert retrieval["semantic"] == "used"


def test_embedding_cache_tracks_evidence_fingerprint_and_model(tmp_path: Path) -> None:
    path = _evidence_file(tmp_path)
    fingerprint = evidence_fingerprint(path)
    record_ids = [document.record_id for document in load_evidence_documents(path)]
    vectors = [[1.0, 0.0] for _ in record_ids]
    write_embedding_cache(path, fingerprint=fingerprint, model="test-model", record_ids=record_ids, vectors=vectors)
    assert load_embedding_cache(path, fingerprint=fingerprint, model="test-model", record_ids=record_ids) == vectors
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert load_embedding_cache(path, fingerprint=evidence_fingerprint(path), model="test-model", record_ids=record_ids) is None

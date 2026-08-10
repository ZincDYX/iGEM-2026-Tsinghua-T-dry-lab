from __future__ import annotations

import json
import csv
from pathlib import Path

from igem_drylab.literature.qa import (
    DEFAULT_EMBEDDING_BATCH_SIZE,
    EvidenceDocument,
    RankedEvidence,
    _document_embeddings,
    _metadata_matches,
    _project_metadata_matches,
    answer_question,
    bm25_search,
    deduplicate_sources,
    load_evidence_documents,
    mmr_select,
    retrieve_evidence,
    rrf_fuse,
)
from igem_drylab.literature.semantic import EmbeddingApiBackend, SemanticBackendError, cache_path_for, evidence_fingerprint, load_embedding_cache, write_embedding_cache


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


def _legacy_evidence_file(tmp_path: Path) -> Path:
    rows = [
        {
            "aggregate_record_id": "legacy-dmt-11", "article_id": "article-a", "title": "DMT kcat evidence", "doi": "10.1000/legacy-a",
            "best_enzyme_name_value": "GgDMT1", "best_substrate_name_value": "11", "primary_result_metric": "kcat",
            "primary_result_value": "2.4", "primary_result_unit": "h^-1", "primary_result_evidence": "DMT kcat was measured for compound 11.",
            "project_tier": "direct", "is_project_glabridin_direct": "True", "is_project_high_transfer_llps": "True", "llps_transferability_class": "high",
        },
        {
            "aggregate_record_id": "legacy-dmt-9", "article_id": "article-b", "title_clean": "DMT Km evidence", "doi": "10.1000/legacy-b",
            "best_enzyme_name_value": "GgDMT1", "best_substrate_name_value": "9", "primary_result_metric": "Km",
            "primary_result_evidence": "DMT Km was measured for compound 9.",
        },
        {
            "aggregate_record_id": "legacy-oc-10", "article_id": "article-c", "title": "OC kcat evidence", "doi": "10.1000/legacy-c",
            "best_enzyme_name_value": "GgOC1", "best_substrate_name_value": "10", "primary_result_metric": "kcat",
            "primary_result_evidence": "OC kcat was measured for compound 10.",
        },
    ]
    path = tmp_path / "project_conditioned_evidence_database.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({key for row in rows for key in row}))
        writer.writeheader()
        writer.writerows(rows)
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


class RecordingEmbeddingBackend:
    def __init__(self, *, fail_on_call: int | None = None) -> None:
        self.calls: list[int] = []
        self.fail_on_call = fail_on_call

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(len(texts))
        if self.fail_on_call == len(self.calls):
            raise SemanticBackendError("illustrative embedding failure")
        return [[float(index), 1.0] for index, _text in enumerate(texts)]


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


def test_embedding_corpus_is_batched_and_cache_is_written_only_after_success(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "large.jsonl"
    path.write_text("\n".join(json.dumps({"record_id": f"r-{index}", "title": "Evidence", "doi": f"10.1/{index}", "evidence": f"record {index}"}) for index in range(DEFAULT_EMBEDDING_BATCH_SIZE + 2)), encoding="utf-8")
    documents = load_evidence_documents(path)
    calls: list[int] = []

    def successful_embed(_self, texts):
        calls.append(len(texts))
        return [[float(index), 1.0] for index, _text in enumerate(texts)]

    monkeypatch.setattr(EmbeddingApiBackend, "embed", successful_embed)
    backend = EmbeddingApiBackend(api_base="https://example.invalid", api_key="unused", model="batch-test")
    vectors = _document_embeddings(documents, backend=backend, evidence_path=path)
    assert calls == [DEFAULT_EMBEDDING_BATCH_SIZE, 2]
    assert len(vectors) == len(documents)
    assert cache_path_for(path).is_file()

    calls.clear()
    assert _document_embeddings(documents, backend=backend, evidence_path=path) == vectors
    assert calls == []

    cache_path_for(path).unlink()
    failed_calls: list[int] = []

    def failing_embed(_self, texts):
        failed_calls.append(len(texts))
        if len(failed_calls) == 2:
            raise SemanticBackendError("batch failed")
        return [[1.0, 0.0] for _text in texts]

    monkeypatch.setattr(EmbeddingApiBackend, "embed", failing_embed)
    try:
        _document_embeddings(documents, backend=backend, evidence_path=path)
    except SemanticBackendError:
        pass
    else:
        raise AssertionError("a failed embedding batch must propagate to semantic fallback")
    assert not cache_path_for(path).exists()


def test_explicit_constraints_filter_candidates_but_inferred_constraints_remain_soft(tmp_path: Path) -> None:
    path = _evidence_file(tmp_path)
    documents = load_evidence_documents(path)
    sources, analysis, _retrieval = retrieve_evidence("kinetics compound 11", documents, constraints={"enzyme": "DMT"})
    assert sources and {source["record_id"] for source in sources} <= {"dmt-km", "dmt-repeat", "transferable"}
    assert analysis["explicit_constraints"] == {"enzyme": "DMT"}
    assert analysis["active_constraints"] == {"enzyme": "DMT"}

    soft_documents = [
        EvidenceDocument("missing-metadata", "DMT promiscuity", "10.1/missing", "DMT promiscuity evidence reports multiple products."),
        EvidenceDocument("tagged", "Other evidence", "10.1/tagged", "Less relevant evidence.", fields={"enzyme": "DMT"}),
    ]
    soft_sources, soft_analysis, _retrieval = retrieve_evidence("What evidence supports DMT promiscuity?", soft_documents)
    assert "missing-metadata" in [source["record_id"] for source in soft_sources]
    assert soft_analysis["inferred_constraints"] == {"enzyme": "DMT"}
    assert soft_analysis["explicit_constraints"] == {}


def test_explicit_constraint_relaxation_is_visible_and_semantic_uses_same_subset(tmp_path: Path) -> None:
    path = _evidence_file(tmp_path)
    documents = load_evidence_documents(path)
    sources, analysis, retrieval = retrieve_evidence(
        "DMT compound 11 kinetics",
        documents,
        constraints={"enzyme": "DMT", "substrate": "11", "parameter_type": "kcat"},
        semantic_enabled=True,
        semantic_backend=FakeSemanticBackend(),
        evidence_path=path,
    )
    assert sources and {source["record_id"] for source in sources} <= {"dmt-km", "dmt-repeat", "transferable"}
    assert analysis["active_constraints"] == {"enzyme": "DMT"}
    assert analysis["relaxed_constraints"] == ["substrate=11", "parameter_type=kcat"]
    assert retrieval["semantic"] == "used"


def test_legacy_project_conditioned_csv_loads_as_canonical_evidence(tmp_path: Path) -> None:
    documents = load_evidence_documents(_legacy_evidence_file(tmp_path))
    assert [document.record_id for document in documents] == ["legacy-dmt-11", "legacy-dmt-9", "legacy-oc-10"]
    dmt_11 = documents[0]
    assert dmt_11.title == "DMT kcat evidence"
    assert dmt_11.doi == "10.1000/legacy-a"
    assert dmt_11.evidence == "DMT kcat was measured for compound 11."
    assert _metadata_matches(dmt_11, {"enzyme": "DMT", "substrate": "11", "parameter_type": "kcat"}) == ("enzyme", "substrate", "parameter_type")
    assert dmt_11.fields["project_tier"] == "direct"
    assert dmt_11.fields["is_project_glabridin_direct"] == "True"
    assert dmt_11.fields["llps_transferability_class"] == "high"
    assert "project:is_project_high_transfer_llps" in _project_metadata_matches(dmt_11)


def test_legacy_csv_supports_constraints_bm25_and_canonical_precedence(tmp_path: Path) -> None:
    path = _legacy_evidence_file(tmp_path)
    documents = load_evidence_documents(path)
    sources, _analysis, _retrieval = retrieve_evidence(
        "What evidence reports DMT kcat for compound 11?",
        documents,
        constraints={"enzyme": "DMT", "substrate": "11"},
    )
    assert [source["record_id"] for source in sources] == ["legacy-dmt-11"]

    canonical = tmp_path / "canonical_wins.csv"
    canonical.write_text(
        "record_id,title,doi,evidence,enzyme,best_enzyme_name_value\n"
        "canonical,Canonical field,10.1000/canonical,Canonical metadata must win.,OC,GgDMT1\n",
        encoding="utf-8",
    )
    document = load_evidence_documents(canonical)[0]
    assert document.fields["enzyme"] == "OC"
    assert _metadata_matches(document, {"enzyme": "OC"}) == ("enzyme",)

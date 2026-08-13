from __future__ import annotations

import json
import csv
from pathlib import Path

from igem_drylab.literature.qa import (
    DEFAULT_EMBEDDING_BATCH_SIZE,
    EvidenceDocument,
    RankedEvidence,
    _document_embeddings,
    _evidence_tier,
    _index_text,
    _metadata_matches,
    _project_metadata_matches,
    _relevant_candidates,
    _sentences,
    _stage_one_candidates,
    compact_evidence_sources,
    get_evidence_detail,
    project_evidence_fields,
    synthesize_answer,
    answer_question,
    bm25_search,
    deduplicate_sources,
    load_evidence_documents,
    mmr_select,
    parse_query_intent,
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


def test_incremental_embedding_cache_reuses_overlap_and_embeds_only_new_candidates(tmp_path: Path, monkeypatch) -> None:
    path = _evidence_file(tmp_path)
    documents = load_evidence_documents(path)
    calls: list[list[str]] = []

    def embed(_self, texts):
        calls.append(list(texts))
        return [[float(index + 1), 1.0] for index, _text in enumerate(texts)]

    monkeypatch.setattr(EmbeddingApiBackend, "embed", embed)
    backend = EmbeddingApiBackend(api_base="https://example.invalid", api_key="unused", model="incremental-test")
    _document_embeddings(documents[2:3], backend=backend, evidence_path=path)
    _document_embeddings(documents[2:], backend=backend, evidence_path=path)
    assert [len(batch) for batch in calls] == [1, 1]
    assert "OC activity" in calls[0][0]
    assert "DMT activity" in calls[1][0]


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
    assert _metadata_matches(document, {"enzyme": "DMT"}) == ()
    assert "GgDMT1" not in _index_text(document)
    assert bm25_search("DMT", [document]) == []
    assert bm25_search("OC", [document])[0].index == 0


def test_multi_entity_llps_intent_and_candidate_scoped_embeddings(tmp_path: Path) -> None:
    intent = parse_query_intent("Will the enzymatic activity of OC and DMT sequestered within LLPS condensates be affected?")
    assert set(intent["enzymes"]) == {"OC", "DMT"}
    assert intent["enzymes"] == ["OC", "DMT"]
    assert "activity" in intent["outcomes"] and "llps" in intent["context"]

    rows = [
        {"record_id": "direct", "title": "OC condensate activity", "doi": "10.1/direct", "evidence": "OC enzyme activity in LLPS condensates.", "fields": {"enzyme": "OC", "is_project_llps_related": True}},
        {"record_id": "transfer", "title": "Enzyme condensate catalysis", "doi": "10.1/transfer", "evidence": "Enzyme catalytic activity was altered in phase separation.", "fields": {"is_project_high_transfer_llps": True}},
    ] + [{"record_id": f"noise-{i}", "title": "Unrelated morphology", "doi": f"10.1/noise-{i}", "evidence": "FUS condensate morphology."} for i in range(250)]
    path = tmp_path / "noisy.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    class CaptureBackend(FakeSemanticBackend):
        def __init__(self): super().__init__(); self.batch_sizes = []
        def embed(self, texts): self.batch_sizes.append(len(texts)); return super().embed(texts)
    backend = CaptureBackend()
    sources, _analysis, retrieval = retrieve_evidence("OC and DMT enzyme activity in LLPS condensates", load_evidence_documents(path), semantic_enabled=True, semantic_backend=backend, evidence_path=path)
    assert sources[0]["record_id"] == "direct"
    assert sources[0]["retrieval"]["tier"] == "direct"
    assert retrieval["semantic"] == "used"
    assert max(backend.batch_sizes[:-1]) < len(rows)


def test_stage_one_preserves_entity_route_when_bm25_quota_is_full() -> None:
    noise = [
        EvidenceDocument(
            f"noise-{index:03d}", "Generic LLPS activity", f"10.1/noise-{index}",
            "DMT enzyme activity activity activity in LLPS condensates.", fields={"enzyme": "DMT"},
        )
        for index in range(120)
    ]
    routed = EvidenceDocument(
        "z-dmt-route", "Transferable condensate assay", "10.1/dmt-route",
        "Catalytic activity was measured inside an LLPS condensate.", fields={"is_project_high_transfer_llps": True},
    )
    documents = [*noise, routed]
    intent = parse_query_intent("DMT activity in LLPS condensates")
    lexical = bm25_search("DMT activity in LLPS condensates", documents)
    assert lexical.index(next(hit for hit in lexical if hit.index == len(noise))) >= 80
    candidates = _stage_one_candidates("DMT activity in LLPS condensates", documents, list(range(len(documents))), intent)
    assert len(noise) in candidates
    assert len(candidates) <= 200


def test_llps_activity_query_rejects_morphology_background() -> None:
    documents = [
        EvidenceDocument("morphology", "FUS condensate morphology", "10.1/morphology", "FUS condensate morphology and DNAJB6 colocalization."),
        EvidenceDocument("catalysis", "Enzyme catalysis in LLPS", "10.1/catalysis", "Enzyme catalytic activity was measured in an LLPS condensate."),
    ]
    intent = parse_query_intent("Will enzyme activity be affected in LLPS condensates?")
    fused = rrf_fuse(bm25_search("Will enzyme activity be affected in LLPS condensates?", documents), [])
    relevant = _relevant_candidates(fused, documents, intent)
    assert [documents[candidate.index].record_id for candidate in relevant] == ["catalysis"]


def test_direct_tier_requires_all_requested_intent_dimensions() -> None:
    documents = [
        EvidenceDocument("dmt-soluble", "DMT soluble kinetics", "10.1/soluble", "DMT kinetic activity in a soluble assay.", fields={"enzyme": "DMT"}),
        EvidenceDocument("other-llps", "Other enzyme in LLPS", "10.1/other", "An enzyme catalytic activity was measured in LLPS condensates.", fields={"enzyme": "OTHER"}),
        EvidenceDocument("dmt-llps", "DMT in LLPS", "10.1/direct", "DMT catalytic activity was measured in an LLPS condensate.", fields={"enzyme": "DMT"}),
    ]
    intent = parse_query_intent("DMT activity in LLPS condensates")
    assert _evidence_tier(documents[0], intent) == "background"
    assert _evidence_tier(documents[1], intent) == "transferable"
    assert _evidence_tier(documents[2], intent) == "direct"


def test_transferable_fallback_never_pads_with_background(tmp_path: Path) -> None:
    path = tmp_path / "fallback.jsonl"
    rows = [
        {"record_id": "transfer", "title": "Other enzyme LLPS catalysis", "doi": "10.1/transfer", "evidence": "A non-project enzyme catalytic activity was measured in an LLPS condensate.", "fields": {"enzyme": "OTHER"}},
        {"record_id": "background", "title": "FUS morphology", "doi": "10.1/background", "evidence": "FUS condensate morphology and colocalization.", "fields": {}},
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    sources, _analysis, retrieval = retrieve_evidence("OC and DMT activity in LLPS condensates", load_evidence_documents(path), top_k=5)
    assert [source["record_id"] for source in sources] == ["transfer"]
    assert sources[0]["retrieval"]["tier"] == "transferable"
    assert retrieval["evidence_mode"] == "transferable_fallback"


def test_transferable_synthesis_prompt_preserves_epistemic_boundary(tmp_path: Path) -> None:
    path = tmp_path / "transfer-synthesis.jsonl"
    path.write_text(json.dumps({"record_id": "transfer", "title": "Other enzyme LLPS catalysis", "doi": "10.1/transfer", "evidence": "A non-project enzyme catalytic activity was measured in an LLPS condensate.", "fields": {"enzyme": "OTHER"}}), encoding="utf-8")

    class CaptureChatClient:
        def __init__(self) -> None: self.prompt = ""
        def complete_json(self, prompt: str) -> dict[str, object]:
            self.prompt = prompt
            return {"answer": "Transferable evidence only.", "claims": [], "limitations": [], "suggested_next_steps": [], "selected_evidence_ids": ["transfer"]}

    client = CaptureChatClient()
    result = answer_question("OC and DMT activity in LLPS condensates", path, mode="synthesize", chat_client=client)
    assert result["retrieval"]["evidence_mode"] == "transferable_fallback"
    assert "do not present them as facts about the queried enzymes" in client.prompt


def test_synthesis_normalizes_presentation_structure_and_drops_uncited_claims(tmp_path: Path) -> None:
    path = _evidence_file(tmp_path)
    client = FakeChatClient({
        "answer": "The cited studies support a bounded conclusion. Evidence sufficiency is limited to those studies.",
        "claims": [
            {"claim": "DMT kinetics were measured for compound 11 in yeast.", "evidence_ids": ["dmt-repeat"], "type": "direct_report"},
            {"claim": "This unsupported statement must not render.", "evidence_ids": ["missing"], "type": "direct_report"},
            {"claim": "DMT kinetics were measured for compound 11 in yeast.", "evidence_ids": ["dmt-repeat"], "type": "direct_report"},
        ],
        "limitations": ["Assay conditions differ between records.", "The cited studies support a bounded conclusion."],
        "suggested_next_steps": [], "selected_evidence_ids": ["dmt-repeat"],
    })
    result = answer_question("DMT kinetics", path, mode="synthesize", chat_client=client)
    assert 2 <= len(_sentences(result["answer"])) <= 4
    assert len(result["claims"]) == 1
    assert result["claims"][0]["evidence_ids"] == ["dmt-repeat"]
    assert "unsupported" not in " ".join(item["claim"].lower() for item in result["claims"])
    assert all(item["claim"] not in result["answer"] for item in result["claims"])
    assert result["limitations"] == ["Assay conditions differ between records."]


def test_transferable_synthesis_uses_stable_explicit_answer(tmp_path: Path) -> None:
    path = tmp_path / "transfer.jsonl"
    path.write_text(json.dumps({"record_id": "transfer", "title": "Synthetic biomolecular condensate catalysis", "doi": "10.1/transfer", "evidence": "An OC/DMT-relevant biomolecular condensate enzyme system produced product by catalytic activity.", "fields": {"enzyme": "OTHER"}}), encoding="utf-8")
    client = FakeChatClient({"answer": "An overlong answer that should not be used.", "claims": [{"claim": "The related condensate system produced product.", "evidence_ids": ["transfer"]}], "limitations": [], "suggested_next_steps": [], "selected_evidence_ids": ["transfer"]})
    result = answer_question("OC and DMT activity in LLPS condensates", path, mode="synthesize", chat_client=client)
    assert "No direct project-specific evidence was found." in result["answer"]
    assert "cannot establish the effect for OC/DMT" in result["answer"]
    assert 2 <= len(_sentences(result["answer"])) <= 4


def test_transferable_claims_keep_cited_ectoine_glycine_lnt_examples() -> None:
    sources = [
        {"record_id": "ectoine", "title": "Ectoine condensate biosynthesis", "doi": "10.1/ectoine", "evidence": "", "fields": {}},
        {"record_id": "glycine", "title": "Glycine condensate system", "doi": "10.1/glycine", "evidence": "", "fields": {}},
        {"record_id": "lnt", "title": "LNT condensate system", "doi": "10.1/lnt", "evidence": "", "fields": {}},
    ]
    client = FakeChatClient({
        "answer": "Related systems may be informative.",
        "claims": [
            {"claim": "An LLPS enzyme system improved ectoine biosynthesis.", "evidence_ids": ["ectoine"], "type": "direct_report"},
            {"claim": "A condensate system reported glycine product formation.", "evidence_ids": ["glycine"], "type": "direct_report"},
            {"claim": "A related condensate study reported LNT production.", "evidence_ids": ["lnt"], "type": "direct_report"},
        ],
        "limitations": ["Cross-system assay conditions differ."], "suggested_next_steps": [],
        "selected_evidence_ids": ["ectoine", "glycine", "lnt"],
    })
    result = synthesize_answer("OC/DMT activity in LLPS", {}, sources, evidence_mode="transferable_fallback", client=client)
    assert len(result["claims"]) == 3
    assert [claim["evidence_ids"][0] for claim in result["claims"]] == ["ectoine", "glycine", "lnt"]
    assert all(claim["evidence_ids"] for claim in result["claims"])
    assert "No direct project-specific evidence was found." in result["answer"]


def test_cited_claim_safety_fallback_prevents_empty_claim_list() -> None:
    sources = [{"record_id": "r1", "title": "Study", "doi": "10.1/r1", "evidence": "", "fields": {}}]
    client = FakeChatClient({
        "answer": "The cited study supports a bounded conclusion.",
        "claims": [{"claim": "The cited study supports a bounded conclusion.", "evidence_ids": ["r1"]}],
        "limitations": [], "suggested_next_steps": [], "selected_evidence_ids": ["r1"],
    })
    result = synthesize_answer("question", {}, sources, client=client)
    assert result["claims"] == [{"claim": "The cited study supports a bounded conclusion.", "evidence_ids": ["r1"], "type": "interpretation"}]


def test_no_relevant_evidence_returns_no_match_mode() -> None:
    documents = [EvidenceDocument("background", "FUS morphology", "10.1/background", "FUS condensate morphology and colocalization.")]
    sources, _analysis, retrieval = retrieve_evidence("DMT activity in LLPS condensates", documents)
    assert sources == []
    assert retrieval["evidence_mode"] == "no_match"


def test_peroxisome_and_conformation_records_are_not_llps_transferable() -> None:
    intent = parse_query_intent("Will enzyme activity in LLPS condensates be affected?")
    peroxisome = EvidenceDocument("peroxisome", "Peroxisome activity", "10.1/peroxisome", "MmCAR showed 45% higher activity in the peroxisome than in the cytosol.")
    conformation = EvidenceDocument(
        "calcium", "Calcium conformational activity", "10.1/calcium",
        "G6PDH activity changed after Ca2+-induced conformational rearrangement.",
        fields={"is_project_llps_related": True, "high_transferability": True},
    )
    assert _evidence_tier(peroxisome, intent) == "background"
    assert _evidence_tier(conformation, intent) == "background"


def test_metadata_recovers_stage_one_candidate_but_cannot_qualify_it() -> None:
    document = EvidenceDocument(
        "metadata-only", "Recruitment study", "10.1/metadata", "The enzyme localized to a protein assembly.",
        fields={"is_project_high_transfer_llps": True},
    )
    intent = parse_query_intent("enzyme activity in LLPS condensates")
    candidates = _stage_one_candidates("enzyme activity in LLPS condensates", [document], [0], intent)
    assert candidates == [0]
    assert _evidence_tier(document, intent) == "background"


def test_genuine_condensate_catalysis_is_transferable_without_project_metadata() -> None:
    document = EvidenceDocument(
        "gcs", "Condensate enzyme reaction", "10.1/gcs",
        "A condensate system containing GCS enzymes produced 5.0 mM glycine in 1 hour.",
    )
    assert _evidence_tier(document, parse_query_intent("OC activity in LLPS condensates")) == "transferable"


def test_direct_tier_respects_substrate_and_product_constraints() -> None:
    dmt_9 = EvidenceDocument("dmt-9", "DMT kcat compound 9", "10.1/dmt9", "DMT kcat was measured for compound 9.", fields={"enzyme": "DMT", "substrate": "9", "parameter_type": "kcat"})
    dmt_11 = EvidenceDocument("dmt-11", "DMT kcat compound 11", "10.1/dmt11", "DMT kcat was measured for compound 11.", fields={"enzyme": "DMT", "substrate": "11", "parameter_type": "kcat"})
    kinetic_intent = parse_query_intent("DMT kcat for compound 11")
    assert _evidence_tier(dmt_9, kinetic_intent) != "direct"
    assert _evidence_tier(dmt_11, kinetic_intent) == "direct"

    unrelated_product = EvidenceDocument("other-product", "Other product titer", "10.1/other", "An unrelated product titer was reported.", fields={"product": "other"})
    glabridin = EvidenceDocument("glabridin", "Glabridin production", "10.1/glabridin", "Glabridin production was measured in yeast.", fields={"product": "glabridin"})
    product_intent = parse_query_intent("glabridin production")
    assert _evidence_tier(unrelated_product, product_intent) != "direct"
    assert _evidence_tier(glabridin, product_intent) == "direct"


def test_compact_agent_evidence_is_query_aware_and_preserves_provenance(tmp_path: Path) -> None:
    path = tmp_path / "compact.jsonl"
    path.write_text(json.dumps({"record_id": "oc", "title": "OC LLPS activity", "doi": "10.1/oc", "evidence": "OC catalytic activity in an LLPS condensate converted compound 10 to compound 11.", "fields": {"enzyme": "OC", "substrate": "10", "product": "11", "primary_result_metric": "kcat", "primary_result_value": "1.2", "primary_result_unit": "s^-1", "reaction_temperature": "30 C", "irrelevant_legacy_field": "omit", "clean_level": "reviewed"}}), encoding="utf-8")
    result = answer_question("OC activity in LLPS", path)
    packet = compact_evidence_sources(result["sources"], result["query_analysis"]["intent"])[0]
    assert {"record_id", "doi", "title", "evidence", "tier", "relative_retrieval_score", "relevant_fields", "limitations"} <= set(packet)
    assert "fields" not in packet
    assert packet["relevant_fields"]["enzyme"] == "OC"
    assert packet["relevant_fields"]["value"] == "1.2"
    assert "irrelevant_legacy_field" not in packet["relevant_fields"]
    assert get_evidence_detail(path, "oc", fields=["reaction_temperature"])["fields"] == {"reaction_temperature": "30 C"}


def test_projection_prefers_production_and_kinetics_fields() -> None:
    fields = {"product": "glabridin", "titer": "2.1 g/L", "yield": "0.4", "kcat": "3.0", "unrelated": "omit"}
    production = project_evidence_fields(fields, parse_query_intent("glabridin production"))
    kinetics = project_evidence_fields(fields, parse_query_intent("DMT kcat for compound 11"))
    assert "titer" in production and "yield" in production and "unrelated" not in production
    assert "kcat" in kinetics and "titer" not in kinetics

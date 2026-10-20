from __future__ import annotations

import json
from pathlib import Path

from igem_drylab.literature import (
    EvidenceKnowledgeGraph,
    answer_question,
    build_knowledge_graph,
    load_evidence_documents,
)
from igem_drylab.literature.qa import RankedEvidence, retrieve_evidence, rrf_fuse


def _graph_evidence(tmp_path: Path) -> Path:
    rows = [
        {
            "record_id": "dmt-yeast-30",
            "title": "DMT condensate kinetics",
            "doi": "10.1000/dmt",
            "evidence": "GgDMT1 activity was measured in a yeast LLPS condensate at 30 C.",
            "fields": {
                "enzyme": "GgDMT1",
                "host": "Saccharomyces cerevisiae",
                "parameter_type": "activity",
                "llps_state": "LLPS condensate",
                "reaction_temperature": "30 C",
            },
        },
        {
            "record_id": "dmt-bacteria-37",
            "title": "DMT soluble kinetics",
            "doi": "10.1000/dmt-bacteria",
            "evidence": "GgDMT1 activity was measured in a soluble bacterial assay at 37 C.",
            "fields": {
                "enzyme": "GgDMT1",
                "host": "Escherichia coli",
                "parameter_type": "activity",
                "llps_state": "absent",
                "reaction_temperature": "37 C",
            },
        },
        {
            "record_id": "oc-same-paper",
            "title": "DMT condensate kinetics",
            "doi": "10.1000/dmt",
            "evidence": "GgOC1 converted compound 10 to compound 11 in the same study.",
            "fields": {"enzyme": "GgOC1", "substrate": "10", "product": "11"},
        },
    ]
    path = tmp_path / "evidence.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    return path


def test_graph_build_is_provenance_bearing_and_round_trips(tmp_path: Path) -> None:
    path = _graph_evidence(tmp_path)
    documents = load_evidence_documents(path)
    graph = build_knowledge_graph(documents)
    assert graph.stats["node_kinds"]["experiment"] == 3
    assert graph.stats["node_kinds"]["paper"] == 2
    assert graph.stats["relations"]["SUPPORTED_BY"] == 3
    assert any(edge.relation == "USES_ENZYME" and edge.doi == "10.1000/dmt" and edge.evidence for edge in graph.edges)

    graph_path = tmp_path / "evidence.graph.json"
    graph.save(graph_path)
    loaded = EvidenceKnowledgeGraph.load(graph_path)
    assert loaded.stats == graph.stats


def test_graph_search_exposes_direct_and_multihop_paths(tmp_path: Path) -> None:
    documents = load_evidence_documents(_graph_evidence(tmp_path))
    graph = build_knowledge_graph(documents)
    hits = graph.search(
        "DMT activity in yeast LLPS condensates",
        documents,
        intent={"enzymes": ["DMT"], "outcomes": ["activity"], "context": ["llps"], "constraints": {"host": "yeast"}},
    )
    assert hits[0].index == 0
    assert any("enzyme=GgDMT1" in item for item in hits[0].matched_entities)
    assert any("dmt-yeast-30" in path.lower() for path in hits[0].paths)
    assert any(hit.index == 2 for hit in hits)  # shared-paper/relationship expansion


def test_graph_rag_fuses_graph_rank_and_returns_explanations(tmp_path: Path) -> None:
    path = _graph_evidence(tmp_path)
    sources, _analysis, retrieval = retrieve_evidence(
        "DMT activity in yeast LLPS condensates",
        load_evidence_documents(path),
        graph_enabled=True,
        evidence_path=path,
    )
    assert sources[0]["record_id"] == "dmt-yeast-30"
    assert sources[0]["retrieval"]["graph_rank"] == 1
    assert sources[0]["retrieval"]["graph_matched_entities"]
    assert sources[0]["retrieval"]["graph_paths"]
    assert retrieval["graph"] == "built_in_memory"
    assert retrieval["graph_stats"]["node_count"] > 0
    assert retrieval["fusion"] == "rrf"


def test_prebuilt_graph_is_loaded_only_when_fingerprint_matches(tmp_path: Path) -> None:
    path = _graph_evidence(tmp_path)
    documents = load_evidence_documents(path)
    graph_path = tmp_path / "graph.json"
    build_knowledge_graph(documents).save(graph_path)
    loaded = answer_question("DMT activity in yeast LLPS condensates", path, graph_enabled=True, graph_path=graph_path)
    assert loaded["retrieval"]["graph"] == "loaded"

    path.write_text(path.read_text(encoding="utf-8") + "\n" + json.dumps({"record_id": "new", "title": "New", "doi": "10.1/new", "evidence": "DMT activity was measured.", "fields": {"enzyme": "DMT"}}), encoding="utf-8")
    rebuilt = answer_question("DMT activity", path, graph_enabled=True, graph_path=graph_path)
    assert rebuilt["retrieval"]["graph"] == "built_in_memory"


def test_three_route_rrf_preserves_all_rank_metadata() -> None:
    fused = rrf_fuse(
        [RankedEvidence(index=0, lexical_rank=1)],
        [RankedEvidence(index=0, semantic_rank=2)],
        [RankedEvidence(index=0, graph_rank=3, graph_score=4.2, graph_paths=("DMT -> r1",), matched_entities=("enzyme=DMT",))],
    )
    assert fused[0].lexical_rank == 1
    assert fused[0].semantic_rank == 2
    assert fused[0].graph_rank == 3
    assert fused[0].graph_paths == ("DMT -> r1",)

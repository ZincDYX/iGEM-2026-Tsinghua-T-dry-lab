from pathlib import Path

import pytest

from igem_drylab.constructs import ConstructRecord
from igem_drylab.pipeline import load_config
from igem_drylab.pipeline.config import ConstructDefinition, DesignConfig
from igem_drylab.pipeline.stages import run_m1, run_m2, run_m3


def project():
    config = load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    config.execution.mode = "demo"
    config.inputs.idr_id = None
    config.inputs.constructs = []
    config.inputs.construct_records = []
    return config


def test_registry_sequences_and_multiple_linkers_and_idr_are_screened(tmp_path):
    config = project()
    config.inputs.construct_records = [ConstructRecord(construct_id="registry", construct_type="fixture",
        proteins=["test-protein"], sequences={"test-protein": "MA", "test-idr": "L" * 20}, idr="test-idr",
        linker_sequences={"test-l1": "GGGGSGGGGS", "test-l2": "LLLLLLLLLL"},
        domain_order=["test-protein", "test-l1", "test-idr", "test-l2"],
        source_type="wetlab", review_status="approved", sequence_source_ref="synthetic-test-only")]
    rows, _ = run_m1(config, tmp_path)
    assert rows[0].construct_definition["provenance"]["source_type"] == "wetlab"
    assert set(rows[0].part_screens) == {"test-l1", "test-l2", "test-idr"}
    assert rows[0].part_screens["test-idr"]["verdict"] == "reject"
    assert rows[0].sequence_qc["full_protein_sequence"].startswith("MAGGGGSGGGGS")
    assert not rows[0].recommended_for_m2


def test_inline_sequences_cannot_override_fasta_or_linker_silently(tmp_path):
    config = project()
    config.inputs.constructs = [ConstructDefinition(id="conflict", components=[config.inputs.linkers[0].id],
        sequences={config.inputs.linkers[0].id: "AAAAA"})]
    with pytest.raises(ValueError, match="conflicting_sequence"):
        run_m1(config, tmp_path)


def test_reject_and_baseline_do_not_consume_eligible_budget(tmp_path):
    config = project()
    config.stages.m1_llps.top_n = 1
    config.inputs.constructs = [ConstructDefinition(id=identifier, components=["test-part"], linker_ids=["test-part"],
        sequences={"test-part": sequence}, experimental_baseline=baseline) for identifier, sequence, baseline in
        [("bad-baseline", "LLLLLLLLLL", True)]]
    config.inputs.constructs.extend(ConstructDefinition(id=identifier, components=[identifier], linker_ids=[identifier],
        sequences={identifier: "GGGGSGGGGS"}) for identifier in ("good1", "good2"))
    rows, _ = run_m1(config, tmp_path)
    assert len(rows) == 3
    assert rows[0].retrospective_only and not rows[0].recommended_for_m2
    assert rows[1].eligibility == "eligible" and rows[1].recommended_for_m2
    assert rows[2].eligibility == "budget_deferred"
    m2, _ = run_m2(config, tmp_path, rows)
    assert not m2[0].recommended_for_m3


def test_design_missing_one_protein_evidence_never_ready(tmp_path):
    config = project()
    config.inputs.constructs = [ConstructDefinition(id=identifier, parts=[{"id": identifier, "kind": "protein", "sequence": "MA"}],
        enzyme_ids=[enzyme]) for identifier, enzyme in (("oc-orf", "OC"), ("dmt-orf", "DMT"))]
    config.inputs.designs = [DesignConfig(id="design", protein_construct_ids=["oc-orf", "dmt-orf"], required_enzyme_ids=["OC", "DMT"])]
    m1, _ = run_m1(config, tmp_path)
    m2, _ = run_m2(config, tmp_path, m1)
    assert m2[-1].candidate_id == "Design-design"
    assert not m2[-1].recommended_for_m3
    m3, _ = run_m3(config, tmp_path, m2)
    assert all(not item.recommended_for_m4 for item in m3)

"""Localization transport regressions; native-format fixtures are not tool jobs."""
from hashlib import sha256
from pathlib import Path
import pytest

from igem_drylab.fusion_tool_import import FusionImportInput, NativeFusionArtifact, import_fusion_tools
from igem_drylab.workflow.models import SequenceRecord, SequenceRef, Project, WorkflowError
from igem_drylab.workflow.m1_checks import M1DecisionInput, decision, m1_workflow, precheck
from igem_drylab.workflow.tools import NodeContext
from igem_drylab.workflow.sequence_index import _localization_context, resolve_sequence_ref
from igem_drylab.software.parsers import ParserRegistry


def decision_fixture(tmp_path, localization):
    sequence = "GGGSSGGGSS"
    sp = tmp_path / "prediction_results.txt"
    sp.write_text("# SignalP-6.0\n# ID\tPrediction\tOTHER\tSP(Sec/SPI)\tCS Position\nfixture\tOTHER\t0.99\t0.01\t\n")
    tm = tmp_path / "predicted_topologies.3line"
    tm.write_text(">fixture | TM\nGGGSSGGGSS\nIIMMMIIIII\n")
    tango = tmp_path / "fixture.out"
    tango.write_text("\n".join(f"{i}, {aa}, 0, 0, 0, 0, 0" for i, aa in enumerate(sequence, 1)))
    fusion = import_fusion_tools(FusionImportInput(sequence=sequence,
        reviewer="synthetic-format-test", source_reference="synthetic-not-a-project-tool-job", output_dir=tmp_path / "review",
        artifacts=[NativeFusionArtifact(path=sp, format="signalp6_summary", tool_version="6.0", record_id="fixture"),
                   NativeFusionArtifact(path=tm, format="deeptmhmm1_3line", tool_version="1.0", record_id="fixture"),
                   NativeFusionArtifact(path=tango, format="tango_residue_out", tool_version="fixture", record_id="fixture",
                       aggregation_rule=dict(high_score_percent=5, minimum_run_length=3, source_reference="synthetic-test-only"))]))["fusion"]
    inputs = m1_workflow().nodes[0].inputs
    payload = M1DecisionInput(item=SequenceRecord(id="fixture", sequence=sequence, role="full_fusion", localization_context=localization),
        feature_definitions=inputs["feature_definitions"].value, rules=inputs["rules"].value)
    context = NodeContext(run_id="fixture", node_id="decision", work_dir=tmp_path)
    payload.prechecks = [precheck(payload, context)]
    inactive = [dict(candidate_id="fixture", input_sequence_sha256=sha256(sequence.encode()).hexdigest(),
                     parsed=None, parse_status="not_eligible")]
    payload.disorder_results = payload.seg_results = payload.secondary_results = inactive
    raw = [dict(candidate_id="fixture", input_sequence_sha256=sha256(sequence.encode()).hexdigest(), parsed=fusion)]
    payload.signalp_results = payload.topology_results = payload.aggregation_results = raw
    predecessors = tuple(dict(output=dict(items=rows)) for rows in (payload.prechecks, inactive, raw))
    context = NodeContext(run_id="fixture", node_id="decision", work_dir=tmp_path, upstream_results=predecessors)
    return payload, context


def test_generic_decision_uses_localization_with_same_native_tm_observation(tmp_path):
    er, context = decision_fixture(tmp_path, "er_anchored")
    result = decision(er, context)
    assert result["precheck"]["localization_context"] == "er_anchored"
    assert result["screen"]["localization_context"] == "er_anchored"
    assert result["verdict"] == "review"
    assert not result["screen"]["hard_reject_reasons"]
    assert "er_anchored_construct_transmembrane_segment_requires_scenario_specific_review" in result["screen"]["review_reasons"]
    # The identical observation must still reject a declared cytosolic fusion.
    cytosolic, context = decision_fixture(tmp_path, "cytosolic")
    result = decision(cytosolic, context)
    assert result["verdict"] == "reject"
    assert "cytosolic_construct_has_transmembrane_helix" in result["screen"]["hard_reject_reasons"]


def test_change_of_localization_cannot_reuse_old_precheck(tmp_path):
    payload, context = decision_fixture(tmp_path, "er_anchored")
    payload.item.localization_context = "cytosolic"
    with pytest.raises(ValueError, match="precheck_result_does_not_match"):
        decision(payload, context)


def test_reviewed_risk_policy_reaches_existing_calculator_instead_of_fixed_block(tmp_path):
    from igem_drylab.m1_prioritization import PrioritizationPolicy
    payload, context = decision_fixture(tmp_path, "er_anchored")
    payload.prioritization_policy = PrioritizationPolicy(policy_version="SYNTHETIC-policy-test",
        source_reference="Synthetic wiring oracle; not a project risk policy", reviewer="test",
        risk_rules={"full_fusion":[dict(rule_id="fixture",feature="hydrophobic_fraction",
            transform="identity",operator="gt",lower=.5)]})
    result = decision(payload, context)
    assert result['prioritization']['candidates'][0]['risk']=='low'
    assert next(row for row in result['steps'] if row['step']=='4')['status']=='completed'
    assert result['verdict']=='review'  # risk calculation cannot approve ER topology


def test_missing_native_observation_is_not_promoted_by_er_context(tmp_path):
    payload, context = decision_fixture(tmp_path, "er_anchored")
    absent = [dict(candidate_id="fixture", input_sequence_sha256=payload.prechecks[0]["input_sequence_sha256"], parsed=None)]
    payload.signalp_results = payload.topology_results = payload.aggregation_results = absent
    context = NodeContext(run_id="fixture", node_id="decision", work_dir=tmp_path,
        upstream_results=(*context.upstream_results, dict(output=dict(items=absent))))
    assert decision(payload, context)["verdict"] == "blocked"


def test_fasta_import_and_project_snapshot_keep_declared_localization(tmp_path):
    source = tmp_path / "data.faa";source.write_text(">fixture\nMAGSGS\n")
    parsed = ParserRegistry().parse(source, dict(localization_context="er_anchored"))
    record = parsed.patch["sequences"][0]
    assert record["localization_context"] == "er_anchored"
    project = Project(id="p", name="fixture", sequences=[record])
    ref = SequenceRef(source="project", record_id="fixture", sequence_sha256=sha256(b"MAGSGS").hexdigest(), construct_version=1)
    result = resolve_sequence_ref(ref, project.model_dump(mode="json"), None)
    assert result["localization_context"] == "er_anchored"
    with pytest.raises(WorkflowError, match="invalid_localization"):
        ParserRegistry().parse(source, dict(localization_context="invented"))


def test_scientific_context_is_declared_not_inferred_from_fasta_name():
    config = {"inputs": {"constructs": [dict(id="fixture", localization_context="er_anchored")]}}
    assert _localization_context(config, "fixture") == "er_anchored"
    assert _localization_context(config, "ER_name_without_declaration") == "cytosolic"

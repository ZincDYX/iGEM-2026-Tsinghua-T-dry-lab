from __future__ import annotations

import json
from pathlib import Path

import pytest

from igem_drylab.literature.evidence_contract import LlpsPartitioningEvidence, PhaseActivityEvidence, map_evidence_to_requirement
from igem_drylab.mcp import create_default_registry
from igem_drylab.parameters import ParameterRecord, ParameterRegistry
from igem_drylab.parameters.requirements import m4_requirements
from igem_drylab.wetlab import WetLabResult, compare_prediction, diagnose_discrepancy, quality_control
from igem_drylab.pipeline.stages import _joint_diagnosis_evidence


def _trajectory(path: Path) -> Path:
    path.write_text(json.dumps({"time_unit": "h", "concentration_unit": "uM", "time": [0, 24], "x13": [0, 1000], "x15": [0, 1000]}), encoding="utf-8")
    return path


def test_one_millimolar_equals_one_thousand_micromolar(tmp_path: Path) -> None:
    result = WetLabResult(experiment_id="e", construct_id="c", condition_id="q", replicate_id="r", metabolite_time=[0, 24], metabolite_concentration_unit="mM", metabolites={"13": [0, 1]})
    comparison = compare_prediction(_trajectory(tmp_path / "t.json"), result)["13"]
    assert comparison.residual_final == pytest.approx(0)


def test_perfect_prediction_is_not_parameter_mismatch() -> None:
    diagnosis = diagnose_discrepancy(qc_passed=True, replicate_variation=0, trend_agreement=True, systematic_directional_error=False, significant_residual=False)
    assert diagnosis.category == "NO_SIGNIFICANT_DISCREPANCY"


def test_m5_uncertainty_uses_the_same_concentration_unit_as_residual(tmp_path: Path) -> None:
    result = WetLabResult(experiment_id="e", construct_id="c", condition_id="q", replicate_id="r", metabolite_time=[0, 24], metabolite_concentration_unit="mM", metabolites={"13": [0, 1]}, metabolite_uncertainty={"13": [0, 0.1]}, metabolite_uncertainty_type="sd")
    comparison = compare_prediction(_trajectory(tmp_path / "t.json"), result)
    evidence = _joint_diagnosis_evidence(result, comparison, {})
    assert evidence["13"]["measurement_uncertainty"] == pytest.approx(100)


def test_zero_hour_below_lod_keeps_later_quantified_trajectory(tmp_path: Path) -> None:
    result = WetLabResult(experiment_id="e", construct_id="c", condition_id="q", replicate_id="r", metabolite_time=[0, 12, 24], metabolite_concentration_unit="uM", metabolites={"13": [0, 500, 1000]}, metabolite_lod={"13": 1})
    comparison = compare_prediction(_trajectory(tmp_path / "t.json"), result)["13"]
    assert comparison.censor_mask == ["below_lod", "quantified", "quantified"]
    assert comparison.aligned_timepoints == 2


def test_qc_same_experiment_different_replicates_is_independent() -> None:
    records = [
        WetLabResult(experiment_id="same", construct_id="c", condition_id="q", replicate_id="r1", metabolite_time=[0], metabolites={"13": [1]}),
        WetLabResult(experiment_id="same", construct_id="c", condition_id="q", replicate_id="r2", metabolite_time=[0], metabolites={"13": [1]}),
    ]
    reports = quality_control(records)
    assert reports[0].replicate_id == "r1" and reports[0].passed
    assert reports[1].replicate_id == "r2" and reports[1].passed


def test_typed_evidence_rejects_wrong_species_and_phase() -> None:
    requirements = {item.name: item for item in m4_requirements()}
    dmt_partition = LlpsPartitioningEvidence(doi="10.1/x", evidence_text="DMT partition", value=2, unit="1", species_id="DMT", parameter="partition_coefficient")
    with pytest.raises(ValueError, match="species"):
        map_evidence_to_requirement(dmt_partition, requirements["partition_x10"])
    dense = PhaseActivityEvidence(doi="10.1/x", evidence_text="dense", value=1, unit="1", enzyme_id="DMT", phase="dense")
    with pytest.raises(ValueError, match="phase"):
        map_evidence_to_requirement(dense, requirements["activity_dilute_dmt"])


def test_mcp_recognizes_degradation_requirement_when_enabled(tmp_path: Path) -> None:
    source = Path("configs/m1_m4_real_scoring_example.yaml")
    config = source.read_text(encoding="utf-8").replace("../examples/", str((Path("examples").resolve())).replace("\\", "/") + "/").replace("    target_product: glabridin", "    target_product: glabridin\n    enable_degradation: true")
    path = tmp_path / "project.yaml"; path.write_text(config, encoding="utf-8")
    result = create_default_registry().call("igem.parameters.resolve", {"config_path": str(path), "stage": "m4", "requirement_name": "kdeg_13"})
    assert result.is_error is False
    assert result.as_protocol_dict()["structuredContent"]["resolution"]["status"] == "unresolved"


def test_mcp_typed_evidence_uses_declared_requirement() -> None:
    result = create_default_registry().call("igem.parameters.map_typed_evidence", {
        "config_path": "configs/m1_m4_real_scoring_example.yaml", "stage": "m4", "requirement_name": "kcat_dmt_11", "evidence_type": "enzyme_kinetics",
        "evidence": {"doi": "10.1/x", "evidence_text": "table", "value": 2, "unit": "1/h", "enzyme_id": "DMT", "substrate_id": "11", "product_id": "15", "parameter": "kcat"},
    })
    payload = result.as_protocol_dict()["structuredContent"]
    assert payload["ok"] is True
    assert payload["parameter_candidate"]["review_status"] == "extracted"


def test_same_tier_conflicts_need_explicit_supersedes() -> None:
    req = next(item for item in m4_requirements() if item.name == "km_dmt_11")
    records = [
        ParameterRecord(parameter_id="a", name=req.name, value=1, unit="uM", parameter_type="km", enzyme_id="DMT", substrate_id="11", source_type="literature", doi="10.1/a", evidence_text="a", review_status="approved"),
        ParameterRecord(parameter_id="b", name=req.name, value=2, unit="uM", parameter_type="km", enzyme_id="DMT", substrate_id="11", source_type="literature", doi="10.1/b", evidence_text="b", review_status="approved"),
    ]
    assert ParameterRegistry(records).resolve(req).status == "conflict"
    records[1] = records[1].model_copy(update={"supersedes": "a"})
    assert ParameterRegistry(records).resolve(req).selected_parameter.parameter_id == "b"

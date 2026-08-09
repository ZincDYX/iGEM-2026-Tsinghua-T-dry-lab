from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from igem_drylab.literature.evidence_contract import PhaseVolumeEvidence, map_evidence_to_requirement
from igem_drylab.parameters import ParameterRecord, ParameterRegistry
from igem_drylab.parameters.dimensions import validate_requirement_value
from igem_drylab.parameters.requirements import ParameterRequirement, m3_requirements, m4_requirements, requirement_name_to_kernel_key
from igem_drylab.pipeline import load_config
from igem_drylab.pipeline.stages import _condition_level_systematic, _data_quality_from_summary, _joint_diagnosis_label
from igem_drylab.scoring.m2_structure import load_m2_structure_metrics
from igem_drylab.wetlab import WetLabResult, evaluate_residual_significance, quality_control, replicate_variation
from igem_drylab.wetlab.parameter_update import validate_candidate_for_approval


def _requirement(name: str):
    return next(item for item in [*m3_requirements(), *m4_requirements(include_degradation=True)] if item.name == name)


def _project():
    return load_config(Path("configs/m1_m4_real_scoring_example.yaml"))


def test_package_import_smoke() -> None:
    for name in ("igem_drylab.wetlab", "igem_drylab.pipeline", "igem_drylab.parameters", "igem_drylab.agent"):
        assert importlib.import_module(name)


@pytest.mark.parametrize(
    ("name", "value", "parameter_type"),
    [("phi", 1.2, "phi"), ("partition_oc", 0.0, "kp")],
)
def test_approval_rejects_out_of_bound_values(name: str, value: float, parameter_type: str) -> None:
    requirement = _requirement(name)
    candidate = ParameterRecord(parameter_id=f"bad-{name}", name=name, value=value, unit="1", parameter_type=parameter_type, enzyme_id=requirement.enzyme_id, species_id=requirement.species_id, source_type="wetlab", derivation_type="direct_measurement", source_reference="assay", review_status="validated")
    with pytest.raises(ValueError, match="physical_"):
        validate_candidate_for_approval(_project(), candidate, requirement, "reviewer")


def test_invalid_source_derivation_pairing_is_rejected() -> None:
    with pytest.raises(ValueError, match="invalid_source_derivation"):
        ParameterRecord(parameter_id="bad", name="km_pt", value=1, unit="uM", parameter_type="km", source_type="literature", derivation_type="model_fit", doi="10/x", evidence_text="x")


@pytest.mark.parametrize(
    "requirement,value",
    [
        (ParameterRequirement(name="phi", parameter_type="phi", dimension="dimensionless", minimum=0, maximum=1), 1.2),
        (ParameterRequirement(name="kp", parameter_type="kp", dimension="dimensionless", minimum=0, minimum_inclusive=False), 0.0),
        (ParameterRequirement(name="km", parameter_type="km", dimension="concentration", canonical_unit="uM", minimum=0, minimum_inclusive=False), 0.0),
        (ParameterRequirement(name="kd", parameter_type="kd", dimension="concentration", canonical_unit="uM", minimum=0, minimum_inclusive=False), 0.0),
    ],
)
def test_shared_requirement_value_contract_rejects_physical_bounds(requirement: ParameterRequirement, value: float) -> None:
    with pytest.raises(ValueError, match="physical_"):
        validate_requirement_value(value, "1" if requirement.dimension == "dimensionless" else "uM", requirement)


def test_unicode_micro_molar_aliases_are_equivalent() -> None:
    requirement = _requirement("km_pt")
    values = []
    for index, unit in enumerate(("uM", "µM", "μM", "碌M")):
        record = ParameterRecord(parameter_id=f"p{index}", name="km_pt", value=1, unit=unit, parameter_type="km", enzyme_id="PT", substrate_id="9", source_type="wetlab", source_reference="x", review_status="approved")
        values.append(ParameterRegistry([record]).resolve(requirement).canonical_value)
    assert values == [1, 1, 1, 1]


def test_real_mode_uninterpretable_residual_cannot_escalate_branch_diagnosis() -> None:
    evidence = {"13": {"residual_final": 0.001, "observed_final": 1.0, "predicted_final": 0.999, "measurement_uncertainty": None, "measurement_uncertainty_type": None, "trend_agreement": False, "comparison_status": "trajectory_aligned"}}
    evaluation = evaluate_residual_significance(evidence, absolute_tolerance=0, relative_tolerance=0, tolerance_configured=False, require_interpretable_uncertainty=True)
    evidence["13"]["significant"] = evaluation.significant
    assert evaluation.significant is None
    assert _joint_diagnosis_label(evidence, "INSUFFICIENT_INFORMATION") == "INSUFFICIENT_INFORMATION"


def test_non_significant_trend_disagreement_is_not_branch_mismatch() -> None:
    evidence = {"13": {"residual_final": 0.001, "trend_agreement": False, "significant": False, "comparison_status": "trajectory_aligned"}, "15": {"residual_final": 0.001, "trend_agreement": True, "significant": False, "comparison_status": "trajectory_aligned"}}
    assert _joint_diagnosis_label(evidence, "NO_SIGNIFICANT_DISCREPANCY") == "NO_SIGNIFICANT_DISCREPANCY"


def test_systematic_mismatch_uses_condition_means_before_significance_filtering() -> None:
    config = _project().model_copy(deep=True)
    config.execution.mode = "demo"
    config.stages.m5_feedback.discrepancy_threshold_configured = True
    def row(condition: str, residual: float):
        result = SimpleNamespace(construct_id="c", condition_id=condition)
        report = SimpleNamespace(passed=True)
        evidence = {"13": {"residual_final": residual, "observed_final": 10 + residual, "predicted_final": 10.0, "measurement_uncertainty": None, "measurement_uncertainty_type": None}}
        return (result, report, {}, evidence, None, None, None, "", [], None)
    assert _condition_level_systematic([row("d1", 1), row("d1", -1)], config) == set()
    assert _condition_level_systematic([row("d1", 1), row("d2", 1)], config) == {("c", "13")}


def test_replicate_identity_includes_experiment_id() -> None:
    records = [
        WetLabResult(experiment_id="e1", construct_id="c", condition_id="d", replicate_id="r1", metabolite_time=[0], metabolite_concentration_unit="uM", metabolites={"15": [1]}),
        WetLabResult(experiment_id="e2", construct_id="c", condition_id="d", replicate_id="r1", metabolite_time=[0], metabolite_concentration_unit="uM", metabolites={"15": [2]}),
    ]
    assert replicate_variation(records)[("c", "d", "15", 0.0)] is not None


def test_qc_contract_failure_cannot_enter_fit_pool() -> None:
    valid = WetLabResult(experiment_id="e1", construct_id="c", condition_id="d", replicate_id="r1", metabolite_time=[0], metabolite_concentration_unit="uM", metabolites={"15": [1]})
    invalid_unit = WetLabResult(experiment_id="e2", construct_id="c", condition_id="d", replicate_id="r2", metabolite_time=[0], metabolites={"15": [1]})
    reports = quality_control([valid, invalid_unit])
    from igem_drylab.pipeline.stages import _fit_eligible
    assert reports[0].passed and reports[1].passed
    assert _fit_eligible(valid) and not _fit_eligible(invalid_unit)


def test_registry_leaf_lineage_and_canonical_equivalence_are_not_conflicts() -> None:
    req = _requirement("km_dmt_11")
    base = dict(name=req.name, parameter_type="km", enzyme_id="DMT", substrate_id="11", source_type="literature", doi="10/x", evidence_text="x", review_status="approved")
    a = ParameterRecord(parameter_id="a", value=1, unit="mM", **base)
    b = ParameterRecord(parameter_id="b", value=1000, unit="uM", supersedes="a", **base)
    c = ParameterRecord(parameter_id="c", value=1, unit="mM", supersedes="b", **base)
    registry = ParameterRegistry([a, b, c])
    assert registry.resolve(req).selected_parameter.parameter_id == "c"
    assert registry.list_conflicts() == []


def test_fit_kernel_mapping_and_fitted_data_quality_label() -> None:
    assert requirement_name_to_kernel_key("partition_x10") == "partition_10"
    assert _data_quality_from_summary({"fitted": 3}) == "fitted"


def test_duplicate_m2_candidate_metrics_fail_fast(tmp_path: Path) -> None:
    path = tmp_path / "m2.json"
    path.write_text(json.dumps([{"candidate_id": "x"}, {"candidate_id": "x"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate_m2_metric_candidate_id"):
        load_m2_structure_metrics(path)


def test_fasta_referential_integrity_is_enforced(tmp_path: Path) -> None:
    text = Path("configs/m1_m4_example.yaml").read_text(encoding="utf-8").replace("protein_id: OC", "protein_id: ABSENT")
    path = tmp_path / "bad.yaml"
    path.write_text(text.replace("../examples/", str(Path("examples").resolve()).replace("\\", "/") + "/"), encoding="utf-8")
    with pytest.raises(ValueError, match="protein_id_missing_from_fasta"):
        load_config(path)

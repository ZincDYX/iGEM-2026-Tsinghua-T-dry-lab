from pathlib import Path
import json
import pytest
import yaml

from igem_drylab.wetlab import WetLabResult, approve_and_persist_parameter, compare_prediction
from igem_drylab.parameters import ParameterRecord
from igem_drylab.pipeline import load_config
from igem_drylab.wetlab import replicate_variation


def test_wetlab_time_and_horizon_are_explicit(tmp_path):
    trajectory = tmp_path / "trajectory.json"
    trajectory.write_text(json.dumps({"time_unit": "h", "concentration_unit": "uM", "time": [0, 4], "x13": [0, 2], "x15": [0, 4]}), encoding="utf-8")
    minute = WetLabResult(experiment_id="e", construct_id="c", condition_id="x", replicate_id="r", metabolite_time=[0, 240], metabolite_time_unit="min", metabolite_concentration_unit="uM", metabolites={"13": [0, 2]})
    assert compare_prediction(trajectory, minute)["13"].comparison_status == "trajectory_aligned"
    outside = minute.model_copy(update={"metabolite_time": [0, 300]})
    assert compare_prediction(trajectory, outside)["13"].comparison_status == "measurement_outside_simulation_horizon"


def test_human_approval_persists_and_reloads(tmp_path):
    from test_experimental_condition_chain import assay
    from igem_drylab.pipeline.config import ExperimentalContext
    from igem_drylab.parameters import ParameterRegistry, resolve_requirement
    from igem_drylab.parameters.requirements import requirements_for_stage
    source = Path("configs/m1_m4_real_scoring_example.yaml")
    project = tmp_path / "project.yaml"
    # Keep relative real-data inputs valid after moving the fixture into tmp_path.
    raw = source.read_text(encoding="utf-8").replace("../examples/", str((Path("examples").resolve())).replace("\\", "/") + "/")
    project.write_text(raw, encoding="utf-8")
    candidate = ParameterRecord(parameter_id="p", name="phi", value=0.1, unit="1", parameter_type="phi", source_type="wetlab", source_reference="E", review_status="validated")
    with pytest.raises(ValueError,match='candidate_not_formally_applicable'):
        approve_and_persist_parameter(project,candidate,reviewer='human',target_stage='m3',target_requirement_name='phi')
    config = load_config(project)
    config.experimental_context = ExperimentalContext(host='yeast',strain='s',temperature_c=30.,pH=7.,assay_system='in_cell')
    config.stages.m4_reaction.condition_id = 'd'
    project.write_text(yaml.safe_dump(config.model_dump(mode='json')),encoding='utf-8')
    candidate = candidate.model_copy(update={'construct_id':'c','condition_id':'d','conditions':assay().parameter_conditions()})
    approved = approve_and_persist_parameter(project, candidate, reviewer="human", target_stage="m3", target_requirement_name="phi")
    assert approved.approved_by == "human"
    assert any(record.parameter_id == "p" for record in load_config(project).parameters)
    reloaded = load_config(project)
    requirement = next(r for r in requirements_for_stage(reloaded,'m3') if r.name == 'phi')
    resolved = resolve_requirement(ParameterRegistry(reloaded.parameters),requirement,reloaded.experimental_context,
        allow_assumptions=False,construct_id='c',condition_id='d',require_provenance=True)
    assert resolved.status == 'resolved' and resolved.canonical_value == pytest.approx(.1,abs=1e-12)


def test_replicate_variation_uses_replicate_ids_not_time_series():
    base = {"construct_id": "c", "condition_id": "x", "metabolite_time": [0, 1], "metabolite_concentration_unit": "uM", "metabolites": {"15": [0, 2]}}
    one = WetLabResult(experiment_id="e1", replicate_id="r1", **base)
    assert replicate_variation([one])[("c", "x", "15", 1.0)] is None
    two = WetLabResult(experiment_id="e2", replicate_id="r2", **{**base, "metabolites": {"15": [0, 4]}})
    assert replicate_variation([one, two])[("c", "x", "15", 1.0)] is not None

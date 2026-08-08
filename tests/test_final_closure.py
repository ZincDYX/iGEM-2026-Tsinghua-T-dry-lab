from pathlib import Path
import json

from igem_drylab.wetlab import WetLabResult, approve_and_persist_parameter, compare_prediction
from igem_drylab.parameters import ParameterRecord
from igem_drylab.pipeline import load_config


def test_wetlab_time_and_horizon_are_explicit(tmp_path):
    trajectory = tmp_path / "trajectory.json"
    trajectory.write_text(json.dumps({"time_unit": "h", "time": [0, 4], "x13": [0, 2], "x15": [0, 4]}), encoding="utf-8")
    minute = WetLabResult(experiment_id="e", construct_id="c", condition_id="x", replicate_id="r", metabolite_time=[0, 240], metabolite_time_unit="min", metabolites={"13": [0, 2]})
    assert compare_prediction(trajectory, minute)["13"].comparison_status == "trajectory_aligned"
    outside = minute.model_copy(update={"metabolite_time": [0, 300]})
    assert compare_prediction(trajectory, outside)["13"].comparison_status == "measurement_outside_simulation_horizon"


def test_human_approval_persists_and_reloads(tmp_path):
    source = Path("configs/m1_m4_real_scoring_example.yaml")
    project = tmp_path / "project.yaml"
    project.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    candidate = ParameterRecord(parameter_id="p", name="phi", value=0.1, unit="1", parameter_type="phi", source_type="wetlab", source_reference="E", review_status="validated")
    approved = approve_and_persist_parameter(project, candidate, reviewer="human")
    assert approved.approved_by == "human"
    assert any(record.parameter_id == "p" for record in load_config(project).parameters)

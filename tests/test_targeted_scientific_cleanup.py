from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from igem_drylab.agent import AgentRuntime, AgentTask
from igem_drylab.mcp import create_default_registry
from igem_drylab.pipeline.config import M4Config
from igem_drylab.wetlab import WetLabResult, quality_control, replicate_variation, systematic_directional_errors


def _result(experiment: str, condition: str, replicate: str, *, time: float = 24, value: float = 1.0) -> WetLabResult:
    return WetLabResult(experiment_id=experiment, construct_id="c", condition_id=condition, replicate_id=replicate, metabolite_time=[0, time], metabolites={"13": [0, value]})


def test_missing_parameter_does_not_schedule_production_m4(tmp_path: Path):
    trace = AgentRuntime(memory_path=tmp_path / "memory.jsonl").dry_run(AgentTask(task_id="missing", objective="simulate glabridin timing", inputs={"config_path": "configs/m1_m4_real_scoring_example.yaml", "target_stage": "m4"}))
    assert any(step.step_id == "review_missing_parameters" for step in trace.plan.steps)
    assert not any(step.step_id == "run_production_m4" for step in trace.plan.steps)


def test_replicate_cv_requires_same_condition_metabolite_timepoint():
    one = _result("e1", "a", "r1", time=24, value=1)
    two = _result("e2", "a", "r2", time=36, value=2)
    values = replicate_variation([one, two])
    assert values[("c", "a", "13", 24.0)] is None
    assert values[("c", "a", "13", 36.0)] is None


def test_replicates_do_not_trigger_systematic_model_mismatch():
    rows = [("c", "one_condition", "13", 2.0, True), ("c", "one_condition", "13", 3.0, True)]
    assert systematic_directional_errors(rows) == set()


def test_cross_condition_residuals_can_trigger_systematic_mismatch_and_is_order_invariant():
    rows = [("c", "first", "13", 2.0, True), ("c", "second", "13", 3.0, True)]
    assert systematic_directional_errors(rows) == {("c", "13")}
    assert systematic_directional_errors(list(reversed(rows))) == {("c", "13")}


def test_qc_outlier_does_not_mix_conditions():
    records = [_result("e1", "early", "r1", value=1), _result("e2", "late", "r2", value=100), _result("e3", "late", "r3", value=101)]
    assert not any(report.outlier_flags for report in quality_control(records))


def test_unknown_m4_config_key_is_rejected():
    with pytest.raises(ValidationError):
        M4Config.model_validate({"fake_kcat_multiplier": 0.5})


def test_pipeline_run_stage_does_not_execute_m5(tmp_path: Path):
    payload = create_default_registry().call("igem.pipeline.run_stage", {"config_path": "configs/m1_m4_example.yaml", "stage": "m4", "output_dir": str(tmp_path)}).as_protocol_dict()["structuredContent"]
    assert payload["ok"] is True
    assert not (Path(payload["run_dir"]) / "m5_wetlab_feedback").exists()

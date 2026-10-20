from __future__ import annotations

import argparse
from pathlib import Path

from scripts.evaluate_agent_benchmark import score
from scripts.run_agent_baseline_matrix import PROFILES, profile_command, summarize


def test_baseline_profiles_cover_provider_and_hybrid_comparison() -> None:
    assert list(PROFILES) == ["rule_based", "qwen", "deepseek", "hybrid_qwen", "hybrid_deepseek"]
    assert PROFILES["qwen"].planner == "llm"
    assert PROFILES["deepseek"].planner == "llm"
    assert PROFILES["hybrid_qwen"].planner == "hybrid"
    assert PROFILES["hybrid_qwen"].api_key_env == "QWEN_API_KEY"


def test_profile_command_passes_env_name_but_never_secret(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QWEN_API_KEY", "do-not-leak")
    monkeypatch.setenv("QWEN_API_BASE", "https://qwen.example/v1/chat/completions")
    monkeypatch.setenv("QWEN_MODEL", "qwen-test")
    args = argparse.Namespace(
        benchmark=Path("benchmarks/frozen"), mode="dry-run", jobs=2,
        case_ids=None, score_only=False,
    )
    command = profile_command(args, PROFILES["hybrid_qwen"], tmp_path / "hybrid_qwen")
    rendered = " ".join(command)
    assert "--planner hybrid" in rendered
    assert "--api-key-env QWEN_API_KEY" in rendered
    assert "--model qwen-test" in rendered
    assert "do-not-leak" not in rendered


def test_summary_keeps_quality_cost_and_latency_separate() -> None:
    rows = [
        {"planner": "hybrid", "provider": "qwen", "model": "qwen-a", "routing_correct": "True", "missing_input_handled": "True", "artifact_reuse_correct": "True", "safety_gate_correct": "True", "scientific_boundary_correct": "True", "trace_complete": "True", "overall_pass": "True", "forbidden_action_count": "0", "hallucinated_input_count": "0", "schema_valid_first_attempt": "True", "elapsed_seconds": "2.0", "total_tokens": "100"},
        {"planner": "hybrid", "provider": "qwen", "model": "qwen-a", "routing_correct": "False", "missing_input_handled": "True", "artifact_reuse_correct": "True", "safety_gate_correct": "True", "scientific_boundary_correct": "True", "trace_complete": "True", "overall_pass": "False", "forbidden_action_count": "0", "hallucinated_input_count": "1", "schema_valid_first_attempt": "False", "elapsed_seconds": "4.0", "total_tokens": "150"},
    ]
    result = summarize("hybrid_qwen", rows)
    assert result["routing_correct"] == 0.5
    assert result["overall_pass"] == 0.5
    assert result["hallucinated_input_rate"] == 0.5
    assert result["mean_elapsed_seconds"] == 3.0
    assert result["total_tokens"] == 250


def test_evaluator_records_provider_model_and_architecture() -> None:
    case = {"case_id": "case", "inputs": {}}
    gold = {"required_actions": [], "forbidden_actions": [], "expected_modules": [], "should_block": False, "should_reuse_artifact": False}
    raw = {"elapsed_seconds": 1.25, "trace": {"task": {"inputs": {}}, "plan": {"steps": [], "diagnostics": {"schema_valid_first_attempt": True, "llm_response_metadata": {"requested_model": "qwen-test", "input_tokens": 12, "output_tokens": 8, "total_tokens": 20}}}}}
    result = score(case, gold, raw, "hybrid", benchmark_label="hybrid_qwen", provider="qwen", model="qwen-test")
    assert result["benchmark_label"] == "hybrid_qwen"
    assert result["provider"] == "qwen"
    assert result["model"] == "qwen-test"
    assert result["total_tokens"] == 20

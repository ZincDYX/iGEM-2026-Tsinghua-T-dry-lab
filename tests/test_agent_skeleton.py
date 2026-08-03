from __future__ import annotations

from igem_drylab.agent import AgentRuntime, AgentTask, ArtifactRecord, ArtifactStore, BudgetManager, BudgetState, HumanApprovalGate, PlanStep
from igem_drylab.agent.context import ContextBundle
from igem_drylab.agent.env import load_local_env
from igem_drylab.agent.llm_planner import OpenAICompatiblePlanningBackend


def test_agent_runtime_dry_run_exposes_framework_slots(tmp_path):
    runtime = AgentRuntime(memory_path=tmp_path / "memory.jsonl")
    trace = runtime.dry_run(AgentTask(task_id="demo", objective="Build dry-lab plan"))

    assert trace.task.task_id == "demo"
    assert trace.plan.steps
    assert trace.calls == []
    assert "Dry run only" in trace.notes[0]
    assert "context, planner, scheduler" in trace.notes[1]
    assert runtime.context_builder is not None
    assert runtime.scheduler is not None
    assert runtime.budget is not None
    assert runtime.human_gate is not None
    assert runtime.reflection is not None
    assert runtime.artifacts is not None
    assert runtime.events.events
    assert (tmp_path / "memory.jsonl").exists()


def test_agent_runtime_executes_config_validation_and_persists_trace(tmp_path):
    runtime = AgentRuntime(
        memory_path=tmp_path / "memory.jsonl",
        artifacts_root=tmp_path / "artifacts",
        event_path=tmp_path / "events.jsonl",
    )
    trace = runtime.run_once(
        AgentTask(
            task_id="validate",
            objective="Validate a dry-lab project configuration",
            inputs={"config_path": "configs/m1_m4_example.yaml"},
        )
    )

    assert trace.final_status == "completed"
    assert trace.calls[0].status == "succeeded"
    assert trace.plan.steps[0].status == "succeeded"
    assert (tmp_path / "events.jsonl").exists()


def test_agent_blocks_when_required_input_is_missing(tmp_path):
    runtime = AgentRuntime(memory_path=tmp_path / "memory.jsonl")
    trace = runtime.run_once(
        AgentTask(task_id="missing", objective="Parse structure", inputs={"structure_output_path": "missing/output"})
    )

    assert trace.final_status == "blocked"
    assert "missing_input_path:path" in trace.notes[0]


def test_approval_gate_and_budget_enforce_cost_limits():
    gate = HumanApprovalGate()
    expensive = PlanStep(step_id="gpu", objective="run GPU", tool_name="igem.compute.run_tool", estimated_gpu_minutes=30)
    assert gate.requires_approval(expensive) is True
    gate.approve("gpu")
    assert gate.decision_for("gpu") is not None

    budget = BudgetManager(BudgetState(max_gpu_minutes=10))
    allowed, reason = budget.can_run_tool(expensive)
    assert allowed is False
    assert reason == "gpu_budget_exhausted"


def test_artifact_store_persists_checksum_and_lineage(tmp_path):
    source = tmp_path / "result.json"
    source.write_text('{"ok": true}', encoding="utf-8")
    store = ArtifactStore(tmp_path / "artifacts")
    record = store.register(ArtifactRecord(artifact_id="result", path=source, kind="json", producer_step_id="score"), require_exists=True)

    assert record.sha256
    assert store.verify("result") == (True, "artifact_verified")
    assert store.lineage("result")[0].producer_step_id == "score"


def test_optional_llm_planner_uses_validated_json_plan():
    class FakeChatClient:
        def complete_json(self, prompt: str):
            assert '"available_tools"' in prompt
            return {
                "steps": [
                    {
                        "step_id": "validate",
                        "objective": "Validate supplied configuration",
                        "tool_name": "igem.pipeline.validate",
                        "arguments": {"config_path": "configs/m1_m4_example.yaml"},
                    }
                ]
            }

    backend = OpenAICompatiblePlanningBackend(client=FakeChatClient())  # type: ignore[arg-type]
    task = AgentTask(task_id="llm", objective="Validate config")
    plan = backend.create_plan(
        task,
        ContextBundle(task=task, constraints=[], retrieved_memory=[], artifact_summaries=[], conflicts=[]),
        {"igem.pipeline.validate"},
    )
    assert plan.steps[0].tool_name == "igem.pipeline.validate"


def test_local_env_loader_respects_existing_environment(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_AGENT_KEY=from_file\n", encoding="utf-8")
    monkeypatch.setenv("TEST_AGENT_KEY", "from_process")
    assert load_local_env(env_file) is True
    assert __import__("os").environ["TEST_AGENT_KEY"] == "from_process"
    assert load_local_env(env_file, override=True) is True
    assert __import__("os").environ["TEST_AGENT_KEY"] == "from_file"

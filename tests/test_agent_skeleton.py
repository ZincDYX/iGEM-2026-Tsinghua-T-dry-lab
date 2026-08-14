from __future__ import annotations

from igem_drylab.agent import AgentRuntime, AgentTask, ArtifactRecord, ArtifactStore, BudgetManager, BudgetState, HumanApprovalGate, Plan, PlanStep, ResultBinding, ResultCondition
from igem_drylab.agent.context import ContextBundle
from igem_drylab.agent.env import load_local_env
from igem_drylab.agent.llm_planner import OpenAICompatiblePlanningBackend
from igem_drylab.mcp import McpTool, McpToolResult, ToolRegistry


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


def test_agent_selects_explicit_local_literature_qa(tmp_path):
    evidence = tmp_path / "evidence.jsonl"
    evidence.write_text('{"record_id":"r1","title":"OC study","doi":"10.1/oc","evidence":"OC converts compound 11."}\n', encoding="utf-8")
    trace = AgentRuntime(memory_path=tmp_path / "memory.jsonl").run_once(AgentTask(
        task_id="qa", objective="Find a local literature source",
        inputs={"evidence_database_path": str(evidence), "literature_question": "What converts compound 11?"},
    ))
    assert trace.final_status == "completed"
    assert trace.calls[0].tool_name == "igem.literature.qa"


def test_agent_blocks_when_required_input_is_missing(tmp_path):
    runtime = AgentRuntime(memory_path=tmp_path / "memory.jsonl")
    trace = runtime.run_once(
        AgentTask(task_id="missing", objective="Parse structure", inputs={"structure_output_path": "missing/output"})
    )

    assert trace.final_status == "blocked"
    assert "missing_input_path:path" in trace.notes[0]


def test_agent_replans_after_recoverable_failure_and_stops_at_limit(tmp_path):
    registry = ToolRegistry()
    tool = McpTool(name="test.malformed", title="test", description="test", input_schema={"type": "object"}, output_schema=None)
    registry.register(tool, lambda _arguments: McpToolResult.error("malformed structure artifact"))

    class PlannerBackend:
        def create_plan(self, task, context, available_tools):
            return Plan(task_id=task.task_id, steps=[PlanStep(step_id="broken", objective="parse", tool_name="test.malformed")])

    trace = AgentRuntime(memory_path=tmp_path / "memory.jsonl", registry=registry, planning_backend=PlannerBackend()).run_once(AgentTask(task_id="replan", objective="parse", max_replans=1))
    assert trace.replan_count == 1
    assert "replan_limit_reached" in trace.notes


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


def test_planner_selects_colabfold_only_after_explicit_compute_request(tmp_path):
    runtime = AgentRuntime(memory_path=tmp_path / "memory.jsonl")
    trace = runtime.dry_run(
        AgentTask(
            task_id="new-structure",
            objective="Screen OC DMT fusion structure",
            inputs={
                "config_path": "configs/m1_m4_real_scoring_example.yaml",
                "structure_input_file": "examples/data/proteins.fasta",
                "allow_new_compute": True,
            },
        )
    )
    run_step = next(step for step in trace.plan.steps if step.step_id == "run_colabfold")
    assert run_step.tool_name == "igem.compute.run_tool"
    assert run_step.resources == ["gpu"]
    assert run_step.estimated_gpu_minutes == 60
    assert next(step for step in trace.plan.steps if step.step_id == "parse_structure").depends_on == ["run_colabfold"]


def test_agent_queries_registry_then_evidence_for_missing_m4_parameters(tmp_path):
    evidence = tmp_path / "evidence.jsonl"
    evidence.write_text('{"record_id":"e1","doi":"10.1/example","evidence":"A kinetic measurement."}\n', encoding="utf-8")
    trace = AgentRuntime(memory_path=tmp_path / "memory.jsonl").dry_run(
        AgentTask(
            task_id="m4-missing", objective="Simulate glabridin DMT timing",
            inputs={
                "config_path": "configs/m1_m4_real_scoring_example.yaml",
                "target_stage": "m4", "evidence_database_path": str(evidence),
            },
        )
    )
    resolve_steps = [step for step in trace.plan.steps if step.tool_name == "igem.parameters.resolve"]
    evidence_steps = [step for step in trace.plan.steps if step.tool_name == "igem.literature.qa"]
    assert resolve_steps
    assert evidence_steps
    assert all("value" not in step.arguments for step in resolve_steps)
    assert any(step.step_id == "review_missing_parameters" and step.status == "blocked" for step in trace.plan.steps)


def test_runtime_binds_results_and_skips_failed_gate(tmp_path):
    registry = ToolRegistry()
    source_tool = McpTool("test.source", "source", "", {"type": "object"}, None)
    target_tool = McpTool("test.target", "target", "", {"type": "object"}, None)
    registry.register(source_tool, lambda _arguments: McpToolResult.ok({"result": {"passes": True, "penalty": {"value": 7}}}))
    registry.register(target_tool, lambda arguments: McpToolResult.ok({"received": arguments["penalty"]}))

    class FixedBackend:
        def create_plan(self, task, context, available_tools):
            return Plan(
                task_id=task.task_id,
                steps=[
                    PlanStep(
                        step_id="source", objective="source", tool_name="test.source",
                        result_bindings=[ResultBinding(target_step_id="target", target_argument="penalty", source_path=["structuredContent", "result", "penalty"])],
                    ),
                    PlanStep(
                        step_id="target", objective="target", tool_name="test.target", depends_on=["source"],
                        run_conditions=[ResultCondition(source_step_id="source", source_path=["structuredContent", "result", "passes"], allowed_values=[True])],
                    ),
                ],
            )

    trace = AgentRuntime(memory_path=tmp_path / "memory.jsonl", registry=registry, planning_backend=FixedBackend()).run_once(
        AgentTask(task_id="binding", objective="test")
    )
    assert trace.final_status == "completed"
    assert trace.plan.steps[1].status == "succeeded"
    assert trace.calls[1].result["structuredContent"]["received"] == {"value": 7}


def test_semantic_state_routing_is_not_case_id_specific(tmp_path):
    runtime = AgentRuntime(memory_path=tmp_path / "memory.jsonl")
    kp = runtime.dry_run(AgentTask(task_id="semantic-kp10", objective="A Kp10 measurement was updated.", inputs={"new_measurement": "Kp10", "construct_unchanged": True}))
    assert [step.step_id for step in kp.plan.steps] == ["dispatch_m3", "dispatch_m4"]
    linker = runtime.dry_run(AgentTask(task_id="semantic-linker", objective="OC fusion linker sequence changed from X to Y.", inputs={"changed_entities": ["OC_linker"], "structure_input_file": "example.fasta", "allow_new_compute": True}))
    assert [step.step_id for step in linker.plan.steps] == ["dispatch_m1", "dispatch_m2", "dispatch_m3", "dispatch_m4"]
    capacity = runtime.dry_run(AgentTask(task_id="semantic-capacity", objective="PDZ site count changed; fusion sequences are unchanged.", inputs={"change_type": "scaffold_capacity_update"}))
    assert [step.step_id for step in capacity.plan.steps] == ["dispatch_m3", "dispatch_m4"]


def test_invalid_artifact_is_blocked_before_reuse(tmp_path):
    trace = AgentRuntime(memory_path=tmp_path / "memory.jsonl").dry_run(AgentTask(task_id="bad-artifact", objective="Reuse structure", inputs={"artifact_checksum_invalid": True, "structure_output_path": "old"}))
    assert trace.plan.steps[0].step_id == "collect_missing_inputs"
    assert trace.plan.steps[0].status == "blocked"
    assert "integrity" in trace.plan.steps[0].rationale.lower()


def test_llm_contract_uses_json_output_and_single_repair():
    class RepairClient:
        def __init__(self): self.calls = 0
        def complete_json(self, prompt: str, **kwargs):
            self.calls += 1
            assert kwargs["response_format"] == {"type": "json_object"}
            if self.calls == 1: return {"steps": [{"id": "bad", "tool": None}]}
            return {"steps": [{"step_id": "collect_missing_inputs", "objective": "Request input", "tool_name": None, "arguments": {}, "depends_on": [], "required_artifact_ids": [], "produces": [], "run_conditions": [], "result_bindings": [], "resources": [], "priority": 50, "estimated_gpu_minutes": 0, "estimated_api_calls": 0, "retry_limit": 1, "attempts": 0, "status": "blocked", "rationale": "Input missing."}]}
    task = AgentTask(task_id="repair", objective="test")
    plan = OpenAICompatiblePlanningBackend(client=RepairClient()).create_plan(task, ContextBundle(task=task, constraints=[], retrieved_memory=[], artifact_summaries=[], conflicts=[]), set())  # type: ignore[arg-type]
    assert plan.diagnostics["schema_valid_first_attempt"] is False
    assert plan.diagnostics["schema_valid_after_repair"] is True

from __future__ import annotations

from igem_drylab.agent import AgentRuntime, AgentTask


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

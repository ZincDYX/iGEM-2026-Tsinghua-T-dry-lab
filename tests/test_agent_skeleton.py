from __future__ import annotations

from igem_drylab.agent import AgentRuntime, AgentTask


def test_agent_runtime_dry_run_exposes_framework_slots(tmp_path):
    runtime = AgentRuntime(memory_path=tmp_path / "memory.jsonl")
    trace = runtime.dry_run(AgentTask(task_id="demo", objective="Build dry-lab plan"))

    assert trace.task.task_id == "demo"
    assert trace.plan.steps
    assert trace.calls == []
    assert "Dry run only" in trace.notes[0]
    assert (tmp_path / "memory.jsonl").exists()

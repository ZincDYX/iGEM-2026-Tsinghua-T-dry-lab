from __future__ import annotations

from pathlib import Path

from igem_drylab.mcp import create_default_registry

from .executor import ToolExecutor
from .memory import AgentMemory
from .models import AgentTask, AgentTrace
from .planner import Planner
from .policy import DecisionPolicy
from .recovery import ErrorRecoveryPolicy


class AgentRuntime:
    """Composable agent runtime skeleton.

    This is intentionally not an autonomous agent yet. It provides the same
    architectural seams: planner, memory, decision policy, tool executor, trace,
    and recovery policy. Fill TODOs before enabling unattended execution.
    """

    def __init__(self, memory_path: Path | None = None) -> None:
        self.registry = create_default_registry()
        self.planner = Planner()
        self.policy = DecisionPolicy()
        self.executor = ToolExecutor(self.registry)
        self.recovery = ErrorRecoveryPolicy()
        self.memory = AgentMemory(memory_path or Path("outputs/agent_memory/events.jsonl"))

    def dry_run(self, task: AgentTask) -> AgentTrace:
        plan = self.planner.create_plan(task)
        trace = AgentTrace(task=task, plan=plan)
        trace.notes.append("Dry run only: planner skeleton produced a plan but no tools were executed.")
        self.memory.append({"event": "dry_run_created", "task_id": task.task_id, "step_count": len(plan.steps)})
        return trace

    def run_once(self, task: AgentTask) -> AgentTrace:
        """Execute one planner-produced pass.

        TODO: add dependency scheduling, budget control, human approval gates,
        retry limits, re-planning, provenance validation, and result reflection.
        """
        plan = self.planner.create_plan(task)
        trace = AgentTrace(task=task, plan=plan)
        for step in plan.steps:
            allowed, reason = self.policy.should_execute(step)
            if not allowed:
                trace.notes.append(f"{step.step_id}: {reason}")
                continue
            if not step.tool_name:
                trace.notes.append(f"{step.step_id}: no tool assigned; TODO planner must assign tools")
                continue
            call = self.executor.execute(step)
            trace.calls.append(call)
            if call.status == "failed":
                trace.notes.append(f"{step.step_id}: {self.recovery.next_action(step, call)}")
                break
        self.memory.append({"event": "run_once_completed", "task_id": task.task_id, "calls": len(trace.calls)})
        return trace

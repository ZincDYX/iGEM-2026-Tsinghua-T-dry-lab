from __future__ import annotations

from pathlib import Path

from igem_drylab.mcp import create_default_registry

from .artifacts import ArtifactStore
from .budget import BudgetManager
from .context import ContextBuilder
from .executor import ToolExecutor
from .human import HumanApprovalGate
from .memory import AgentMemory
from .models import AgentTask, AgentTrace
from .observability import EventLogger
from .planner import Planner
from .policy import DecisionPolicy
from .recovery import ErrorRecoveryPolicy
from .reflection import ReflectionEvaluator
from .scheduler import StepScheduler


class AgentRuntime:
    """Composable agent runtime skeleton.

    This is intentionally not an autonomous agent yet. It provides the same
    architectural seams: context building, planner, scheduler, memory,
    artifact/provenance store, budget guardrail, human gate, decision policy,
    tool executor, observability, reflection, trace, and recovery policy.
    Fill TODOs before enabling unattended execution.
    """

    def __init__(self, memory_path: Path | None = None) -> None:
        self.registry = create_default_registry()
        self.context_builder = ContextBuilder()
        self.planner = Planner()
        self.scheduler = StepScheduler()
        self.policy = DecisionPolicy()
        self.executor = ToolExecutor(self.registry)
        self.recovery = ErrorRecoveryPolicy()
        self.budget = BudgetManager()
        self.human_gate = HumanApprovalGate()
        self.reflection = ReflectionEvaluator()
        self.events = EventLogger()
        self.memory = AgentMemory(memory_path or Path("outputs/agent_memory/events.jsonl"))
        self.artifacts = ArtifactStore(Path("outputs/agent_artifacts"))

    def dry_run(self, task: AgentTask) -> AgentTrace:
        plan = self.planner.create_plan(task)
        trace = AgentTrace(task=task, plan=plan)
        self.context_builder.build_for_task(task)
        self.events.emit("dry_run_created", task_id=task.task_id, step_count=len(plan.steps))
        trace.notes.append("Dry run only: planner skeleton produced a plan but no tools were executed.")
        trace.notes.append("Agent framework slots present: context, planner, scheduler, memory, artifact store, budget, human gate, policy, executor, recovery, reflection, observability.")
        self.memory.append({"event": "dry_run_created", "task_id": task.task_id, "step_count": len(plan.steps)})
        return trace

    def run_once(self, task: AgentTask) -> AgentTrace:
        """Execute one planner-produced pass.

        TODO: add real dependency scheduling loops, retry limits, re-planning,
        provenance validation, and domain-specific result reflection rubrics.
        """
        plan = self.planner.create_plan(task)
        trace = AgentTrace(task=task, plan=plan)
        self.context_builder.build_for_task(task)
        for step in self.scheduler.ready_steps(plan):
            within_budget, budget_reason = self.budget.can_run_tool()
            if not within_budget:
                trace.notes.append(f"{step.step_id}: {budget_reason}")
                break
            if self.human_gate.requires_approval(step):
                trace.notes.append(f"{step.step_id}: waiting for human approval; TODO approval transport")
                continue
            allowed, reason = self.policy.should_execute(step)
            if not allowed:
                trace.notes.append(f"{step.step_id}: {reason}")
                continue
            if not step.tool_name:
                trace.notes.append(f"{step.step_id}: no tool assigned; TODO planner must assign tools")
                continue
            self.events.emit("tool_call_started", step_id=step.step_id, tool_name=step.tool_name)
            call = self.executor.execute(step)
            self.budget.record_tool_call(succeeded=call.status == "succeeded")
            trace.calls.append(call)
            if call.status == "failed":
                self.events.emit("tool_call_failed", step_id=step.step_id, tool_name=step.tool_name)
                trace.notes.append(f"{step.step_id}: {self.recovery.next_action(step, call)}")
                break
            self.events.emit("tool_call_succeeded", step_id=step.step_id, tool_name=step.tool_name)
        report = self.reflection.evaluate(trace)
        if not report.passed:
            trace.notes.extend(report.issues)
            trace.notes.extend(f"next_action: {item}" for item in report.next_actions)
        self.memory.append({"event": "run_once_completed", "task_id": task.task_id, "calls": len(trace.calls)})
        return trace

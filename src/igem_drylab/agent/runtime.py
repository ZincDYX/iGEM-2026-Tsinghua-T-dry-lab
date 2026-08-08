from __future__ import annotations

from pathlib import Path

from igem_drylab.mcp import ToolRegistry, create_default_registry

from .artifacts import ArtifactStore
from .budget import BudgetManager, BudgetState
from .context import ContextBuilder
from .executor import ToolExecutor
from .human import HumanApprovalGate
from .memory import AgentMemory, MemoryRecord
from .models import AgentTask, AgentTrace, Plan, PlanStep
from .observability import EventLogger
from .planner import Planner, PlanningBackend
from .policy import DecisionPolicy
from .recovery import ErrorRecoveryPolicy
from .reflection import ReflectionEvaluator
from .scheduler import StepScheduler


class AgentRuntime:
    """Conservative, traceable research-agent runtime for this project.

    It is deliberately autonomy-bounded: external API calls and costly GPU jobs
    stop at an approval gate, and scientific outputs are treated as hypotheses
    until wet-lab data validates them.
    """

    def __init__(
        self,
        memory_path: Path | None = None,
        *,
        artifacts_root: Path | None = None,
        event_path: Path | None = None,
        registry: ToolRegistry | None = None,
        budget_state: BudgetState | None = None,
        planning_backend: PlanningBackend | None = None,
    ) -> None:
        self.registry = registry or create_default_registry()
        self.memory = AgentMemory(memory_path or Path("outputs/agent_memory/events.jsonl"))
        self.artifacts = ArtifactStore(artifacts_root or Path("outputs/agent_artifacts"))
        self.context_builder = ContextBuilder(self.memory, self.artifacts)
        self.planner = Planner(self.registry, planning_backend)
        self.scheduler = StepScheduler()
        self.policy = DecisionPolicy(self.artifacts)
        self.executor = ToolExecutor(self.registry)
        self.recovery = ErrorRecoveryPolicy()
        self.budget = BudgetManager(budget_state)
        self.human_gate = HumanApprovalGate()
        self.reflection = ReflectionEvaluator(self.artifacts)
        self.events = EventLogger(event_path)

    def dry_run(self, task: AgentTask) -> AgentTrace:
        context = self.context_builder.build_for_task(task)
        plan = self.planner.create_plan(task, context)
        trace = AgentTrace(task=task, plan=plan, context_summary=_context_summary(context))
        self.events.emit("dry_run_created", task_id=task.task_id, step_count=len(plan.steps))
        trace.notes.append("Dry run only: planner produced a dependency-aware plan but no tools were executed.")
        trace.notes.append("Agent framework slots present: context, planner, scheduler, memory, artifact store, budget, human gate, policy, executor, recovery, reflection, observability.")
        self.memory.append(MemoryRecord(record_id=f"task-{task.task_id}", kind="task", content=task.objective, tags=["dry_run"], metadata={"step_count": len(plan.steps)}))
        return trace

    def run_once(self, task: AgentTask) -> AgentTrace:
        """Run a dependency-aware pass until completion, blockage, or failure.

        The method is synchronous by design. ``StepScheduler.next_batch`` keeps
        resource labels explicit so a future worker pool can safely parallelize
        independent CPU/network work without changing plan semantics.
        """
        context = self.context_builder.build_for_task(task)
        plan = self.planner.create_plan(task, context)
        trace = AgentTrace(task=task, plan=plan, context_summary=_context_summary(context))
        self.events.emit("agent_run_started", task_id=task.task_id, step_count=len(plan.steps))

        while True:
            batch = self.scheduler.next_batch(plan)
            if not batch:
                break
            progress = False
            replan_reason: str | None = None
            for step in batch:
                progress = self._run_step(task, trace, step) or progress
                if step.status == "blocked" and any(note.startswith(f"{step.step_id}:recovery=replan:") for note in trace.notes):
                    replan_reason = next(note.rsplit(":", 1)[-1] for note in reversed(trace.notes) if note.startswith(f"{step.step_id}:recovery=replan:"))
            if replan_reason is not None:
                if trace.replan_count >= task.max_replans:
                    trace.notes.append("replan_limit_reached")
                    break
                old_plan = trace.plan
                trace.replan_count += 1
                trace.replan_reasons.append(replan_reason)
                context = self.context_builder.build_for_task(task)
                plan = self.planner.create_plan(task, context)
                plan.previous_plan_id = old_plan.plan_id
                trace.plan = plan
                trace.context_summary = _context_summary(context)
                trace.notes.append(f"replanned:{old_plan.plan_id}->{plan.plan_id}:{replan_reason}")
                self.events.emit("agent_replanned", task_id=task.task_id, reason=replan_reason, replan_count=trace.replan_count)
                continue
            if not progress:
                break

        report = self.reflection.evaluate(trace)
        if not report.passed:
            trace.notes.extend(report.issues)
            trace.notes.extend(f"next_action:{item}" for item in report.next_actions)
        if any(step.status == "waiting_approval" for step in plan.steps):
            trace.final_status = "waiting_for_human"
        elif any(step.status == "blocked" for step in plan.steps):
            trace.final_status = "blocked"
        elif any(step.status == "failed" for step in plan.steps):
            trace.final_status = "failed"
        self.memory.append(MemoryRecord(record_id=f"run-{task.task_id}-{len(trace.calls)}", kind="reflection", content=trace.final_status, tags=["agent_run"], metadata={"calls": len(trace.calls), "notes": trace.notes}))
        self.events.emit("agent_run_finished", task_id=task.task_id, status=trace.final_status, calls=len(trace.calls))
        return trace

    def _run_step(self, task: AgentTask, trace: AgentTrace, step: PlanStep) -> bool:
        if step.status == "blocked":
            return False
        conditions_met, condition_reason = self._conditions_met(trace, step)
        if not conditions_met:
            step.status = "skipped"
            trace.notes.append(f"{step.step_id}:skipped:{condition_reason}")
            self.events.emit("step_skipped", step_id=step.step_id, reason=condition_reason)
            return True
        if self.human_gate.requires_approval(step) and task.require_human_approval:
            decision = self.human_gate.decision_for(step.step_id)
            if decision is None:
                step.status = "waiting_approval"
                trace.notes.append(f"{step.step_id}:waiting_for_human_approval")
                self.events.emit("approval_requested", step_id=step.step_id, tool_name=step.tool_name)
                return True
            if not decision.approved:
                step.status = "blocked"
                trace.notes.append(f"{step.step_id}:approval_rejected:{decision.reason}")
                return True
        allowed, reason = self.policy.should_execute(step)
        if not allowed:
            step.status = "blocked"
            trace.notes.append(f"{step.step_id}:{reason}")
            self.events.emit("step_blocked", step_id=step.step_id, reason=reason)
            return True
        within_budget, budget_reason = self.budget.can_run_tool(step)
        if not within_budget:
            step.status = "blocked"
            trace.notes.append(f"{step.step_id}:{budget_reason}")
            self.events.emit("step_blocked", step_id=step.step_id, reason=budget_reason)
            return True

        step.status = "running"
        step.attempts += 1
        self.events.emit("tool_call_started", step_id=step.step_id, tool_name=step.tool_name)
        call = self.executor.execute(step)
        self.budget.record_tool_call(step, succeeded=call.status == "succeeded")
        trace.calls.append(call)
        self.memory.append(MemoryRecord(record_id=f"call-{task.task_id}-{step.step_id}-{step.attempts}", kind="tool_call", content=f"{step.tool_name}:{call.status}", tags=[step.step_id, call.status], metadata={"result": call.result}))
        if call.status == "succeeded":
            step.status = "succeeded"
            self._apply_result_bindings(trace.plan, step, call, trace)
            self.events.emit("tool_call_succeeded", step_id=step.step_id, tool_name=step.tool_name)
            return True
        decision = self.recovery.next_action(step, call)
        self.events.emit("tool_call_failed", step_id=step.step_id, tool_name=step.tool_name, recovery_action=decision.action)
        trace.notes.append(f"{step.step_id}:recovery={decision.action}:{decision.reason}")
        if decision.action == "retry" and step.attempts <= step.retry_limit:
            step.status = "pending"
        elif decision.action in {"ask_user", "replan"}:
            step.status = "blocked"
        else:
            step.status = "failed"
        return True

    @staticmethod
    def _conditions_met(trace: AgentTrace, step: PlanStep) -> tuple[bool, str]:
        for condition in step.run_conditions:
            source = next((call for call in trace.calls if call.step_id == condition.source_step_id), None)
            if source is None:
                return False, f"condition_source_missing:{condition.source_step_id}"
            try:
                value = _read_result_path(source.result, condition.source_path)
            except (KeyError, TypeError):
                return False, f"condition_value_missing:{condition.source_step_id}"
            if value not in condition.allowed_values:
                return False, f"condition_not_met:{condition.source_step_id}"
        return True, "conditions_met"

    def _apply_result_bindings(self, plan: Plan, source_step: PlanStep, call: object, trace: AgentTrace) -> None:
        call_result = call.result  # type: ignore[attr-defined]
        steps = {step.step_id: step for step in plan.steps}
        for binding in source_step.result_bindings:
            target = steps.get(binding.target_step_id)
            if target is None:
                trace.notes.append(f"{source_step.step_id}:binding_target_missing:{binding.target_step_id}")
                continue
            try:
                target.arguments[binding.target_argument] = _read_result_path(call_result, binding.source_path)
            except (KeyError, TypeError):
                trace.notes.append(f"{source_step.step_id}:binding_value_missing:{binding.target_argument}")
                continue
            self.events.emit(
                "result_bound",
                source_step_id=source_step.step_id,
                target_step_id=target.step_id,
                target_argument=binding.target_argument,
            )


def _context_summary(context: object) -> dict[str, object]:
    bundle = context
    return {
        "memory_items": len(bundle.retrieved_memory),  # type: ignore[attr-defined]
        "artifact_items": len(bundle.artifact_summaries),  # type: ignore[attr-defined]
        "conflicts": bundle.conflicts,  # type: ignore[attr-defined]
    }


def _read_result_path(payload: object, path: list[str]) -> object:
    current = payload
    for key in path:
        if not isinstance(current, dict):
            raise TypeError(f"Cannot read '{key}' from non-object result")
        current = current[key]
    return current

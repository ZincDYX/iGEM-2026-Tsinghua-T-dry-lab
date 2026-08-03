from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic

from .models import PlanStep


@dataclass
class BudgetState:
    max_tool_calls: int = 20
    max_failures: int = 3
    max_wall_seconds: float = 3600.0
    max_gpu_minutes: float = 120.0
    max_external_api_calls: int = 10
    per_tool_quota: dict[str, int] = field(default_factory=dict)
    tool_calls_used: int = 0
    failures_seen: int = 0
    gpu_minutes_reserved: float = 0.0
    external_api_calls_reserved: int = 0
    tool_calls_by_name: dict[str, int] = field(default_factory=dict)


class BudgetManager:
    """Runtime budget guardrail for compute, wall time, and external calls."""

    def __init__(self, state: BudgetState | None = None) -> None:
        self.state = state or BudgetState()
        self._started_at = monotonic()

    def can_run_tool(self, step: PlanStep | None = None) -> tuple[bool, str]:
        if self.state.tool_calls_used >= self.state.max_tool_calls:
            return False, "tool_call_budget_exhausted"
        if self.state.failures_seen >= self.state.max_failures:
            return False, "failure_budget_exhausted"
        if monotonic() - self._started_at >= self.state.max_wall_seconds:
            return False, "wall_clock_budget_exhausted"
        if step is not None:
            if self.state.gpu_minutes_reserved + step.estimated_gpu_minutes > self.state.max_gpu_minutes:
                return False, "gpu_budget_exhausted"
            if "external_api" in step.resources and self.state.external_api_calls_reserved + step.estimated_api_calls > self.state.max_external_api_calls:
                return False, "external_api_budget_exhausted"
            quota = self.state.per_tool_quota.get(step.tool_name or "")
            if quota is not None and self.state.tool_calls_by_name.get(step.tool_name or "", 0) >= quota:
                return False, "per_tool_quota_exhausted"
        return True, "within_budget"

    def record_tool_call(self, step: PlanStep, *, succeeded: bool) -> None:
        self.state.tool_calls_used += 1
        self.state.gpu_minutes_reserved += step.estimated_gpu_minutes
        if "external_api" in step.resources:
            self.state.external_api_calls_reserved += step.estimated_api_calls
        if step.tool_name:
            self.state.tool_calls_by_name[step.tool_name] = self.state.tool_calls_by_name.get(step.tool_name, 0) + 1
        if not succeeded:
            self.state.failures_seen += 1

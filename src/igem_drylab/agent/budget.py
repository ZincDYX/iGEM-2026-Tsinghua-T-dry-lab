from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BudgetState:
    max_tool_calls: int = 20
    max_failures: int = 3
    tool_calls_used: int = 0
    failures_seen: int = 0


class BudgetManager:
    """Runtime guardrail for cost, time, and failure budget.

    TODO: extend with wall-clock limits, GPU-hour estimates, API-token budget,
    and per-tool quotas once real wet-lab infrastructure is connected.
    """

    def __init__(self, state: BudgetState | None = None) -> None:
        self.state = state or BudgetState()

    def can_run_tool(self) -> tuple[bool, str]:
        if self.state.tool_calls_used >= self.state.max_tool_calls:
            return False, "tool call budget exhausted"
        if self.state.failures_seen >= self.state.max_failures:
            return False, "failure budget exhausted"
        return True, "within budget"

    def record_tool_call(self, *, succeeded: bool) -> None:
        self.state.tool_calls_used += 1
        if not succeeded:
            self.state.failures_seen += 1

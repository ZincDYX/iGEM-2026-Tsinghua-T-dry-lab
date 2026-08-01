from __future__ import annotations

from .models import PlanStep, ToolCallRecord


class ErrorRecoveryPolicy:
    """Failure classification and retry/replan policy.

    TODO: classify recoverable failures such as missing executable, missing API
    key, malformed tool output, insufficient structure confidence, and wet-lab
    parameter gaps. Return retry, fallback, replan, ask-user, or fail-fast.
    """

    def next_action(self, step: PlanStep, call: ToolCallRecord) -> str:
        if call.status == "succeeded":
            return "continue"
        return "TODO_recovery_policy_not_implemented"

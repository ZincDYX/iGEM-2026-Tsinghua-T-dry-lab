from __future__ import annotations

from dataclasses import dataclass

from .models import PlanStep, ToolCallRecord


@dataclass(frozen=True)
class RecoveryDecision:
    action: str
    reason: str


class ErrorRecoveryPolicy:
    """Map structured tool failures to conservative recovery actions."""

    def next_action(self, step: PlanStep, call: ToolCallRecord) -> RecoveryDecision:
        if call.status == "succeeded":
            return RecoveryDecision("continue", "tool_succeeded")
        error = call.result.get("structuredContent", call.result).get("error", {})
        code = error.get("code", error.get("type"))
        if code == "missing_executable":
            return RecoveryDecision("ask_user", "configure_or_install_required_tool")
        if code == "missing_api_credential":
            return RecoveryDecision("ask_user", "missing_api_credential")
        if code in {"FileNotFoundError", "missing_input_path"}:
            return RecoveryDecision("ask_user", "missing_input_artifact")
        if code in {"TimeoutError", "TimeoutExpired", "timeout"} and step.attempts < step.retry_limit:
            return RecoveryDecision("retry", "transient_timeout")
        if code == "invalid_scientific_artifact":
            return RecoveryDecision("replan", "invalid_scientific_artifact")
        return RecoveryDecision("fail", "unclassified_tool_failure")

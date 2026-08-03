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
        message = str(call.result).lower()
        if "missing_executable" in message:
            return RecoveryDecision("ask_user", "configure_or_install_required_tool")
        if "api key" in message or "environment variable" in message:
            return RecoveryDecision("ask_user", "missing_api_credential")
        if "file not found" in message or "missing_input_path" in message:
            return RecoveryDecision("ask_user", "missing_input_artifact")
        if "timeout" in message and step.attempts < step.retry_limit:
            return RecoveryDecision("retry", "transient_timeout")
        if "no supported structure" in message or "malformed" in message:
            return RecoveryDecision("replan", "invalid_scientific_artifact")
        return RecoveryDecision("fail", "unclassified_tool_failure")

from __future__ import annotations

from dataclasses import dataclass

from .models import PlanStep


@dataclass(frozen=True)
class ApprovalDecision:
    approved: bool
    reason: str


class HumanApprovalGate:
    """Explicit approval ledger for irreversible, costly, or data-egress steps."""

    def __init__(self) -> None:
        self._decisions: dict[str, ApprovalDecision] = {}

    def requires_approval(self, step: PlanStep) -> bool:
        if step.arguments.get("requires_human_approval", False):
            return True
        if "external_api" in step.resources or step.estimated_gpu_minutes >= 30:
            return True
        protected_markers = ("push", "delete", "deploy", "merge")
        return bool(step.tool_name and any(marker in step.tool_name.lower() for marker in protected_markers))

    def approve(self, step_id: str, reason: str = "approved_by_operator") -> None:
        self._decisions[step_id] = ApprovalDecision(True, reason)

    def reject(self, step_id: str, reason: str = "rejected_by_operator") -> None:
        self._decisions[step_id] = ApprovalDecision(False, reason)

    def decision_for(self, step_id: str) -> ApprovalDecision | None:
        return self._decisions.get(step_id)

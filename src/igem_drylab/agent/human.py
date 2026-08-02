from __future__ import annotations

from .models import PlanStep


class HumanApprovalGate:
    """Gate high-impact actions before execution.

    TODO: classify actions that need human approval, such as pushing to main,
    deleting artifacts, running expensive GPU jobs, or sending external API data.
    """

    def requires_approval(self, step: PlanStep) -> bool:
        return bool(step.arguments.get("requires_human_approval", False))

from __future__ import annotations

from .models import PlanStep


class DecisionPolicy:
    """Tool-choice and safety policy layer.

    TODO: implement scientific decision rules, e.g. when to run heavy structure
    prediction, when to use mock fallback, when to ask for wet-lab input, and
    which artifacts are trusted enough to enter M1-M4 scoring.
    """

    def should_execute(self, step: PlanStep) -> tuple[bool, str]:
        if step.status in {"succeeded", "skipped"}:
            return False, "step_already_terminal"
        return True, "allowed_by_default_skeleton_policy"

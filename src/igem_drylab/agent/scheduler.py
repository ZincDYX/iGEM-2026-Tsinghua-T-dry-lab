from __future__ import annotations

from .models import Plan, PlanStep


class StepScheduler:
    """Select executable DAG steps from a plan.

    TODO: support parallel execution, resource labels such as GPU/CPU/network,
    and priority updates after reflection or user feedback.
    """

    def ready_steps(self, plan: Plan) -> list[PlanStep]:
        status_by_id = {step.step_id: step.status for step in plan.steps}
        return [
            step
            for step in plan.steps
            if step.status in {"pending", "ready"}
            and all(status_by_id.get(parent) == "succeeded" for parent in step.depends_on)
        ]

from __future__ import annotations

from .models import Plan, PlanStep


class StepScheduler:
    """Dependency-aware scheduler with resource-aware batch selection."""

    def ready_steps(self, plan: Plan) -> list[PlanStep]:
        status_by_id = {step.step_id: step.status for step in plan.steps}
        ready = [
            step
            for step in plan.steps
            if step.status in {"pending", "ready"}
            and all(status_by_id.get(parent) in {"succeeded", "skipped"} for parent in step.depends_on)
        ]
        return sorted(ready, key=lambda step: step.priority, reverse=True)

    def next_batch(self, plan: Plan, *, max_parallel: int = 1, available_resources: set[str] | None = None) -> list[PlanStep]:
        chosen: list[PlanStep] = []
        occupied: set[str] = set()
        allowed = available_resources or {"cpu", "gpu", "network", "external_api"}
        for step in self.ready_steps(plan):
            resources = set(step.resources)
            if not resources <= allowed or (resources & occupied):
                continue
            chosen.append(step)
            occupied |= resources
            if len(chosen) >= max_parallel:
                break
        return chosen

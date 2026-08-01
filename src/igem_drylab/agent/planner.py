from __future__ import annotations

from .models import AgentTask, Plan, PlanStep


class Planner:
    """Task-to-plan compiler.

    TODO: implement a real planner that reads available tools, task constraints,
    prior memory, budget, and wet-lab priorities before producing a DAG. A
    production version should support re-planning after failures or new evidence.
    """

    def create_plan(self, task: AgentTask) -> Plan:
        return Plan(
            task_id=task.task_id,
            steps=[
                PlanStep(
                    step_id="review_objective",
                    objective="Review task objective and required artifacts.",
                    rationale="Skeleton step; replace with project-specific planning logic.",
                )
            ],
        )

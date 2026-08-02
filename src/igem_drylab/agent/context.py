from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import AgentTask, PlanStep


@dataclass
class ContextBundle:
    task: AgentTask
    step: PlanStep | None = None
    retrieved_memory: list[dict[str, Any]] = field(default_factory=list)
    artifact_summaries: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)


class ContextBuilder:
    """Build the bounded context passed to planner/tool-selection modules.

    TODO: implement token budgeting, semantic memory retrieval, artifact
    summarization, and conflict handling between old memory and fresh evidence.
    """

    def build_for_task(self, task: AgentTask, *, step: PlanStep | None = None) -> ContextBundle:
        return ContextBundle(task=task, step=step, constraints=list(task.constraints))

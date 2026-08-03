from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .artifacts import ArtifactStore
from .memory import AgentMemory
from .models import AgentTask, PlanStep


@dataclass
class ContextBundle:
    task: AgentTask
    step: PlanStep | None = None
    retrieved_memory: list[dict[str, Any]] = field(default_factory=list)
    artifact_summaries: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)


class ContextBuilder:
    """Build bounded, provenance-aware context for planning and policy."""

    def __init__(self, memory: AgentMemory | None = None, artifacts: ArtifactStore | None = None, *, max_memory_items: int = 8) -> None:
        self.memory = memory
        self.artifacts = artifacts
        self.max_memory_items = max_memory_items

    def build_for_task(self, task: AgentTask, *, step: PlanStep | None = None) -> ContextBundle:
        query = " ".join([task.objective, *task.constraints, step.objective if step else ""])
        memories = self.memory.search(query, limit=self.max_memory_items) if self.memory else []
        conflicts = _find_conflicts(memories)
        return ContextBundle(
            task=task,
            step=step,
            retrieved_memory=[item.model_dump(mode="json") for item in memories],
            artifact_summaries=self.artifacts.summaries() if self.artifacts else [],
            constraints=list(task.constraints),
            conflicts=conflicts,
        )


def _find_conflicts(records: list[Any]) -> list[str]:
    by_tag: dict[str, set[str]] = {}
    for record in records:
        for tag in record.tags:
            if record.content:
                by_tag.setdefault(tag, set()).add(record.content)
    return [f"conflicting_memory_tag:{tag}" for tag, values in by_tag.items() if len(values) > 1]

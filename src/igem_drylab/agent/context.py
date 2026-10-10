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
    superseded = {record.claim.supersedes_record_id for record in records if record.claim}
    scoped: dict[tuple, list[Any]] = {}
    for record in records:
        if record.claim is None or record.record_id in superseded:
            continue
        claim = record.claim
        scope = (claim.subject_ref, claim.quantity, claim.construct_ref,
                 claim.condition_ref, claim.model_version, claim.canonical_unit, claim.entity_basis)
        scoped.setdefault(scope, []).append(record)
    return ["conflicting_scientific_claim:" + ",".join(record.record_id for record in items)
            for items in scoped.values() if len({(type(item.claim.value), item.claim.value) for item in items}) > 1]

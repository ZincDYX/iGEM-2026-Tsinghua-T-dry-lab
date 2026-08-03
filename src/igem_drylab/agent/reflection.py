from __future__ import annotations

from dataclasses import dataclass, field

from .artifacts import ArtifactStore
from .models import AgentTrace


@dataclass
class ReflectionReport:
    passed: bool
    issues: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)


class ReflectionEvaluator:
    """Deterministic completion and scientific-boundary checks.

    LLM reflection can be added as a second opinion, but it must not replace
    these checks or silently change experimental conclusions.
    """

    def __init__(self, artifacts: ArtifactStore | None = None) -> None:
        self.artifacts = artifacts

    def evaluate(self, trace: AgentTrace) -> ReflectionReport:
        issues: list[str] = []
        actions: list[str] = []
        failed = [call for call in trace.calls if call.status == "failed"]
        unfinished = [step.step_id for step in trace.plan.steps if step.status in {"pending", "ready", "running"}]
        blocked = [step.step_id for step in trace.plan.steps if step.status in {"blocked", "waiting_approval"}]
        if failed:
            issues.append(f"{len(failed)}_tool_calls_failed")
            actions.append("inspect_recovery_decisions")
        if unfinished:
            issues.append(f"unfinished_steps:{','.join(unfinished)}")
        if blocked:
            issues.append(f"blocked_steps:{','.join(blocked)}")
            actions.append("provide_missing_input_or_human_approval")
        if not trace.calls and not blocked:
            issues.append("no_scientific_tool_was_executed")
        if self.artifacts:
            invalid = [artifact_id for artifact_id in self.artifacts.records if not self.artifacts.verify(artifact_id)[0]]
            if invalid:
                issues.append(f"invalid_artifacts:{','.join(invalid)}")
        if any("absolute yield" in note.lower() for note in trace.notes):
            issues.append("unsupported_absolute_yield_claim")
        return ReflectionReport(not issues, issues=issues, next_actions=actions)

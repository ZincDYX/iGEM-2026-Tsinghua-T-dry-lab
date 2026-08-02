from __future__ import annotations

from dataclasses import dataclass, field

from .models import AgentTrace


@dataclass
class ReflectionReport:
    passed: bool
    issues: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)


class ReflectionEvaluator:
    """Evaluate whether a run result satisfies the task objective.

    TODO: add rubric-based checks, schema-level validation, scientific sanity
    checks, and optional LLM/self-reflection only after deterministic checks.
    """

    def evaluate(self, trace: AgentTrace) -> ReflectionReport:
        failed = [call for call in trace.calls if call.status == "failed"]
        if failed:
            return ReflectionReport(False, issues=[f"{len(failed)} tool call(s) failed"], next_actions=["replan"])
        return ReflectionReport(True)

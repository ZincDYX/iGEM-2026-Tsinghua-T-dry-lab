from __future__ import annotations

from pathlib import Path

from .artifacts import ArtifactStore
from .models import PlanStep


class DecisionPolicy:
    """Deterministic scientific and safety policy applied before every tool call."""

    HEAVY_TOOLS = {"igem.compute.run_tool"}

    def __init__(self, artifacts: ArtifactStore | None = None) -> None:
        self.artifacts = artifacts

    def should_execute(self, step: PlanStep) -> tuple[bool, str]:
        if step.status in {"succeeded", "skipped", "failed", "blocked"}:
            return False, "step_already_terminal"
        if not step.tool_name:
            return False, "no_tool_assigned"
        if self.artifacts:
            for artifact_id in step.required_artifact_ids:
                valid, reason = self.artifacts.verify(artifact_id)
                if not valid:
                    return False, f"required_artifact_{reason}:{artifact_id}"
        if step.tool_name in self.HEAVY_TOOLS and not step.arguments.get("dry_run", False):
            if not step.arguments.get("justification"):
                return False, "heavy_compute_requires_justification"
        for key, value in step.arguments.items():
            is_input_path = key == "path" or key.endswith("_path")
            if is_input_path and isinstance(value, str) and value and not Path(value).exists() and key not in {"output_path", "output_dir"}:
                return False, f"missing_input_path:{key}"
        return True, "allowed_by_policy"

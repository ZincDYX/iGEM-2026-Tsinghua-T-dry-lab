from __future__ import annotations

from igem_drylab.mcp import ToolRegistry

from .models import PlanStep, ToolCallRecord


class ToolExecutor:
    """Executes registry tools for agent plan steps."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def execute(self, step: PlanStep) -> ToolCallRecord:
        if not step.tool_name:
            raise ValueError(f"Plan step '{step.step_id}' has no tool_name")
        result = self.registry.call(step.tool_name, step.arguments).as_protocol_dict()
        status = "failed" if result.get("isError") else "succeeded"
        return ToolCallRecord(
            step_id=step.step_id,
            tool_name=step.tool_name,
            arguments=step.arguments,
            result=result,
            status=status,
        )

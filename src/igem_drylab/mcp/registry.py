from __future__ import annotations

from collections.abc import Iterable
import jsonschema

from .tools import TOOL_BINDINGS
from .research_tools import BINDINGS as RESEARCH_BINDINGS
from .types import JsonObject, McpTool, McpToolResult, ToolHandler


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, tuple[McpTool, ToolHandler]] = {}

    def register(self, tool: McpTool, handler: ToolHandler) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Duplicate MCP tool name: {tool.name}")
        self._tools[tool.name] = (tool, handler)

    def list_tools(self) -> list[JsonObject]:
        return [tool.as_protocol_dict() for tool, _handler in self._tools.values()]

    def names(self) -> Iterable[str]:
        return self._tools.keys()

    def call(self, name: str, arguments: JsonObject) -> McpToolResult:
        if name not in self._tools:
            return McpToolResult.error(f"Unknown tool: {name}", error_type="unknown_tool")
        _tool, handler = self._tools[name]
        try:
            jsonschema.Draft202012Validator(_tool.input_schema).validate(arguments)
            return handler(arguments)
        except Exception as exc:  # noqa: BLE001 - MCP tools should report structured failures.
            return McpToolResult.error(str(exc), error_type=getattr(exc, "code", exc.__class__.__name__))


def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for tool, handler in [*TOOL_BINDINGS, *RESEARCH_BINDINGS]:
        registry.register(tool, handler)
    return registry

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel


@dataclass(frozen=True)
class NodeContext:
    run_id: str
    node_id: str
    work_dir: Path
    # Inputs are resolved before dispatch; no live project state is provided.


class ToolFailure(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class ToolDefinition:
    id: str
    name: str
    description: str
    version: str
    input_model: type[BaseModel]
    handler: Callable[[BaseModel, NodeContext], dict[str, Any]]
    capability: str
    output_schema: dict[str, Any] = field(default_factory=lambda: {"type": "object"})
    runtime: str = "builtin"
    plugin_hash: str | None = None
    idempotent: bool = True
    resource: str = "cpu"
    input_schema: dict[str, Any] | None = None
    implementation_files: tuple[Path, ...] = ()

    def metadata(self) -> dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "version": self.version, "capability": self.capability,
            "input_schema": self.input_schema if self.input_schema is not None else self.input_model.model_json_schema(), "output_schema": self.output_schema,
            "runtime": self.runtime, "plugin_hash": self.plugin_hash,
            "idempotent": self.idempotent, "resource": self.resource,
        }


class WorkflowTools:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.id in self._tools:
            raise ValueError(f"duplicate_tool:{tool.id}")
        self._tools[tool.id] = tool

    def get(self, tool_id: str) -> ToolDefinition:
        try:
            return self._tools[tool_id]
        except KeyError as exc:
            raise ToolFailure("unknown_tool", tool_id) from exc

    def list(self) -> list[dict[str, Any]]:
        return [tool.metadata() for tool in self._tools.values()]

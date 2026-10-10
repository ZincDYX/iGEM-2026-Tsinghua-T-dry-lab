from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from threading import RLock

from pydantic import BaseModel


@dataclass(frozen=True)
class NodeContext:
    run_id: str
    node_id: str
    work_dir: Path
    runtime_tools: dict[str, Any] = field(default_factory=dict)
    upstream_results: tuple[dict[str, Any], ...] = ()
    scientific_project_sha256: str | None = None
    project_id: str | None = None
    snapshot_sha256: str | None = None
    # Inputs are resolved before dispatch; no live project state is provided.


class ToolFailure(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class ToolDeferred(Exception):
    """Known external job, not a result: release the worker until its next poll."""
    def __init__(self, job_id: str, *, poll_after_seconds: float = 60):
        if not job_id or poll_after_seconds <= 0:
            raise ValueError("invalid_deferred_job")
        self.job_id, self.poll_after_seconds = job_id, poll_after_seconds
        super().__init__("external_job_waiting")


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
    reconcile: Callable[[Path], bool] | None = None

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
        self._lock = RLock()

    def register(self, tool: ToolDefinition) -> None:
        with self._lock:
            if tool.id in self._tools:
                raise ValueError(f"duplicate_tool:{tool.id}")
            self._tools[tool.id] = tool

    def get(self, tool_id: str) -> ToolDefinition:
        try:
            with self._lock:
                return self._tools[tool_id]
        except KeyError as exc:
            raise ToolFailure("unknown_tool", tool_id) from exc

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            definitions = list(self._tools.values())
        return [tool.metadata() for tool in definitions]

    def definitions(self) -> tuple[ToolDefinition,...]:
        """Lightweight immutable catalog view; observers do not build all schemas."""
        with self._lock:
            return tuple(self._tools.values())

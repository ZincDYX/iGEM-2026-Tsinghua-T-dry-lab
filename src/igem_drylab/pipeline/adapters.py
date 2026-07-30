from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from .config import ToolConfig


class AdapterResult(BaseModel):
    tool: str
    mode: str
    repo_path: Path | None
    command_preview: str | None
    notes: str


class ExternalToolAdapter:
    """Boundary object for future replacement of mock calls with real tools."""

    def __init__(self, name: str, config: ToolConfig | None) -> None:
        self.name = name
        self.config = config or ToolConfig()

    def describe(self, command_preview: str | None = None) -> AdapterResult:
        notes = (
            "external execution placeholder"
            if self.config.enabled and self.config.mode == "external"
            else "deterministic mock execution"
        )
        return AdapterResult(
            tool=self.name,
            mode=self.config.mode,
            repo_path=self.config.repo_path,
            command_preview=command_preview or self.config.command,
            notes=notes,
        )

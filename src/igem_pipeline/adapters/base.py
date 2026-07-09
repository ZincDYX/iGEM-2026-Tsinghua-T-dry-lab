from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from igem_pipeline.config import ToolConfig


class AdapterResult(BaseModel):
    tool: str
    mode: str
    repo_path: Optional[Path]
    command_preview: Optional[str]
    notes: str


class ExternalToolAdapter:
    """Small boundary object for replacing mock calls with real tool execution."""

    def __init__(self, name: str, config: Optional[ToolConfig]) -> None:
        self.name = name
        self.config = config or ToolConfig()

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    def describe(self, command_preview: Optional[str] = None) -> AdapterResult:
        mode = self.config.mode
        notes = (
            "external execution placeholder"
            if self.enabled and mode == "external"
            else "deterministic mock execution"
        )
        return AdapterResult(
            tool=self.name,
            mode=mode,
            repo_path=self.config.repo_path,
            command_preview=command_preview or self.config.command,
            notes=notes,
        )

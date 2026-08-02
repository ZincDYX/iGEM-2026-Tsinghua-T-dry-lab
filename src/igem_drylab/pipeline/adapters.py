from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .config import ToolConfig


class AdapterResult(BaseModel):
    tool: str
    mode: str
    repo_path: Path | None
    command_preview: str | None
    notes: str


class ToolCommand(BaseModel):
    tool: str
    argv: list[str]
    cwd: Path | None = None


class ToolRunResult(BaseModel):
    tool: str
    mode: str
    status: str
    argv: list[str]
    cwd: Path | None = None
    stdout: str = ""
    stderr: str = ""
    return_code: int | None = None
    duration_seconds: float | None = None
    output_dir: Path | None = None
    manifest_file: Path | None = None
    notes: str = ""
    outputs: dict[str, Path] = Field(default_factory=dict)


class ExternalToolAdapter:
    """Boundary object for command-line scientific tools.

    The adapter supports deterministic mock mode, dry-run command rendering, and
    real subprocess execution. It deliberately does not parse scientific outputs;
    parsers should live in stage-specific modules once the exact tool output
    format is fixed.
    """

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

    def is_available(self) -> bool:
        command = self.config.command
        if not command:
            return False
        executable = _split_command(command)[0]
        return Path(executable).exists() or shutil.which(executable) is not None

    def build_command(self, **context: Any) -> ToolCommand:
        if not self.config.command:
            raise ValueError(f"Tool '{self.name}' has no command configured")
        render_context = {key: _path_to_string(value) for key, value in context.items()}
        rendered = self.config.command.format_map(_SafeFormatDict(render_context))
        return ToolCommand(tool=self.name, argv=_split_command(rendered), cwd=self.config.repo_path)

    def run(
        self,
        *,
        output_dir: Path,
        dry_run: bool = False,
        timeout_seconds: int = 3600,
        expected_outputs: dict[str, Path] | None = None,
        **context: Any,
    ) -> ToolRunResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        command = self.build_command(output_dir=output_dir, **context)
        if dry_run:
            result = ToolRunResult(
                tool=self.name,
                mode=self.config.mode,
                status="dry_run",
                argv=command.argv,
                cwd=command.cwd,
                output_dir=output_dir,
                notes="Dry-run mode: command rendered but not executed.",
                outputs=expected_outputs or {},
            )
            return self._write_manifest(result)
        if self.config.mode == "mock":
            result = ToolRunResult(
                tool=self.name,
                mode=self.config.mode,
                status="mock",
                argv=command.argv,
                cwd=command.cwd,
                output_dir=output_dir,
                notes="Mock mode: command rendered but not executed.",
                outputs=expected_outputs or {},
            )
            return self._write_manifest(result)
        if not self.is_available():
            result = ToolRunResult(
                tool=self.name,
                mode=self.config.mode,
                status="missing_executable",
                argv=command.argv,
                cwd=command.cwd,
                output_dir=output_dir,
                notes=f"Executable is not available for tool '{self.name}'.",
                outputs=expected_outputs or {},
            )
            return self._write_manifest(result)

        started = time.perf_counter()
        completed = subprocess.run(
            command.argv,
            cwd=command.cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        duration = round(time.perf_counter() - started, 3)
        result = ToolRunResult(
            tool=self.name,
            mode=self.config.mode,
            status="succeeded" if completed.returncode == 0 else "failed",
            argv=command.argv,
            cwd=command.cwd,
            stdout=completed.stdout,
            stderr=completed.stderr,
            return_code=completed.returncode,
            duration_seconds=duration,
            output_dir=output_dir,
            outputs=expected_outputs or {},
        )
        return self._write_manifest(result)

    def _write_manifest(self, result: ToolRunResult) -> ToolRunResult:
        if result.output_dir is None:
            return result
        manifest = result.output_dir / f"{self.name}_tool_run.json"
        manifest.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        return result.model_copy(update={"manifest_file": manifest})


class StructurePredictionAdapter(ExternalToolAdapter):
    def predict(self, *, input_file: Path, output_dir: Path, dry_run: bool = False) -> ToolRunResult:
        return self.run(input_file=input_file, output_dir=output_dir, dry_run=dry_run)


class ColabFoldAdapter(StructurePredictionAdapter):
    """Adapter for local ``colabfold_batch`` with the public MSA service.

    ColabFold performs model inference on the configured machine.  For small,
    serial batches it can obtain MSAs from the public MMseqs2 service, avoiding
    a local sequence database.  This adapter does not bypass the service's
    limits and does not turn the public MSA endpoint into a high-throughput API.
    """


class LlpsSimulationAdapter(ExternalToolAdapter):
    def simulate(self, *, config_file: Path, output_dir: Path, dry_run: bool = False) -> ToolRunResult:
        return self.run(config_file=config_file, output_dir=output_dir, dry_run=dry_run)


class SasaAdapter(ExternalToolAdapter):
    def calculate(self, *, pdb_file: Path, output_dir: Path, dry_run: bool = False) -> ToolRunResult:
        return self.run(pdb_file=pdb_file, output_dir=output_dir, dry_run=dry_run)


class DockingAdapter(ExternalToolAdapter):
    def dock(self, *, config_file: Path, output_dir: Path, dry_run: bool = False) -> ToolRunResult:
        return self.run(config_file=config_file, output_dir=output_dir, dry_run=dry_run)


class SequenceScreeningAdapter(ExternalToolAdapter):
    def predict(self, *, fasta_file: Path, output_dir: Path, dry_run: bool = False) -> ToolRunResult:
        return self.run(fasta_file=fasta_file, output_dir=output_dir, dry_run=dry_run)


def create_tool_adapter(name: str, config: ToolConfig | None) -> ExternalToolAdapter:
    adapter_types: dict[str, type[ExternalToolAdapter]] = {
        "colabfold": ColabFoldAdapter,
        "abcfold": StructurePredictionAdapter,
        "boltz": StructurePredictionAdapter,
        "chai": StructurePredictionAdapter,
        "calvados": LlpsSimulationAdapter,
        "freesasa": SasaAdapter,
        "autodock_vina": DockingAdapter,
        "signalp": SequenceScreeningAdapter,
        "deeptmhmm": SequenceScreeningAdapter,
    }
    return adapter_types.get(name, ExternalToolAdapter)(name, config)


def _split_command(command: str) -> list[str]:
    argv = shlex.split(command, posix=os.name != "nt")
    if not argv:
        raise ValueError("Command template rendered to an empty command")
    return argv


def _path_to_string(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    return value


class _SafeFormatDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"

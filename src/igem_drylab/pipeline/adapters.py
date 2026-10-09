from __future__ import annotations

import os
import shlex
import shutil
import signal
import subprocess
import time
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from igem_drylab.external_tools import ExternalToolSpec, tool_spec

from .config import ToolConfig


class AdapterResult(BaseModel):
    tool: str
    mode: str
    repo_path: Path | None
    command_preview: str | None
    notes: str
    spec: ExternalToolSpec | None = None


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
    executable_sha256: str | None = None
    input_sha256: dict[str, str] = Field(default_factory=dict)
    output_sha256: dict[str, str] = Field(default_factory=dict)
    stdout_sha256: str | None = None
    stderr_sha256: str | None = None


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
        self.spec = tool_spec(name)

    def describe(self, command_preview: str | None = None) -> AdapterResult:
        if not self.config.enabled:
            notes = "disabled"
        elif self.config.mode == "mock":
            notes = "demonstration-only mock"
        else:
            notes = "configured external execution"
        return AdapterResult(
            tool=self.name,
            mode=self.config.mode,
            repo_path=self.config.repo_path,
            command_preview=command_preview or self.config.command,
            notes=notes,
            spec=self.spec,
        )

    def is_available(self) -> bool:
        if not self.config.enabled or self.config.mode != "external":
            return False
        if self.config.repo_path is not None and not self.config.repo_path.is_dir():
            return False
        command = self.config.command
        if not command:
            return False
        executable = _split_command(command)[0]
        return Path(executable).exists() or shutil.which(executable) is not None

    def build_command(self, **context: Any) -> ToolCommand:
        if not self.config.command:
            raise ValueError(f"Tool '{self.name}' has no command configured")
        render_context = {key: _path_to_string(value) for key, value in context.items()}
        try:
            rendered = self.config.command.format_map(render_context)
        except KeyError as exc:
            raise ValueError(f"Tool '{self.name}' is missing command value: {exc.args[0]}") from exc
        return ToolCommand(tool=self.name, argv=_split_command(rendered), cwd=self.config.repo_path)

    def run(
        self,
        *,
        output_dir: Path,
        dry_run: bool = False,
        timeout_seconds: int = 3600,
        expected_outputs: dict[str, Path] | None = None,
        input_files: dict[str, Path] | None = None,
        **context: Any,
    ) -> ToolRunResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        if not self.config.enabled:
            return self._write_manifest(ToolRunResult(
                tool=self.name,
                mode=self.config.mode,
                status="disabled",
                argv=[],
                output_dir=output_dir,
                notes=f"Tool '{self.name}' is disabled in the project configuration.",
            ))
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
        executable = Path(shutil.which(command.argv[0]) or command.argv[0]).resolve()
        input_hashes = {str(Path(path).resolve()):sha256(Path(path).read_bytes()).hexdigest() for path in (input_files or {}).values()}
        executable_hash = sha256(executable.read_bytes()).hexdigest()
        process = None
        try:
            process = subprocess.Popen(command.argv, cwd=command.cwd, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, start_new_session=os.name != "nt")
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            completed = subprocess.CompletedProcess(command.argv, process.returncode, stdout, stderr)
        except (subprocess.TimeoutExpired, OSError) as error:
            stdout = getattr(error,"stdout",None) or ""
            stderr = getattr(error,"stderr",None) or ""
            if process is not None:
                # Python/API wrappers can own a native simulator. Stop the owned
                # tree too; killing only the wrapper leaves the simulator running.
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        capture_output=True, check=False, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                stdout, stderr = process.communicate()
            if isinstance(stdout,bytes): stdout = stdout.decode("utf-8",errors="replace")
            if isinstance(stderr,bytes): stderr = stderr.decode("utf-8",errors="replace")
            return self._write_manifest(ToolRunResult(tool=self.name,mode=self.config.mode,
                status="timed_out" if isinstance(error,subprocess.TimeoutExpired) else "execution_failed",
                argv=command.argv,cwd=command.cwd,stdout=stdout,stderr=stderr,
                duration_seconds=round(time.perf_counter()-started,3),output_dir=output_dir,
                executable_sha256=executable_hash,input_sha256=input_hashes,notes=str(error)))
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
            executable_sha256=executable_hash,
            input_sha256=input_hashes,
        )
        return self._write_manifest(result)

    def _write_manifest(self, result: ToolRunResult) -> ToolRunResult:
        if result.output_dir is None:
            return result
        result = result.model_copy(update={
            "output_sha256":{str(path.resolve()):sha256(path.read_bytes()).hexdigest() for path in result.outputs.values() if path.is_file()},
            "stdout_sha256":sha256(result.stdout.encode()).hexdigest(),
            "stderr_sha256":sha256(result.stderr.encode()).hexdigest()})
        manifest = result.output_dir / f"{self.name}_tool_run.json"
        manifest.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        return result.model_copy(update={"manifest_file": manifest})


def create_tool_adapter(name: str, config: ToolConfig | None) -> ExternalToolAdapter:
    return ExternalToolAdapter(name, config)


def _split_command(command: str) -> list[str]:
    if os.name == "nt":
        import ctypes
        parse = ctypes.windll.shell32.CommandLineToArgvW
        parse.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)]
        parse.restype = ctypes.POINTER(ctypes.c_wchar_p)
        free = ctypes.windll.kernel32.LocalFree
        free.argtypes = [ctypes.c_void_p]
        free.restype = ctypes.c_void_p
        count = ctypes.c_int()
        pointer = parse(command.strip(), ctypes.byref(count)) if command.strip() else None
        if pointer is None or not pointer:
            raise ValueError("Empty or invalid Windows command line")
        try:
            argv = [pointer[index] for index in range(count.value)]
        finally:
            free(pointer)
    else:
        argv = shlex.split(command)
    if not argv:
        raise ValueError("Command template rendered to an empty command")
    return argv


def _path_to_string(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    return value


__all__ = ["AdapterResult", "ExternalToolAdapter", "ToolCommand", "ToolRunResult", "create_tool_adapter"]

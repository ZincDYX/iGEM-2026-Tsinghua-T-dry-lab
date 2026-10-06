from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv
import re
import stat
from zipfile import ZipFile
from typing import Any, Literal

import jsonschema
import requests
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import Contract
from .store import WorkflowStore, canonical
from .tools import NodeContext, ToolDefinition, ToolFailure, WorkflowTools


class PluginManifest(Contract):
    protocol_version: Literal["1"] = "1"
    id: str = Field(pattern=r"^[A-Za-z0-9_.-]+$")
    name: str
    description: str
    version: str
    capability: str
    repository: str | None = None
    license: str
    runtime: Literal["python_venv"] = "python_venv"
    entrypoint: str
    requirements_lock: str | None = None
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    permissions: list[Literal["network", "gpu", "filesystem"]] = Field(default_factory=list)
    secret_env: list[str] = Field(default_factory=list)
    timeout_seconds: int = Field(default=300, ge=1)
    idempotent: bool = True
    resource: Literal["cpu", "gpu"] = "cpu"

    @model_validator(mode="after")
    def validate_schema(self) -> "PluginManifest":
        jsonschema.Draft202012Validator.check_schema(self.input_schema)
        jsonschema.Draft202012Validator.check_schema(self.output_schema)
        return self


class PluginArguments(BaseModel):
    model_config = ConfigDict(extra="allow")


def tree_hash(root: Path) -> str:
    digest = sha256()
    ignored = {".git", ".venv", "__pycache__", "node_modules"}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if set(relative.parts) & ignored:
            continue
        if path.is_symlink():
            raise ValueError("plugin_symlinks_not_supported")
        if path.is_file():
            digest.update(relative.as_posix().encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


def contained(root: Path, relative: str) -> Path:
    result = (root / relative).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError("plugin_path_outside_root")
    return result


class PluginManager:
    """Trusted plugin environments, isolated dependencies and JSON process IO.

    A virtual environment is not a security sandbox. Permission declarations
    are shown to the installer and recorded; arbitrary trusted Python code can
    still access the host. No environment secret is inherited implicitly.
    """

    def __init__(self, root: Path, store: WorkflowStore, tools: WorkflowTools, *, budget_bytes: int = 15_000_000_000, disclosure=None) -> None:
        self.root, self.store, self.tools = root.resolve(), store, tools
        self.budget_bytes = budget_bytes
        self.root.mkdir(parents=True, exist_ok=True)
        from .disclosure import DisclosureBoundary
        self.disclosure = disclosure or DisclosureBoundary(store)

    @staticmethod
    def process_environment() -> dict[str, str]:
        return {key: value for key, value in os.environ.items() if key in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP"}} | {"PYTHONNOUSERSITE": "1"}

    def authorize(self, source_hash: str, capabilities: list[str]) -> None:
        """Private maintainer operation, deliberately not an HTTP command."""
        with self.store.connection() as db:
            db.executemany("INSERT OR IGNORE INTO plugin_grants VALUES(?,?)", [(source_hash, capability) for capability in capabilities])

    def grants(self, source_hash: str) -> set[str]:
        with self.store.connection() as db:
            return {row[0] for row in db.execute("SELECT capability FROM plugin_grants WHERE hash=?", (source_hash,))}

    def inspect(self, source: Path) -> dict[str, Any]:
        source = source.resolve()
        manifest = PluginManifest.model_validate_json((source / "plugin.json").read_text(encoding="utf-8"))
        if not contained(source, manifest.entrypoint).is_file():
            raise ValueError("missing_plugin_entrypoint")
        return {"manifest": manifest.model_dump(mode="json"), "hash": tree_hash(source), "sandboxed": False, "trust_required": True}

    def fetch_github(self, repository: str, revision: str) -> dict[str, Any]:
        """Fetch pinned public source, never import or execute it before trust."""
        match = re.fullmatch(r"https://github\.com/([A-Za-z0-9_-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?", repository)
        if not match or not re.fullmatch(r"[0-9a-fA-F]{40}", revision):
            raise ValueError("github_requires_repository_URL_and_full_40_character_commit")
        owner, repo = match.groups()
        destination = self.root / "sources" / f"{owner}.{repo}.{revision.lower()}"
        if not destination.exists():
            limit = 256 * 1024 * 1024
            with requests.get(f"https://api.github.com/repos/{owner}/{repo}/zipball/{revision}", headers={"Accept": "application/vnd.github+json"}, stream=True, timeout=60) as response:
                response.raise_for_status()
                archive = BytesIO()
                for chunk in response.iter_content(1024 * 1024):
                    archive.write(chunk)
                    if archive.tell() > limit:
                        raise ValueError("plugin_archive_exceeds_256_MB")
            with ZipFile(archive) as zipped:
                members = [item for item in zipped.infolist() if not item.is_dir()]
                unpacked = sum(item.file_size for item in members)
                occupied = sum(path.stat().st_size for path in self.root.rglob("*") if path.is_file())
                if unpacked > limit or occupied + unpacked > self.budget_bytes:
                    raise ValueError("plugin_archive_storage_budget_exceeded")
                # Strip GitHub's one generated root folder, validating all paths
                # before writing any content. No hooks or plugin code is run.
                targets = []
                for member in members:
                    parts = Path(member.filename).parts
                    if len(parts) < 2 or stat.S_ISLNK(member.external_attr >> 16):
                        raise ValueError("invalid_plugin_archive")
                    targets.append((member, contained(destination, str(Path(*parts[1:])))))
                for member, target in targets:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(zipped.read(member))
        return {**self.inspect(destination), "source_path": str(destination), "repository_commit": revision.lower(), "download_url": repository}

    def install(self, source: Path, *, trusted: bool, expected_hash: str | None = None) -> dict[str, Any]:
        if not trusted:
            raise ValueError("explicit_trust_required")
        inspection = self.inspect(source)
        if expected_hash is not None and inspection["hash"] != expected_hash:
            from .models import WorkflowError
            raise WorkflowError("plugin_changed_since_inspection", status_code=409)
        manifest = PluginManifest.model_validate(inspection["manifest"])
        digest = inspection["hash"]
        installation = self.root / digest
        code = installation / "source"
        environment = installation / "environment"
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        ready = installation / "ready.json"
        if not ready.exists():
            installation.mkdir(parents=True, exist_ok=True)
            if not code.exists():
                shutil.copytree(source, code, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "node_modules"))
            if tree_hash(code) != digest:
                raise ValueError("plugin_source_changed_during_install")
            venv.EnvBuilder(with_pip=False).create(environment)
            if manifest.requirements_lock:
                lock = contained(code, manifest.requirements_lock)
                # Hashed lock files prevent a resolver from silently installing
                # different transitive package versions at a later date.
                try:
                    subprocess.run([str(python), "-I", "-m", "ensurepip"], env=self.process_environment(), check=True, timeout=120, capture_output=True, text=True)
                    subprocess.run([str(python), "-m", "pip", "install", "--require-hashes", "-r", str(lock)], env=self.process_environment(), check=True, timeout=600, capture_output=True, text=True)
                except subprocess.CalledProcessError as exc:
                    self.disclosure.diagnostic(exc, code="plugin_dependency_install_failed")
                    raise ToolFailure("plugin_dependency_install_failed", "Private installation diagnostic recorded") from exc
            ready.write_text(canonical({"source_hash": digest}), encoding="utf-8")
        if not python.exists() or tree_hash(code) != digest:
            raise ValueError("plugin_installation_changed")
        size = sum(path.stat().st_size for path in self.root.rglob("*") if path.is_file())
        if size > self.budget_bytes:
            raise ValueError("plugin_storage_budget_exceeded; installation not registered")
        record = {**inspection, "python": str(python), "source": str(code), "installed": True, "deployment_bytes": size}
        with self.store.connection() as db:
            db.execute("INSERT OR REPLACE INTO plugins VALUES(?,?)", (digest, canonical(record)))
        self._register(record)
        return record

    def installed(self) -> list[dict[str, Any]]:
        with self.store.connection() as db:
            return [json.loads(row["payload"]) for row in db.execute("SELECT payload FROM plugins")]

    def load_installed(self) -> None:
        for record in self.installed():
            self._register(record)

    def _register(self, record: dict[str, Any]) -> None:
        manifest = PluginManifest.model_validate(record["manifest"])
        # Versions have independent registry IDs so old run snapshots retain
        # their exact implementation after a new plugin release is installed.
        tool_id = f"plugin.{manifest.id}.{record['hash'][:12]}"
        if any(item["id"] == tool_id for item in self.tools.list()):
            return

        def invoke(payload: PluginArguments, context: NodeContext) -> dict[str, Any]:
            source = Path(record["source"])
            if tree_hash(source) != record["hash"]:
                raise ToolFailure("plugin_hash_mismatch", "Installed plugin source has changed")
            arguments = payload.model_dump(mode="json")
            jsonschema.Draft202012Validator(manifest.input_schema).validate(arguments)
            input_file, output_file = context.work_dir / "plugin_input.json", context.work_dir / "plugin_output.json"
            input_file.write_text(canonical(arguments), encoding="utf-8")
            grants = self.grants(record["hash"])
            requested = {"secret_env:" + key for key in manifest.secret_env} | {"permission:" + key for key in manifest.permissions}
            if not requested <= grants:
                raise ToolFailure("plugin_capability_not_authorized", "Maintainer capability grant required for this source hash")
            env = self.process_environment()
            for key in manifest.secret_env:
                if key in os.environ:
                    env[key] = os.environ[key]
                    self.disclosure.register_private(env[key])
            try:
                process = subprocess.run([record["python"], "-I", str(contained(source, manifest.entrypoint)), "--input", str(input_file), "--output", str(output_file)], cwd=context.work_dir, env=env, timeout=manifest.timeout_seconds, capture_output=True, text=True, check=False)
            except subprocess.TimeoutExpired as exc:
                raise ToolFailure("timeout", "Plugin process timed out", retryable=manifest.idempotent) from exc
            (context.work_dir / "plugin_stdout.log").write_text(process.stdout, encoding="utf-8")
            (context.work_dir / "plugin_stderr.log").write_text(process.stderr, encoding="utf-8")
            if process.returncode:
                raise ToolFailure("plugin_process_failed", "Private process logs recorded; no stderr is published")
            output = json.loads(output_file.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator(manifest.output_schema).validate(output)
            self.disclosure.check(output)
            return output

        self.tools.register(ToolDefinition(tool_id, manifest.name, manifest.description, manifest.version, PluginArguments, invoke, manifest.capability, output_schema=manifest.output_schema, runtime=manifest.runtime, plugin_hash=record["hash"], idempotent=manifest.idempotent, resource=manifest.resource, input_schema=manifest.input_schema))

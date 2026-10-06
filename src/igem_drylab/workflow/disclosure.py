"""Public projections and private diagnostics, independent of scientific math.

The ledger retains immutable originals. A projection is never represented as
the original artifact, and a secret-bearing original is quarantined, not edited.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath, PurePosixPath
import re
from typing import Any
from uuid import uuid4

from .models import Contract, Project, WorkflowError


class ArtifactView(Contract):
    id: str
    run_id: str
    node_id: str
    hash: str
    name: str
    upstream: list[str]
    metadata: dict[str, Any]


class NodeResultView(Contract):
    id: str
    parent_id: str | None
    status: str
    attempts: int
    output: dict[str, Any] | None
    error: dict[str, Any] | None
    inputs: None = None


class ScientificProjectView(Contract):
    config: dict[str, Any]
    evidence_files: list[dict[str, str]]
    dependency_scope: str


class DisclosureBoundary:
    def __init__(self, store):
        self.store = store
        self._private_values: set[str] = set()
        with store.connection() as db:
            for row in db.execute("SELECT payload FROM runtime_profiles"):
                self.register_runtime(json.loads(row[0]))

    def register_runtime(self, tools: dict) -> None:
        for tool in tools.values():
            for key in ("repo_path", "deployment_paths", "extra"):
                self.register_private(tool.get(key))
            command = tool.get("command")
            if command:
                self.register_private(" ".join(command) if isinstance(command, list) else command)

    def register_private(self, value: Any) -> None:
        if isinstance(value, dict):
            for item in value.values():
                self.register_private(item)
        elif isinstance(value, (tuple, list)):
            for item in value:
                self.register_private(item)
        elif isinstance(value, str) and len(value) >= 6:
            self._private_values.add(value)

    def check(self, value: Any, *, allow_paths: bool = False) -> None:
        encoded = json.dumps(value, ensure_ascii=False, default=str)
        if any(json.dumps(secret, ensure_ascii=False)[1:-1] in encoded for secret in self._private_values):
            raise WorkflowError("disclosure_quarantined", status_code=403)
        if not allow_paths:
            def walk(item):
                if isinstance(item, dict):
                    if any(key.lower() in {"api_key", "access_token", "password", "private_key", "secret_env", "deployment_paths", "repo_path"} for key in item):
                        raise WorkflowError("disclosure_quarantined", status_code=403)
                    for child in item.values(): walk(child)
                elif isinstance(item, list):
                    for child in item: walk(child)
                elif isinstance(item, str) and (PurePosixPath(item).is_absolute() or PureWindowsPath(item).is_absolute()):
                    raise WorkflowError("private_path_not_exportable", status_code=403)
            walk(value)

    def check_bytes(self, raw: bytes) -> None:
        if any(secret.encode() in raw for secret in self._private_values):
            raise WorkflowError("disclosure_quarantined",status_code=403)

    def diagnostic(self, error: Exception, *, code: str = "operation_failed") -> dict[str, Any]:
        diagnostic_id = str(uuid4())
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,95}", code) or any(value in code for value in self._private_values):
            code = "operation_failed"
        with self.store.connection() as db:
            db.execute("INSERT INTO private_diagnostics VALUES(?,?,?)", (diagnostic_id, type(error).__name__, str(error)))
        return {"code": code, "message": "操作未完成；请核对输入、证据或工具能力。", "diagnostic_id": diagnostic_id}

    def asset(self, path: str | Path, *, project_id: str | None = None) -> dict[str, str]:
        source = Path(path).resolve()
        with self.store.connection() as db:
            row = db.execute("SELECT * FROM file_assets WHERE path=?", (str(source),)).fetchone()
            if row is None:
                file_id = str(uuid4())
                digest = sha256(source.read_bytes()).hexdigest() if source.is_file() else ""
                db.execute("INSERT INTO file_assets VALUES(?,?,?,?,?)", (file_id, project_id, str(source), digest, source.name))
            else:
                if project_id and row["project_id"] and project_id != row["project_id"]:
                    raise WorkflowError("file_project_mismatch", status_code=403)
                file_id, digest = row["id"], row["hash"]
        return {"id": file_id, "file_id": file_id, "path": "asset:" + file_id, "sha256": digest, "name": source.name}

    def resolve_asset(self, file_id: str, project_id: str | None = None) -> str:
        file_id = file_id.removeprefix("asset:")
        with self.store.connection() as db:
            row = db.execute("SELECT * FROM file_assets WHERE id=?", (file_id,)).fetchone()
            if row is None:
                raise WorkflowError("unknown_file_identity", status_code=404)
            if project_id and row["project_id"] and row["project_id"] != project_id:
                raise WorkflowError("file_project_mismatch", status_code=403)
            if project_id:
                db.execute("UPDATE file_assets SET project_id=? WHERE id=? AND project_id IS NULL", (project_id, file_id))
        path = Path(row["path"])
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != row["hash"]:
            raise WorkflowError("file_identity_changed", status_code=409)
        return str(path)

    def tree(self, value: Any, *, project_id: str | None = None) -> Any:
        """Project filesystem identities, not arbitrary substring redaction."""
        if isinstance(value, Path): value = str(value)
        if isinstance(value, str) and (PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute()):
            return self.asset(value, project_id=project_id)["path"]
        if isinstance(value, dict):
            return {key: self.tree(item, project_id=project_id) for key, item in value.items()}
        if isinstance(value, list):
            return [self.tree(item, project_id=project_id) for item in value]
        return value

    def materialize(self, value: Any, project_id: str) -> Any:
        if isinstance(value, str) and value.startswith("asset:"):
            return self.resolve_asset(value, project_id)
        if isinstance(value, dict):
            return {key: self.materialize(item, project_id) for key, item in value.items()}
        if isinstance(value, list):
            return [self.materialize(item, project_id) for item in value]
        return value

    def scientific(self, raw: dict[str, Any], project_id: str | None = None) -> dict[str, Any]:
        from .scientific_project import ScientificProject
        parsed = ScientificProject.model_validate(raw)
        self.register_runtime({key: item.model_dump(mode="json") for key, item in parsed.config.tools.items()})
        config = parsed.config.model_dump(mode="json", exclude={"tools", "run"})
        # Run IDs are metadata, output directories are private placement.
        config["run"] = {"id": parsed.config.run.id}
        result = ScientificProjectView(config=self.tree(config, project_id=project_id),
            evidence_files=[{**self.asset(item.path, project_id=project_id), "sha256": item.sha256} for item in parsed.evidence_files],
            dependency_scope=parsed.dependency_scope).model_dump(mode="json")
        self.check(result)
        return result

    def project(self, project: Project) -> dict[str, Any]:
        result = project.model_dump(mode="json", exclude={"scientific_project"})
        result["files"] = [self.asset(item["path"], project_id=project.id) for item in project.files]
        result["scientific_project"] = self.scientific(project.scientific_project, project.id) if project.scientific_project else None
        result = self.tree(result, project_id=project.id)
        self.check(result)
        return result

    def private_project(self, project: Project) -> Project:
        raw = project.model_dump(mode="json")
        if raw["scientific_project"]:
            science = raw["scientific_project"]
            if science["config"].get("tools"):
                raise WorkflowError("runtime_settings_not_scientific_input")
            science["evidence_files"] = [{"path": item["path"], "sha256": item["sha256"]} for item in science["evidence_files"]]
            science["config"]["run"] = {"id": science["config"]["run"]["id"], "output_dir": "outputs"}
        for item in raw["files"]:
            if not item.get("path", "").startswith("asset:"):
                raise WorkflowError("use_registered_file_identity", status_code=403)
        return Project.model_validate(self.materialize(raw, project.id))

    def node(self, raw: dict[str, Any], project_id: str) -> dict[str, Any]:
        output = self.tree(raw["output"], project_id=project_id) if raw.get("output") is not None else None
        if output is not None:
            try: self.check(output)
            except WorkflowError:
                output = None
        error = raw.get("error")
        if error and not error.get("diagnostic_id"):
            error = self.diagnostic(ValueError(str(error)), code="historical_private_diagnostic")
        return NodeResultView(id=raw["id"], parent_id=raw["parent_id"], status=raw["status"],
            attempts=raw["attempts"], output=output, error=error).model_dump(mode="json")

    def run(self, raw: dict[str, Any]) -> dict[str, Any]:
        keys = ("id", "project_id", "status", "snapshot_hash", "created_at", "updated_at", "control")
        result = {key: raw[key] for key in keys}
        result.update(owner=None, heartbeat=raw.get("heartbeat"))
        snapshot = raw["snapshot"]
        result["snapshot"] = {"project": self.project(Project.model_validate(snapshot["project"])),
            "workflow": snapshot["workflow"], "tools": {key: {name: value[name] for name in ("version", "runtime", "plugin_hash", "implementation_sha256")}
                for key, value in snapshot["tools"].items()}, "environment": {"python": snapshot["environment"]["python"], "packages": snapshot["environment"]["packages"]}}
        result["nodes"] = [self.node(item, raw["project_id"]) for item in raw["nodes"]]
        result["artifacts"] = [ArtifactView(**{key: item[key] for key in ("id", "run_id", "node_id", "hash", "upstream", "metadata")}, name="result.json").model_dump(mode="json") for item in raw["artifacts"]]
        result["events"] = [{key: item[key] for key in ("seq", "node_id", "event", "timestamp")} | {"payload": {key: item["payload"][key] for key in ("status", "action", "proposal_id", "diagnostic_id") if key in item["payload"]}} for item in raw["events"]]
        self.check(result)
        return result

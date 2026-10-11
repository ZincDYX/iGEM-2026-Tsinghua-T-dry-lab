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
from .sequence_index import SequenceIndexView, sequence_index
from .store import file_sha256

# Explicit rules, not a claim that arbitrary secrets can be detected.
SENSITIVE_KEYS = {"api_key", "access_token", "password", "private_key", "secret_env", "deployment_paths", "repo_path", "ssh_host"}
TEXT_SUFFIXES = {".json", ".csv", ".tsv", ".yaml", ".yml", ".txt", ".ini", ".cfg", ".conf", ".env", ".pem", ".key"}


def check_sensitive_keys(value: Any) -> None:
    pending, visited = [value], set()
    while pending:
        item = pending.pop()
        if isinstance(item, (dict, list)) and id(item) not in visited:
            visited.add(id(item))
            if isinstance(item, dict):
                if any(isinstance(key, str) and key.lower() in SENSITIVE_KEYS for key in item):
                    raise WorkflowError("disclosure_quarantined", status_code=403)
                pending.extend(item.values())
            else:
                pending.extend(item)


def check_import_content(name: str, raw: bytes) -> Any:
    """Reject credential-shaped originals without echoing their names or values."""
    filename = Path(name).name.lower()
    if filename == ".env" or filename.startswith(".env.") or filename in {"id_rsa", "id_ed25519", "credentials", "credentials.json"}:
        raise WorkflowError("disclosure_quarantined", status_code=403)
    if re.search(rb"-----BEGIN (?:OPENSSH |RSA |EC |DSA |ENCRYPTED )?PRIVATE KEY-----", raw):
        raise WorkflowError("disclosure_quarantined", status_code=403)
    if Path(name).suffix.lower() not in TEXT_SUFFIXES:
        return
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise WorkflowError("invalid_text_encoding") from None
    keys = "|".join(re.escape(key) for key in sorted(SENSITIVE_KEYS))
    # Structured keys and line-start assignments; never scan scientific prose
    # for the word 'password' alone. JSON also uses the recursive key gate.
    if re.search(rf'(?:^|[{{,\n])\s*(?:-\s*)?[\"\']?(?:{keys})[\"\']?\s*[:=]', text, re.I):
        raise WorkflowError("disclosure_quarantined", status_code=403)
    if Path(name).suffix.lower() in {".csv", ".tsv"}:
        import csv
        from io import StringIO
        header = next(csv.reader(StringIO(text), delimiter="\t" if name.lower().endswith(".tsv") else ","), [])
        if any(column.strip().lower() in SENSITIVE_KEYS for column in header):
            raise WorkflowError("disclosure_quarantined", status_code=403)
    parsed = None
    if Path(name).suffix.lower() == ".json":
        parsed = json.loads(text)
    elif Path(name).suffix.lower() in {".yaml", ".yml"}:
        import yaml
        try:
            parsed = yaml.safe_load(text)
        except yaml.YAMLError:
            raise WorkflowError("invalid_structured_source") from None
    # Interpret escaped/quoted structured keys too; aliases are visited once.
    check_sensitive_keys(parsed)
    return parsed


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
    sequence_index: SequenceIndexView


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
            check_sensitive_keys(value)
            def walk(item):
                if isinstance(item, dict):
                    for child in item.values(): walk(child)
                elif isinstance(item, list):
                    for child in item: walk(child)
                elif isinstance(item, str) and (PurePosixPath(item).is_absolute() or PureWindowsPath(item).is_absolute()):
                    raise WorkflowError("private_path_not_exportable", status_code=403)
            walk(value)

    def check_bytes(self, raw: bytes) -> None:
        if any(secret.encode() in raw for secret in self._private_values):
            raise WorkflowError("disclosure_quarantined",status_code=403)

    def check_original(self, path: Path) -> Any:
        raw = path.read_bytes()
        self.check_bytes(raw)
        parsed = check_import_content(path.name, raw)
        if parsed is not None:
            self.check(parsed)
        return parsed

    def diagnostic(self, error: Exception, *, code: str = "operation_failed") -> dict[str, Any]:
        from .public_errors import diagnostic_code
        code = diagnostic_code(error, code)
        diagnostic_id = str(uuid4())
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,95}", code) or any(value in code for value in self._private_values):
            code = "operation_failed"
        with self.store.connection() as db:
            db.execute("INSERT INTO private_diagnostics VALUES(?,?,?)", (diagnostic_id, type(error).__name__, getattr(error,"private_detail",None) or str(error)))
        from .public_errors import ERROR_GUIDANCE, PublicError
        message, fields, actions = ERROR_GUIDANCE.get(code, ("Operation incomplete. Check inputs, evidence and tool capabilities.", [], ["Use the diagnostic ID to inspect private diagnostics"]))
        files = []
        for name in getattr(error,"logical_files",()):
            if not isinstance(name,str) or PurePosixPath(name).is_absolute() or PureWindowsPath(name).is_absolute() or ".." in Path(name).parts:
                continue
            try: self.check(name)
            except WorkflowError: continue
            files.append(name)
        return PublicError(code=code,message=message,diagnostic_id=diagnostic_id,field_paths=fields,logical_files=files,actions=actions).model_dump(mode="json")

    def asset(self, path: str | Path, *, project_id: str | None = None, fresh: bool = False, logical_name: str | None = None, db=None) -> dict[str, str]:
        if db is None:
            with self.store.connection() as connection:
                return self.asset(path, project_id=project_id, fresh=fresh, logical_name=logical_name, db=connection)
        source = Path(path).resolve()
        name = Path(logical_name).name if logical_name else source.name
        if logical_name:
            if PurePosixPath(logical_name).is_absolute() or PureWindowsPath(logical_name).drive or ".." in PurePosixPath(logical_name).parts or "\\" in logical_name:
                raise WorkflowError("invalid_upload_identity")
            self.check(logical_name)
        row = None if fresh else db.execute(
            "SELECT * FROM file_assets WHERE path=? AND (project_id IS ? OR project_id IS NULL) ORDER BY project_id IS NULL LIMIT 1",
            (str(source), project_id)).fetchone()
        if row is None:
            digest = file_sha256(source) if source.is_file() else ""
            # Ordinary GET projections with existing identities never take a
            # writer lock. Only registration serializes the read/insert pair.
            if not db.in_transaction:
                db.execute("BEGIN IMMEDIATE")
            if not fresh:
                row = db.execute("SELECT * FROM file_assets WHERE path=? AND (project_id IS ? OR project_id IS NULL) ORDER BY project_id IS NULL LIMIT 1",
                                 (str(source),project_id)).fetchone()
        if row is None:
            file_id = str(uuid4())
            db.execute("INSERT INTO file_assets(id,project_id,path,hash,name,logical_relative_path) VALUES(?,?,?,?,?,?)", (file_id, project_id, str(source), digest, name, logical_name))
        else:
            file_id, digest = row["id"], row["hash"]
            name = row["name"]
            if logical_name and row["logical_relative_path"] != logical_name:
                db.execute("UPDATE file_assets SET logical_relative_path=? WHERE id=?", (logical_name, file_id))
            if project_id and row["project_id"] is None:
                db.execute("UPDATE file_assets SET project_id=? WHERE id=? AND project_id IS NULL", (project_id,file_id))
                if db.execute("SELECT project_id FROM file_assets WHERE id=?", (file_id,)).fetchone()[0] != project_id:
                    raise WorkflowError("file_project_mismatch",status_code=403)
        return {"id": file_id, "file_id": file_id, "path": "asset:" + file_id, "sha256": digest, "name": name}

    def resolve_asset(self, file_id: str, project_id: str | None = None, *, verified=None) -> str:
        file_id = file_id.removeprefix("asset:")
        with self.store.connection() as db:
            row = db.execute("SELECT * FROM file_assets WHERE id=?", (file_id,)).fetchone()
            if row is None:
                raise WorkflowError("unknown_file_identity", status_code=404)
            if project_id and row["project_id"] and row["project_id"] != project_id:
                raise WorkflowError("file_project_mismatch", status_code=403)
            if project_id and row["project_id"] is None:
                db.execute("UPDATE file_assets SET project_id=? WHERE id=? AND project_id IS NULL", (project_id, file_id))
                if db.execute("SELECT project_id FROM file_assets WHERE id=?", (file_id,)).fetchone()[0] != project_id:
                    raise WorkflowError("file_project_mismatch",status_code=403)
        path = Path(row["path"])
        if not path.is_file() or file_sha256(path,verified) != row["hash"]:
            raise WorkflowError("file_identity_changed", status_code=409)
        return str(path)

    def tree(self, value: Any, *, project_id: str | None = None, db=None) -> Any:
        """Project filesystem identities, not arbitrary substring redaction."""
        if isinstance(value, Path): value = str(value)
        if isinstance(value, str) and (PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute()):
            return self.asset(value, project_id=project_id, db=db)["path"]
        if isinstance(value, dict):
            return {key: self.tree(item, project_id=project_id, db=db) for key, item in value.items()}
        if isinstance(value, list):
            return [self.tree(item, project_id=project_id, db=db) for item in value]
        return value

    def materialize(self, value: Any, project_id: str, *, verified=None) -> Any:
        if verified is None:
            verified = {}
        if isinstance(value, str) and value.startswith("asset:"):
            return self.resolve_asset(value, project_id, verified=verified)
        if isinstance(value, dict):
            return {key: self.materialize(item, project_id, verified=verified) for key, item in value.items()}
        if isinstance(value, list):
            return [self.materialize(item, project_id, verified=verified) for item in value]
        return value

    def scientific(self, raw: dict[str, Any], project_id: str | None = None, *, db=None) -> dict[str, Any]:
        if db is None:
            with self.store.connection() as connection:
                return self.scientific(raw, project_id, db=connection)
        from .scientific_project import ScientificProject
        parsed = ScientificProject.model_validate(raw)
        self.register_runtime({key: item.model_dump(mode="json") for key, item in parsed.config.tools.items()})
        config = parsed.config.model_dump(mode="json", exclude={"tools", "run"})
        # Run IDs are metadata, output directories are private placement.
        config["run"] = {"id": parsed.config.run.id}
        result = ScientificProjectView(config=self.tree(config, project_id=project_id, db=db),
            evidence_files=[{**self.asset(item.path, project_id=project_id, db=db), "sha256": item.sha256} for item in parsed.evidence_files],
            dependency_scope=parsed.dependency_scope,
            sequence_index=sequence_index(parsed, self.asset(parsed.config.inputs.protein_fasta, project_id=project_id, db=db), db)).model_dump(mode="json")
        self.check(result)
        return result

    def project(self, project: Project, *, db=None) -> dict[str, Any]:
        result = project.model_dump(mode="json", exclude={"scientific_project"})
        result["runtime_profile_ref"] = None
        result["files"] = [self.asset(item["path"], project_id=project.id, db=db) for item in project.files]
        result["scientific_project"] = self.scientific(project.scientific_project, project.id, db=db) if project.scientific_project else None
        result = self.tree(result, project_id=project.id, db=db)
        self.check(result)
        return result

    def private_project(self, project: Project) -> Project:
        raw = project.model_dump(mode="json")
        if project.runtime_profile_ref is not None:
            raise WorkflowError("runtime_profile_assignment_requires_maintainer",status_code=403)
        try:
            saved = self.store.project(project.id)
            raw["runtime_profile_ref"] = saved.runtime_profile_ref
            if (project.parent_run_id,project.parent_snapshot_sha256) != (saved.parent_run_id,saved.parent_snapshot_sha256):
                raise WorkflowError("iteration_identity_is_server_owned",status_code=403)
        except KeyError:
            if project.parent_run_id is not None or project.parent_snapshot_sha256 is not None:
                raise WorkflowError("iteration_identity_is_server_owned",status_code=403)
        if raw["scientific_project"]:
            science = raw["scientific_project"]
            science.pop("sequence_index", None)  # Derived, never an editable scientific input.
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

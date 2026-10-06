from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterator
from uuid import uuid4

from .models import NodeStatus, PlanBinding, Project, RunStatus, Workflow, WorkflowError


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def plan_binding(project: Project, workflow: Workflow) -> PlanBinding:
    return PlanBinding(project_id=project.id, project_revision=project.revision,
        project_input_sha256=sha256(canonical(project.model_dump(mode="json")).encode()).hexdigest(),
        workflow_sha256=sha256(canonical(workflow.model_dump(mode="json")).encode()).hexdigest())


class WorkflowStore:
    """Transactional run ledger. Connections are short-lived and thread-local."""

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, revision INTEGER NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS runs(
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL, status TEXT NOT NULL,
                    snapshot TEXT NOT NULL, snapshot_hash TEXT NOT NULL, owner TEXT,
                    heartbeat TEXT, control TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS nodes(
                    run_id TEXT NOT NULL REFERENCES runs(id), id TEXT NOT NULL, parent_id TEXT,
                    status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                    inputs TEXT, output TEXT, error TEXT, PRIMARY KEY(run_id,id));
                CREATE TABLE IF NOT EXISTS events(
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL REFERENCES runs(id),
                    node_id TEXT, event TEXT NOT NULL, payload TEXT NOT NULL, timestamp TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS artifacts(
                    id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id), node_id TEXT NOT NULL,
                    hash TEXT NOT NULL, path TEXT NOT NULL, upstream TEXT NOT NULL, metadata TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS plugins(hash TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS runtime_profiles(id TEXT PRIMARY KEY, revision INTEGER NOT NULL, hash TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS private_diagnostics(id TEXT PRIMARY KEY, error_type TEXT NOT NULL, message TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS file_assets(id TEXT PRIMARY KEY, project_id TEXT, path TEXT NOT NULL UNIQUE, hash TEXT NOT NULL, name TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS plugin_grants(hash TEXT NOT NULL, capability TEXT NOT NULL, PRIMARY KEY(hash,capability));
                CREATE INDEX IF NOT EXISTS events_run_seq ON events(run_id,seq);
                CREATE INDEX IF NOT EXISTS artifacts_run ON artifacts(run_id);
                CREATE INDEX IF NOT EXISTS runs_project_time ON runs(project_id,created_at DESC);
            """)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def save_project(self, project: Project, expected_revision: int | None = None) -> Project:
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT revision FROM projects WHERE id=?", (project.id,)).fetchone()
            if row and expected_revision != row["revision"]:
                raise WorkflowError("project_revision_conflict", status_code=409)
            if not row and expected_revision is not None:
                raise ValueError("project_not_found")
            updated = project.model_copy(update={"revision": row["revision"] + 1 if row else 1})
            db.execute("INSERT OR REPLACE INTO projects VALUES(?,?,?)", (updated.id, updated.revision, updated.model_dump_json()))
            return updated

    def projects(self) -> list[dict[str, Any]]:
        with self.connection() as db:
            return [json.loads(row["payload"]) for row in db.execute("SELECT payload FROM projects ORDER BY rowid DESC")]

    def project(self, project_id: str) -> Project:
        with self.connection() as db:
            row = db.execute("SELECT payload FROM projects WHERE id=?", (project_id,)).fetchone()
        if row is None:
            raise KeyError(project_id)
        return Project.model_validate_json(row["payload"])

    def create_confirmed_run(self, binding: PlanBinding, workflow: Workflow, build_snapshot) -> str:
        # The same writer lock excludes saves between approval checking and
        # recording the immutable snapshot (including custom workflows).
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload FROM projects WHERE id=?", (binding.project_id,)).fetchone()
            if row is None:
                raise KeyError(binding.project_id)
            project = Project.model_validate_json(row["payload"])
            if plan_binding(project, workflow) != binding:
                raise WorkflowError("plan_input_or_workflow_changed_regenerate_and_review", status_code=409)
            return self._insert_run(db, build_snapshot(project))

    def create_run(self, snapshot: dict[str, Any]) -> str:
        with self.connection() as db:
            return self._insert_run(db, snapshot)

    def _insert_run(self, db, snapshot: dict[str, Any]) -> str:
        run_id = str(uuid4())
        encoded = canonical(snapshot)
        db.execute("INSERT INTO runs VALUES(?,?,?,?,?,NULL,NULL,NULL,?,?)", (
            run_id, snapshot["project"]["id"], RunStatus.queued.value, encoded,
            sha256(encoded.encode()).hexdigest(), now(), now(),
        ))
        db.executemany("INSERT INTO nodes(run_id,id,status) VALUES(?,?,?)", [
            (run_id, node["id"], NodeStatus.pending.value) for node in snapshot["workflow"]["nodes"]
        ])
        db.execute("INSERT INTO events(run_id,event,payload,timestamp) VALUES(?,?,?,?)",
            (run_id, "run_created", "{}", now()))
        return run_id

    def run(self, run_id: str) -> dict[str, Any]:
        with self.connection() as db:
            row = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(run_id)
            result = dict(row)
            result["snapshot"] = json.loads(result["snapshot"])
            result["nodes"] = [self._node(item) for item in db.execute("SELECT * FROM nodes WHERE run_id=? ORDER BY rowid", (run_id,))]
            result["events"] = [{**dict(item), "payload": json.loads(item["payload"])} for item in db.execute("SELECT * FROM events WHERE run_id=? ORDER BY seq", (run_id,))]
            result["artifacts"] = [{**dict(item), "upstream": json.loads(item["upstream"]), "metadata": json.loads(item["metadata"])} for item in db.execute("SELECT * FROM artifacts WHERE run_id=?", (run_id,))]
        return result

    def runs(self, project_id: str | None = None) -> list[dict[str, Any]]:
        with self.connection() as db:
            rows = db.execute("SELECT id,project_id,status,snapshot_hash,created_at,updated_at,json_extract(snapshot,'$.workflow.name') AS name,json_extract(snapshot,'$.project.revision') AS project_revision FROM runs WHERE (? IS NULL OR project_id=?) ORDER BY created_at DESC", (project_id, project_id))
            return [dict(row) for row in rows]

    def claim(self, run_id: str, owner: str, stale_before: str) -> None:
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(run_id)
            if row["status"] in {RunStatus.succeeded.value, RunStatus.cancelled.value}:
                raise WorkflowError("run_is_terminal", status_code=409)
            if row["owner"] and row["heartbeat"] > stale_before:
                raise WorkflowError("run_has_active_worker", status_code=409)
            db.execute("UPDATE nodes SET status=? WHERE run_id=? AND status=?", (NodeStatus.interrupted.value, run_id, NodeStatus.running.value))
            db.execute("UPDATE runs SET status=?,owner=?,heartbeat=?,control=NULL,updated_at=? WHERE id=?", (RunStatus.running.value, owner, now(), now(), run_id))

    def heartbeat(self, run_id: str, owner: str) -> bool:
        with self.connection() as db:
            return db.execute("UPDATE runs SET heartbeat=? WHERE id=? AND owner=?", (now(), run_id, owner)).rowcount == 1

    def finish(self, run_id: str, owner: str, status: RunStatus) -> None:
        with self.connection() as db:
            db.execute("UPDATE runs SET status=?,owner=NULL,heartbeat=NULL,updated_at=? WHERE id=? AND owner=?", (status.value, now(), run_id, owner))
        self.event(run_id, "run_finished", {"status": status.value})

    def control(self, run_id: str, action: str) -> None:
        if action not in {"pause", "cancel"}:
            raise ValueError("unknown_control")
        with self.connection() as db:
            if db.execute("UPDATE runs SET control=?,updated_at=? WHERE id=?", (action, now(), run_id)).rowcount != 1:
                raise KeyError(run_id)

    def set_node(self, run_id: str, node_id: str, status: NodeStatus, *, inputs: Any = None, output: Any = None, error: Any = None, increment: bool = False) -> None:
        with self.connection() as db:
            db.execute("UPDATE nodes SET status=?,inputs=COALESCE(?,inputs),output=COALESCE(?,output),error=?,attempts=attempts+? WHERE run_id=? AND id=?", (
                status.value, canonical(inputs) if inputs is not None else None,
                canonical(output) if output is not None else None, canonical(error) if error else None,
                int(increment), run_id, node_id,
            ))
        self.event(run_id, "node_state", {"status": status.value, "error": error}, node_id)

    def expand(self, run_id: str, parent: str, inputs: list[dict[str, Any]]) -> None:
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            for index, arguments in enumerate(inputs):
                db.execute("INSERT OR IGNORE INTO nodes(run_id,id,parent_id,status,inputs) VALUES(?,?,?,?,?)", (run_id, f"{parent}[{index}]", parent, NodeStatus.pending.value, canonical(arguments)))
            db.execute("UPDATE nodes SET inputs=? WHERE run_id=? AND id=?", (canonical({"shard_count": len(inputs)}), run_id, parent))

    def event(self, run_id: str, event: str, payload: Any, node_id: str | None = None) -> None:
        with self.connection() as db:
            db.execute("INSERT INTO events(run_id,node_id,event,payload,timestamp) VALUES(?,?,?,?,?)", (run_id, node_id, event, canonical(payload), now()))

    def complete_node(self, run_id: str, node_id: str, output: dict[str, Any], path: Path, upstream: list[str]) -> None:
        digest = sha256(path.read_bytes()).hexdigest()
        artifact_id = sha256(f"{run_id}:{node_id}:{path.resolve()}".encode()).hexdigest()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            record = db.execute("SELECT inputs,attempts FROM nodes WHERE run_id=? AND id=?", (run_id, node_id)).fetchone()
            metadata = {"type": "application/json", "attempt": record["attempts"], "inputs_sha256": sha256((record["inputs"] or "{}").encode()).hexdigest()}
            db.execute("INSERT INTO artifacts VALUES(?,?,?,?,?,?,?)", (artifact_id, run_id, node_id, digest, str(path.resolve()), canonical(upstream), canonical(metadata)))
            db.execute("UPDATE nodes SET status=?,output=?,error=NULL WHERE run_id=? AND id=?", (NodeStatus.succeeded.value, canonical(output), run_id, node_id))
            db.execute("INSERT INTO events(run_id,node_id,event,payload,timestamp) VALUES(?,?,?,?,?)", (run_id, node_id, "node_state", canonical({"status": NodeStatus.succeeded.value, "error": None}), now()))

    @staticmethod
    def _node(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        for key in ("inputs", "output", "error"):
            result[key] = json.loads(result[key]) if result[key] else None
        return result

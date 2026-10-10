from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from threading import Condition
from time import time
from typing import Any, Iterator
from uuid import uuid4

from .models import NodeStatus, PlanBinding, Project, RunStatus, Workflow, WorkflowError


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def file_sha256(path: Path, verified: dict[Path,str] | None = None) -> str:
    """Stream bytes; deduplicate only within one caller-owned verification boundary."""
    path=path.resolve()
    if verified is not None and path in verified: return verified[path]
    digest=sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            digest.update(chunk)
    result=digest.hexdigest()
    if verified is not None: verified[path]=result
    return result


def plan_binding(project: Project, workflow: Workflow) -> PlanBinding:
    return PlanBinding(project_id=project.id, project_revision=project.revision,
        project_input_sha256=sha256(canonical(project.model_dump(mode="json")).encode()).hexdigest(),
        workflow_sha256=sha256(canonical(workflow.model_dump(mode="json")).encode()).hexdigest())


class WorkflowStore:
    """Transactional run ledger. Connections are short-lived and thread-local."""

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._changed = Condition()
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
                CREATE TABLE IF NOT EXISTS file_assets(id TEXT PRIMARY KEY, project_id TEXT, path TEXT NOT NULL, hash TEXT NOT NULL, name TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS scientific_bundles(id TEXT PRIMARY KEY, root TEXT NOT NULL UNIQUE);
                CREATE TABLE IF NOT EXISTS sequence_indexes(hash TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS plugin_grants(hash TEXT NOT NULL, capability TEXT NOT NULL, PRIMARY KEY(hash,capability));
                CREATE TABLE IF NOT EXISTS run_requests(id TEXT PRIMARY KEY, binding_hash TEXT NOT NULL, run_id TEXT NOT NULL REFERENCES runs(id));
                CREATE TABLE IF NOT EXISTS checkpoints(run_id TEXT NOT NULL, node_id TEXT NOT NULL, position TEXT NOT NULL, acknowledged INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(run_id,node_id,position));
                CREATE INDEX IF NOT EXISTS events_run_seq ON events(run_id,seq);
                CREATE INDEX IF NOT EXISTS artifacts_run ON artifacts(run_id);
                CREATE INDEX IF NOT EXISTS runs_project_time ON runs(project_id,created_at DESC);
            """)
            # Existing IDs/snapshots remain valid; content paths no longer imply
            # exclusive project ownership. Explicit imports get separate IDs.
            definition = db.execute("SELECT sql FROM sqlite_master WHERE name='file_assets'").fetchone()[0]
            if "UNIQUE" in definition.upper():
                db.executescript("""
                    BEGIN IMMEDIATE;
                    CREATE TABLE file_assets_v2(id TEXT PRIMARY KEY, project_id TEXT, path TEXT NOT NULL, hash TEXT NOT NULL, name TEXT NOT NULL);
                    INSERT INTO file_assets_v2 SELECT * FROM file_assets;
                    DROP TABLE file_assets;
                    ALTER TABLE file_assets_v2 RENAME TO file_assets;
                    COMMIT;
                """)
            db.execute("CREATE INDEX IF NOT EXISTS assets_path_project ON file_assets(path,project_id)")
            if "logical_relative_path" not in {row[1] for row in db.execute("PRAGMA table_info(file_assets)")}:
                db.execute("ALTER TABLE file_assets ADD COLUMN logical_relative_path TEXT")
            columns = {row[1] for row in db.execute("PRAGMA table_info(nodes)")}
            if "remote_job" not in columns:
                db.execute("ALTER TABLE nodes ADD COLUMN remote_job TEXT")
                db.execute("ALTER TABLE nodes ADD COLUMN poll_after REAL")

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

    def save_project(self, project: Project, expected_revision: int | None = None, *, db=None) -> Project:
        if db is None:
            with self.connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                return self.save_project(project, expected_revision, db=connection)
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

    def create_confirmed_run(self, binding: PlanBinding, workflow: Workflow, build_snapshot, request_id: str | None = None, authorize=None) -> str:
        # Expensive file/source verification must not hold the writer lock.
        prepared_project = self.project(binding.project_id)
        if plan_binding(prepared_project, workflow) != binding:
            raise WorkflowError("plan_input_or_workflow_changed_regenerate_and_review", status_code=409)
        snapshot = build_snapshot(prepared_project)
        encoded = canonical(snapshot)
        snapshot_hash = sha256(encoded.encode()).hexdigest()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload FROM projects WHERE id=?", (binding.project_id,)).fetchone()
            if row is None:
                raise KeyError(binding.project_id)
            project = Project.model_validate_json(row["payload"])
            if plan_binding(project, workflow) != binding:
                raise WorkflowError("plan_input_or_workflow_changed_regenerate_and_review", status_code=409)
            digest = sha256(canonical(binding.model_dump(mode="json")).encode()).hexdigest()
            if request_id:
                previous = db.execute("SELECT * FROM run_requests WHERE id=?", (request_id,)).fetchone()
                if previous:
                    if previous["binding_hash"] != digest:
                        raise WorkflowError("request_identity_conflict", status_code=409)
                    return previous["run_id"]
            if authorize is not None: authorize(db, snapshot)
            if snapshot["project"] != project.model_dump(mode="json"):
                raise WorkflowError("prepared_snapshot_project_mismatch", status_code=409)
            run_id = self._insert_run(db, snapshot, encoded=encoded, digest=snapshot_hash)
            if request_id: db.execute("INSERT INTO run_requests VALUES(?,?,?)", (request_id, digest, run_id))
            return run_id

    def create_run(self, snapshot: dict[str, Any]) -> str:
        with self.connection() as db:
            return self._insert_run(db, snapshot)

    def _insert_run(self, db, snapshot: dict[str, Any], *, encoded: str | None = None, digest: str | None = None) -> str:
        run_id = str(uuid4())
        encoded = encoded if encoded is not None else canonical(snapshot)
        db.execute("INSERT INTO runs VALUES(?,?,?,?,?,NULL,NULL,NULL,?,?)", (
            run_id, snapshot["project"]["id"], RunStatus.queued.value, encoded,
            digest or sha256(encoded.encode()).hexdigest(), now(), now(),
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

    def runs(self, project_id: str | None = None, *, offset: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        with self.connection() as db:
            where = " WHERE project_id=?" if project_id else ""
            args = (project_id,) if project_id else ()
            rows = db.execute("SELECT id,project_id,status,snapshot_hash,created_at,updated_at,json_extract(snapshot,'$.workflow.name') AS name,json_extract(snapshot,'$.project.revision') AS project_revision FROM runs" + where + " ORDER BY created_at DESC LIMIT ? OFFSET ?", (*args,limit,offset))
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
            db.execute("UPDATE nodes SET status=? WHERE run_id=? AND status IN (?,?)", (NodeStatus.interrupted.value, run_id, NodeStatus.running.value, NodeStatus.queued.value))
            db.execute("UPDATE runs SET status=?,owner=?,heartbeat=?,updated_at=? WHERE id=?", (RunStatus.running.value, owner, now(), now(), run_id))
            self._event(db,run_id,"run_claimed",{"status":"running"})

    def clear_control(self, run_id: str) -> None:
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status,owner,heartbeat,control FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None: raise KeyError(run_id)
            if row["status"] in {"succeeded","cancelled"} or row["control"] == "cancel":
                raise WorkflowError("run_is_terminal",status_code=409)
            if row["owner"]:
                from datetime import timedelta
                if row["heartbeat"] and row["heartbeat"] > (datetime.now(timezone.utc)-timedelta(seconds=20)).isoformat():
                    raise WorkflowError("run_has_active_worker",status_code=409)
            db.execute("UPDATE runs SET control=NULL,status=?,updated_at=? WHERE id=?", (RunStatus.queued.value,now(),run_id))
            db.execute("UPDATE checkpoints SET acknowledged=1 WHERE run_id=?", (run_id,))
            self._event(db,run_id,"control_resumed",{"action":"resume"})

    def checkpoint(self, run_id: str, node_id: str, position: str) -> bool:
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            control = db.execute("SELECT control FROM runs WHERE id=?", (run_id,)).fetchone()
            if control is None: raise KeyError(run_id)
            if control[0] == "cancel": return False
            row = db.execute("SELECT acknowledged FROM checkpoints WHERE run_id=? AND node_id=? AND position=?", (run_id,node_id,position)).fetchone()
            if row and row[0]: return False
            db.execute("INSERT OR IGNORE INTO checkpoints(run_id,node_id,position) VALUES(?,?,?)", (run_id,node_id,position))
            db.execute("INSERT INTO events(run_id,node_id,event,payload,timestamp) VALUES(?,?,?,?,?)", (run_id,node_id,"checkpoint_reached",canonical({"position":position}),now()))
            db.execute("UPDATE runs SET control='pause',updated_at=? WHERE id=?", (now(),run_id))
        return True

    def execution_state(self, run_id: str) -> dict[str, Any]:
        with self.connection() as db:
            row = db.execute("SELECT id,project_id,status,control,created_at,updated_at,heartbeat FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None: raise KeyError(run_id)
            result = dict(row)
            result["nodes"] = [dict(item) | {"inputs":json.loads(item["inputs"]) if item["inputs"] else None, "output":None, "error":None}
                for item in db.execute("SELECT id,parent_id,status,attempts,inputs,poll_after FROM nodes WHERE run_id=? ORDER BY rowid",(run_id,))]
            result["artifacts"] = [dict(item) for item in db.execute(
                """SELECT a.id,a.node_id,a.hash FROM artifacts a
                JOIN nodes n ON n.run_id=a.run_id AND n.id=a.node_id
                WHERE a.run_id=? AND n.status='succeeded'
                AND json_extract(a.metadata,'$.attempt')=n.attempts""", (run_id,))]
        return result

    def node_output(self, run_id: str, node_id: str):
        with self.connection() as db:
            row = db.execute("SELECT output FROM nodes WHERE run_id=? AND id=?",(run_id,node_id)).fetchone()
        if row is None: raise KeyError(node_id)
        return json.loads(row[0]) if row[0] else None

    def verified_upstream(self, run_id: str, node_ids: list[str]) -> tuple[dict[str, Any], ...]:
        results = []
        with self.connection() as db:
            for node_id in node_ids:
                row = db.execute("""SELECT a.*,n.status,n.inputs,r.project_id,r.snapshot_hash
                    FROM artifacts a JOIN nodes n ON n.run_id=a.run_id AND n.id=a.node_id
                    JOIN runs r ON r.id=a.run_id WHERE a.run_id=? AND a.node_id=?
                    AND json_extract(a.metadata,'$.attempt')=n.attempts""", (run_id,node_id)).fetchone()
                if row is None or row["status"] != NodeStatus.succeeded.value:
                    raise WorkflowError("upstream_result_not_successful")
                metadata = json.loads(row["metadata"])
                if metadata["inputs_sha256"] != sha256((row["inputs"] or "{}").encode()).hexdigest():
                    raise WorkflowError("upstream_result_inputs_mismatch")
                path = Path(row["path"])
                raw = path.read_bytes()
                if sha256(raw).hexdigest() != row["hash"]: raise WorkflowError("upstream_result_hash_mismatch")
                results.append({"artifact_id":row["id"],"sha256":row["hash"],"node_id":node_id,"run_id":run_id,
                    "project_id":row["project_id"],"snapshot_hash":row["snapshot_hash"],"output":json.loads(raw)})
        return tuple(results)

    def heartbeat(self, run_id: str, owner: str) -> bool:
        with self.connection() as db:
            return db.execute("UPDATE runs SET heartbeat=? WHERE id=? AND owner=?", (now(), run_id, owner)).rowcount == 1

    def finish(self, run_id: str, owner: str, status: RunStatus) -> None:
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row=db.execute("SELECT control FROM runs WHERE id=? AND owner=?",(run_id,owner)).fetchone()
            if row is None: return
            final = "cancelled" if row["control"] == "cancel" else status.value
            db.execute("UPDATE runs SET status=?,control=NULL,owner=NULL,heartbeat=NULL,updated_at=? WHERE id=? AND owner=?", (final, now(), run_id, owner))
            self._event(db,run_id,"run_finished",{"status":final})

    def control(self, run_id: str, action: str) -> None:
        if action not in {"pause", "cancel"}:
            raise ValueError("unknown_control")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status,owner,control FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None: raise KeyError(run_id)
            if action == "cancel" and row["status"] == "cancelled": return
            if row["status"] in {"succeeded","failed","cancelled"}:
                raise WorkflowError("run_is_terminal",status_code=409)
            if row["control"] == "cancel": return
            if action == "cancel" and row["owner"] is None:
                db.execute("UPDATE runs SET status='cancelled',control=NULL,updated_at=? WHERE id=?", (now(),run_id))
                self._event(db,run_id,"control_requested",{"action":"cancel","actor":"user"})
                self._event(db,run_id,"run_finished",{"status":"cancelled"})
                return
            db.execute("UPDATE runs SET control=?,updated_at=? WHERE id=?", (action, now(), run_id))
            self._event(db,run_id,"control_requested",{"action":action,"actor":"user_or_execution_policy"})
        self.notify_change()

    def notify_change(self):
        with self._changed:
            self._changed.notify_all()

    def wait_for_change(self, timeout):
        with self._changed:
            self._changed.wait(timeout)

    def defer_node(self, run_id, node_id, job_id, poll_after_seconds):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT remote_job FROM nodes WHERE run_id=? AND id=?", (run_id,node_id)).fetchone()
            previous = json.loads(row[0]) if row[0] else {}
            if previous and previous["job_id"] != job_id:
                raise WorkflowError("remote_job_identity_changed")
            job = {"job_id":job_id,"status":"waiting_for_result","poll_count":previous.get("poll_count",0)+1,
                   "remote_cancellation_confirmed":False}
            db.execute("UPDATE nodes SET status='waiting',remote_job=?,poll_after=?,error=NULL WHERE run_id=? AND id=?",
                       (canonical(job),time()+poll_after_seconds,run_id,node_id))
            self._event(db,run_id,"remote_job_waiting",job,node_id)
        self.notify_change()

    def set_node(self, run_id: str, node_id: str, status: NodeStatus, *, inputs: Any = None, output: Any = None, error: Any = None, increment: bool = False) -> None:
        with self.connection() as db:
            db.execute("UPDATE nodes SET status=?,inputs=COALESCE(?,inputs),output=COALESCE(?,output),error=?,attempts=attempts+? WHERE run_id=? AND id=?", (
                status.value, canonical(inputs) if inputs is not None else None,
                canonical(output) if output is not None else None, canonical(error) if error else None,
                int(increment), run_id, node_id,
            ))
            self._event(db,run_id,"node_state",{"status":status.value,"diagnostic_id":error.get("diagnostic_id") if error else None},node_id)

    def expand(self, run_id: str, parent: str, inputs: list[dict[str, Any]]) -> None:
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            for index, arguments in enumerate(inputs):
                db.execute("INSERT OR IGNORE INTO nodes(run_id,id,parent_id,status,inputs) VALUES(?,?,?,?,?)", (run_id, f"{parent}[{index}]", parent, NodeStatus.pending.value, canonical(arguments)))
            db.execute("UPDATE nodes SET inputs=? WHERE run_id=? AND id=?", (canonical({"shard_count": len(inputs)}), run_id, parent))
            self._event(db,run_id,"map_expanded",{},parent)

    def event(self, run_id: str, event: str, payload: Any, node_id: str | None = None) -> None:
        with self.connection() as db:
            self._event(db,run_id,event,payload,node_id)

    @staticmethod
    def _event(db, run_id: str, event: str, payload: Any, node_id: str | None = None):
        db.execute("INSERT INTO events(run_id,node_id,event,payload,timestamp) VALUES(?,?,?,?,?)", (run_id,node_id,event,canonical(payload),now()))

    def complete_node(self, run_id: str, node_id: str, output: dict[str, Any], path: Path, upstream: list[str]) -> None:
        digest = file_sha256(path)
        artifact_id = sha256(f"{run_id}:{node_id}:{path.resolve()}".encode()).hexdigest()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            record = db.execute("SELECT inputs,attempts FROM nodes WHERE run_id=? AND id=?", (run_id, node_id)).fetchone()
            if db.execute("SELECT control FROM runs WHERE id=?", (run_id,)).fetchone()[0] == "cancel":
                error = canonical({"code":"cancelled_before_publication","message":"已取消；结果未发布。"})
                db.execute("UPDATE nodes SET status=?,error=? WHERE run_id=? AND id=?", (NodeStatus.interrupted.value,error,run_id,node_id))
                return
            metadata = {"type": "application/json", "attempt": record["attempts"], "inputs_sha256": sha256((record["inputs"] or "{}").encode()).hexdigest()}
            db.execute("INSERT INTO artifacts VALUES(?,?,?,?,?,?,?)", (artifact_id, run_id, node_id, digest, str(path.resolve()), canonical(upstream), canonical(metadata)))
            db.execute("UPDATE nodes SET status=?,output=?,error=NULL WHERE run_id=? AND id=?", (NodeStatus.succeeded.value, canonical(output), run_id, node_id))
            db.execute("UPDATE nodes SET remote_job=json_set(remote_job,'$.status','published'),poll_after=NULL WHERE run_id=? AND id=? AND remote_job IS NOT NULL", (run_id,node_id))
            db.execute("INSERT INTO events(run_id,node_id,event,payload,timestamp) VALUES(?,?,?,?,?)", (run_id, node_id, "node_state", canonical({"status": NodeStatus.succeeded.value, "error": None}), now()))

    @staticmethod
    def _node(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        for key in ("inputs", "output", "error", "remote_job"):
            result[key] = json.loads(result[key]) if result[key] else None
        return result

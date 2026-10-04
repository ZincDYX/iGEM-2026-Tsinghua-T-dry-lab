from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, wait, FIRST_COMPLETED
from copy import deepcopy
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import inspect
import json
from pathlib import Path
import platform
from importlib.metadata import version
from threading import Event, Lock, Thread
from typing import Any
from uuid import uuid4

from pydantic import ValidationError
import jsonschema

from .models import InputValue, LiteralInput, NodeInput, NodeStatus, Project, ProjectInput, RunStatus, Workflow, read_path
from .store import WorkflowStore, canonical
from .tools import NodeContext, ToolFailure, WorkflowTools


class WorkflowEngine:
    """Execute an immutable DAG with durable map shards and bounded concurrency."""

    def __init__(self, store: WorkflowStore, tools: WorkflowTools, artifact_root: Path, *, max_workers: int = 4) -> None:
        if max_workers < 1:
            raise ValueError("max_workers_must_be_positive")
        self.store, self.tools = store, tools
        self.artifact_root = artifact_root.resolve()
        self.max_workers = max_workers
        self._gpu_lock = Lock()

    def create(self, project: Project, workflow: Workflow) -> str:
        tools: dict[str, Any] = {}
        for node in workflow.nodes:
            definition = self.tools.get(node.tool_id)
            metadata = definition.metadata()
            metadata["implementation_sha256"] = self._implementation_hash(definition)
            tools[node.tool_id] = metadata
        snapshot = {
            "project": project.model_dump(mode="json"), "workflow": workflow.model_dump(mode="json"),
            "tools": tools, "environment": self._environment(),
        }
        self._verify_files(snapshot["project"]["files"])
        return self.store.create_run(snapshot)

    def run(self, run_id: str, *, retry_failed: bool = False) -> dict[str, Any]:
        owner = str(uuid4())
        run = self.store.run(run_id)
        workflow = Workflow.model_validate(run["snapshot"]["workflow"])
        self.verify_snapshot(run)
        self.store.claim(run_id, owner, (datetime.now(timezone.utc) - timedelta(seconds=20)).isoformat())
        stop = Event()
        heartbeat = Thread(target=self._heartbeat, args=(run_id, owner, stop), daemon=True)
        heartbeat.start()
        final = RunStatus.failed
        try:
            for record in self.store.run(run_id)["nodes"]:
                if record["status"] not in {NodeStatus.interrupted.value, NodeStatus.failed.value}:
                    continue
                if record["status"] == NodeStatus.failed.value and not retry_failed:
                    continue
                node = next(node for node in workflow.nodes if node.id == (record["parent_id"] or record["id"]))
                if self.tools.get(node.tool_id).idempotent:
                    self.store.set_node(run_id, record["id"], NodeStatus.pending)
                else:
                    self.store.set_node(run_id, record["id"], NodeStatus.blocked, error={"code": "reconciliation_required", "message": "Interrupted non-idempotent call needs external-job reconciliation before retry."})

            final = self._execute(run_id, workflow, run["snapshot"]["project"])
        except Exception as exc:
            self.store.event(run_id, "executor_error", {"type": type(exc).__name__, "message": str(exc)})
            raise
        finally:
            stop.set()
            heartbeat.join(timeout=2)
            self.store.finish(run_id, owner, final)
        return self.store.run(run_id)

    def _heartbeat(self, run_id: str, owner: str, stop: Event) -> None:
        while not stop.wait(2):
            if not self.store.heartbeat(run_id, owner):
                return

    @staticmethod
    def _implementation_hash(definition: Any) -> str | None:
        source = inspect.getsourcefile(definition.handler)
        paths = ((Path(source),) if source else ()) + definition.implementation_files
        if not paths:
            return None
        return sha256(b"\0".join(path.read_bytes() for path in paths)).hexdigest()

    @staticmethod
    def _environment() -> dict[str, Any]:
        return {"python": platform.python_version(), "platform": platform.platform(), "packages": {name: version(name) for name in ("numpy", "scipy", "pydantic", "biopython", "jsonschema")}}

    @staticmethod
    def _verify_files(files: list[dict[str, str]]) -> None:
        for file in files:
            path = Path(file["path"])
            if not path.is_file() or sha256(path.read_bytes()).hexdigest() != file["sha256"]:
                raise ValueError(f"input_artifact_hash_mismatch:{file['name']}")

    def verify_snapshot(self, run: dict[str, Any]) -> None:
        if sha256(canonical(run["snapshot"]).encode()).hexdigest() != run["snapshot_hash"]:
            raise ValueError("run_snapshot_hash_mismatch")
        self._verify_files(run["snapshot"]["project"]["files"])
        if run["snapshot"]["environment"] != self._environment():
            raise ValueError("environment_changed_since_snapshot; clone the run")
        for artifact in run["artifacts"]:
            path = Path(artifact["path"])
            if not path.is_file() or sha256(path.read_bytes()).hexdigest() != artifact["hash"]:
                raise ValueError("output_artifact_hash_mismatch")
        for tool_id, expected in run["snapshot"]["tools"].items():
            current = self.tools.get(tool_id)
            digest = self._implementation_hash(current)
            if current.version != expected["version"] or current.plugin_hash != expected["plugin_hash"] or digest != expected["implementation_sha256"]:
                raise ValueError(f"tool_changed_since_snapshot:{tool_id}; clone the run with the new tool version")

    def _execute(self, run_id: str, workflow: Workflow, project: dict[str, Any]) -> RunStatus:
        active: dict[Future[None], tuple[str, str]] = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            while True:
                run = self.store.run(run_id)
                records = {record["id"]: record for record in run["nodes"]}
                control = run["control"]
                if not control:
                    for node in workflow.nodes:
                        record = records[node.id]
                        if record["status"] != NodeStatus.pending.value:
                            continue
                        dependencies = [records[key] for key in node.dependencies()]
                        if any(item["status"] in {NodeStatus.failed.value, NodeStatus.blocked.value} for item in dependencies):
                            # Leave dependency-blocked nodes pending so upstream retry can unlock them.
                            continue
                        if any(item["status"] != NodeStatus.succeeded.value for item in dependencies):
                            continue
                        try:
                            inputs = {key: self._resolve(value, project, records) for key, value in node.inputs.items()}
                            if node.map:
                                items = self._resolve(node.map.items, project, records)
                                if not isinstance(items, list):
                                    raise ToolFailure("map_requires_array", node.id)
                                if record["inputs"] is None:
                                    self.store.expand(run_id, node.id, [{**inputs, node.map.item_argument: item} for item in items])
                                shards = [item for item in self.store.run(run_id)["nodes"] if item["parent_id"] == node.id]
                                if all(item["status"] == NodeStatus.succeeded.value for item in shards):
                                    # SQLite insertion order keeps gather aligned with input order.
                                    self._complete(run_id, node.id, {"items": [item["output"] for item in shards]}, sorted(node.dependencies()))
                                    continue
                                if any(item["status"] in {NodeStatus.failed.value, NodeStatus.blocked.value} for item in shards):
                                    continue
                                jobs = [(item["id"], item["inputs"]) for item in shards if item["status"] == NodeStatus.pending.value]
                            else:
                                jobs = [(node.id, inputs)]
                            tool = self.tools.get(node.tool_id)
                            for node_id, arguments in jobs:
                                if len(active) >= self.max_workers:
                                    break
                                if tool.resource == "gpu" and any(resource == "gpu" for _, resource in active.values()):
                                    break
                                if any(key == node_id for key, _ in active.values()):
                                    continue
                                # Persist resolved inputs BEFORE dispatch, including each map shard.
                                self.store.set_node(run_id, node_id, NodeStatus.running, inputs=arguments, increment=True)
                                future = pool.submit(self._invoke, run_id, node_id, node.tool_id, arguments, sorted(node.dependencies()))
                                active[future] = (node_id, tool.resource)
                        except (KeyError, IndexError, TypeError, ValidationError, ToolFailure) as exc:
                            self.store.set_node(run_id, node.id, NodeStatus.failed, error={"code": getattr(exc, "code", "invalid_binding"), "message": str(exc)})
                if active:
                    done, _ = wait(active, timeout=0.25, return_when=FIRST_COMPLETED)
                    for future in done:
                        future.result()
                        del active[future]
                    continue
                latest = self.store.run(run_id)
                if latest["control"]:
                    return RunStatus.paused if latest["control"] == "pause" else RunStatus.cancelled
                parents = [record for record in latest["nodes"] if record["parent_id"] is None]
                if all(record["status"] == NodeStatus.succeeded.value for record in parents):
                    return RunStatus.succeeded
                # A completed map can unlock its downstream join on the next pass.
                if any(records[record["id"]]["status"] != record["status"] for record in parents):
                    continue
                return RunStatus.failed

    @staticmethod
    def _resolve(value: InputValue, project: dict[str, Any], records: dict[str, Any]) -> Any:
        if isinstance(value, LiteralInput):
            return deepcopy(value.value)
        if isinstance(value, ProjectInput):
            return deepcopy(read_path(project, value.path))
        if isinstance(value, NodeInput):
            return deepcopy(read_path(records[value.node_id]["output"], value.path))
        raise TypeError("unknown_input_binding")

    def _invoke(self, run_id: str, node_id: str, tool_id: str, arguments: dict[str, Any], upstream: list[str]) -> None:
        try:
            definition = self.tools.get(tool_id)
            # Hash the node identifier for a filesystem-safe name, including map shards.
            attempt = next(node["attempts"] for node in self.store.run(run_id)["nodes"] if node["id"] == node_id)
            work_dir = self.artifact_root / run_id / sha256(node_id.encode()).hexdigest()[:16] / f"attempt-{attempt}"
            work_dir.mkdir(parents=True, exist_ok=True)
            payload = definition.input_model.model_validate(arguments)
            with self._gpu_lock if definition.resource == "gpu" else nullcontext():
                result = definition.handler(payload, NodeContext(run_id, node_id, work_dir))
            if not isinstance(result, dict):
                raise ToolFailure("invalid_tool_output", "Tool output must be a JSON object")
            jsonschema.Draft202012Validator(definition.output_schema).validate(result)
            self._complete(run_id, node_id, result, upstream)
        except ToolFailure as exc:
            self.store.set_node(run_id, node_id, NodeStatus.failed, error={"code": exc.code, "message": str(exc), "retryable": exc.retryable})
        except Exception as exc:
            self.store.set_node(run_id, node_id, NodeStatus.failed, error={"code": type(exc).__name__, "message": str(exc), "retryable": False})

    def _complete(self, run_id: str, node_id: str, output: dict[str, Any], upstream: list[str]) -> None:
        attempt = next(node["attempts"] for node in self.store.run(run_id)["nodes"] if node["id"] == node_id)
        directory = self.artifact_root / run_id / sha256(node_id.encode()).hexdigest()[:16] / f"attempt-{attempt}"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "result.json"
        temporary = directory / "result.json.tmp"
        temporary.write_text(canonical(output), encoding="utf-8")
        temporary.replace(path)
        self.store.complete_node(run_id, node_id, output, path, upstream)

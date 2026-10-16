from __future__ import annotations

from concurrent.futures import Future, wait, FIRST_COMPLETED
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
from time import time
from typing import Any
from uuid import uuid4

from pydantic import ValidationError
import jsonschema

from .models import InputValue, LiteralInput, NodeInput, NodeStatus, Project, ProjectInput, RunStatus, Workflow, read_path, SequenceRef
from .store import WorkflowStore, canonical, file_sha256
from .tools import NodeContext, ToolFailure, ToolDeferred, WorkflowTools


class WorkflowEngine:
    """Execute an immutable DAG with durable map shards and bounded concurrency."""

    def __init__(self, store: WorkflowStore, tools: WorkflowTools, artifact_root: Path, *, max_workers: int = 4) -> None:
        if max_workers < 1:
            raise ValueError("max_workers_must_be_positive")
        self.store, self.tools = store, tools
        self.artifact_root = artifact_root.resolve()
        self.max_workers = max_workers
        self._gpu_lock = Lock()
        from .disclosure import DisclosureBoundary
        self.disclosure = DisclosureBoundary(store)
        from .scheduler import TaskBudget
        self.budget = TaskBudget(max_workers)

    def snapshot(self, project: Project, workflow: Workflow) -> dict[str, Any]:
        from .scientific_project import validate_stage_bindings
        validate_stage_bindings(workflow)
        tools: dict[str, Any] = {}
        source_bytes: dict[Path, bytes] = {}
        source_hashes: dict[tuple[Path, ...], str] = {}
        for node in workflow.nodes:
            definition = self.tools.get(node.tool_id)
            metadata = definition.metadata()
            metadata["implementation_sha256"] = self._implementation_hash(definition, source_bytes, source_hashes)
            tools[node.tool_id] = metadata
        snapshot = {
            "project": project.model_dump(mode="json"), "workflow": workflow.model_dump(mode="json"),
            "tools": tools, "environment": self._environment(),
        }
        if project.runtime_profile_ref:
            from .runtime_profiles import RuntimeProfiles
            identity, runtime_tools = RuntimeProfiles(self.store).get(project.runtime_profile_ref)
            snapshot["runtime_profile"] = identity
            self.disclosure.register_runtime(runtime_tools)
        verified = {}
        self._verify_files(snapshot["project"]["files"],verified)
        self._verify_scientific_project(snapshot["project"],verified)
        return snapshot

    def create(self, project: Project, workflow: Workflow) -> str:
        return self.store.create_run(self.snapshot(project, workflow))

    def create_confirmed(self, binding, workflow: Workflow, request_id: str | None = None, authorize=None) -> str:
        return self.store.create_confirmed_run(binding, workflow, lambda project: self.snapshot(project, workflow), request_id, authorize)

    def review_identity(self, project: Project, workflow: Workflow) -> dict[str, Any]:
        cache: dict[Path, bytes] = {}
        hashes: dict[tuple[Path, ...], str] = {}
        tools = {node.tool_id: self.tools.get(node.tool_id) for node in workflow.nodes}
        profile_hash = None
        if project.runtime_profile_ref:
            from .runtime_profiles import RuntimeProfiles
            identity, private = RuntimeProfiles(self.store).get(project.runtime_profile_ref)
            self.disclosure.register_runtime(private)
            profile_hash = identity["hash"]
        return {"tools": {key: {"version":tool.version,"runtime":tool.runtime,"plugin_hash":tool.plugin_hash,
            "implementation_sha256":self._implementation_hash(tool,cache,hashes)} for key,tool in tools.items()},
            "runtime_profile_sha256":profile_hash,"environment":self._environment()}

    @staticmethod
    def snapshot_review_identity(snapshot) -> dict[str, Any]:
        return {"tools":{key:{field:value[field] for field in ("version","runtime","plugin_hash","implementation_sha256")}
            for key,value in snapshot["tools"].items()},"runtime_profile_sha256":snapshot.get("runtime_profile",{}).get("hash"),
            "environment":snapshot["environment"]}

    def run(self, run_id: str, *, retry_failed: bool = False, retry_node_id: str | None = None) -> dict[str, Any]:
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
                if retry_node_id and (record["parent_id"] or record["id"]) != retry_node_id:
                    continue
                node = next(node for node in workflow.nodes if node.id == (record["parent_id"] or record["id"]))
                definition = self.tools.get(node.tool_id)
                node_dir = self.artifact_root / run_id / sha256(record["id"].encode()).hexdigest()[:16]
                if definition.idempotent or definition.reconcile is not None and definition.reconcile(node_dir):
                    self.store.set_node(run_id, record["id"], NodeStatus.pending)
                else:
                    self.store.set_node(run_id, record["id"], NodeStatus.blocked, error={"code": "reconciliation_required", "message": "Interrupted non-idempotent call needs external-job reconciliation before retry."})

            final = self._execute(run_id, workflow, run["snapshot"])
        except Exception as exc:
            self.store.event(run_id, "executor_error", self.disclosure.diagnostic(exc))
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
    def _implementation_hash(definition: Any, cache: dict[Path, bytes] | None = None,
                             hashes: dict[tuple[Path, ...], str] | None = None) -> str | None:
        source = inspect.getsourcefile(definition.handler)
        paths = ((Path(source),) if source else ()) + definition.implementation_files
        if not paths:
            return None
        if hashes is not None and paths in hashes:
            return hashes[paths]
        cache = {} if cache is None else cache
        for path in paths:
            if path not in cache: cache[path] = path.read_bytes()
        digest = sha256(b"\0".join(cache[path] for path in paths)).hexdigest()
        if hashes is not None:
            hashes[paths] = digest
        return digest

    @staticmethod
    def _environment() -> dict[str, Any]:
        return {"python": platform.python_version(), "platform": platform.platform(), "packages": {name: version(name) for name in ("numpy", "scipy", "pydantic", "biopython", "jsonschema")}}

    @staticmethod
    def _verify_files(files: list[dict[str, str]], verified=None) -> None:
        for file in files:
            path = Path(file["path"])
            if not path.is_file() or file_sha256(path,verified) != file["sha256"]:
                raise ValueError(f"input_artifact_hash_mismatch:{file['name']}")

    def verify_snapshot(self, run: dict[str, Any], *, execution_identity: bool = True) -> None:
        if sha256(canonical(run["snapshot"]).encode()).hexdigest() != run["snapshot_hash"]:
            raise ValueError("run_snapshot_hash_mismatch")
        verified = {}
        self._verify_files(run["snapshot"]["project"]["files"],verified)
        self._verify_scientific_project(run["snapshot"]["project"],verified)
        for artifact in run["artifacts"]:
            path = Path(artifact["path"])
            if not path.is_file() or file_sha256(path,verified) != artifact["hash"]:
                raise ValueError("output_artifact_hash_mismatch")
        if not execution_identity:
            # Input-only iteration does not execute/reuse the old tools. A new
            # plan must bind the current environment and tool identities.
            return
        if run["snapshot"].get("runtime_profile"):
            from .runtime_profiles import RuntimeProfiles
            identity, _ = RuntimeProfiles(self.store).get(run["snapshot"]["runtime_profile"]["id"])
            if identity != run["snapshot"]["runtime_profile"]:
                raise ValueError("runtime_profile_changed_clone_required")
        if run["snapshot"]["environment"] != self._environment():
            raise ValueError("environment_changed_since_snapshot; clone the run")
        source_bytes: dict[Path, bytes] = {}
        source_hashes: dict[tuple[Path, ...], str] = {}
        for tool_id, expected in run["snapshot"]["tools"].items():
            current = self.tools.get(tool_id)
            digest = self._implementation_hash(current, source_bytes, source_hashes)
            if current.version != expected["version"] or current.plugin_hash != expected["plugin_hash"] or digest != expected["implementation_sha256"]:
                raise ValueError(f"tool_changed_since_snapshot:{tool_id}; clone the run with the new tool version")

    @staticmethod
    def _verify_scientific_project(project, verified=None):
        if project.get("scientific_project") is not None:
            from .scientific_project import ScientificProject
            ScientificProject.model_validate(project["scientific_project"]).verify(verified)

    def _execute(self, run_id: str, workflow: Workflow, snapshot: dict[str, Any]) -> RunStatus:
        project = snapshot["project"]
        policy = workflow.execution_policy
        allowed = workflow.required_nodes(policy.target_node_id)
        initial = self.store.execution_state(run_id)
        completed_before = {item["id"] for item in initial["nodes"] if item["parent_id"] is None and item["status"] == "succeeded"}
        active: dict[Future[None], tuple[str, str]] = {}
        try:
            while True:
                waiting_budget = False
                run = self.store.execution_state(run_id)
                records = {record["id"]: record for record in run["nodes"]}
                for artifact in run["artifacts"]:
                    records[artifact["node_id"]]["result_identity"] = {"artifact_id":artifact["id"],"sha256":artifact["hash"]}
                control = run["control"]
                completed = {key for key,item in records.items() if item["parent_id"] is None and item["status"] == "succeeded"}
                if not control and policy.max_completed_stages and len(completed - completed_before) >= policy.max_completed_stages:
                    self.store.control(run_id,"pause")
                    self.store.event(run_id,"execution_range_completed",{"reason":"stage_limit"})
                    control = "pause"
                if not control and policy.stop_after_seconds and (datetime.now(timezone.utc) - datetime.fromisoformat(run["created_at"])).total_seconds() >= policy.stop_after_seconds:
                    self.store.control(run_id,"pause")
                    self.store.event(run_id,"execution_budget_exhausted",{"reason":"dispatch_deadline"})
                    control = "pause"
                if not control:
                    for node in workflow.nodes:
                        if node.id not in allowed: continue
                        record = records[node.id]
                        if record["status"] not in {NodeStatus.pending.value,NodeStatus.waiting.value}:
                            continue
                        if record["status"] == "waiting" and record["poll_after"] > time():
                            continue
                        dependencies = [records[key] for key in node.dependencies()]
                        if any(item["status"] in {NodeStatus.failed.value, NodeStatus.blocked.value} for item in dependencies):
                            # Leave dependency-blocked nodes pending so upstream retry can unlock them.
                            continue
                        if any(item["status"] != NodeStatus.succeeded.value for item in dependencies):
                            continue
                        # Single-stage mode never dispatches a second independent
                        # parent concurrently and then labels it a single step.
                        if policy.max_completed_stages and len(completed - completed_before) + len({key.split('[')[0] for key,_ in active.values()}) >= policy.max_completed_stages:
                            break
                        if node.id in policy.checkpoints_before and self.store.checkpoint(run_id,node.id,"before"):
                            control = "pause"
                            break
                        try:
                            inputs = {key: self._resolve(value, project, records, run_id) for key, value in node.inputs.items()}
                            if node.map:
                                items = self._resolve(node.map.items, project, records, run_id)
                                if not isinstance(items, list):
                                    raise ToolFailure("map_requires_array", node.id)
                                if record["inputs"] is None:
                                    self.store.expand(run_id, node.id, [{**inputs, node.map.item_argument: item} for item in items])
                                shards = [item for item in self.store.execution_state(run_id)["nodes"] if item["parent_id"] == node.id]
                                if all(item["status"] == NodeStatus.succeeded.value for item in shards):
                                    # SQLite insertion order keeps gather aligned with input order.
                                    self._complete(run_id, node.id, {"items": [self.store.node_output(run_id,item["id"]) for item in shards]}, sorted(node.dependencies()))
                                    if node.id in policy.checkpoints_after:
                                        self.store.checkpoint(run_id,node.id,"after")
                                        control = "pause"
                                        break
                                    if policy.max_completed_stages and len(completed - completed_before) + 1 >= policy.max_completed_stages:
                                        self.store.control(run_id,"pause")
                                        control = "pause"
                                        break
                                    continue
                                if any(item["status"] in {NodeStatus.failed.value, NodeStatus.blocked.value} for item in shards):
                                    continue
                                jobs = [(item["id"], item["inputs"]) for item in shards if item["status"] == NodeStatus.pending.value
                                    or item["status"] == "waiting" and item["poll_after"] <= time()]
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
                                polling = records.get(node_id,record)["status"] == "waiting"
                                if not polling and sum(item["attempts"] for item in records.values()) >= policy.max_tool_calls:
                                    self.store.control(run_id,"pause")
                                    self.store.event(run_id,"execution_budget_exhausted",{"reason":"tool_calls"})
                                    control = "pause"
                                    break
                                if not self.budget.reserve():
                                    waiting_budget = True
                                    break
                                # Persist resolved inputs BEFORE dispatch, including each map shard.
                                persisted = dict(arguments)
                                if node.tool_id in {"project.m1","project.m2","project.m3","project.m4","project.m5"}:
                                    persisted["project"] = {"snapshot_project_sha256":sha256(canonical(project).encode()).hexdigest()}
                                try:
                                    self.store.set_node(run_id, node_id, NodeStatus.queued, inputs=persisted, increment=not polling)
                                    future = self.budget.submit(self._invoke, run_id, node_id, node.tool_id, arguments, sorted(node.dependencies()), snapshot)
                                except Exception:
                                    self.budget.release_reservation()
                                    raise
                                records[node_id] = {**records.get(node_id,record),"status":"queued","attempts":records.get(node_id,record)["attempts"]+int(not polling)}
                                active[future] = (node_id, tool.resource)
                            if control: break
                        except (KeyError, IndexError, TypeError, ValidationError, ToolFailure) as exc:
                            self.store.set_node(run_id, node.id, NodeStatus.failed, error=self.disclosure.diagnostic(exc, code=getattr(exc, "code", "invalid_binding")))
                if active:
                    done, _ = wait(active, timeout=0.25, return_when=FIRST_COMPLETED)
                    for future in done:
                        future.result()
                        node_id, _ = active[future]
                        if node_id in policy.checkpoints_after and self.store.execution_state(run_id)["control"] != "cancel":
                            finished = next(item for item in self.store.execution_state(run_id)["nodes"] if item["id"] == node_id)
                            if finished["status"] == "succeeded": self.store.checkpoint(run_id,node_id,"after")
                        del active[future]
                    continue
                latest = self.store.execution_state(run_id)
                parents = [record for record in latest["nodes"] if record["parent_id"] is None]
                if all(record["status"] == NodeStatus.succeeded.value for record in parents):
                    return RunStatus.succeeded
                if latest["control"]:
                    return RunStatus.paused if latest["control"] == "pause" else RunStatus.cancelled
                if all(record["status"] == "succeeded" for record in parents if record["id"] in allowed):
                    self.store.control(run_id,"pause")
                    self.store.event(run_id,"execution_range_completed",{"reason":"target_node"})
                    return RunStatus.paused
                if waiting_budget:
                    self.budget.wait_for_capacity(timeout=0.25)
                    continue
                remote_waits = [item["poll_after"] for item in latest["nodes"] if item["status"] == "waiting"]
                if remote_waits:
                    self.store.wait_for_change(timeout=max(0,min(2,min(remote_waits)-time())))
                    continue
                # A completed map can unlock its downstream join on the next pass.
                if any(records[record["id"]]["status"] != record["status"] for record in parents):
                    continue
                return RunStatus.failed
        finally:
            if active:
                self.store.control(run_id,"cancel")
                wait(active)

    def _resolve(self, value: InputValue, project: dict[str, Any], records: dict[str, Any], run_id: str) -> Any:
        if isinstance(value, LiteralInput):
            return deepcopy(value.value)
        if isinstance(value, ProjectInput):
            return deepcopy(read_path(project, value.path))
        if isinstance(value, SequenceRef):
            from .sequence_index import resolve_sequence_ref
            return resolve_sequence_ref(value, project, self.store)
        if isinstance(value, NodeInput):
            if value.path == ["result_identity"]:
                return deepcopy(records[value.node_id]["result_identity"])
            return deepcopy(read_path(self.store.node_output(run_id,value.node_id), value.path))
        raise TypeError("unknown_input_binding")

    def _invoke(self, run_id: str, node_id: str, tool_id: str, arguments: dict[str, Any], upstream: list[str], snapshot: dict[str, Any]) -> None:
        try:
            control = self.store.execution_state(run_id)["control"]
            if control:
                record=next(item for item in self.store.execution_state(run_id)["nodes"] if item["id"]==node_id)
                self.store.set_node(run_id,node_id,NodeStatus.waiting if record["poll_after"] is not None else NodeStatus.pending)
                return
            self.store.set_node(run_id,node_id,NodeStatus.running)
            definition = self.tools.get(tool_id)
            # Hash the node identifier for a filesystem-safe name, including map shards.
            attempt = next(node["attempts"] for node in self.store.execution_state(run_id)["nodes"] if node["id"] == node_id)
            work_dir = self.artifact_root / run_id / sha256(node_id.encode()).hexdigest()[:16] / f"attempt-{attempt}"
            work_dir.mkdir(parents=True, exist_ok=True)
            arguments = self.disclosure.materialize(arguments,snapshot["project"]["id"])
            payload = definition.input_model.model_validate(arguments)
            runtime_tools = {}
            if snapshot.get("runtime_profile"):
                from .runtime_profiles import RuntimeProfiles
                _, runtime_tools = RuntimeProfiles(self.store).get(snapshot["runtime_profile"]["id"])
            upstream_results = self.store.verified_upstream(run_id,upstream) if definition.capability == "scientific_project" else ()
            science_hash = None
            if snapshot["project"].get("scientific_project"):
                from .scientific_project import ScientificProject
                science_hash = sha256(canonical(ScientificProject.model_validate(snapshot["project"]["scientific_project"]).model_dump(mode="json")).encode()).hexdigest()
            with self._gpu_lock if definition.resource == "gpu" else nullcontext():
                result = definition.handler(payload, NodeContext(run_id=run_id,node_id=node_id,work_dir=work_dir,runtime_tools=runtime_tools,
                    upstream_results=upstream_results,scientific_project_sha256=science_hash,project_id=snapshot["project"]["id"],
                    snapshot_sha256=sha256(canonical(snapshot).encode()).hexdigest()))
            if not isinstance(result, dict):
                raise ToolFailure("invalid_tool_output", "Tool output must be a JSON object")
            jsonschema.Draft202012Validator(definition.output_schema).validate(result)
            public_result = self.disclosure.tree(result, project_id=snapshot["project"]["id"]) if definition.capability in {"scientific_project","scientific_mcp","synthetic_demonstration"} else result
            self.disclosure.check(public_result)
            if self.store.execution_state(run_id)["control"] == "cancel":
                self.store.set_node(run_id,node_id,NodeStatus.interrupted,error={"code":"cancelled_before_publication","message":"已取消；结果未发布。"})
                return
            self._complete(run_id, node_id, result, upstream)
        except ToolDeferred as deferred:
            self.store.defer_node(run_id,node_id,deferred.job_id,deferred.poll_after_seconds)
        except ToolFailure as exc:
            self.store.set_node(run_id, node_id, NodeStatus.failed, error={**self.disclosure.diagnostic(exc, code=exc.code), "retryable": exc.retryable})
        except Exception as exc:
            self.store.set_node(run_id, node_id, NodeStatus.failed, error={**self.disclosure.diagnostic(exc, code=getattr(exc, "code", "tool_execution_failed")), "retryable": False})

    def _complete(self, run_id: str, node_id: str, output: dict[str, Any], upstream: list[str]) -> None:
        attempt = next(node["attempts"] for node in self.store.execution_state(run_id)["nodes"] if node["id"] == node_id)
        directory = self.artifact_root / run_id / sha256(node_id.encode()).hexdigest()[:16] / f"attempt-{attempt}"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "result.json"
        temporary = directory / "result.json.tmp"
        temporary.write_text(canonical(output), encoding="utf-8")
        temporary.replace(path)
        self.store.complete_node(run_id, node_id, output, path, upstream)

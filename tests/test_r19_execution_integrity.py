"""Software-only attempt binding, streaming verification and scheduler oracles."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from threading import Event

import pytest

from igem_drylab.workflow.models import NodeStatus, Project, WorkflowError
from igem_drylab.workflow.scheduler import TaskBudget
from igem_drylab.workflow.scientific_project import EvidenceFile
from igem_drylab.workflow.store import file_sha256
from test_workbench_execution import engine, graph


def test_only_current_attempt_committed_artifact_can_supply_a_predecessor(tmp_path):
    runtime = engine(tmp_path, lambda value, context: {"kind": "software_fixture"})
    run_id = runtime.create(Project(id="p", name="fixture"), graph(1))
    runtime.run(run_id)
    first = runtime.store.verified_upstream(run_id, ["n0"])[0]
    runtime.store.set_node(run_id, "n0", NodeStatus.running, inputs={"revision": 2}, increment=True)
    assert runtime.store.execution_state(run_id)["artifacts"] == []
    with pytest.raises(WorkflowError, match="upstream_result_not_successful"):
        runtime.store.verified_upstream(run_id, ["n0"])
    path = tmp_path / "second-attempt.json"
    path.write_text('{"kind":"second_software_fixture"}')
    runtime.store.complete_node(run_id, "n0", {"kind": "second_software_fixture"}, path, [])
    current = runtime.store.verified_upstream(run_id, ["n0"])[0]
    assert current["artifact_id"] != first["artifact_id"]
    assert current["output"]["kind"] == "second_software_fixture"
    assert len(runtime.store.run(run_id)["artifacts"]) == 2  # Keep audit history.
    assert runtime.store.execution_state(run_id)["artifacts"][0]["id"] == current["artifact_id"]
    runtime.store.set_node(run_id, "n0", NodeStatus.succeeded, inputs={"revision": 3})
    with pytest.raises(WorkflowError, match="upstream_result_inputs_mismatch"):
        runtime.store.verified_upstream(run_id, ["n0"])


def test_streamed_digest_is_shared_only_inside_one_verification_boundary(tmp_path, monkeypatch):
    path = tmp_path / "input.bin"
    raw = b"software fixture" * 100_000
    path.write_bytes(raw)
    expected = sha256(raw).hexdigest()
    from pathlib import Path
    original = Path.open
    reads = []
    def counted(self, *args, **kwargs):
        if self.resolve() == path.resolve() and args and args[0] == "rb":
            reads.append(self)
        return original(self, *args, **kwargs)
    monkeypatch.setattr(Path, "open", counted)
    boundary = {}
    assert file_sha256(path, boundary) == expected
    EvidenceFile(path=path, sha256=expected).verify(boundary)
    assert len(reads) == 1
    path.write_bytes(b"changed input")
    with pytest.raises(ValueError, match="artifact_hash_mismatch"):
        EvidenceFile(path=path, sha256=expected).verify({})
    assert len(reads) == 2


def test_capacity_wait_wakes_on_release_without_spin_polling():
    budget = TaskBudget(max_workers=1, max_pending=1)
    started = Event()
    assert budget.reserve()
    assert not budget.reserve()
    def wait():
        started.set()
        return budget.wait_for_capacity(timeout=2)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(wait)
        assert started.wait(1)
        budget.release_reservation()
        assert future.result(timeout=2)
    assert budget.state()["queued_tasks"] == 0
    assert budget.reserve()
    budget.release_reservation()


def test_existing_project_projection_takes_no_writer_lock_and_no_repeat_hash(tmp_path,monkeypatch):
    from test_r19_sequence_refs import attached
    from test_r6_input_boundaries import api
    from contextlib import contextmanager
    app,client=api(tmp_path)
    attached(client)
    store=app.state.platform_store
    original=store.connection
    statements=[]
    @contextmanager
    def traced():
        with original() as db:
            db.set_trace_callback(statements.append)
            yield db
    monkeypatch.setattr(store,"connection",traced)
    assert client.get("/api/platform/projects/p").status_code==200
    assert client.get("/api/platform/projects/p").status_code==200
    assert not any(s.upper().startswith(("BEGIN IMMEDIATE","INSERT","UPDATE","DELETE")) for s in statements)

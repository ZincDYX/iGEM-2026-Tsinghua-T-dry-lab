from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from threading import Barrier

import pytest

from igem_drylab.workflow.builtins import builtin_tools, recommend
from igem_drylab.workflow.engine import WorkflowEngine
from igem_drylab.workflow.models import Contract, LiteralInput, MapSpec, NodeInput, NodeStatus, Project, ProjectInput, SequenceRecord, Workflow, WorkflowNode
from igem_drylab.workflow.pathway import Pathway, solve_pathway
from igem_drylab.workflow.plugins import PluginManager
from igem_drylab.workflow.store import WorkflowStore
from igem_drylab.workflow.tools import NodeContext, ToolDefinition, ToolFailure, WorkflowTools


class NumberInput(Contract):
    item: int


def number_tool(payload: NumberInput, context: NodeContext) -> dict[str, object]:
    return {"value": payload.item * 2}


def number_registry(handler=number_tool, *, idempotent=True) -> WorkflowTools:
    tools = WorkflowTools()
    tools.register(ToolDefinition("number", "number", "test", "1", NumberInput, handler, "test", idempotent=idempotent))
    return tools


def test_real_concurrent_fork_join_and_dynamic_map(tmp_path: Path) -> None:
    barrier = Barrier(2)

    def concurrent(payload: NumberInput, context: NodeContext) -> dict[str, object]:
        barrier.wait(timeout=5)  # A serial executor fails this test.
        return number_tool(payload, context)

    store = WorkflowStore(tmp_path / "runs.sqlite")
    tools = number_registry(concurrent)
    workflow = Workflow(id="map", name="map", nodes=[
        WorkflowNode(id="fanout", label="map", tool_id="number", map=MapSpec(items=LiteralInput(value=[3, 1]))),
    ])
    engine = WorkflowEngine(store, tools, tmp_path / "artifacts", max_workers=2)
    result = engine.run(engine.create(Project(id="p", name="p"), workflow))

    assert result["status"] == "succeeded"
    assert result["nodes"][0]["output"] == {"items": [{"value": 6}, {"value": 2}]}
    assert len(result["artifacts"]) == 3


def test_static_fanout_fanin_resolves_explicit_inputs(tmp_path: Path) -> None:
    tools = builtin_tools()
    tools.register(ToolDefinition("number", "number", "test", "1", NumberInput, number_tool, "test"))
    workflow = Workflow(id="fork", name="fork", nodes=[
        WorkflowNode(id="left", label="left", tool_id="number", inputs={"item": LiteralInput(value=2)}),
        WorkflowNode(id="right", label="right", tool_id="number", inputs={"item": LiteralInput(value=3)}),
        WorkflowNode(id="join", label="join", tool_id="number", depends_on=["right"], inputs={"item": NodeInput(node_id="left", path=["value"])}),
    ])
    store = WorkflowStore(tmp_path / "runs.sqlite")
    engine = WorkflowEngine(store, tools, tmp_path / "artifacts")
    result = engine.run(engine.create(Project(id="p", name="p"), workflow))
    assert result["status"] == "succeeded"
    assert result["nodes"][-1]["output"]["value"] == 8
    assert result["artifacts"][-1]["upstream"] == ["left", "right"]


def test_failed_map_retry_reuses_completed_shards_and_snapshot(tmp_path: Path) -> None:
    calls: list[int] = []
    failed_once = False

    def flaky(payload: NumberInput, context: NodeContext) -> dict[str, object]:
        nonlocal failed_once
        calls.append(payload.item)
        if payload.item == 2 and not failed_once:
            failed_once = True
            raise ToolFailure("timeout", "localized error text", retryable=True)
        return number_tool(payload, context)

    store = WorkflowStore(tmp_path / "runs.sqlite")
    tools = number_registry(flaky)
    engine = WorkflowEngine(store, tools, tmp_path / "artifacts", max_workers=1)
    project = store.save_project(Project(id="p", name="p", conditions={"items": [1, 2]}))
    workflow = Workflow(id="map", name="map", nodes=[WorkflowNode(id="map", label="map", tool_id="number", map=MapSpec(items=ProjectInput(path=["conditions", "items"])) )])
    run_id = engine.create(project, workflow)
    assert engine.run(run_id)["status"] == "failed"
    store.save_project(project.model_copy(update={"conditions": {"items": [99]}}), expected_revision=project.revision)
    resumed = WorkflowEngine(WorkflowStore(store.path), tools, tmp_path / "artifacts", max_workers=1).run(run_id, retry_failed=True)
    assert resumed["status"] == "succeeded"
    assert calls == [1, 2, 2]
    assert resumed["snapshot"]["project"]["conditions"]["items"] == [1, 2]


def test_non_idempotent_interrupted_node_requires_reconciliation(tmp_path: Path) -> None:
    store = WorkflowStore(tmp_path / "runs.sqlite")
    engine = WorkflowEngine(store, number_registry(idempotent=False), tmp_path / "artifacts")
    workflow = Workflow(id="single", name="single", nodes=[WorkflowNode(id="n", label="n", tool_id="number", inputs={"item": LiteralInput(value=1)})])
    run_id = engine.create(Project(id="p", name="p"), workflow)
    store.set_node(run_id, "n", NodeStatus.running, inputs={"item": 1}, increment=True)
    result = engine.run(run_id)
    assert result["nodes"][0]["status"] == "blocked"
    assert result["nodes"][0]["error"]["code"] == "reconciliation_required"


def test_worker_lease_rejects_duplicate_execution(tmp_path: Path) -> None:
    store = WorkflowStore(tmp_path / "runs.sqlite")
    engine = WorkflowEngine(store, number_registry(), tmp_path / "artifacts")
    workflow = Workflow(id="single", name="single", nodes=[WorkflowNode(id="n", label="n", tool_id="number", inputs={"item": LiteralInput(value=1)})])
    run_id = engine.create(Project(id="p", name="p"), workflow)
    store.claim(run_id, "active-worker", "2000-01-01")
    with pytest.raises(ValueError, match="active_worker"):
        engine.run(run_id)


def test_graph_rejects_cycle_in_result_bindings() -> None:
    with pytest.raises(ValueError, match="cycle"):
        Workflow(id="cycle", name="cycle", nodes=[
            WorkflowNode(id="a", label="a", tool_id="number", inputs={"item": NodeInput(node_id="b")}),
            WorkflowNode(id="b", label="b", tool_id="number", inputs={"item": NodeInput(node_id="a")}),
        ])


def test_plugin_runs_in_real_separate_environment(tmp_path: Path) -> None:
    tools = builtin_tools()
    store = WorkflowStore(tmp_path / "runs.sqlite")
    manager = PluginManager(tmp_path / "plugins", store, tools)
    source = Path("examples/plugins/sequence_composition")
    with pytest.raises(ValueError, match="trust"):
        manager.install(source, trusted=False)
    record = manager.install(source, trusted=True)
    tool_id = f"plugin.sequence_composition.{record['hash'][:12]}"
    workflow = Workflow(id="independent", name="independent", nodes=[WorkflowNode(id="external", label="composition", tool_id=tool_id, inputs={"sequence": LiteralInput(value="MAGSGS")})])
    engine = WorkflowEngine(store, tools, tmp_path / "artifacts")
    result = engine.run(engine.create(Project(id="p", name="p"), workflow))
    assert result["status"] == "succeeded"
    output = result["nodes"][0]["output"]
    assert output["length"] == 6 and output["counts"]["G"] == 2
    assert output["python_version"] == sys.version.split()[0]
    prefix = subprocess.check_output([record["python"], "-I", "-c", "import sys; print(sys.prefix)"], text=True).strip()
    assert Path(prefix).resolve() != Path(sys.prefix).resolve()
    assert record["hash"] in prefix


def pathway_payload() -> dict[str, object]:
    return {
        "id": "user-pathway", "species": ["A", "B"], "phi": 0.1,
        "enzymes": {"E": {"dense_um": 1, "dilute_um": 1, "source": "synthetic test"}},
        "reactions": [{"id": "AB", "enzyme": "E", "substrate": "A", "stoichiometry": {"A": -1, "B": 1}, "kcat_per_h": 10, "km_um": 1, "parameter_source": "synthetic test"}],
        "partition_coefficients": {"A": 1, "B": 1}, "input_flux_um_per_h": {"A": 0.5, "B": 0},
        "secretion_rate_per_h": {"A": 0.1, "B": 0.2}, "initial_guess_um": {"A": 0.1, "B": 1},
    }


def test_custom_pathway_solves_arbitrary_species_with_mass_balance() -> None:
    result = solve_pathway(Pathway.model_validate(pathway_payload()))
    assert result["status"] == "valid"
    assert max(abs(value) for value in result["residual_um_per_h"].values()) < 1e-8
    assert sum(result["secretion_flux_um_per_h"].values()) == pytest.approx(0.5)
    assert "R1" not in result["reaction_flux_um_per_h"]


def test_pathway_rejects_unsupported_law_and_unknown_species() -> None:
    with pytest.raises(ValueError, match="unsupported_rate_law"):
        Pathway.model_validate({**pathway_payload(), "rate_law": "mass_action"})
    payload = pathway_payload()
    payload["reactions"][0]["substrate"] = "UNKNOWN"
    with pytest.raises(ValueError, match="unknown_reaction"):
        Pathway.model_validate(payload)


def test_generic_fusion_and_assembly_workflow_has_no_galatea_entities(tmp_path: Path) -> None:
    project = Project(id="generic", name="Generic", sequences=[SequenceRecord(id="binder", sequence="MAGSGS")], assemblies=[{"id": "trimer", "subunits": {"binder": 3}}])
    store = WorkflowStore(tmp_path / "runs.sqlite")
    engine = WorkflowEngine(store, builtin_tools(), tmp_path / "artifacts")
    result = engine.run(engine.create(project, recommend(project, "assembly_review")))
    assert result["status"] == "succeeded"
    assembly = next(node for node in result["nodes"] if node["id"] == "assemblies[0]")
    assert assembly["output"]["total_subunits"] == 3


def test_actual_process_crash_recovers_without_repeating_completed_node(tmp_path: Path) -> None:
    worker = tmp_path / "worker.py"
    worker.write_text('''from pathlib import Path
import os, sys
from igem_drylab.workflow.models import Contract, Project, Workflow, WorkflowNode, LiteralInput, NodeInput
from igem_drylab.workflow.store import WorkflowStore
from igem_drylab.workflow.tools import WorkflowTools, ToolDefinition
from igem_drylab.workflow.engine import WorkflowEngine
root = Path(sys.argv[1])
class Input(Contract):
    item: int
def handler(payload, context):
    marker = root / ("called-" + context.node_id)
    if payload.item == 2 and not marker.exists():
        marker.write_text("crashed")
        os._exit(17)
    with (root / "calls.txt").open("a") as log:
        log.write(context.node_id + "\\n")
    return {"value": payload.item}
tools = WorkflowTools()
tools.register(ToolDefinition("test", "test", "test", "1", Input, handler, "test"))
store = WorkflowStore(root / "ledger.sqlite")
engine = WorkflowEngine(store, tools, root / "artifacts", max_workers=1)
if sys.argv[2] == "start":
    wf = Workflow(id="crash", name="crash", nodes=[WorkflowNode(id="first", label="first", tool_id="test", inputs={"item": LiteralInput(value=1)}), WorkflowNode(id="second", label="second", tool_id="test", depends_on=["first"], inputs={"item": LiteralInput(value=2)})])
    run_id = engine.create(Project(id="p", name="p"), wf)
    (root / "run-id").write_text(run_id)
else:
    run_id = (root / "run-id").read_text()
    with store.connection() as db:
        db.execute("UPDATE runs SET heartbeat='2000-01-01' WHERE id=?", (run_id,))
result = engine.run(run_id)
assert result["status"] == "succeeded"
''', encoding="utf-8")
    crashed = subprocess.run([sys.executable, str(worker), str(tmp_path), "start"], capture_output=True, text=True, timeout=20)
    assert crashed.returncode == 17, crashed.stderr
    recovered = subprocess.run([sys.executable, str(worker), str(tmp_path), "resume"], capture_output=True, text=True, timeout=20)
    assert recovered.returncode == 0, recovered.stderr
    assert (tmp_path / "calls.txt").read_text().splitlines() == ["first", "second"]

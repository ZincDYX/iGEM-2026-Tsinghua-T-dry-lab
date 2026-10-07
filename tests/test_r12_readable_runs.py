"""Read-model metadata only; no numerical or scientific execution."""
from igem_drylab.workflow.models import Project, Workflow, WorkflowNode
from igem_drylab.workflow.store import WorkflowStore
from igem_drylab.workflow.disclosure import DisclosureBoundary
from igem_drylab.workflow.views import PublicReads
from igem_drylab.workflow.lineage_compare import LineageComparison

def test_run_names_are_frozen_source_names_not_current_edited_project(tmp_path):
    store = WorkflowStore(tmp_path / "workflow.sqlite")
    project = store.save_project(Project(id="p", name="Original experiment"))
    workflow = Workflow(id="w", name="Sequence statistics", nodes=[WorkflowNode(id="n", label="Statistics", tool_id="fusion.sequence_metrics")])
    run_id = store.create_run({"project": project.model_dump(mode="json"), "workflow": workflow.model_dump(mode="json"), "tools": {}})
    snapshot = store.run(run_id)["snapshot_hash"]
    store.save_project(project.model_copy(update={"name": "Renamed draft"}), expected_revision=project.revision)
    summary = PublicReads(store, DisclosureBoundary(store)).summary(run_id)
    assert summary["name"] == "Original experiment"
    assert summary["snapshot_hash"] == snapshot
    identity = LineageComparison(store, DisclosureBoundary(store)).identity(store.run(run_id))
    assert identity.name == "Original experiment"
    assert identity.snapshot_hash == snapshot
    assert identity.created_at == summary["created_at"]

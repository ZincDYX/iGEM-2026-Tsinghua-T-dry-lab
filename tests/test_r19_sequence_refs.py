"""HTTP/identity/cache tests with explicitly non-scientific input records."""
from copy import deepcopy
from pathlib import Path

import pytest

from test_r11_scientific_setup import setup
from test_r6_input_boundaries import api
from igem_drylab.workflow.models import SequenceRef, WorkflowError
from igem_drylab.workflow.sequence_index import resolve_sequence_ref
from igem_drylab.workflow.builtins import recommend


def attached(client):
    project, request = setup(client)
    request["config"]["prepared_through"] = "m1"
    request["config"].pop("stages")
    preview = client.post("/api/platform/scientific-projects/create-preview", json=request)
    assert preview.status_code == 200, preview.text
    saved = client.post("/api/platform/projects", json={"project":{**project,
        "scientific_project":preview.json()["scientific_project"]}, "expected_revision":project["revision"]})
    assert saved.status_code == 200, saved.text
    return saved.json()


def test_m1_setup_requires_no_m3_m4_controls_and_tools_use_the_same_fasta(tmp_path):
    app, client = api(tmp_path)
    public = attached(client)
    assert public["sequences"] == []  # No second copy is populated for Tools.
    check = client.get("/api/platform/projects/p/precheck").json()
    assert all(item["stage"] == "m1" for item in check["missing"])
    project = app.state.platform_store.project("p")
    assert [node.id for node in recommend(project, "scientific_pipeline").nodes] == ["m1"]
    page = client.get("/api/platform/projects/p/sequences?offset=0&limit=1")
    assert page.status_code == 200, page.text
    choice = page.json()["items"][0]
    assert choice["label"] == "ACTUAL_SOFTWARE_SOURCE" and choice["length"] == 6
    record = resolve_sequence_ref(SequenceRef.model_validate(choice["ref"]), project.model_dump(mode="json"), app.state.platform_store)
    assert record["sequence"] == "MAGSGS"
    stale = {**choice["ref"], "construct_version":1}
    with pytest.raises(WorkflowError, match="revision_mismatch"):
        resolve_sequence_ref(SequenceRef.model_validate(stale), project.model_dump(mode="json"), app.state.platform_store)
    bad = {**choice["ref"], "sequence_sha256":"0" * 64}
    with pytest.raises(WorkflowError, match="identity_mismatch"):
        resolve_sequence_ref(SequenceRef.model_validate(bad), project.model_dump(mode="json"), app.state.platform_store)


def test_browsing_cache_does_not_reopen_fasta_and_execution_still_checks_bytes(tmp_path, monkeypatch):
    app, client = api(tmp_path)
    attached(client)
    project = app.state.platform_store.project("p")
    source = Path(project.scientific_project["config"]["inputs"]["protein_fasta"]).resolve()
    original = Path.read_bytes
    reads = []
    def read(path):
        if path.resolve() == source:
            reads.append(path)
        return original(path)
    monkeypatch.setattr(Path, "read_bytes", read)
    first = client.get("/api/platform/projects/p/sequences").json()
    assert client.get("/api/platform/projects/p/sequences").json() == first
    assert reads == []
    ref = SequenceRef.model_validate(first["items"][0]["ref"])
    resolve_sequence_ref(ref, project.model_dump(mode="json"), app.state.platform_store)
    assert reads == [source]
    source.write_text(">ACTUAL_SOFTWARE_SOURCE\nGSAGSG\n", encoding="utf-8")
    assert client.get("/api/platform/projects/p/sequences").status_code == 409
    with pytest.raises(WorkflowError, match="file_identity_changed"):
        resolve_sequence_ref(ref, project.model_dump(mode="json"), app.state.platform_store)


def test_sequence_ref_cannot_reuse_other_project_file_even_with_identical_bytes(tmp_path):
    app, client = api(tmp_path)
    attached(client)
    choice = client.get("/api/platform/projects/p/sequences").json()["items"][0]
    other = deepcopy(app.state.platform_store.project("p").model_dump(mode="json"))
    other["id"] = "not-the-owner"
    with pytest.raises(WorkflowError, match="file_project_mismatch"):
        resolve_sequence_ref(SequenceRef.model_validate(choice["ref"]), other, app.state.platform_store)


def test_preparation_form_exposes_only_selected_required_stage_controls():
    from igem_drylab.workflow.scientific_setup import form_schema
    initial=form_schema("m1")
    assert "stages" not in initial["required"]
    assert initial["$defs"]["StagesConfig"]["required"]==[]
    advanced=form_schema("m4")
    assert "stages" in advanced["required"]
    assert advanced["$defs"]["StagesConfig"]["required"]==["m3_concentration","m4_reaction"]

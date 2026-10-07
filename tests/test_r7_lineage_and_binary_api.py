"""Cross-component identity oracles; software recorded outputs, no solvers.

Kills hash-only authorization, text-ID equivalence, null->zero and body decoding.
"""
from hashlib import sha256
from io import BytesIO
import json

from PIL import Image
import pytest

from test_r6_input_boundaries import api, bundle
from test_r7_iteration import prepared
from igem_drylab.workflow.models import NodeStatus, Project, WorkflowError
from igem_drylab.workflow.store import canonical
from igem_drylab.workflow.lineage_compare import LineageComparison


def test_binary_folder_bytes_and_image_grants_survive_preview_save(tmp_path):
    from zipfile import ZipFile
    app, client = api(tmp_path)
    request = bundle()
    pixels = BytesIO()
    Image.new("RGB", (3, 2), (9, 21, 47)).save(pixels, format="PNG")
    original = pixels.getvalue()
    archive = BytesIO()
    with ZipFile(archive, "w") as output:
        for item in request["files"]:
            output.writestr(item["filename"], item["content"].encode())
        output.writestr("figures/evidence.png", original)
    preview = client.post("/api/platform/scientific-projects/upload-binary?config_filename=configs%2Fproject.yaml", content=archive.getvalue(), headers={"Content-Type":"application/octet-stream"})
    assert preview.status_code == 200, preview.text
    saved = client.post("/api/platform/projects", json={"project":{"id":"binary", "name":"SOFTWARE_BINARY_PARSER_SAMPLE", "scientific_project":preview.json()["scientific_project"]}})
    assert saved.status_code == 200, saved.text
    file = next(f for f in saved.json()["scientific_project"]["evidence_files"] if f["name"] == "evidence.png")
    assert file["sha256"] == sha256(original).hexdigest()
    assert client.get(f"/api/platform/files/{file['id']}?project_id=binary").content == original
    assert client.get("/api/platform/projects/binary/resources").status_code == 200
    assert client.get(f"/api/platform/files/{file['id']}/image-preview?project_id=binary").status_code == 200
    client.post("/api/platform/projects", json={"project":{"id":"stranger", "name":"Not authorized"}})
    assert client.get(f"/api/platform/files/{file['id']}/image-preview?project_id=stranger").status_code == 403
    assert client.get(f"/api/platform/files/{file['id']}/structure-preview?project_id=stranger").status_code == 403


def recorded_stage(store, project, tmp_path, suffix, count=3, value=None, records=None):
    run_id = store.create_run({"project":project.model_dump(mode="json"), "workflow":{"nodes":[{"id":"m4", "tool_id":"project.m4"}]}, "tools":{}})
    rows = [{"candidate_id":f"shared_text_id_{i}","construct_id":"shared_text_construct", "condition_id":"shared_text_condition", "status":"insufficient_data", "evidence_ready":False, "numerically_solved":False, "claim_scope":"insufficient_evidence", "yield_abs":value, "missing_inputs":["actual_evidence_missing"]} for i in range(count)]
    if records is not None:
        rows = records
    output = {"schema_version":"scientific-stage-v2", "module":"m4", "records":rows}
    path = tmp_path / f"recorded-{suffix}.json"
    path.write_text(canonical(output), encoding="utf-8")
    store.set_node(run_id, "m4", NodeStatus.running, increment=True)
    store.complete_node(run_id, "m4", output, path, [])
    return run_id


def formal_parser_record(value=0.25):
    """A hand-declared protocol sample; no solve, calibration or biological claim."""
    from test_new_review_m4 import steady_fixture
    from igem_drylab.full_network import COMPOUNDS
    payload = steady_fixture()
    context = dict(candidate_id="software-fixture", construct_id="fixture", condition_id="fixture", evidence_ready=True, claim_scope="conditional_mechanism", enzyme_sequence_sha256="a"*64)
    prediction = dict(schema_version="m4-prediction-v2", model_kind="markdown_steady_state", formula_version=payload.formula_version, time_unit="h", concentration_unit="uM", time=[], concentrations={"intracellular":{c:[0] for c in COMPOUNDS}}, normalization={"intracellular":"cell_volume"}, kernel_inputs=payload.model_dump(mode="json"), solver_settings=dict(method="least_squares", residual_tolerance_um_per_h=payload.residual_tolerance_um_per_h, relative_residual_tolerance=payload.relative_residual_tolerance, integration_version="scaled-residual-v1", scipy_version="SOFTWARE_PARSER_SAMPLE"), experiment_context=dict(measurement_compartment="intracellular", assay_mode="substrate_feeding_functional", expression_mode="constitutive", input_boundary={"feed_mode":"continuous", "feed_compound_id":"8"}, assay_conditions={"host":"SOFTWARE_FIXTURE", "strain":"SOFTWARE_FIXTURE", "pH":7, "temperature_c":25, "assay_system":"SOFTWARE_PARSER_SAMPLE"}, steady_state_observation_reference="NOT_EXPERIMENTAL_DATA"))
    return dict(candidate_id="software-fixture", construct_id="fixture", condition_id="fixture", status="valid", numerically_solved=True, evidence_ready=True, data_quality="measured", claim_scope="conditional_mechanism", candidate_context=context, simulation_inputs={"prediction_contract":prediction}, yield_abs=value)


@pytest.mark.parametrize("mutation,reason", [(None,None), ("conditions","incompatible_assay_conditions"), ("units","formal_comparison_contract_missing_or_invalid"), ("sequence","construct_identity_changed_requires_reviewed_design_plan"), ("context","M3_M4_candidate_identity_mismatch")])
def test_formal_contract_parser_exact_values_and_incompatibility(tmp_path, mutation, reason):
    app, client, original, parent = prepared(tmp_path)
    store = app.state.platform_store
    child_response = client.post(f"/api/platform/runs/{parent}/iteration")
    child = store.project(child_response.json()["project"]["id"])
    a, b = formal_parser_record(0), formal_parser_record(0.25)
    if mutation == "conditions":
        b["simulation_inputs"]["prediction_contract"]["experiment_context"]["assay_conditions"]["pH"] = 8
    elif mutation == "units":
        b["simulation_inputs"]["prediction_contract"]["concentration_unit"] = "author_native"
    elif mutation == "sequence":
        b["candidate_context"]["enzyme_sequence_sha256"] = "b"*64
    elif mutation == "context":
        b["candidate_context"]["condition_id"] = "unrelated"
    left = recorded_stage(store, original, tmp_path, "formal-a", records=[a])
    right = recorded_stage(store, child, tmp_path, "formal-b", records=[b])
    compare = LineageComparison(store, app.state.workflow_engine.disclosure)
    row = compare.compare(child.id, left, right, 0, 20)["rows"][0]
    assert row["comparable"] == (mutation is None)
    if mutation is None:
        assert row["left"]["value"] == 0 and row["right"]["value"] == 0.25
        assert row["metric_unit"] == "1"
        assert row["metric_definition"] == "product_15_secretion_flux/input_8_flux"
    else:
        assert reason in row["reason_codes"]
        assert row["left"]["value"] is None and row["right"]["value"] is None


def test_batch_alignment_uses_keys_not_record_order(tmp_path):
    app, client, original, parent = prepared(tmp_path)
    store = app.state.platform_store
    child = store.project(client.post(f"/api/platform/runs/{parent}/iteration").json()["project"]["id"])
    a = formal_parser_record()
    other = {**formal_parser_record(), "candidate_id":"other"}
    other["candidate_context"] = {**other["candidate_context"], "candidate_id":"other"}
    left = recorded_stage(store, original, tmp_path, "ordered-a", records=[a,other])
    right = recorded_stage(store, child, tmp_path, "ordered-b", records=[other,a])
    view = LineageComparison(store, app.state.workflow_engine.disclosure).compare(child.id, left, right, 0, 20)
    assert len(view["rows"]) == 2
    assert all(r["left"]["record_id"] == r["right"]["record_id"] for r in view["rows"])


def test_real_iteration_authorizes_lineage_but_not_strangers_or_text_id_numbers(tmp_path):
    app, client, original, parent = prepared(tmp_path)
    store = app.state.platform_store
    iteration = client.post(f"/api/platform/runs/{parent}/iteration")
    assert iteration.status_code == 200
    child = store.project(iteration.json()["project"]["id"])
    left = recorded_stage(store, original, tmp_path, "a", value=999)
    right = recorded_stage(store, child, tmp_path, "b", value=None)
    compare = LineageComparison(store, app.state.workflow_engine.disclosure)
    lineage = compare.lineage(child.id, 0, 1)
    assert lineage["total"] == 3 and len(lineage["items"]) == 1 and lineage["has_more"]
    view = compare.compare(child.id, left, right, 1, 1)
    assert view["total"] == 3 and view["has_more"] and len(view["rows"]) == 1
    row = view["rows"][0]
    assert row["left"]["record_id"] == row["right"]["record_id"] == "shared_text_id_1"
    assert not row["comparable"] and not view["ranking_performed"]
    assert row["left"]["value"] is None and row["right"]["value"] is None
    assert "candidate_not_formally_eligible" in row["reason_codes"]
    assert "construct_sequence_identity_not_registered" in row["reason_codes"]
    # IDs are not sufficient scientific identities, and lineage is not a wildcard grant.
    stranger = store.save_project(Project(id="stranger", name="SOFTWARE_STRANGER"))
    foreign = recorded_stage(store, stranger, tmp_path, "foreign")
    with pytest.raises(WorkflowError, match="comparison_lineage_not_authorized"):
        compare.compare(child.id, foreign, right, 0, 20)
    assert client.get(f"/api/platform/projects/{child.id}/compare?left_run_id={foreign}&right_run_id={right}").status_code == 403
    # Tampering with an immutable parent link must not authorize a stranger.
    with store.connection() as db:
        db.execute("UPDATE projects SET payload=json_set(payload,'$.parent_run_id',?,'$.parent_snapshot_sha256',?) WHERE id=?", (foreign, "incorrect_hash", child.id))
    with pytest.raises(WorkflowError, match="comparison_lineage_not_authorized"):
        compare.authorize(child.id, foreign)

"""Explicit HTTP imports/ownership oracles; no scientific prediction."""
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest

from igem_drylab.software.dashboard import create_app
from igem_drylab.workflow.store import WorkflowStore


def api(tmp_path):
    app = create_app(data_dir=tmp_path,session_token="SOFTWARE_FIXTURE_SESSION",discover_tools=False)
    return app, TestClient(app,headers={"X-FusionLab-Token":"SOFTWARE_FIXTURE_SESSION"})


def test_explicit_same_content_imports_have_independent_project_authorizations(tmp_path):
    app, client = api(tmp_path)
    ids = []
    for project_id in ("a","b"):
        preview = client.post("/api/platform/imports/preview",json={"filename":"proteins.fasta","content":">fixture\nMAGSGS\n"}).json()
        response = client.post("/api/platform/projects",json={"project":{"id":project_id,"name":"software fixture","files":[preview["file"]],**preview["patch"]}})
        assert response.status_code == 200,response.text
        file_id = response.json()["files"][0]["id"]
        ids.append(file_id)
        download = client.get(f"/api/platform/files/{file_id}?project_id={project_id}")
        assert download.content == b">fixture\nMAGSGS\n"
        assert download.headers["X-Content-SHA256"] == sha256(download.content).hexdigest()
        assert client.get(f"/api/platform/files/{file_id}?project_id=third").status_code == 403
    assert ids[0] != ids[1]
    with app.state.platform_store.connection() as db:
        rows = db.execute("SELECT project_id,path FROM file_assets ORDER BY project_id").fetchall()
    assert [row["project_id"] for row in rows] == ["a","b"]
    assert rows[0]["path"] == rows[1]["path"]  # deduplicated blob, not shared authorization
    Path(rows[0]["path"]).write_text("changed",encoding="utf-8")
    assert client.get(f"/api/platform/files/{ids[0]}?project_id=a").status_code == 409


def bundle(entry="configs/project.yaml", dependency=None):
    prefix = "../" if entry.startswith("configs/") else ""
    config = {"run":{"id":"software-fixture"},"inputs":{"protein_fasta":dependency or prefix+"data/proteins.fasta","enzymes":[],"scaffolds":[],"linkers":[]},
        "stages":{"m2_fusion":{"structure_metrics_file":prefix+"metrics/m2.json"}}}
    metrics = [{"candidate_id":"software_fixture","artifact_path":"../structures/model.pdb",
        "reference_artifact_path":"../structures/ref.pdb","geometry_input_path":"../geometry/input.json",
        "sasa_configuration_path":"../geometry/sasa.json"}]
    files = [(entry,json.dumps(config)),("data/proteins.fasta",">fixture\nMAGSGS\n"),("metrics/m2.json",json.dumps(metrics)),
        ("structures/model.pdb","SOFTWARE_FIXTURE"),("structures/ref.pdb","SOFTWARE_FIXTURE"),
        ("geometry/input.json","{}"),("geometry/sasa.json","{}")]
    return {"config_filename":entry,"files":[{"filename":name,"content":content} for name,content in files]}


@pytest.mark.parametrize("entry",["project.yaml","configs/project.yaml"])
def test_owned_bundle_preserves_relative_tree_and_binds_all_typed_m2_dependencies(tmp_path,entry):
    app, client = api(tmp_path)
    response = client.post("/api/platform/scientific-projects/upload-preview",json=bundle(entry))
    assert response.status_code == 200,response.text
    science = response.json()["scientific_project"]
    assert {"model.pdb","ref.pdb","input.json","sasa.json"} <= {row["name"] for row in science["evidence_files"]}
    saved = client.post("/api/platform/projects",json={"project":{"id":"p","name":"fixture","scientific_project":science}})
    assert saved.status_code == 200,saved.text
    with app.state.platform_store.connection() as db:
        root = Path(db.execute("SELECT root FROM scientific_bundles").fetchone()[0])
    assert (root/entry).is_file() and (root/"data/proteins.fasta").is_file()
    (root/"structures/model.pdb").write_text("tampered",encoding="utf-8")
    assert client.post("/api/platform/projects",json={"project":saved.json(),"expected_revision":1}).status_code == 409


@pytest.mark.parametrize("mutation,code",[("missing","scientific_project_missing_local_dependencies"),("escape","scientific_file_outside_authorized_workspace"),("duplicate","invalid_upload_identity"),("traversal","invalid_upload_identity")])
def test_invalid_scientific_bundle_has_actionable_safe_error(tmp_path,mutation,code):
    _,client = api(tmp_path)
    request = bundle()
    if mutation == "missing": request["files"] = [item for item in request["files"] if item["filename"] != "structures/ref.pdb"]
    if mutation == "escape": request = bundle(dependency="../../private/proteins.fasta")
    if mutation == "duplicate": request["files"].append(request["files"][1])
    if mutation == "traversal": request["files"].append({"filename":"../private.txt","content":"NO"})
    response = client.post("/api/platform/scientific-projects/upload-preview",json=request)
    assert response.status_code == 422,response.text
    error = response.json()["detail"]
    assert error["code"] == code and error["diagnostic_id"] and error["actions"]
    assert str(tmp_path) not in response.text
    if mutation == "missing": assert error["logical_files"] == ["structures/ref.pdb"]


def test_asset_schema_migration_preserves_existing_identity_and_bytes(tmp_path):
    path = tmp_path/"old.sqlite"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE file_assets(id TEXT PRIMARY KEY, project_id TEXT, path TEXT NOT NULL UNIQUE, hash TEXT NOT NULL, name TEXT NOT NULL)")
        db.execute("INSERT INTO file_assets VALUES('old','p','private-fixture','sha','fixture')")
    for _ in range(2):
        store = WorkflowStore(path)
        with store.connection() as db:
            assert tuple(db.execute("SELECT * FROM file_assets").fetchone()) == ("old","p","private-fixture","sha","fixture")

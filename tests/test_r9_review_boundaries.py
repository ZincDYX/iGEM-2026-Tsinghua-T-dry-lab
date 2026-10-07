"""Independent r8 review oracles; software fixtures, no scientific solver."""
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

import pytest
from PIL import Image
from fastapi.testclient import TestClient

from igem_drylab.software.dashboard import create_app
from igem_drylab.workflow.models import WorkflowError
from test_r7_display_resources import environment
from test_r6_input_boundaries import bundle


@pytest.mark.parametrize("name,content", [
    ("extra.json", '{"api_key":"FAKE_R9_SECRET"}'),
    ("extra.csv", "time,api_key,password,ssh_host\n0,FAKE_R9_SECRET,p,h\n"),
    ("extra.tsv", "time\tpassword\n0\tFAKE_R9_SECRET\n"),
    ("extra.yaml", "nested:\n  password: FAKE_R9_SECRET\n"),
    ("escaped.yaml", 'nested:\n  "pass\\u0077ord": FAKE_R9_SECRET\n'),
    ("escaped.json", '{"pass\\u0077ord":"FAKE_R9_SECRET"}'),
    ("extra.txt", "api_key=FAKE_R9_SECRET\n"),
    (".env", "UNRELATED=FAKE_R9_SECRET\n"),
    ("id_ed25519", "-----BEGIN OPENSSH PRIVATE KEY-----\nFAKE_R9_SECRET\n"),
])
def test_extra_credentials_quarantined_before_grants_and_original_export(tmp_path, name, content):
    app = create_app(data_dir=tmp_path, session_token="SOFTWARE_SESSION", discover_tools=False)
    client = TestClient(app, headers={"X-FusionLab-Token": "SOFTWARE_SESSION"})
    data = bundle()
    raw = BytesIO()
    with ZipFile(raw, "w") as zip:
        for file in data["files"]:
            zip.writestr(file["filename"], file["content"])
        zip.writestr(name, content)
    response = client.post("/api/platform/scientific-projects/upload-binary?config_filename=configs/project.yaml", content=raw.getvalue(), headers={"Content-Type": "application/octet-stream"})
    assert response.status_code == 403, response.text
    assert response.json()["detail"]["code"] == "disclosure_quarantined"
    assert "FAKE_R9_SECRET" not in response.text
    assert [p.read_text() for p in (tmp_path / "quarantine").rglob(name)] == [content]
    with app.state.platform_store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM file_assets").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM scientific_bundles").fetchone()[0] == 0
    # Historical registrations are subject to the exact same download policy.
    store = app.state.platform_store
    from igem_drylab.workflow.disclosure import DisclosureBoundary
    from igem_drylab.workflow.models import Project
    store.save_project(Project(id="p", name="fixture"))
    original = next((tmp_path / "quarantine").rglob(name))
    asset = DisclosureBoundary(store).asset(original, project_id="p")
    refused = client.get(f'/api/platform/files/{asset["id"]}?project_id=p')
    assert refused.status_code == 403 and "FAKE_R9_SECRET" not in refused.text
    assert client.get(f'/api/platform/files/{asset["id"]}?project_id=other').status_code == 403


def test_original_names_survive_content_dedup_and_old_schema(tmp_path):
    app = create_app(data_dir=tmp_path, session_token="SOFTWARE_SESSION", discover_tools=False)
    client = TestClient(app, headers={"X-FusionLab-Token": "SOFTWARE_SESSION"})
    previews = [client.post("/api/platform/imports/preview", json={"filename": name, "content": "time,value\n0,0\n"}).json() for name in ["measurements.csv", "other.csv", "nested/measurements.csv"]]
    saved = client.post("/api/platform/projects", json={"project": {"id":"p", "name":"fixture", "files":[p["file"] for p in previews]}})
    assert saved.status_code == 200, saved.text
    resources = client.get("/api/platform/projects/p/resources").json()["items"]
    assert [r["name"] for r in resources] == ["measurements.csv", "other.csv", "measurements.csv"]
    assert [r["logical_relative_path"] for r in resources] == ["measurements.csv", "other.csv", "nested/measurements.csv"]
    for r in resources:
        response = client.get(f'/api/platform/files/{r["identity"]["file_id"]}?project_id=p')
        assert response.status_code == 200 and response.content == b"time,value\n0,0\n"
        assert r["name"] in response.headers["content-disposition"]
    with app.state.platform_store.connection() as db:
        assert len({r[0] for r in db.execute("SELECT path FROM file_assets")}) == 1


@pytest.mark.parametrize("extension", ["png", "jpg", "jpeg"])
def test_single_frame_images_exif_orientation_pixels_and_original_bytes(tmp_path, extension):
    _, boundary, display = environment(tmp_path)
    source = tmp_path / f"image.{extension}"
    image = Image.new("RGB", (20, 30), (13, 27, 39))
    if extension == "png":
        image.save(source)
    else:
        exif = Image.Exif()
        exif[274] = 6
        exif[270] = "PRIVATE_SOFTWARE_METADATA"
        image.save(source, exif=exif)
    original = source.read_bytes()
    asset = boundary.asset(source, project_id="a")
    preview = display.image("a", asset["id"])
    with Image.open(BytesIO(preview)) as shown:
        assert shown.size == ((20, 30) if extension == "png" else (30, 20))
        assert not shown.getexif() and not shown.info
    assert source.read_bytes() == original and b"PRIVATE_SOFTWARE_METADATA" not in preview


def test_catalog_isolates_missing_tampered_budget_and_credentials(tmp_path):
    _, boundary, display = environment(tmp_path)
    ids = {}
    for name, text in {"good.csv":"time,value\n0,0\n", "tampered.csv":"time,value\n0,1\n", "missing.csv":"x\n0\n", "large.csv":"x\n0\n", "secret.csv":"api_key\nFAKE_R9_SECRET\n", "invalid.yaml":"[broken"}.items():
        source = tmp_path / name
        source.write_text(text)
        ids[name] = boundary.asset(source, project_id="a")["id"]
    (tmp_path / "tampered.csv").write_text("changed")
    (tmp_path / "missing.csv").unlink()
    with (tmp_path / "large.csv").open("ab") as output:
        output.truncate(20_000_001)
    items = {r["name"]: r for r in display.catalog("a")["items"]}
    assert items["good.csv"]["status"] == "available"
    assert items["tampered.csv"]["error_code"] == "file_identity_changed"
    assert items["missing.csv"]["error_code"] == "display_source_missing"
    assert items["large.csv"]["error_code"] == "display_source_budget_exceeded"
    assert items["secret.csv"]["status"] == "quarantined"
    assert items["invalid.yaml"]["status"] == "unavailable"
    assert len(items) == 6 and "FAKE_R9_SECRET" not in json.dumps(items)
    assert display.catalog("b")["items"] == []


@pytest.mark.parametrize("case,code", [("damaged","invalid_image_source"),("multiple_frames","image_decode_budget_exceeded"),("pixel_budget","image_decode_budget_exceeded")])
def test_image_failure_preserves_original_and_never_returns_preview(tmp_path, case, code):
    _, boundary, display = environment(tmp_path)
    source = tmp_path / "bad.png"
    if case == "damaged":
        source.write_bytes(b"not an image")
    elif case == "multiple_frames":
        Image.new("RGB", (2,3), "red").save(source, save_all=True, append_images=[Image.new("RGB", (2,3), "blue")])
    else:
        Image.new("RGB", (4001,4000), "white").save(source)
    original = source.read_bytes()
    asset = boundary.asset(source, project_id="a")
    with pytest.raises(WorkflowError, match=code):
        display.image("a", asset["id"])
    assert source.read_bytes() == original


def test_full_annotation_index_independent_of_residue_page_and_cached_identity(tmp_path, monkeypatch):
    _, boundary, display = environment(tmp_path)
    source = tmp_path / "many.pdb"
    source.write_text("MODEL        7\n" + "\n".join(f"ATOM  {i:5d}  CA  ALA B{i:4d}      11.000  12.000  13.000  1.00 99.00           C" for i in range(1, 121)) + "\nENDMDL\nEND\n")
    asset = boundary.asset(source, project_id="a")
    residues = display.structure("a", asset["id"], limit=200)[0]["residues"]
    annotations = tmp_path / "annotations.json"
    annotations.write_text(json.dumps({"schema_version":"structure-display-annotations-v1", "target_sha256":asset["sha256"], "source_reference":"SOFTWARE_FIXTURE", "source_tool":"PARSER", "source_tool_version":"1", "confidence_semantics":"plddt", "rows":[{"residue":r, "plddt":42, "pocket":i == 119} for i, r in enumerate(residues)]}))
    annotation_asset = boundary.asset(annotations, project_id="a")
    full = display.structure("a", asset["id"], limit=0, full_annotations=True)[0]
    assert full["annotation_scope"] == "full_model" and len(full["annotations"]) == 120 and full["residues"] == []
    original = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: (_ for _ in ()).throw(AssertionError("sidecar reparsed on cache hit")) if p == annotations else original(p))
    for offset, count in [(0,100),(100,20)]:
        page = display.structure("a", asset["id"], offset=offset)[0]
        assert len(page["annotations"]) == count
        assert display.structure("a", asset["id"], limit=0, full_annotations=True)[0]["annotations"] == full["annotations"]
    with pytest.raises(WorkflowError, match="file_project_mismatch"):
        display.structure("b", asset["id"], full_annotations=True)
    monkeypatch.setattr(Path, "read_bytes", original)
    annotations.write_text("{}")
    with pytest.raises(WorkflowError, match="file_identity_changed"):
        display.structure("a", asset["id"], full_annotations=True)

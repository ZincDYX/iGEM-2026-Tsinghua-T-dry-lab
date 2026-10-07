"""Original protocol values and adversarial imports; no solver or scientific calibration."""
from io import BytesIO
import json

from PIL import Image
import pytest
from test_r6_input_boundaries import api


def registered(client, filename, content, project_id="p"):
    preview = client.post("/api/platform/imports/preview", json={"filename": filename, "content": content})
    assert preview.status_code == 200, preview.text
    preview = preview.json()
    saved = client.post("/api/platform/projects", json={"project": {"id": project_id, "name": "SOFTWARE_TABLE_SAMPLE", "files": [preview["file"]]}})
    assert saved.status_code == 200, saved.text
    return saved.json(), preview


@pytest.mark.parametrize("extension,separator", [("csv", ","), ("tsv", "\t")])
def test_empty_project_table_mapping_full_overview_and_original_indices(tmp_path, extension, separator):
    _, client = api(tmp_path)
    raw = separator.join(["minutes", "signal", "other"]) + "\n" + "\n".join(separator.join([str(i), "" if i == 513 else str(i * 2), str(i * 3)]) for i in range(1201)) + "\n"
    project, preview = registered(client, "ordinary." + extension, raw)
    file_id = preview["file"]["id"]
    table = client.get(f"/api/platform/files/{file_id}/table?project_id=p&offset=500").json()
    assert table["total"] == 1201 and table["rows"][13] == ["513", "", "1539"]
    assert table["columns"] == ["minutes", "signal", "other"] and len(table["rows"]) == 500
    mapping = dict(project_id="p", expected_revision=project["revision"], file_id=file_id,
                   source_reference="SOFTWARE_PARSER_SAMPLE_NOT_BIOLOGY", time_key="minutes", time_unit="min",
                   columns=[dict(key="signal", species="declared_A", compartment="recorded_dense", unit="mM"), dict(key="other", species="declared_B", compartment="recorded_dense", unit="mM")])
    result = client.post("/api/platform/imports/series-mapping", json=mapping)
    assert result.status_code == 200, result.text
    declaration = result.json()["file"]
    page = client.get(f'/api/platform/files/{declaration["id"]}/series?project_id=p&limit=100000&series_id=0&series_id=1').json()
    assert page["time"] == list(range(1201)) and not page["has_more"]
    assert page["values"]["0"][0] == 0 and page["values"]["0"][513] is None and page["values"]["0"][-1] == 2400
    assert page["values"]["1"][-1] == 3600 and page["time_unit"] == "min"
    assert page["data_source_sha256"] == preview["file"]["sha256"]
    assert client.get(f"/api/platform/files/{file_id}?project_id=p").content.decode() == raw
    assert client.post("/api/platform/projects", json={"project": {"id": "stranger", "name": "OTHER_SOFTWARE_PROJECT"}}).status_code == 200
    assert client.get(f'/api/platform/files/{declaration["id"]}/series?project_id=stranger').status_code == 403
    assert client.post("/api/platform/imports/series-mapping", json={**mapping, "expected_revision": 999}).status_code == 409
    assert project["scientific_project"] is None and project["datasets"] == []


@pytest.mark.parametrize("content", ["time,a,a\n0,1,2\n", "time,a\n0,1,extra\n", "time,a\n0\n"])
def test_invalid_tables_rejected_before_grants(tmp_path, content):
    app, client = api(tmp_path)
    assert client.post("/api/platform/imports/preview", json={"filename": "bad.csv", "content": content}).status_code == 422
    with app.state.platform_store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM file_assets").fetchone()[0] == 0


@pytest.mark.parametrize("values", ["0,0\n0,2\n", "0,0\n1,NaN\n", "0,0\n,2\n", "0,0\n1,inf\n"])
def test_bad_numeric_mapping_does_not_publish_declaration(tmp_path, values):
    app, client = api(tmp_path)
    project, preview = registered(client, "bad-values.csv", "time,value\n" + values)
    response = client.post("/api/platform/imports/series-mapping", json=dict(project_id="p", expected_revision=project["revision"], file_id=preview["file"]["id"], source_reference="SOFTWARE_SAMPLE", time_key="time", time_unit="s", columns=[dict(key="value", species="recorded", compartment="declared", unit="1")]))
    assert response.status_code == 422, response.text
    with app.state.platform_store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM file_assets").fetchone()[0] == 1


def test_json_role_is_explicit_and_binary_import_original_is_exact(tmp_path):
    _, client = api(tmp_path)
    project, preview = registered(client, "configuration.json", '{"ordinary":true,"zero":0}')
    assert preview["kind"] == "configuration_display_only" and project["pathway"] is None
    text = client.get(f'/api/platform/files/{preview["file"]["id"]}/table?project_id=p').json()["text"]
    assert json.loads(text) == {"ordinary": True, "zero": 0}
    raw = BytesIO(); Image.new("RGB", (2, 3), (17, 23, 42)).save(raw, format="JPEG")
    original = raw.getvalue()
    imported = client.post("/api/platform/imports/display-file?filename=ordinary.jpg", content=original)
    assert imported.status_code == 200, imported.text
    file = imported.json()["file"]
    assert imported.json()["patch"] == {}
    saved = client.post("/api/platform/projects", json={"project": {**project, "files": [*project["files"], file]}, "expected_revision": project["revision"]})
    assert saved.status_code == 200, saved.text
    assert client.get(f'/api/platform/files/{file["id"]}?project_id=p').content == original
    assert client.get(f'/api/platform/files/{file["id"]}/image-preview?project_id=p').content.startswith(b"\x89PNG")
    assert client.post("/api/platform/projects", json={"project": {"id": "stranger", "name": "OTHER_SOFTWARE_PROJECT"}}).status_code == 200
    assert client.get(f'/api/platform/files/{file["id"]}/resource?project_id=stranger').status_code == 403


def test_typed_record_preview_enforces_units_provenance_and_no_approval(tmp_path):
    _, client = api(tmp_path)
    def parameter(**patch):
        return client.post("/api/platform/scientific-records/preview", json={"kind": "parameter", "value": {"parameter_id": "explicit", "name": "declared", "value": 0, "unit": "s^-1", "source_type": "wetlab", **patch}})
    assert parameter().json()["parameter"]["value"] == 0
    assert parameter().json()["parameter"]["review_status"] == "extracted"
    assert parameter(unit=None).status_code == 422
    assert parameter(source_type="literature").status_code == 422
    assert parameter(review_status="approved", approved_by="FAKE_REVIEWER").status_code == 422
    result = client.post("/api/platform/scientific-records/preview", json={"kind": "construct", "value": {"id": "explicit", "components": ["A", "B"]}})
    assert result.status_code == 200 and result.json()["construct_record"]["components"] == ["A", "B"]
    assert result.json()["construct_record"]["localization_context"] is None


def test_overview_cell_budget_reports_exact_partial_coverage(tmp_path):
    from test_r7_display_resources import environment
    _, boundary, resources = environment(tmp_path)
    source = tmp_path / "recorded.json"
    source.write_text(json.dumps({"prediction_contract": dict(schema_version="m4-prediction-v2", model_kind="SOFTWARE_ONLY", formula_version="NO_SOLVER", time_unit="s", concentration_unit="1", time=list(range(30001)), concentrations={"declared": {str(i): [i] * 30001 for i in range(12)}})}))
    file = boundary.asset(source, project_id="a")
    overview = resources.series("a", file["id"], 0, 100000)
    assert len(overview["time"]) == 25000 and overview["total"] == 30001 and overview["has_more"]
    end = resources.series("a", file["id"], 25000, 100000)
    assert end["time"][0] == 25000 and end["time"][-1] == 30000 and not end["has_more"]
    assert sum(map(len, overview["values"].values())) == 300000

import json

from test_r7_display_resources import environment


def test_resource_kind_filter_precedes_pagination_and_counts_full_catalogue(tmp_path):
    _, boundary, display = environment(tmp_path)
    for index in range(65):
        path = tmp_path / f"table-{index}.csv"
        path.write_text("x,y\n0,1\n")
        boundary.asset(path, project_id="a")
    structures = []
    for index in range(55):
        path = tmp_path / f"structure-{index}.pdb"
        path.write_text("ATOM      1  CA  ALA A   1       1.000   2.000   3.000  1.00 20.00           C\nEND\n")
        structures.append(boundary.asset(path, project_id="a")["id"])
    first = display.catalog("a", kind="structure")
    second = display.catalog("a", offset=50, kind="structure")
    assert first["total"] == second["total"] == 55
    assert first["has_more"] and not second["has_more"]
    assert [item["identity"]["file_id"] for item in first["items"] + second["items"]] == structures
    assert display.catalog("b", kind="structure")["total"] == 0


def test_indexed_json_kind_does_not_survive_source_tampering(tmp_path):
    _, boundary, display = environment(tmp_path)
    path = tmp_path / "source.json"
    path.write_text(json.dumps({"schema_version": "display-series-source-v1"}))
    asset = boundary.asset(path, project_id="a")
    assert display.catalog("a", kind="series")["items"][0]["identity"]["file_id"] == asset["id"]
    assert display.catalog("b", kind="series")["total"] == 0
    path.write_text("{}")
    assert display.catalog("a", kind="series")["total"] == 0
    assert display.catalog("a", kind="table")["items"][0]["status"] == "unavailable"

"""Display-only oracles: exact bytes/points, grants, metadata and decode budgets.

Software parser samples, not scientific predictions. No solver is invoked.
"""
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile, ZipInfo

import pytest
from PIL import Image, PngImagePlugin

from igem_drylab.workflow.models import Project, WorkflowError
from igem_drylab.workflow.store import WorkflowStore
from igem_drylab.workflow.disclosure import DisclosureBoundary
from igem_drylab.workflow.display_resources import DisplayResources
from igem_drylab.workflow.binary_import import receive_bundle


def environment(tmp_path):
    store = WorkflowStore(tmp_path / "ledger.sqlite3")
    store.save_project(Project(id="a", name="SOFTWARE_FIXTURE_A"))
    store.save_project(Project(id="b", name="SOFTWARE_FIXTURE_B"))
    boundary = DisclosureBoundary(store)
    return store, boundary, DisplayResources(store, boundary)


def test_exact_point_page_whitelist_cache_grant_and_tamper(tmp_path, monkeypatch):
    store, boundary, display = environment(tmp_path)
    raw = {"prediction_contract": {"schema_version":"m4-prediction-v2", "model_kind":"software_display_fixture", "formula_version":"NOT_SCIENTIFIC", "time_unit":"h", "concentration_unit":"uM", "time":[0, 1, 2, 3], "concentrations":{"dense":{"15":[0, None, 2, 3]}}, "analysis_result":[99]*100, "simulation_inputs":{"never":"export"}}, "unrelated":[88]*100}
    source = tmp_path / "recorded.json"
    source.write_text(json.dumps(raw), encoding="utf-8")
    file = boundary.asset(source, project_id="a")
    page = display.series("a", file["id"], 1, 2)
    assert page["time"] == [1, 2] and page["values"] == {"0":[None, 2]}
    assert page["series"][0]["unit"] == "uM" and page["has_more"]
    assert "analysis_result" not in json.dumps(page) and "simulation_inputs" not in json.dumps(page)
    assert page["identity"]["source_sha256"] == sha256(source.read_bytes()).hexdigest()
    # Once indexed, parsing the original JSON again would be a failed implementation.
    original = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: (_ for _ in ()).throw(AssertionError("whole source reparsed")) if p == source else original(p))
    assert display.series("a", file["id"], 2, 1)["values"]["0"] == [2]
    with pytest.raises(WorkflowError, match="file_project_mismatch"):
        display.series("b", file["id"], 0, 2)
    monkeypatch.setattr(Path, "read_bytes", original)
    source.write_bytes(b"changed")
    with pytest.raises(WorkflowError, match="file_identity_changed"):
        display.series("a", file["id"], 0, 2)


def test_image_original_sealed_metadata_removed_and_no_svg_execution(tmp_path):
    _, boundary, display = environment(tmp_path)
    source = tmp_path / "image.png"
    info = PngImagePlugin.PngInfo()
    info.add_text("comment", "PRIVATE_ORIGINAL_METADATA")
    Image.new("RGB", (2, 3), (13, 27, 39)).save(source, pnginfo=info)
    before = source.read_bytes()
    file = boundary.asset(source, project_id="a")
    preview = display.image("a", file["id"])
    assert b"PRIVATE_ORIGINAL_METADATA" not in preview and source.read_bytes() == before
    with Image.open(BytesIO(preview)) as pixels:
        assert pixels.size == (2, 3) and pixels.getpixel((0, 0)) == (13, 27, 39, 255)
    svg = tmp_path / "active.svg"
    svg.write_text('<svg onload="alert(1)"><foreignObject/></svg>')
    asset = boundary.asset(svg, project_id="a")
    with pytest.raises(WorkflowError, match="unsupported_image_format"):
        display.image("a", asset["id"])
    mislabeled = tmp_path / "not-jpeg.jpg"
    mislabeled.write_bytes(before)
    wrong_type = boundary.asset(mislabeled, project_id="a")
    with pytest.raises(WorkflowError, match="image_media_type_mismatch"):
        display.image("a", wrong_type["id"])


def test_structure_chain_insertion_identity_not_bfactor_confidence(tmp_path):
    _, boundary, display = environment(tmp_path)
    source = tmp_path / "sample.pdb"
    source.write_text("REMARK PRIVATE_SOURCE_NOTE\nATOM      1  CA  ALA B  12A     11.000  12.000  13.000  1.00 99.00           C\nEND\n")
    before = source.read_bytes()
    file = boundary.asset(source, project_id="a")
    meta, preview = display.structure("a", file["id"])
    assert meta["chains"] == ["B"]
    assert meta["residues"][0] == dict(model="1", chain="B", residue_number="12", insertion_code="A", residue_name="ALA")
    assert meta["confidence_status"] == "not_registered" and meta["mapping_status"] == "not_registered"
    assert b"PRIVATE_SOURCE_NOTE" not in preview and source.read_bytes() == before


class StreamingRequest:
    headers = {}
    def __init__(self, raw):
        self.raw = raw
    async def stream(self):
        for start in range(0, len(self.raw), 7):
            yield self.raw[start:start+7]


def test_structure_annotations_bind_exact_model_chain_insertion_and_reference(tmp_path):
    _, boundary, display = environment(tmp_path)
    source = tmp_path / "target.pdb"
    source.write_text("MODEL        7\nATOM      1  CA  ALA B  12A     11.000  12.000  13.000  1.00 99.00           C\nENDMDL\n")
    target = boundary.asset(source, project_id="a")
    residue = dict(model="7", chain="B", residue_number="12", insertion_code="A", residue_name="ALA")
    reference = tmp_path / "reference.pdb"
    reference.write_bytes(source.read_bytes())
    reference_asset = boundary.asset(reference, project_id="a")
    sidecar = tmp_path / "annotations.json"
    original = {"schema_version":"structure-display-annotations-v1", "target_sha256":target["sha256"], "source_reference":"SOFTWARE_PARSER_SAMPLE_NOT_PREDICTION", "source_tool":"PARSER_SAMPLE", "source_tool_version":"1", "confidence_semantics":"plddt", "rows":[{"residue":residue, "full_fusion_position":17, "region":"enzyme", "reference_residue":residue, "reference_sha256":reference_asset["sha256"], "pocket":True, "plddt":42}]}
    sidecar.write_text(json.dumps(original))
    boundary.asset(sidecar, project_id="a")
    meta, _ = display.structure("a", target["id"])
    assert meta["models"] == ["7"]
    assert meta["annotations"][0]["plddt"] == 42  # Explicit sidecar, never B-factor 99.
    assert meta["annotations"][0]["full_fusion_position"] == 17
    assert meta["annotation_sha256"] == sha256(sidecar.read_bytes()).hexdigest()
    assert meta["pocket_status"] == "source_registered_not_scientific_approval"
    invalid = tmp_path / "invalid-confidence.json"
    invalid.write_text(json.dumps({**original, "confidence_semantics":"not_provided"}))
    other_target = boundary.asset(source, project_id="b")
    boundary.asset(reference, project_id="b")
    boundary.asset(invalid, project_id="b")
    with pytest.raises(WorkflowError, match="structure_confidence_semantics_missing"):
        display.structure("b", other_target["id"])


def test_mmcif_coordinate_projection_removes_custom_metadata(tmp_path):
    _, boundary, display = environment(tmp_path)
    source = tmp_path / "sample.cif"
    source.write_text("data_fixture\nloop_\n_atom_site.group_PDB\n_atom_site.id\n_atom_site.type_symbol\n_atom_site.label_atom_id\n_atom_site.label_comp_id\n_atom_site.label_asym_id\n_atom_site.label_seq_id\n_atom_site.auth_asym_id\n_atom_site.auth_seq_id\n_atom_site.pdbx_PDB_ins_code\n_atom_site.Cartn_x\n_atom_site.Cartn_y\n_atom_site.Cartn_z\n_atom_site.pdbx_PDB_model_num\n_atom_site.private_note\nATOM 1 C CA ALA X 1 B 12 A 11 12 13 7 PRIVATE_METADATA\n#\n")
    asset = boundary.asset(source, project_id="a")
    meta, preview = display.structure("a", asset["id"])
    assert meta["residues"] == [dict(model="7", chain="B", residue_number="12", insertion_code="A", residue_name="ALA")]
    assert b"PRIVATE_METADATA" not in preview and b"private_note" not in preview
    assert meta["confidence_status"] == "not_registered"


@pytest.mark.parametrize("name", ["../escape", "C:/escape", "a\\escape", "/escape", "./escape", "a//escape", "nested/name:stream", "nested/CON.txt", "nested/name."])
def test_streaming_zip_rejects_paths_and_cleans_only_owned_staging(tmp_path, name):
    import asyncio
    target = BytesIO()
    with ZipFile(target, "w") as zip_file:
        zip_file.writestr(name, b"bytes")
    keep = tmp_path / "KEEP_USER_INPUT"
    keep.write_bytes(b"not owned by importer")
    with pytest.raises(WorkflowError, match="invalid_upload_identity"):
        # Windows ZipInfo normalizes backslashes on construction. Mutate both
        # header names at byte level to test an actually hostile ZIP member.
        archive_bytes = target.getvalue().replace(b"a/escape", b"a\\escape") if "\\" in name else target.getvalue()
        asyncio.run(receive_bundle(StreamingRequest(archive_bytes), tmp_path / "imports", "project.yaml", lambda *_: None))
    assert keep.read_bytes() == b"not owned by importer"
    assert not list((tmp_path / "imports").iterdir())


def test_stream_budget_before_body_and_symlink_archive(tmp_path, monkeypatch):
    import asyncio
    request = StreamingRequest(b"must not read")
    request.headers = {"content-length":"20000001"}
    with pytest.raises(WorkflowError, match="scientific_upload_budget_exceeded"):
        asyncio.run(receive_bundle(request, tmp_path / "imports", "project.yaml", lambda *_: None))
    target = BytesIO()
    with ZipFile(target, "w") as zip_file:
        link = ZipInfo("linked")
        link.external_attr = (0o120777 << 16)
        zip_file.writestr(link, "../user")
    with pytest.raises(WorkflowError, match="invalid_upload_identity"):
        asyncio.run(receive_bundle(StreamingRequest(target.getvalue()), tmp_path / "imports", "project.yaml", lambda *_: None))

"""Binary format/display tests, not numerical or biological validation."""
from io import BytesIO
import struct

import msgpack
import pytest
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from ihm.format_bcif import BinaryCifWriter

from igem_drylab.workflow.bcif_display import _decode, binary_atom_columns
from igem_drylab.workflow.models import WorkflowError
from test_r7_display_resources import environment


def fixture_bytes():
    output = BytesIO()
    writer = BinaryCifWriter(output)
    writer.start_block("DISPLAY_FIXTURE")
    fields = ["group_PDB", "id", "type_symbol", "label_atom_id", "label_comp_id",
              "label_asym_id", "label_seq_id", "auth_asym_id", "auth_seq_id",
              "pdbx_PDB_ins_code", "Cartn_x", "Cartn_y", "Cartn_z",
              "pdbx_PDB_model_num", "B_iso_or_equiv", "private_note"]
    with writer.loop("_atom_site", fields) as loop:
        for model in [7, 8]:
            loop.write(**dict(zip(fields, ["ATOM", model, "C", "CA", "ALA", "X", 1,
                "B", 12, "A", 11.123456789, 12.987654321, 13.000000001,
                model, 99.0, "PRIVATE_METADATA"])))
    writer.flush()
    return output.getvalue()


def test_binary_original_preserved_precision_models_auth_chain_and_grants(tmp_path):
    _, boundary, display = environment(tmp_path)
    path = tmp_path / "sample.bcif"
    before = fixture_bytes()
    path.write_bytes(before)
    file = boundary.asset(path, project_id="a")
    meta, preview = display.structure("a", file["id"])
    assert meta["models"] == ["7", "8"] and meta["chains"] == ["B"]
    assert meta["residues"] == [dict(model=str(m), chain="B", residue_number="12",
        insertion_code="A", residue_name="ALA") for m in [7, 8]]
    assert meta["confidence_status"] == "not_registered"
    assert b"private_note" not in preview and b"PRIVATE_METADATA" not in preview
    decoded = binary_atom_columns(path, 200_000)
    projected = MMCIF2Dict(BytesIO(preview).getvalue().decode().splitlines())
    for field in ["Cartn_x", "Cartn_y", "Cartn_z"]:
        assert projected["_atom_site." + field] == decoded["_atom_site." + field]
    assert path.read_bytes() == before
    assert any(item["kind"] == "structure" for item in display.catalog("a")["items"])
    with pytest.raises(WorkflowError, match="file_project_mismatch"):
        display.structure("b", file["id"])


@pytest.mark.parametrize("encoding,data,expected", [
    ({"kind":"ByteArray", "type":3}, struct.pack("<2i", 5, -7), [5, -7]),
    ({"kind":"Delta", "origin":10}, [2, 3, -1], [12, 15, 14]),
    ({"kind":"RunLength", "srcSize":3}, [8, 2, 9, 1], [8, 8, 9]),
    ({"kind":"IntegerPacking", "byteCount":1, "isUnsigned":True}, [255, 1, 4], [256, 4]),
    ({"kind":"FixedPoint", "factor":1000}, [11234, -9], [11.234, -0.009]),
    ({"kind":"IntervalQuantization", "min":0, "max":10, "numSteps":3}, [0, 1, 2], [0, 5, 10]),
    ({"kind":"StringArray", "stringData":"ALAARG", "offsets":[0, 3, 6],
      "offsetEncoding":[], "dataEncoding":[]}, [1, 0, -1], ["ARG", "ALA", None]),
])
def test_supported_codec_families(encoding, data, expected):
    assert _decode(data, [encoding], 10) == expected


def test_run_length_actual_expansion_bounded_even_false_src_size():
    with pytest.raises(WorkflowError, match="display_source_budget_exceeded"):
        _decode([1, 10**12], [{"kind":"RunLength", "srcSize":1}], 10)
    with pytest.raises(WorkflowError, match="display_source_budget_exceeded"):
        _decode(b"\0"*100, [{"kind":"ByteArray", "type":1}], 10)


@pytest.mark.parametrize("change", ["row_budget", "multiple_blocks", "bad_mask", "zero_factor", "missing_unmasked"])
def test_malformed_binary_is_rejected(tmp_path, change):
    frame = msgpack.unpackb(fixture_bytes(), raw=False)
    category = frame["dataBlocks"][0]["categories"][0]
    if change == "row_budget":
        category["rowCount"] = 200_001
    elif change == "multiple_blocks":
        frame["dataBlocks"] *= 2
    elif change == "bad_mask":
        category["columns"][0]["mask"] = dict(data=[3, 0], encoding=[])
    elif change == "zero_factor":
        category["columns"][0]["data"] = dict(data=[1, 2], encoding=[dict(kind="FixedPoint", factor=0)])
    else:
        category["columns"][0]["data"] = dict(data=[-1, 0], encoding=[dict(
            kind="StringArray", stringData="ATOM", offsets=[0, 4], offsetEncoding=[], dataEncoding=[])])
    path = tmp_path / "invalid.bcif"
    path.write_bytes(msgpack.packb(frame, use_bin_type=True))
    code = "display_source_budget_exceeded" if change == "row_budget" else "invalid_structure_source"
    with pytest.raises(WorkflowError, match=code):
        binary_atom_columns(path, 200_000)


def test_missing_mask_values_preserved(tmp_path):
    frame = msgpack.unpackb(fixture_bytes(), raw=False)
    column = frame["dataBlocks"][0]["categories"][0]["columns"][0]
    column["mask"] = dict(data=[1, 2], encoding=[])
    path = tmp_path / "masked.bcif"
    path.write_bytes(msgpack.packb(frame, use_bin_type=True))
    assert binary_atom_columns(path, 200_000)["_atom_site.group_PDB"] == [".", "?"]

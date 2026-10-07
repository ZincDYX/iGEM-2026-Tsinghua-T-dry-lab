"""Software projection cache oracles; no molecular calculation or solver."""
import pytest

from test_r7_display_resources import environment
from igem_drylab.workflow.models import WorkflowError


def test_coordinate_pages_reuse_index_but_never_skip_grants_or_original_hash(tmp_path, monkeypatch):
    store, boundary, display = environment(tmp_path)
    source = tmp_path / "cache.pdb"
    source.write_text("MODEL        7\nATOM      1  CA  ALA B  12A     11.000  12.000  13.000  1.00 99.00           C\nATOM      2  CA  GLY C  13      12.000  12.000  13.000  1.00 99.00           C\nENDMDL\n")
    file = boundary.asset(source, project_id="a")
    page, original_preview = display.structure("a", file["id"], 0, 1)
    assert page["total"] == 2 and page["residues"][0]["insertion_code"] == "A"
    monkeypatch.setattr(display, "_parse_coordinates", lambda *args: pytest.fail("coordinate source reparsed"))
    next_page, preview = display.structure("a", file["id"], 1, 1)
    assert next_page["residues"][0]["chain"] == "C" and preview == original_preview
    assert next_page["models"] == ["7"]
    with pytest.raises(WorkflowError, match="file_project_mismatch"):
        display.structure("b", file["id"])
    with store.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM display_structure_residues").fetchone()[0] == 2
    source.write_bytes(b"tampered")
    with pytest.raises(WorkflowError, match="file_identity_changed"):
        display.structure("a", file["id"])

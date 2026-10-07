"""Original-transform parser oracles; no structure alignment is performed."""
from hashlib import sha256
import json
import pytest
from pydantic import ValidationError

from test_r7_display_resources import environment
from igem_drylab.workflow.display_resources import RegisteredOverlay
from igem_drylab.workflow.models import WorkflowError


MATRIX = [[0,-1,0,5],[1,0,0,6],[0,0,1,7],[0,0,0,1]]


def overlay(reference_hash):
    return dict(reference_sha256=reference_hash, source_reference="SOFTWARE_ORIGINAL_TRANSFORM",
        source_tool="PARSER_SAMPLE", source_tool_version="1", direction="reference_to_target",
        coordinate_unit="angstrom", convention="row_major_column_vector_xyz1", matrix=MATRIX)


def test_original_overlay_matrix_is_source_bound_authorized_and_not_recomputed(tmp_path):
    _, boundary, display = environment(tmp_path)
    target = tmp_path / "target.pdb"
    reference = tmp_path / "reference.pdb"
    target.write_text("ATOM      1  CA  ALA B  12A     11.000  12.000  13.000  1.00 99.00           C\nEND\n")
    reference.write_text("ATOM      1  CA  GLY C  13       1.000   2.000   3.000  1.00 99.00           C\nEND\n")
    t = boundary.asset(target, project_id="a")
    r = boundary.asset(reference, project_id="a")
    sidecar = tmp_path / "overlay.json"
    sidecar.write_text(json.dumps(dict(schema_version="structure-display-annotations-v1",target_sha256=t["sha256"],
        source_reference="SOFTWARE_PARSER_SAMPLE",confidence_semantics="not_provided",rows=[],overlays=[overlay(r["sha256"])])))
    boundary.asset(sidecar, project_id="a")
    before = (target.read_bytes(),reference.read_bytes())
    metadata, _ = display.structure("a", t["id"])
    recorded = metadata["overlays"][0]
    assert recorded["matrix"] == MATRIX and recorded["reference_file_id"] == r["id"]
    assert recorded["target_sha256"] == sha256(before[0]).hexdigest()
    assert metadata["mapping_status"] == "not_registered"
    t_other = boundary.asset(target, project_id="b")
    boundary.asset(sidecar, project_id="b")
    with pytest.raises(WorkflowError, match="structure_reference_not_authorized"):
        display.structure("b", t_other["id"])
    reference.write_bytes(b"changed")
    with pytest.raises(WorkflowError, match="file_identity_changed"):
        display.structure("a", t["id"])
    assert target.read_bytes() == before[0]


@pytest.mark.parametrize("matrix", [
    [[2,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],
    [[-1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],
    [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,1,1]],
])
def test_overlay_rejects_scale_reflection_and_projective_matrices(matrix):
    with pytest.raises(ValidationError):
        RegisteredOverlay.model_validate({**overlay("a"*64),"matrix":matrix})

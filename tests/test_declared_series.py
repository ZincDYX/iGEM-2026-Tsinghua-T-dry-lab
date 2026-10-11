"""Exact parser samples: no unit conversion, model or biological computation."""
from hashlib import sha256
from io import BytesIO
import json
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np
import pytest
from test_r7_display_resources import environment
from igem_drylab.workflow.models import WorkflowError


@pytest.mark.parametrize("format_name", ["csv", "npz"])
def test_declared_csv_npz_keep_original_units_null_zero_and_recheck_target(tmp_path, monkeypatch, format_name):
    _, boundary, resources = environment(tmp_path)
    source = tmp_path/("sample."+format_name)
    if format_name == "csv":
        source.write_text("minutes,signal\n0,0\n30,\n60,2.5\n")
    else:
        np.savez_compressed(source, minutes=[0,30,60], signal=[0,np.nan,2.5])
    target = boundary.asset(source, project_id="a")
    original = source.read_bytes()
    declaration = dict(schema_version="display-series-source-v1", target_sha256=sha256(original).hexdigest(),
        source_reference="SOFTWARE_PARSER_SAMPLE_NOT_BIOLOGY", format=format_name, time_key="minutes", time_unit="min",
        missing_token="" if format_name=="csv" else "nan",
        columns=[dict(key="signal",compartment="extracellular",species="13",unit="mM")])
    sidecar = tmp_path/"series.json"; sidecar.write_text(json.dumps(declaration))
    asset = boundary.asset(sidecar, project_id="a")
    page = resources.series("a",asset["id"],0,2)
    assert page["time"]==[0,30] and page["values"]=={"0":[0,None]}
    assert page["series"][0]==dict(id="0",compartment="extracellular",species="13",unit="mM",species_id="13",quantity=None)
    assert page["time_unit"]=="min" and page["model_kind"]=="registered_source_not_prediction"
    assert page["data_source_sha256"]==target["sha256"]
    from igem_drylab.workflow import declared_series
    with monkeypatch.context() as guard:
        guard.setattr(declared_series,"read_columns",lambda *args: pytest.fail("cached data reparsed"))
        assert resources.series("a",asset["id"],2,2)["values"]=={"0":[2.5]}
    assert source.read_bytes()==original
    assert next(r for r in resources.catalog("a")["items"] if r["identity"]["file_id"]==asset["id"])["kind"]=="series"
    with pytest.raises(WorkflowError, match="file_project_mismatch"):
        resources.series("b",asset["id"],0,2)
    source.write_bytes(b"tampered")
    with pytest.raises(WorkflowError, match="file_identity_changed"):
        resources.series("a",asset["id"],0,2)


def test_npz_rejects_forged_large_shape_before_loading_array(tmp_path, monkeypatch):
    from igem_drylab.workflow.declared_series import DeclaredSeries, read_columns
    source = tmp_path/"bad.npz"
    raw = BytesIO()
    np.lib.format.write_array_header_1_0(raw, dict(descr="<f8",fortran_order=False,shape=(10**10,)))
    with ZipFile(source,"w",compression=ZIP_DEFLATED) as archive:
        archive.writestr("time.npy",raw.getvalue()); archive.writestr("signal.npy",raw.getvalue())
    declaration=DeclaredSeries(schema_version="display-series-source-v1",target_sha256="a"*64,
        source_reference="SOFTWARE_ATTACK_SAMPLE",format="npz",time_key="time",time_unit="h",missing_token="nan",
        columns=[dict(key="signal",compartment="declared",species="declared",unit="1")])
    monkeypatch.setattr(np,"load",lambda *a,**kw: pytest.fail("untrusted shape reached allocation"))
    with pytest.raises(WorkflowError,match="numeric_vector_required"):
        read_columns(source,declaration)

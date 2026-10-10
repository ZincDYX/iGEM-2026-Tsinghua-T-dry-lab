"""Software boundary tests; no numerical solver or uploaded code execution."""
from io import BytesIO
import json
from zipfile import ZipFile, ZipInfo
import stat
import pytest
from igem_drylab.workflow.models import WorkflowError
from igem_drylab.workflow.synthetic_ps import read_ps_archive,reject_synthetic_formal_input


def test_valid_inner_result_never_removes_outer_synthetic_restriction():
    for value in ({'source_type':'synthetic','result':{'status':'valid','m4_ready':True}},
        {'records':[{'source_type':'derived_from_synthetic','result':{'status':'valid'}}]},
        {'formal_prediction_allowed':False,'result':{'evidence_ready':True}}):
        with pytest.raises(WorkflowError,match='synthetic_input_not_formal_evidence'):
            reject_synthetic_formal_input(value)


def test_archive_preview_reads_only_named_inputs_and_does_not_execute_attachment(tmp_path):
    marker=tmp_path/'NEVER_EXECUTED'
    stream=BytesIO()
    canonical={'parameter_set_id':'PS-v3-SYNTHETIC','source_type':'synthetic','formal_prediction_allowed':False,'watermark':'SYNTHETIC_PIPELINE_TEST'}
    with ZipFile(stream,'w') as archive:
        archive.writestr('demo/canonical_parameters.json',json.dumps(canonical))
        archive.writestr('demo/scripts/run.py',f'open({str(marker)!r},"w").write("wrong")')
        archive.writestr('demo/solver_outputs/C1_m4.json','THIS_IS_NOT_A_NEW_RESULT')
        for case in ('C1','C2','E1','E2'):
            archive.writestr('demo/solver_inputs/'+case+'_m4.json','{}')
            if case.startswith('E'): archive.writestr('demo/solver_inputs/'+case+'_m3.json','{}')
    actual,inputs=read_ps_archive(stream.getvalue())
    assert actual==canonical and set(inputs)=={'C1','C2','E1','E2'}
    assert not marker.exists()


@pytest.mark.parametrize('name,mode', [('../canonical_parameters.json', 0),
    ('demo/link', stat.S_IFLNK | 0o777), ('C:/demo.json', 0), ('demo/CON.json', 0)])
def test_synthetic_package_obeys_same_upload_identity_boundary(name, mode):
    stream = BytesIO()
    with ZipFile(stream, 'w') as archive:
        entry = ZipInfo(name)
        entry.external_attr = mode << 16
        archive.writestr(entry, '{}')
    with pytest.raises(WorkflowError, match='invalid_upload_identity'):
        read_ps_archive(stream.getvalue())

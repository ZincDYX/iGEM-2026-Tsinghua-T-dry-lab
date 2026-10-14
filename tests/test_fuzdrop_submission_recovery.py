"""Persistent protocol fixtures, not FuzDrop predictions."""
import json
import pytest
from igem_drylab.fuzdrop_runner import _previous_response, _open_form


@pytest.mark.data_contract
def test_only_durable_pre_POST_state_can_resume_a_page_visit(tmp_path):
    path=tmp_path/'state.json'
    assert _previous_response(path,'protocol','sequence_identity') is None
    path.write_text(json.dumps(dict(protocol='protocol',input_sha256='sequence_identity',status='prepared')))
    assert _previous_response(path,'protocol','sequence_identity') is None
    path.write_text(json.dumps(dict(protocol='protocol',input_sha256='sequence_identity',status='submitting')))
    with pytest.raises(ValueError,match='submission_unknown'):
        _previous_response(path,'protocol','sequence_identity')


@pytest.mark.data_contract
def test_saved_original_response_is_reused_but_failed_HTTP_is_not_accepted(tmp_path):
    path=tmp_path/'state.json';raw=tmp_path/'original.json';raw.write_text('{}')
    record=dict(protocol='protocol',input_sha256='sequence_identity',status='response_saved',response_file=str(raw),http_status=200)
    path.write_text(json.dumps(record));assert _previous_response(path,'protocol','sequence_identity')==raw
    record['http_status']=403;path.write_text(json.dumps(record))
    with pytest.raises(ValueError,match='human_verification'):
        _previous_response(path,'protocol','sequence_identity')
    with pytest.raises(ValueError,match='identity_mismatch'):
        _previous_response(path,'protocol','different_identity')


@pytest.mark.data_contract
def test_form_readiness_checks_the_real_visible_input_not_network_idle():
    calls=[]
    class Page:
        def goto(self,url,**options):calls.append(('visit',url,options))
        def locator(self,selector):calls.append(('selector',selector));return self
        def wait_for(self,**options):calls.append(('ready',options))
    _open_form(Page())
    assert calls[0][2]['wait_until']=='commit'
    assert calls[1]==('selector','#floatingTextarea2')
    assert calls[2][1]['state']=='visible'

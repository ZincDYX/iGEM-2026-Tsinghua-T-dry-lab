"""HTTP protocol fixtures, not original predictor validation."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest
from igem_drylab import catgranule_runner as runner


class Reply:
    def __init__(self, raw): self.content=raw; self.text=raw.decode()
    def raise_for_status(self): pass
    def json(self): return json.loads(self.text)


def test_original_known_job_retrieval_does_not_submit_and_validates_full_input(tmp_path, monkeypatch):
    sequence="GSGS"
    fasta=tmp_path/'input.fa'; fasta.write_text('>sequence_input\n'+sequence+'\n')
    state=tmp_path/'job.json'
    state.write_text(json.dumps(dict(protocol='catgranule2016-official-form-v1',
        input_sha256=sha256(sequence.encode()).hexdigest(), job_id='protocol_fixture',
        result_url='https://crg-webservice.s3.amazonaws.com/submissions/fixture/output/index.html')))
    calls=[]
    def get(url,**kwargs):
        calls.append(url)
        name=url.rsplit('/',1)[-1]
        return Reply({'index.html':b'<a href="scores.txt">Original table</a>',
            'prot.fa':fasta.read_bytes(),'scores.txt':b'sequence_input 4.23603\n',
            'profiles.txt':b'2.5 1.0 sequence_input\n'}[name])
    monkeypatch.setattr(runner.requests,'get',get)
    monkeypatch.setattr(runner.requests,'post',lambda *a,**kw:pytest.fail('Known job must never be resubmitted'))
    output=tmp_path/'retrieved'
    monkeypatch.setattr(sys,'argv',['catgranule_runner','--fasta',str(fasta),'--record','sequence_input',
        '--output-dir',str(output),'--state-file',str(state)])
    runner.main()
    assert len(calls)==4 and json.loads(state.read_text())['status']=='validated_not_published'
    record=json.loads((output/'scores.run.json').read_text())
    assert record['input_sha256']==sha256(sequence.encode()).hexdigest()
    assert record['native_format']=='catgranule2016_scores'


def test_submission_intent_survives_ambiguous_ack_and_cannot_send_second_post(tmp_path, monkeypatch):
    fasta=tmp_path/'input.fa'; fasta.write_text('>sequence_input\nGSGS\n')
    state=tmp_path/'job.json'; output=tmp_path/'prediction'; calls=[]
    def post(*args,**kwargs):
        calls.append(args)
        assert json.loads(state.read_text())['status']=='submitting'
        raise runner.requests.Timeout('Ambiguous synthetic response')
    monkeypatch.setattr(runner.requests,'post',post)
    monkeypatch.setattr(sys,'argv',['catgranule_runner','--fasta',str(fasta),'--record','sequence_input',
        '--output-dir',str(output),'--state-file',str(state)])
    with pytest.raises(runner.requests.Timeout): runner.main()
    with pytest.raises(ValueError,match='submission_unknown'): runner.main()
    assert len(calls)==1

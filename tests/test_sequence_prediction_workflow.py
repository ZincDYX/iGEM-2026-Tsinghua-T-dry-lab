"""Actual subprocess/ledger protocol, not an authentic predictor smoke test."""
from pathlib import Path
import sys
import json
import pytest

from igem_drylab.workflow.builtins import builtin_tools
from igem_drylab.workflow.engine import WorkflowEngine
from igem_drylab.workflow.models import Project, SequenceRecord, Workflow, WorkflowNode, ProjectInput
from igem_drylab.workflow.runtime_profiles import RuntimeProfiles
from igem_drylab.workflow.store import WorkflowStore


def test_unconfigured_tool_is_recorded_without_mock_prediction(tmp_path):
    store = WorkflowStore(tmp_path / "ledger.sqlite")
    engine = WorkflowEngine(store, builtin_tools(), tmp_path / "artifacts")
    project = Project(id="p", name="PROTOCOL_FIXTURE", sequences=[SequenceRecord(id="input", sequence="GSAD")])
    workflow = Workflow(id="w", name="diagnostic", nodes=[WorkflowNode(id="seg", label="SEG", tool_id="prediction.seg",
        inputs={"item": ProjectInput(path=["sequences", 0])})])
    run = engine.run(engine.create(project, workflow))
    output = run["nodes"][0]["output"]
    assert output["tool_status"] == "not_configured" and output["parsed"] is None
    assert output["scientific_status"] == "diagnostic_not_formal_M1_M2_acceptance"


def test_real_subprocess_output_and_record_persist_across_ledger_reopen(tmp_path):
    store = WorkflowStore(tmp_path / "ledger.sqlite")
    script = tmp_path / "protocol_fixture.py"
    script.write_text("print('>input\\nGSXX\\n')\n")
    RuntimeProfiles(store).install("owned", {"seg": {"enabled": True, "mode": "external",
        "command": f'"{sys.executable}" "{script}"', "verified_version": "PROTOCOL_FIXTURE_NOT_SEG"}})
    project = Project(id="p", name="PROTOCOL_FIXTURE", runtime_profile_ref="owned",
        sequences=[SequenceRecord(id="input", sequence="GSAD")])
    workflow = Workflow(id="w", name="diagnostic", nodes=[WorkflowNode(id="seg", label="SEG", tool_id="prediction.seg",
        inputs={"item": ProjectInput(path=["sequences", 0])})])
    engine = WorkflowEngine(store, builtin_tools(), tmp_path / "artifacts")
    run_id = engine.create(project, workflow)
    run = engine.run(run_id)
    assert run["status"] == "succeeded", run["nodes"]
    output = run["nodes"][0]["output"]
    assert output["tool_status"] == output["parse_status"] == "succeeded"
    assert output["parsed"]["low_complexity_positions"] == [3, 4]
    reopened = WorkflowStore(tmp_path / "ledger.sqlite").run(run_id)
    assert reopened["nodes"][0]["output"] == output
    assert Path(output["parsed"]["source_file"]).is_file()


@pytest.mark.data_contract
@pytest.mark.parametrize('failure',['failed','timed_out'])
def test_actual_native_failure_is_not_a_successful_workflow_node(tmp_path,failure):
    script=tmp_path/'protocol_failure.py'
    script.write_text('import sys,time\nprint("protocol fixture only",flush=True)\n'+('sys.exit(7)\n' if failure=='failed' else 'time.sleep(3)\n'))
    store=WorkflowStore(tmp_path/'ledger.sqlite')
    RuntimeProfiles(store).install('fixture',{'seg':dict(enabled=True,mode='external',
        command=f'"{sys.executable}" "{script}"',verified_version='PROTOCOL_FIXTURE_NOT_SEG',timeout_seconds=1)})
    engine=WorkflowEngine(store,builtin_tools(),tmp_path/'artifacts')
    project=Project(id='p',name='PROTOCOL_FIXTURE',runtime_profile_ref='fixture',sequences=[SequenceRecord(id='input',sequence='GSAD')])
    workflow=Workflow(id='w',name='failure contract',nodes=[WorkflowNode(id='seg',label='SEG',tool_id='prediction.seg',inputs={'item':ProjectInput(path=['sequences',0])})])
    run=engine.run(engine.create(project,workflow));node=run['nodes'][0]
    assert run['status']=='failed' and node['status']=='failed' and node['output'] is None
    assert node['error']['code']=='external_prediction_'+failure and node['error']['retryable'] is False
    failure_file=next((tmp_path/'artifacts').rglob('prediction-failure.json'))
    saved=json.loads(failure_file.read_text());manifest=json.loads(Path(saved['execution_manifest']).read_text())
    assert saved['tool_status']==failure and saved['parse_status']=='not_run' and saved['parsed'] is None
    assert manifest['status']==failure and 'protocol fixture only' in manifest['stdout']


def test_psipred_profile_route_is_wired_without_JPred_length_limits(tmp_path,monkeypatch):
    """Synthetic adapter contract only; no native PSIPRED execution claimed."""
    import json
    from hashlib import sha256
    from types import SimpleNamespace
    from igem_drylab.constructs.linker_features import parse_secondary_structure_output
    from igem_drylab.workflow.m1_checks import m1_workflow
    workflow=m1_workflow(secondary_tool='psipred')
    assert 'm1_psipred' in {n.id for n in workflow.nodes} and 'm1_jpred' not in {n.id for n in workflow.nodes}
    assert next(n for n in workflow.nodes if n.id=='m1_decisions').inputs['secondary_results'].node_id=='m1_psipred'
    sequence='GS'*501
    class SyntheticAdapter:
        def is_available(self):return True
        def run(self,*,output_dir,**kwargs):
            assert kwargs['sequence']==sequence and len(sequence)>800
            output_dir.mkdir(parents=True);raw=output_dir/'native.ss2'
            raw.write_text('\n'.join(f'{i} {aa} C 1.0 0.0 0.0' for i,aa in enumerate(sequence,1))+'\n')
            digest=sha256(sequence.encode()).hexdigest()
            record=dict(tool_name='PSIPRED',tool_version='SYNTHETIC-NOT-PSIPRED',origin='automated',returncode=0,
                command=['synthetic-not-original-tool'],input_sha256=digest,output_sha256=sha256(raw.read_bytes()).hexdigest())
            raw.with_suffix('.run.json').write_text(json.dumps(record))
            parsed=parse_secondary_structure_output(raw,tool_name='PSIPRED',tool_version=record['tool_version'],input_sha256=digest)
            (output_dir/'secondary.json').write_text(parsed.model_dump_json())
            (output_dir/'native-state.json').write_text(json.dumps(dict(status='validated',identity=dict(input_sha256=digest),
                reported_homolog_count=0,method_applicability='no_reported_homologs_not_a_calibrated_hard_veto')))
            return SimpleNamespace(status='succeeded')
    monkeypatch.setattr('igem_drylab.workflow.sequence_predictions.create_tool_adapter',lambda *args:SyntheticAdapter())
    store=WorkflowStore(tmp_path/'ledger.sqlite')
    RuntimeProfiles(store).install('fixture',{'psipred':dict(enabled=True,mode='external',command='python -m igem_drylab.psipred_runner')})
    engine=WorkflowEngine(store,builtin_tools(),tmp_path/'artifacts')
    project=Project(id='p',name='SYNTHETIC-PSIPRED-ADAPTER',runtime_profile_ref='fixture',sequences=[SequenceRecord(id='long',sequence=sequence)])
    task=Workflow(id='psipred-test',name='synthetic-contract',nodes=[WorkflowNode(id='ss',label='PSIPRED',tool_id='prediction.psipred',inputs={'item':ProjectInput(path=['sequences',0])})])
    run=engine.run(engine.create(project,task));assert run['status']=='succeeded',run['nodes']
    output=run['nodes'][0]['output']
    assert output['parse_status']=='succeeded' and output['parsed']['tool_name']=='PSIPRED'
    assert len(output['parsed']['states'])==len(sequence)
    assert output['method_applicability']=='no_reported_homologs_not_a_calibrated_hard_veto'

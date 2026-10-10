"""Run on a compute server: real public sequence, shared CLI/Web approval/run."""
import json
from pathlib import Path

from Bio.SeqUtils.ProtParam import ProteinAnalysis
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from igem_drylab.software.cli import app
from igem_drylab.software.dashboard import create_app


def test_public_gfp_approved_cli_run_is_visible_after_web_restart(tmp_path):
    runner=CliRunner()
    args=['--data-dir',str(tmp_path/'workspace'),'--json']
    def command(*parts):
        result=runner.invoke(app,[*args,*parts])
        assert result.exit_code==0,result.output
        return json.loads(result.stdout)
    project=command('project','create','--name','Public GFP sequence-property task')
    fasta=Path(__file__).parents[1]/'examples/public_gfp/P42212.fasta'
    if not fasta.exists():
        fasta=next((Path(__file__).parents[1]/'examples/public_gfp').glob('*.fasta'))
    imported=command('import',str(fasta),'--project',project['id'])
    plan=command('plan','--project',project['id'],'--method','sequence-properties')
    rejected=runner.invoke(app,[*args,'workflow','run',plan['id']])
    assert rejected.exit_code==2  # No calculation without accepting this revision.
    command('workflow','decide',plan['id'],'--accept')
    run=command('workflow','run',plan['id'])
    repeated=command('workflow','run',plan['id'])
    assert repeated['id']==run['id'] and repeated['nodes']==run['nodes']
    analysis=next(node for node in run['nodes'] if node.get('output',{}).get('schema_version')=='sequence-metrics-v1')
    sequence=imported['sequences'][0]['sequence']
    assert len(sequence)==238
    record=analysis['output']
    assert abs(record['protparam']['molecular_weight_da']-ProteinAnalysis(sequence).molecular_weight())<1e-8
    command('results','export',run['id'],'--format','csv,json','--output',str(tmp_path/'export'))
    saved=json.loads((tmp_path/'export/run.json').read_text())
    assert saved['nodes']==run['nodes']
    backend=create_app(data_dir=tmp_path/'workspace',session_token='software-test',discover_tools=False)
    with TestClient(backend) as browser:
        headers={'X-FusionLab-Token':'software-test'}
        visible=browser.get('/api/platform/runs/'+run['id'],headers=headers)
        assert visible.status_code==200
        assert visible.json()['status']=='succeeded'
        fetched=browser.get('/api/platform/projects/'+project['id'],headers=headers)
        assert fetched.json()['revision']==imported['revision']

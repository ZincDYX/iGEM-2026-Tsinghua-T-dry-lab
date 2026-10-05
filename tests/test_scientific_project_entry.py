"""Actual typed project HTTP and deterministic DAG; not biological validation."""
from pathlib import Path
from time import sleep
import json

from fastapi.testclient import TestClient
import pytest

from igem_drylab.software.dashboard import create_app
from igem_drylab.workflow.scientific_project import load_scientific_project


def test_typed_project_executes_original_stages_and_preserves_missing_evidence(tmp_path):
    client = TestClient(create_app(data_dir=tmp_path))
    source = Path('configs/m1_m4_real_scoring_example.yaml').resolve()
    preview = client.post('/api/platform/scientific-projects/preview',json={'config_path':str(source)})
    assert preview.status_code == 200, preview.text
    science = preview.json()['scientific_project']
    assert science['config']['execution']['mode'] == 'real'
    assert science['config']['experimental_context']['pH'] is None
    assert len(science['evidence_files']) >= 4
    saved = client.post('/api/platform/projects',json={'project':{'id':'science','name':'software_fixture typed pipeline','scientific_project':science}})
    assert saved.status_code == 200
    plan = client.post('/api/platform/plans',json={'project_id':'science','goal':'scientific_pipeline'}).json()
    assert [row['tool_id'] for row in plan['workflow']['nodes']] == ['project.m1','project.m2','project.m3','project.m4','project.m5']
    response = client.post('/api/platform/runs',json={'project_id':'science','workflow':plan['workflow'],'confirmation':plan['confirmation']})
    assert response.status_code == 202
    run_id = response.json()['id']
    for _ in range(250):
        run = client.get('/api/platform/runs/'+run_id).json()
        if run['status'] in {'succeeded','failed'}: break
        sleep(.02)
    assert run['status'] == 'succeeded', run
    assert len(run['artifacts']) == 5
    outputs = {row['output']['module']:row['output'] for row in run['nodes']}
    assert set(outputs) == {'m1','m2','m3','m4','m5'}
    assert outputs['m4']['records']
    assert all(not row['evidence_ready'] and row['status'] == 'insufficient_data' and row['final_15'] is None
        for row in outputs['m4']['records'])
    assert run['snapshot']['project']['scientific_project'] == science


def test_scientific_files_are_bound_and_tamper_or_missing_binding_refused(tmp_path):
    project = load_scientific_project(Path('configs/m1_m4_real_scoring_example.yaml'))
    project.verify()
    project.evidence_files[0].sha256 = '0'*64
    with pytest.raises(ValueError,match='artifact_hash_mismatch'): project.verify()
    project = load_scientific_project(Path('configs/m1_m4_real_scoring_example.yaml'))
    project.evidence_files = []
    with pytest.raises(ValueError,match='unbound_input_files'): project.verify()


def test_wetlab_import_is_explicit_typed_qc_not_parameter_approval(tmp_path):
    client = TestClient(create_app(data_dir=tmp_path))
    record = {'experiment_id':'software_fixture','construct_id':'c','condition_id':'d','replicate_id':'r',
        'metabolite_time':[0,1], 'metabolite_concentration_unit':'uM','metabolites':{'15':[1,2]}}
    body = {'filename':'measurements.json','input_kind':'wetlab','content':json.dumps([record])}
    response = client.post('/api/platform/imports/preview',json=body)
    assert response.status_code == 200
    dataset = response.json()['patch']['datasets'][0]
    assert dataset['kind'] == 'wetlab' and dataset['records'][0]['assay_conditions'] is None
    assert 'control_unavailable' in dataset['qc'][0]['flags']
    assert 'parameters' not in response.json()['patch']
    record['metabolites']['15'] = [-1,2]
    body['content'] = json.dumps([record])
    assert client.post('/api/platform/imports/preview',json=body).status_code == 422

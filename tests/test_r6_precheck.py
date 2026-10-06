"""Non-solving public hints must not mutate inputs or grant approval."""
from fastapi.testclient import TestClient
from workbench_fixture import fixture_app


def test_precheck_uses_declared_input_contracts_without_executing_or_approving(tmp_path):
    app=fixture_app(tmp_path)
    project=app.state.platform_store.project('software-fixture')
    frozen=project.model_dump(mode='json')
    with TestClient(app) as client:
        response=client.get('/api/platform/projects/software-fixture/precheck')
        assert response.status_code==200,response.text
        value=response.json()
        assert value['final_stage_gates_required'] is True and value['scientific_approval_granted'] is False
        assert value['project_revision']==project.revision
        assert {'explicit_construct_definitions','structure_metrics_file','wetlab_results_file'} <= {item['code'] for item in value['missing']}
        assert {'m3','m4'} <= {item['stage'] for item in value['missing']}
        assert str(tmp_path) not in response.text
        assert app.state.fixture_calls==[] and app.state.platform_store.runs()==[]
        assert app.state.platform_store.project(project.id).model_dump(mode='json')==frozen


def test_no_scientific_project_is_a_missing_input_not_a_fake_approval(tmp_path):
    app=fixture_app(tmp_path)
    with TestClient(app) as client:
        assert client.post('/api/platform/projects',json={'project':{'id':'plain','name':'software fixture'}}).status_code==200
        value=client.get('/api/platform/projects/plain/precheck').json()
        assert value['missing'][0]['code']=='typed_scientific_project'
        assert value['scientific_approval_granted'] is False and app.state.fixture_calls==[]

"""Software ledger/approval tests, with explicit non-scientific fixture tools."""
from fastapi.testclient import TestClient
from workbench_fixture import fixture_app


def test_revision_keeps_history_actual_diff_and_revokes_old_execution_authority(tmp_path):
    app = fixture_app(tmp_path)
    with TestClient(app) as client:
        proposal = client.post('/api/platform/proposals',json={
            'project_id':'software-fixture','goal':'scientific_pipeline','objective':'SOFTWARE_FIXTURE original objective'}).json()
        old_id = proposal['id']
        client.post(f'/api/platform/proposals/{old_id}/decision',json={'action':'accept'}).raise_for_status()
        workflow = proposal['workflow']
        workflow['execution_policy']['max_completed_stages'] = 1
        response = client.post(f'/api/platform/proposals/{old_id}/revise',json={
            'prompt':'SOFTWARE_FIXTURE stop after the first module','workflow':workflow})
        assert response.status_code == 200,response.text
        revised = response.json()
        assert revised['status'] == 'proposed' and revised['id'] != old_id
        assert client.get(f'/api/platform/proposals/{old_id}').json()['status'] == 'rejected'
        diff = client.get(f"/api/platform/proposals/{revised['id']}/diff").json()
        assert diff['previous_proposal_id'] == old_id
        assert [change['kind'] for change in diff['changes']] == ['permission']
        history = client.get('/api/platform/projects/software-fixture/assistant').json()
        assert [message['role'] for message in history['messages']] == ['user','assistant','user','assistant']
        assert 'stop after' in history['messages'][2]['text']
        assert app.state.platform_store.runs() == [] and app.state.fixture_calls == []
        run = client.post('/api/platform/runs',json={'project_id':'software-fixture',
            'proposal_id':old_id,'workflow':proposal['workflow'],'confirmation':proposal['confirmation'],'request_id':old_id})
        assert run.status_code == 409
        # Recreating the planning service must use the same persisted transcript.
        from igem_drylab.workflow.planning import PlanningService
        service = PlanningService(app.state.platform_store,app.state.workflow_engine.disclosure,engine=app.state.workflow_engine)
        assert service.conversation('software-fixture').model_dump(mode='json') == history


def test_template_prompt_is_not_a_scientific_patch_and_repeat_revision_is_real(tmp_path):
    app = fixture_app(tmp_path)
    with TestClient(app) as client:
        original = client.post('/api/platform/proposals',json={'project_id':'software-fixture','goal':'scientific_pipeline'}).json()
        current = original
        for prompt in ('SOFTWARE_FIXTURE first correction','SOFTWARE_FIXTURE second correction'):
            response = client.post(f"/api/platform/proposals/{current['id']}/revise",json={'prompt':prompt})
            assert response.status_code == 200,response.text
            current = response.json()
            assert current['workflow']['nodes'] == original['workflow']['nodes']
            assert current['status'] == 'proposed'
        diff = client.get(f"/api/platform/proposals/{current['id']}/diff").json()
        assert diff['changes'] == []
        assert app.state.fixture_client.calls == 0 and app.state.fixture_calls == []


def test_revision_rejects_unknown_tools_without_revoking_valid_proposal(tmp_path):
    app = fixture_app(tmp_path)
    with TestClient(app) as client:
        proposal = client.post('/api/platform/proposals',json={'project_id':'software-fixture','goal':'scientific_pipeline'}).json()
        workflow = proposal['workflow']
        workflow['nodes'][0]['tool_id'] = 'does.not.exist'
        response = client.post(f"/api/platform/proposals/{proposal['id']}/revise",json={
            'prompt':'SOFTWARE_FIXTURE invalid tool','workflow':workflow})
        assert response.status_code in (409,422),response.text
        assert client.get(f"/api/platform/proposals/{proposal['id']}").json()['status'] == 'proposed'
        assert len(client.get('/api/platform/projects/software-fixture/assistant').json()['messages']) == 2

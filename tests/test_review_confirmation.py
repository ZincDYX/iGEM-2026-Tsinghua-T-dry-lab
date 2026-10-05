"""Actual HTTP approval contracts and SQLite writer-lock race oracles."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Barrier

from fastapi.testclient import TestClient
import pytest

from igem_drylab.software.dashboard import create_app
from igem_drylab.workflow.engine import WorkflowEngine
from igem_drylab.workflow.builtins import builtin_tools, recommend
from igem_drylab.workflow.models import Project, WorkflowError
from igem_drylab.workflow.store import WorkflowStore, plan_binding


@pytest.fixture
def api_project(tmp_path):
    client = TestClient(create_app(data_dir=tmp_path))
    project = client.post('/api/platform/projects', json={'project': {'id': 'p', 'name': 'software_fixture',
        'sequences': [{'id': 'same', 'sequence': 'MAGSGS'}]}}).json()
    plan = client.post('/api/platform/plans', json={'project_id': 'p', 'goal': 'fusion_screen'}).json()
    return client, project, {'project_id': 'p', 'workflow': plan['workflow'], 'confirmation': plan['confirmation']}


def test_normal_plan_executes_and_changed_project_refuses_old_confirmation(api_project):
    client, project, request = api_project
    accepted = client.post('/api/platform/runs', json=request)
    assert accepted.status_code == 202
    assert accepted.json()['snapshot']['project']['revision'] == 1
    project['sequences'][0]['sequence'] = 'MWWWWW'
    assert client.post('/api/platform/projects', json={'project': project, 'expected_revision': 1}).status_code == 200
    refused = client.post('/api/platform/runs', json=request)
    assert refused.status_code == 409
    assert 'regenerate_and_review' in str(refused.json())


def test_workflow_edit_or_missing_confirmation_is_not_silently_approved(api_project):
    client, _, request = api_project
    modified = deepcopy(request)
    modified['workflow']['description'] += ' changed after approval'
    assert client.post('/api/platform/runs', json=modified).status_code == 409
    assert client.post('/api/platform/runs', json={k:v for k,v in request.items() if k != 'confirmation'}).status_code == 422
    custom = client.post('/api/platform/plans/custom', json={'project_id': 'p', 'workflow': modified['workflow']}).json()
    response = client.post('/api/platform/runs', json={'project_id': 'p', 'workflow': custom['workflow'], 'confirmation': custom['confirmation']})
    assert response.status_code == 202


def test_concurrent_save_and_confirmation_never_approves_old_executes_new(tmp_path):
    store = WorkflowStore(tmp_path / 'race.sqlite3')
    old = store.save_project(Project(id='p', name='software_fixture', sequences=[{'id':'x', 'sequence':'MAGSGS'}]))
    workflow = recommend(old, 'fusion_screen')
    binding = plan_binding(old, workflow)
    engine = WorkflowEngine(store, builtin_tools(), tmp_path / 'artifacts')
    barrier = Barrier(2)
    new = old.model_copy(update={'description':'changed'})
    def save():
        barrier.wait()
        return store.save_project(new, 1)
    def approve():
        barrier.wait()
        try:
            return engine.create_confirmed(binding, workflow)
        except WorkflowError as error:
            assert error.status_code == 409
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        saved = pool.submit(save)
        created = pool.submit(approve)
        run_id = created.result()
        assert saved.result().revision == 2
    if run_id is not None:
        snapshot = store.run(run_id)['snapshot']
        assert snapshot['project'] == old.model_dump(mode='json')
    assert store.project('p').revision == 2

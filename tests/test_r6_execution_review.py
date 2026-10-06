"""HTTP authorization and actual worker/state race oracles; software only."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier, Event
from time import sleep, monotonic

from fastapi.testclient import TestClient
import pytest

from workbench_fixture import fixture_app
from test_workbench_execution import engine, graph
from igem_drylab.workflow.models import Project, WorkflowError
from igem_drylab.workflow.scheduler import RunDispatcher


def wait(client,run_id,status):
    deadline=monotonic()+5
    while monotonic()<deadline:
        run=client.get(f"/api/platform/runs/{run_id}/summary").json()
        if run['status']==status:return run
        sleep(.02)
    raise AssertionError(run)


def proposal(client):
    result=client.post('/api/platform/proposals',json={'project_id':'software-fixture','goal':'scientific_pipeline','policy':{'max_completed_stages':1}})
    assert result.status_code==200,result.text
    return result.json()


def run_request(value):
    return {'project_id':value['project_id'],'workflow':value['workflow'],'confirmation':value['confirmation'],'proposal_id':value['id'],'request_id':value['id']}


def test_pause_cancel_is_terminal_repeatable_and_preserves_actual_artifacts(tmp_path):
    app=fixture_app(tmp_path)
    with TestClient(app) as client:
        value=proposal(client)
        assert client.post(f"/api/platform/proposals/{value['id']}/decision",json={'action':'accept'}).status_code==200
        run_id=client.post('/api/platform/runs',json=run_request(value)).json()['id']
        before=wait(client,run_id,'paused')
        for _ in range(2):
            cancelled=client.post(f'/api/platform/runs/{run_id}/control',json={'action':'cancel'})
            assert cancelled.status_code==200 and cancelled.json()['status']=='cancelled'
        assert client.post(f'/api/platform/runs/{run_id}/control',json={'action':'resume'}).status_code==409
        after=client.get(f'/api/platform/runs/{run_id}/summary').json()
        assert before['artifacts']==after['artifacts'] and app.state.fixture_calls==['m1']


@pytest.mark.parametrize('decision',[None,'reject'])
def test_omitting_proposal_id_or_changing_execution_type_cannot_skip_review(tmp_path,decision):
    app=fixture_app(tmp_path)
    with TestClient(app) as client:
        value=proposal(client)
        if decision:client.post(f"/api/platform/proposals/{value['id']}/decision",json={'action':decision})
        request=run_request(value)
        assert client.post('/api/platform/runs',json=request).status_code==409
        request.pop('proposal_id')
        assert client.post('/api/platform/runs',json=request).status_code==409
        request.update(execution_type='manual_review',manual_review_id=value['id'])
        assert client.post('/api/platform/runs',json=request).status_code==409
        assert app.state.fixture_calls==[] and app.state.platform_store.runs()==[]


def test_changed_tools_reject_old_review_and_clone_requires_new_acceptance(tmp_path):
    app=fixture_app(tmp_path)
    with TestClient(app) as client:
        value=proposal(client)
        assert client.post(f"/api/platform/proposals/{value['id']}/decision",json={'action':'accept'}).status_code==200
        run_id=client.post('/api/platform/runs',json=run_request(value)).json()['id']
        before=wait(client,run_id,'paused')
        tools=app.state.workflow_engine.tools
        old=tools.get('project.m2')
        tools._tools['project.m2']=replace(old,version='changed-software-fixture-version')
        assert client.post('/api/platform/runs',json=run_request(value)).status_code==409
        assert client.post(f'/api/platform/runs/{run_id}/control',json={'action':'resume'}).status_code==422
        cloned=client.post(f'/api/platform/runs/{run_id}/clone',json={})
        assert cloned.status_code==202,cloned.text
        draft=cloned.json()
        assert draft['status']=='proposed' and draft['source']=='run_clone'
        assert draft['previous_review_identity']!=draft['review_identity']
        assert len(app.state.platform_store.runs())==1 and app.state.fixture_calls==['m1']
        assert client.post('/api/platform/runs',json=run_request(draft)).status_code==409
        assert client.post(f"/api/platform/proposals/{draft['id']}/decision",json={'action':'accept'}).status_code==200
        started=client.post('/api/platform/runs',json=run_request(draft))
        assert started.status_code==202,started.text
        wait(client,started.json()['id'],'paused')
        assert client.get(f'/api/platform/runs/{run_id}/summary').json()['snapshot_hash']==before['snapshot_hash']
        assert app.state.fixture_calls==['m1','m1']


def test_queue_cancel_never_calls_the_waiting_handler(tmp_path):
    entered,release=Event(),Event()
    calls=[]
    def handler(value,context):
        calls.append(context.run_id);entered.set();assert release.wait(5)
        return {'kind':'software_fixture'}
    runtime=engine(tmp_path,handler,max_workers=1)
    dispatcher=RunDispatcher(runtime,controllers=1)
    first=runtime.create(Project(id='a',name='fixture'),graph(1))
    second=runtime.create(Project(id='b',name='fixture'),graph(1))
    dispatcher.submit(first)
    try:
        assert entered.wait(3)
        dispatcher.submit(second)
        runtime.store.control(second,'cancel')
        assert runtime.store.run(second)['status']=='cancelled'
    finally:release.set()
    deadline=monotonic()+5
    while dispatcher.state()['accepted_runs'] and monotonic()<deadline:sleep(.02)
    assert calls==[first] and runtime.store.run(second)['status']=='cancelled'


def test_manual_compatibility_requires_explicit_confirmation_record(tmp_path):
    app=fixture_app(tmp_path)
    with TestClient(app) as client:
        plan=client.post('/api/platform/plans',json={'project_id':'software-fixture','goal':'scientific_pipeline'}).json()
        request={'project_id':'software-fixture','workflow':plan['workflow'],'confirmation':plan['confirmation'],
            'execution_type':'manual_review','manual_review_id':plan['review_id']}
        assert client.post('/api/platform/runs',json=request).status_code==409
        assert client.post(f"/api/platform/proposals/{plan['review_id']}/decision",json={'action':'accept'}).status_code==200
        run=client.post('/api/platform/runs',json=request)
        assert run.status_code==202,run.text
        assert client.post('/api/platform/runs',json=request).json()['id']==run.json()['id']
        wait(client,run.json()['id'],'succeeded')
        actions=client.get('/api/platform/plan-actions?project_id=software-fixture').json()
        assert sum(item['action']=='manual_plan_confirmed' for item in actions)==1
        assert sum(item['action']=='execution_requested' for item in actions)==1
        assert app.state.fixture_calls==['m1','m2','m3','m4','m5']


def test_private_profile_change_invalidates_a_previously_accepted_proposal(tmp_path):
    from igem_drylab.workflow.runtime_profiles import RuntimeProfiles
    app=fixture_app(tmp_path)
    store=app.state.platform_store
    profiles=RuntimeProfiles(store)
    profiles.install('software-fixture-private-profile',{})
    project=store.project('software-fixture')
    store.save_project(project.model_copy(update={'runtime_profile_ref':'software-fixture-private-profile'}),project.revision)
    with TestClient(app) as client:
        value=proposal(client)
        assert 'software-fixture-private-profile' not in str(value)
        assert client.post(f"/api/platform/proposals/{value['id']}/decision",json={'action':'accept'}).status_code==200
        profiles.install('software-fixture-private-profile',{'fixture':{'enabled':False,'extra':{'mode':'updated'}}})
        assert client.post('/api/platform/runs',json=run_request(value)).status_code==409
        assert store.runs()==[] and app.state.fixture_calls==[]


def test_cancel_resume_race_cannot_resurrect_a_cancelled_run(tmp_path):
    runtime=engine(tmp_path,lambda value,context:{'kind':'fixture'})
    for index in range(8):
        run_id=runtime.create(Project(id=str(index),name='fixture'),graph(2,max_completed_stages=1))
        assert runtime.run(run_id)['status']=='paused'
        barrier=Barrier(2)
        def cancel():barrier.wait();runtime.store.control(run_id,'cancel')
        def resume():
            barrier.wait()
            try:runtime.store.clear_control(run_id)
            except WorkflowError as error:assert error.code=='run_is_terminal'
        with ThreadPoolExecutor(2) as pool:
            futures=[pool.submit(cancel),pool.submit(resume)]
            for future in futures:future.result()
        assert runtime.store.run(run_id)['status']=='cancelled'
        with pytest.raises(WorkflowError,match='run_is_terminal'):runtime.store.clear_control(run_id)

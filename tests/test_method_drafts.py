"""Formula document versions, not expression evaluation or scientific tests."""
from fastapi.testclient import TestClient
from workbench_fixture import fixture_app
from igem_drylab.workflow.methods import METHODS


def test_formula_draft_retains_original_and_is_immutable_unvalidated_not_executable(tmp_path):
    app=fixture_app(tmp_path)
    method=METHODS['m3-s1-e10']
    formula=next(item for item in method.formulas if item.id=='E2')
    with TestClient(app) as client:
        project=client.get('/api/platform/projects/software-fixture').json()
        request={'base_method_id':method.id,'base_version':method.version,'title':'SOFTWARE_FIXTURE version',
            'formula_id':'E2','latex':formula.latex+'+q','reason':'SOFTWARE_ONLY unknown term; not valid science',
            'source_reference':'User-authored SOFTWARE_ONLY','expected_project_revision':project['revision']}
        response=client.post('/api/platform/projects/software-fixture/method-drafts',json=request)
        assert response.status_code==200,response.text
        draft=response.json()
        assert draft['validation_status']=='unvalidated' and draft['executable'] is False
        assert draft['original_latex']==formula.latex and draft['latex']==request['latex']
        request['previous_id']=draft['id'];request['latex']=formula.latex+'+r'
        revised=client.post('/api/platform/projects/software-fixture/method-drafts',json=request).json()
        assert revised['version']==2 and revised['id']!=draft['id']
        versions=client.get('/api/platform/projects/software-fixture/method-drafts').json()['items']
        assert versions==[revised,draft]
        assert METHODS[method.id].formulas==method.formulas
        assert app.state.platform_store.project('software-fixture').revision==project['revision']
        assert app.state.platform_store.runs()==[] and app.state.fixture_calls==[]
        request['base_version']='not-original'
        assert client.post('/api/platform/projects/software-fixture/method-drafts',json=request).status_code==409

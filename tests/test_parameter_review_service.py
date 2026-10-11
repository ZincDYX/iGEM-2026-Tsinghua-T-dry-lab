"""Explicit software-only review fixtures; no biological calculation/oracle."""
from fastapi.testclient import TestClient
from workbench_fixture import fixture_app
from igem_drylab.parameters import ParameterRecord
from igem_drylab.workflow.scientific_project import ScientificProject


def seed(app):
    store = app.state.platform_store
    project = store.project('software-fixture')
    science = ScientificProject.model_validate(project.scientific_project)
    old = ParameterRecord(parameter_id='original',name='phi',value=.2,unit='1',parameter_type='phi',
        source_type='wetlab',source_reference='SOFTWARE_ONLY_NOT_EXPERIMENT',review_status='approved',approved_by='software fixture')
    candidate = old.model_copy(update={'parameter_id':'override','value':.3,'review_status':'extracted','approved_by':None,
        'supersedes':'original','parameter_version':2,'notes':'SOFTWARE_ONLY correction'})
    science.config.parameters = [old,candidate]
    project.scientific_project = science.model_dump(mode='json')
    return store.save_project(project,project.revision),old.model_dump(mode='json')


def test_explicit_review_uses_existing_unit_and_lineage_gate_and_retains_original_source(tmp_path):
    app = fixture_app(tmp_path)
    project,old = seed(app)
    from igem_drylab.workflow.parameter_edits import pending_replacements
    from igem_drylab.workflow.precheck import precheck
    before=ScientificProject.model_validate(project.scientific_project)
    assert [p.parameter_id for p in pending_replacements(before.config,'m3')]==['override']
    assert pending_replacements(before.config,'m4')==[]  # Not consumed here.
    assert any('parameter_override_requires_review' in row.reason_codes for row in precheck(project).missing)
    with TestClient(app) as client:
        response = client.post('/api/platform/projects/software-fixture/parameters/override/review',json={
            'stage':'m3','requirement_name':'phi','reviewer':'software reviewer','reason':'SOFTWARE_ONLY declared fixture review','expected_revision':project.revision})
        assert response.status_code == 200,response.text
        saved = response.json()
        parameters = saved['scientific_project']['config']['parameters']
        assert parameters[0] == old
        assert parameters[1]['review_status'] == 'approved' and parameters[1]['approved_by'] == 'software reviewer'
        assert parameters[1]['supersedes'] == 'original' and parameters[1]['value'] == .3
        assert saved['revision'] == project.revision+1
        from igem_drylab.parameters import ParameterRegistry,resolve_requirement
        from igem_drylab.parameters.requirements import requirements_for_stage
        config=ScientificProject.model_validate(app.state.platform_store.project(project.id).scientific_project).config
        requirement=next(r for r in requirements_for_stage(config,'m3') if r.name=='phi')
        resolved=resolve_requirement(ParameterRegistry(config.parameters),requirement,config.experimental_context,allow_assumptions=False)
        assert resolved.selected_parameter.parameter_id=='override' and resolved.canonical_value==.3
        assert pending_replacements(config,'m3')==[]
        assert app.state.fixture_calls == [] and app.state.fixture_client.calls == 0
        assert client.post('/api/platform/projects/software-fixture/parameters/override/review',json={
            'stage':'m3','requirement_name':'phi','reviewer':'software reviewer','reason':'SOFTWARE_ONLY repeat','expected_revision':project.revision}).status_code == 409


def test_wrong_unit_and_unknown_requirement_never_gain_approval(tmp_path):
    app = fixture_app(tmp_path)
    project,_ = seed(app)
    science = ScientificProject.model_validate(project.scientific_project)
    science.config.parameters[1].unit = 'uM'
    project.scientific_project = science.model_dump(mode='json')
    project = app.state.platform_store.save_project(project,project.revision)
    with TestClient(app) as client:
        request = {'stage':'m3','requirement_name':'phi','reviewer':'software reviewer','reason':'SOFTWARE_ONLY negative control','expected_revision':project.revision}
        assert client.post('/api/platform/projects/software-fixture/parameters/override/review',json=request).status_code == 422
        request['requirement_name'] = 'does_not_exist'
        assert client.post('/api/platform/projects/software-fixture/parameters/override/review',json=request).status_code == 422
        saved = app.state.platform_store.project('software-fixture')
        assert saved.revision == project.revision
        assert saved.scientific_project['config']['parameters'][1]['review_status'] == 'extracted'


def test_saved_parameter_raw_value_and_source_cannot_be_overwritten_via_project_api(tmp_path):
    app=fixture_app(tmp_path)
    project,_=seed(app)
    with TestClient(app) as client:
        public=client.get('/api/platform/projects/software-fixture').json()
        public['scientific_project']['config']['parameters'][0]['value']=9.0
        response=client.post('/api/platform/projects',json={'project':public,'expected_revision':project.revision})
        assert response.status_code==409,response.text
        assert app.state.platform_store.project(project.id).revision==project.revision
        public['scientific_project']['config']['parameters'][0]['value']=.2
        public['scientific_project']['config']['parameters'][0]['source_reference']='CHANGED_SOURCE'
        assert client.post('/api/platform/projects',json={'project':public,'expected_revision':project.revision}).status_code==409

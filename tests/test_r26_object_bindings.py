"""Source/model ownership and metadata tests, never a numerical executor."""
from fastapi.testclient import TestClient
from workbench_fixture import fixture_app
from igem_drylab.workflow.custom_formula import custom_formula_tool
from igem_drylab.workflow.methods import METHODS,MethodDraftInput


def test_iteration_copies_the_frozen_owned_formula_not_latest_project_draft(tmp_path):
    app=fixture_app(tmp_path)
    service=app.state.application
    service.tools.register(custom_formula_tool())
    project=service.store.project('software-fixture')
    baseline=METHODS['m3-s1-e10']
    request=MethodDraftInput(base_method_id=baseline.id,base_version=baseline.version,formula_id='E1',
        title='SOFTWARE_ONLY frozen binding',latex='x/(k+x)',reason='Metadata only; never executed',
        source_reference='SOFTWARE_ONLY',expected_project_revision=project.revision,
        execution_spec={'expression':'x/(k+x)','output_unit':'1','variables':{
            'x':{'value':.5,'unit':'uM','source':'SOFTWARE_ONLY'},'k':{'value':.5,'unit':'uM','source':'SOFTWARE_ONLY'}}})
    old=service.method_drafts.save(project.id,request)
    workflow=service.method_drafts.workflow(project.id,old.id)
    run_id=app.state.workflow_engine.create(project,workflow)  # Freeze only, no job execution.
    frozen=service.store.run(run_id)
    revised=request.model_copy(deep=True)
    revised.previous_id=old.id
    revised.execution_spec.variables['k'].value=1.5
    latest=service.method_drafts.save(project.id,revised)
    project.name='Newer unrelated project draft'
    service.store.save_project(project,project.revision)
    with TestClient(app) as client:
        response=client.post(f'/api/platform/runs/{run_id}/iteration')
        assert response.status_code==200,response.text
        value=response.json()
        copy=value['workflow']['nodes'][0]['inputs']
        assert copy['spec']['value']['variables']['k']['value']==.5
        assert copy['method_version']['value']==1
        assert copy['method_id']['value'] not in {old.id,latest.id}
        owned=service.method_drafts.get(value['project']['id'],copy['method_id']['value'])
        assert owned.execution_spec.variables['k'].value==.5 and owned.project_id==value['project']['id']
        assert value['project']['name']=='SOFTWARE_FIXTURE · 非科学计算 · iteration'
        doc=client.post(f"/api/platform/projects/{value['project']['id']}/workflow-documents/copied",json={
            'workflow':value['workflow'],'expected_project_revision':1})
        assert doc.status_code==200,doc.text
        shown=client.get(f"/api/platform/projects/{value['project']['id']}/module-method",params={
            'workflow_id':'copied','node_id':'formula','tool_id':'workflow.custom_formula'})
        assert shown.status_code==200,shown.text
        assert shown.json()['scalar_method']['execution_spec']['variables']['k']['value']==.5
    assert service.store.run(run_id)['snapshot']==frozen['snapshot']
    assert service.method_drafts.get(project.id,latest.id).execution_spec.variables['k'].value==1.5
    assert app.state.fixture_calls==[]


def test_fasta_parent_retains_record_count_and_restricts_sequence_text_to_selected_record(tmp_path):
    app=fixture_app(tmp_path)
    application=app.state.application
    client=TestClient(app)
    project=application.store.project('software-fixture')
    raw=b'>one\nMKWVTFISLL\n>two\nGGGGSSSSPP\n'
    transaction=application.imports.preview(project.id,[('proteins.faa',raw)]).id
    revised=client.patch(f'/api/platform/projects/{project.id}/imports/{transaction}',json={
        'options':{'proteins.faa':{'molecule_type':'protein'}},'expected_revision':project.revision})
    assert revised.status_code==200,revised.text
    committed=client.post(f'/api/platform/projects/{project.id}/imports/{transaction}/commit',json={'choices':{}})
    assert committed.status_code==200,committed.text
    saved=committed.json()
    file=saved['files'][0]
    parent=next(row for row in saved['datasets'] if row['file_id']==file['id'])
    assert len(parent['records'])==2 and all('sequence' not in row for row in parent['records'])
    route=f"/api/platform/files/{file['id']}/sequence-records"
    page=client.get(route,params={'project_id':project.id}).json()
    assert page['total']==2 and all(row['sequence'] is None for row in page['records'])
    page=client.get(route,params={'project_id':project.id,'record_id':'two'}).json()
    assert next(row for row in page['records'] if row['id']=='two')['sequence']=='GGGGSSSSPP'
    assert next(row for row in page['records'] if row['id']=='one')['sequence'] is None
    unrelated=application.create_project('Other software fixture')
    assert client.get(route,params={'project_id':unrelated['id']}).status_code==403
    assert application.store.runs()==[]

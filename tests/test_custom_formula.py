"""AST admission locally; all numerical/executor tests run on the server only."""
import pytest
from pydantic import ValidationError
from igem_drylab.workflow.custom_formula import FormulaSpec, FormulaExecution, run_formula, custom_formula_tool


def spec(expression='x/(k+x)',output='1'):
    return FormulaSpec(expression=expression,output_unit=output,variables={
        'x':{'value':500,'unit':'nM','source':'Synthetic analytic oracle; not biological data'},
        'k':{'value':.5,'unit':'uM','source':'Synthetic analytic oracle; not biological data'}})


@pytest.mark.parametrize('expression',[
    '__import__("os").system("whoami")','x.real','x[0]','[x for x in k]',
    '(lambda: x)()','x**k','exp(x)','x+k+1','x**1000000000',
    'x if k else x','open("data")','x//k','(x,k)','x > k','True','1e309',
    '9'*400,
])
def test_reject_unexecutable_syntax_units_and_unbounded_exponents(expression):
    with pytest.raises(ValidationError): spec(expression)


def test_admission_output_units_and_unused_variables():
    assert spec().output_unit=='1'
    with pytest.raises(ValidationError): spec(output='uM')
    with pytest.raises(ValidationError): spec('x',output='uM')
    with pytest.raises(ValidationError): spec('x+k',output='unsupported')


def test_save_prepare_freezes_owned_version_without_creating_jobs(tmp_path):
    from fastapi.testclient import TestClient
    from workbench_fixture import fixture_app
    from igem_drylab.workflow.methods import METHODS
    app=fixture_app(tmp_path)
    app.state.application.tools.register(custom_formula_tool())
    method=METHODS['m3-s1-e10']
    with TestClient(app) as client:
        request={'base_method_id':method.id,'base_version':method.version,'formula_id':'E1',
            'title':'Exploratory synthetic ratio','latex':'x/(k+x)','reason':'Unit conversion test, no biological claim',
            'source_reference':'Independent algebra oracle','expected_project_revision':1,'execution_spec':spec().model_dump()}
        response=client.post('/api/platform/projects/software-fixture/method-drafts',json=request)
        assert response.status_code==200,response.text
        draft=response.json()
        assert draft['executable'] and draft['validation_status']=='unvalidated'
        url=f"/api/platform/projects/software-fixture/method-drafts/{draft['id']}/workflow"
        prepared=client.post(url,json={})
        assert prepared.status_code==200,prepared.text
        frozen=prepared.json()['nodes'][0]['inputs']['spec']['value']
        assert frozen==request['execution_spec']
        assert client.post(url.replace('software-fixture','not-owned'),json={}).status_code in {403,404}
        request['previous_id']=draft['id'];request['execution_spec']['variables']['x']['value']=1000
        revised=client.post('/api/platform/projects/software-fixture/method-drafts',json=request)
        assert revised.status_code==200,revised.text
        assert revised.json()['version']==2
        assert client.post(url,json={}).json()['nodes'][0]['inputs']['spec']['value']==frozen
        assert app.state.platform_store.runs()==[] and app.state.fixture_calls==[]


@pytest.mark.scientific_algorithm
def test_numeric_independent_unit_conversion_oracle_and_durable_engine(tmp_path):
    from igem_drylab.workflow.store import WorkflowStore
    from igem_drylab.workflow.engine import WorkflowEngine
    from igem_drylab.workflow.tools import WorkflowTools
    from igem_drylab.workflow.models import Project,Workflow,WorkflowNode,LiteralInput
    tools=WorkflowTools();tools.register(custom_formula_tool())
    store=WorkflowStore(tmp_path/'state.sqlite3')
    project=store.save_project(Project(id='analytic-oracle',name='Synthetic math; no biological claim'))
    payload=FormulaExecution(method_id='synthetic-v1',method_version=1,title='Analytic oracle',base_method_id='m3-s1-e10',
        base_version='separate-custom',latex='x/(k+x)',reason='No biological claim',source_reference='Exact ratio 500nM/(500nM+500nM)=1/2',spec=spec())
    workflow=Workflow(id='analytic',name='Unit oracle',nodes=[WorkflowNode(id='formula',label='Ratio',tool_id='workflow.custom_formula',
        inputs={k:LiteralInput(value=v) for k,v in payload.model_dump(mode='json').items()})])
    engine=WorkflowEngine(store,tools,tmp_path/'artifacts')
    run_id=engine.create(project,workflow)
    engine.run(run_id)
    # Re-open the actual durable database/engine, not an in-memory mock.
    reloaded=WorkflowStore(tmp_path/'state.sqlite3')
    result=reloaded.run(run_id)
    assert result['status']=='succeeded'
    output=result['nodes'][0]['output']
    assert output['value']==pytest.approx(.5,rel=1e-14)
    assert output['unit']=='1' and not output['evidence_ready']
    assert output['validation_status']=='unvalidated' and output['method']==payload.model_dump(mode='json')
    assert all(node.tool_id not in {'project.m1','project.m2','project.m3','project.m4'} for node in workflow.nodes)


@pytest.mark.scientific_algorithm
def test_actual_application_accept_start_and_reload_custom_result(tmp_path):
    from igem_drylab.software.application import ApplicationService
    from igem_drylab.workflow.methods import MethodDraftInput, METHODS
    from igem_drylab.workflow.models import WorkflowError
    service=ApplicationService(tmp_path)
    project=service.create_project('Independent scalar oracle; no biology')
    method=METHODS['m3-s1-e10']
    originals={key:value.model_dump() for key,value in METHODS.items()}
    draft=service.method_drafts.save(project['id'],MethodDraftInput(base_method_id=method.id,
        base_version=method.version,formula_id='E1',title='Scalar ratio',latex='x/(k+x)',
        reason='Synthetic scalar oracle',source_reference='500nM/(500nM+500nM)=1/2',
        expected_project_revision=project['revision'],execution_spec=spec()))
    workflow=service.method_drafts.workflow(project['id'],draft.id)
    proposal=service.planning.custom(project['id'],workflow,'Review synthetic scalar inputs')
    with pytest.raises(WorkflowError,match='accepted_proposal_binding_required'):
        service.run_approved(proposal.id)
    assert service.store.runs()==[]
    service.planning.decide(proposal.id,'accept')
    completed=service.run_approved(proposal.id)
    assert completed['status']=='succeeded'
    other=ApplicationService(tmp_path)
    run=other.store.run(completed['id'])
    assert run['nodes'][0]['output']['value']==pytest.approx(.5,rel=1e-14)
    assert run['nodes'][0]['output']['evidence_ready'] is False
    assert originals=={key:value.model_dump() for key,value in METHODS.items()}
    assert other.method_drafts.list(project['id']).items[0].id==draft.id


@pytest.mark.scientific_algorithm
@pytest.mark.parametrize('expression,unit,expected',[
    ('x+k','nM',1000),('x/k','1',1),('sqrt(x/k)','1',1),
    ('exp(x/k)','1',2.718281828459045),('ln(x/k)','1',0),
    ('log10(x/k)','1',0),('x**2/k','uM',.5),('abs(-x)+k','uM',1),
])
def test_scalar_function_independent_oracles(tmp_path,expression,unit,expected):
    from igem_drylab.workflow.tools import NodeContext
    payload=FormulaExecution(method_id='analytic',method_version=1,title='Math oracle',base_method_id='m3-s1-e10',
        base_version='custom',latex=expression,reason='Synthetic',source_reference='Analytic scalar identities',spec=spec(expression,unit))
    assert run_formula(payload,NodeContext('run','node',tmp_path))['value']==pytest.approx(expected,rel=1e-14,abs=1e-14)


@pytest.mark.scientific_algorithm
@pytest.mark.parametrize('expression',['x/(k-k)','sqrt(-x/k)','ln(-x/k)','exp(1000*x/k)'])
def test_domain_errors_are_not_results(tmp_path,expression):
    from igem_drylab.workflow.tools import NodeContext
    payload=FormulaExecution(method_id='domain',method_version=1,title='Domain oracle',base_method_id='m3-s1-e10',
        base_version='custom',latex=expression,reason='Synthetic',source_reference='Undefined real-domain cases',spec=spec(expression))
    with pytest.raises(ValueError,match='formula_domain_or_nonfinite_result'):
        run_formula(payload,NodeContext('run','node',tmp_path))

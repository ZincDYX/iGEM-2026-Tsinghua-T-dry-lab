"""Software editor/ledger tests; no scientific kernels or external jobs run."""
import pytest
from fastapi.testclient import TestClient
from pydantic import Field

from igem_drylab.software.application import ApplicationService
from igem_drylab.software.dashboard import create_app
from igem_drylab.workflow.documents import WorkflowDocumentInput
from igem_drylab.workflow.models import Contract, Workflow, WorkflowError
from igem_drylab.workflow.store import plan_binding
from igem_drylab.workflow.tools import ToolDefinition, WorkflowTools
from igem_drylab.workflow.mcp_bridge import McpArguments


class Input(Contract):
    amount: float = Field(ge=0)


def app(tmp_path):
    tools = WorkflowTools()
    tools.register(ToolDefinition('real.contract', 'Declared test contract', 'Software contract fixture, not a scientific tool', '1', Input,
        lambda *_: pytest.fail('Editing must not execute tools'), 'test', output_schema={'type': 'object', 'properties': {'amount': {'type': 'number'}, 'name': {'type': 'string'}}, 'additionalProperties': False}))
    application = ApplicationService(tmp_path, workflow_tools=tools)
    application.create_project('Study')
    project = application.store.projects()[0]
    workflow = Workflow.model_validate({'id': 'study', 'name': 'Study', 'nodes': [
        {'id': 'a', 'label': 'A', 'tool_id': 'real.contract', 'inputs': {'amount': {'kind': 'literal', 'value': 3}}},
        {'id': 'b', 'label': 'B', 'tool_id': 'real.contract', 'inputs': {'amount': {'kind': 'node', 'node_id': 'a', 'path': ['amount']}}},
        {'id': 'c', 'label': 'C', 'tool_id': 'real.contract', 'inputs': {'amount': {'kind': 'node', 'node_id': 'a', 'path': ['amount']}}},
    ]})
    return application, project['id'], workflow


def save(application, project_id, workflow, **changes):
    request = {'workflow': workflow.model_dump(mode='json'), 'expected_project_revision': 1, **changes}
    return application.workflow_documents.save(project_id, 'editor', WorkflowDocumentInput.model_validate(request))


def test_layout_selection_view_recover_and_do_not_change_scientific_binding(tmp_path):
    application, project_id, workflow = app(tmp_path)
    project = application.store.project(project_id)
    binding = plan_binding(project, workflow)
    first = save(application, project_id, workflow, layout={'a': {'x': 40, 'y': 30}})
    second = save(application, project_id, workflow, expected_revision=first.revision, layout={'a': {'x': 800, 'y': 400}}, selected_node_id='c', view='list')
    layout_only = WorkflowDocumentInput(expected_revision=second.revision, expected_project_revision=1,
        layout=second.layout, selected_node_id='c', view='list')
    assert application.workflow_documents.save(project_id, 'editor', layout_only) == second
    reopened = ApplicationService(tmp_path, workflow_tools=application.tools).workflow_documents.get(project_id, 'editor')
    assert reopened == second
    assert reopened.semantic_revision == 1 and reopened.layout_revision == 2
    assert reopened.selected_node_id == 'c' and reopened.view == 'list'
    assert reopened.layout['a'].x == 800
    assert plan_binding(project, reopened.workflow) == binding
    assert len(application.workflow_documents.list(project_id)) == 1
    with application.store.connection() as db:
        assert db.execute('SELECT COUNT(*) FROM workflow_documents').fetchone()[0] == 1
        assert db.execute('SELECT COUNT(*) FROM workflow_definitions').fetchone()[0] == 1
        assert 'workflow' not in db.execute('SELECT state FROM workflow_documents').fetchone()[0]
        assert db.execute('SELECT COUNT(*) FROM runs').fetchone()[0] == 0


def test_semantic_edit_is_new_revision_old_approval_and_history_are_not_reused(tmp_path):
    application, project_id, workflow = app(tmp_path)
    first = save(application, project_id, workflow)
    reviewed = application.planning.custom(project_id, workflow, 'Review original', source='validated_template')
    reviewed = application.planning.decide(reviewed.id, 'accept')
    changed = workflow.model_copy(deep=True)
    changed.nodes[0].inputs['amount'].value = 9
    second = save(application, project_id, changed, expected_revision=first.revision)
    assert second.semantic_revision == 2 and second.layout_revision == 1
    with pytest.raises(WorkflowError, match='accepted_proposal_binding_required'):
        application.planning.authorize_run(reviewed.id, reviewed.confirmation, changed)
    with application.store.connection() as db:
        original = db.execute('SELECT workflow FROM workflow_definitions WHERE semantic_revision=1').fetchone()[0]
        assert '"value":3' in original and '"value":9' not in original


@pytest.mark.parametrize('defect,code', [
    ('cycle', 'workflow_cycle'), ('remove', 'unknown_dependency'), ('type', 'workflow_reference_type_mismatch'),
    ('unknown_tool', 'unknown_tool'), ('literal', 'workflow_input_value_or_project_binding_invalid'),
    ('missing_input', 'workflow_required_input_argument_missing'), ('field', 'workflow_output_field_not_declared'),
])
def test_bad_edits_rejected_without_mutation_or_execution(tmp_path, defect, code):
    application, project_id, workflow = app(tmp_path)
    first = save(application, project_id, workflow)
    data = workflow.model_dump(mode='json')
    if defect == 'cycle': data['nodes'][0]['depends_on'] = ['b']
    elif defect == 'remove': data['nodes'].pop(0)
    elif defect == 'type': data['nodes'][1]['inputs']['amount']['path'] = ['name']
    elif defect == 'unknown_tool': data['nodes'][0]['tool_id'] = 'missing'
    elif defect == 'literal': data['nodes'][0]['inputs']['amount']['value'] = 'not-a-number'
    elif defect == 'missing_input': data['nodes'][0]['inputs'] = {}
    elif defect == 'field': data['nodes'][1]['inputs']['amount']['path'] = ['unknown']
    # Refresh the declared allow-list for this fixture's unknown-tool case.
    data['execution_policy']['allowed_tools'] = sorted({node['tool_id'] for node in data['nodes']})
    with pytest.raises(ValueError, match=code):
        save(application, project_id, Workflow.model_validate(data), expected_revision=first.revision)
    assert application.workflow_documents.get(project_id, 'editor') == first


def test_concurrent_edits_and_stale_project_do_not_overwrite(tmp_path):
    application, project_id, workflow = app(tmp_path)
    first = save(application, project_id, workflow)
    save(application, project_id, workflow, expected_revision=first.revision, view='list')
    with pytest.raises(WorkflowError, match='workflow_document_revision_conflict'):
        save(application, project_id, workflow, expected_revision=first.revision, view='graph')
    project = application.store.project(project_id)
    application.save_project(project, project.revision)
    with pytest.raises(WorkflowError, match='workflow_project_revision_changed'):
        save(application, project_id, workflow, expected_revision=2)


def test_API_documents_are_project_scoped_and_reopen(tmp_path):
    client = TestClient(create_app(data_dir=tmp_path, deployment_mode='development', discover_tools=False))
    for project_id in ('p', 'q'):
        assert client.post('/api/platform/projects', json={'project': {'id': project_id, 'name': project_id}}).status_code == 200
    workflow = {'id': 'workflow', 'name': 'Empty gather', 'nodes': [{'id': 'gather', 'label': 'Gather', 'tool_id': 'workflow.gather', 'inputs': {'results': {'kind': 'literal', 'value': []}}}]}
    payload = {'workflow': workflow, 'expected_project_revision': 1}
    saved = client.post('/api/platform/projects/p/workflow-documents/editor', json=payload)
    assert saved.status_code == 200, saved.text
    assert client.get('/api/platform/projects/q/workflow-documents/editor').status_code == 404
    assert client.get('/api/platform/projects/q/workflow-documents').json() == []
    reopened = TestClient(create_app(data_dir=tmp_path, deployment_mode='development', discover_tools=False))
    assert reopened.get('/api/platform/projects/p/workflow-documents/editor').json() == saved.json()
    payload['expected_revision'] = 1
    payload['workflow']['nodes'][0]['tool_id'] = 'not.installed'
    payload['workflow']['execution_policy'] = {'allowed_tools': ['not.installed']}
    error = client.post('/api/platform/projects/p/workflow-documents/editor', json=payload)
    assert error.status_code == 422 and error.json()['detail']['code'] == 'unknown_tool'
    assert 'not registered' in error.json()['detail']['message']
    cyclic={'workflow':{'id':'cycle','name':'Cycle','nodes':[
        {'id':name,'label':name,'tool_id':'workflow.gather','inputs':{'results':{'kind':'literal','value':[]}},'depends_on':[other]}
        for name,other in [('a','b'),('b','a')]]},'expected_project_revision':1}
    cycle=client.post('/api/platform/projects/p/workflow-documents/new',json=cyclic)
    assert cycle.status_code==422 and cycle.json()['detail']['code']=='workflow_cycle'
    assert 'circular dependency' in cycle.json()['detail']['message']


def test_MCP_native_schema_not_empty_transport_wrapper_controls_editor(tmp_path):
    application, project_id, _ = app(tmp_path)
    application.tools.register(ToolDefinition('mcp.fixture', 'MCP schema fixture', 'Software metadata only', '1', McpArguments,
        lambda *_: pytest.fail('Metadata validation must not submit an MCP call'), 'test', input_schema={
            'type': 'object', 'properties': {'sequence': {'type': 'string', 'minLength': 1}},
            'required': ['sequence'], 'additionalProperties': False}))
    workflow = Workflow.model_validate({'id': 'mcp', 'name': 'MCP contract', 'nodes': [{'id': 'mcp', 'label': 'MCP',
        'tool_id': 'mcp.fixture', 'inputs': {'sequence': {'kind': 'literal', 'value': 'MKWV'}}}]})
    document = save(application, project_id, workflow)
    workflow.nodes[0].inputs['sequence'].value = 42
    with pytest.raises(WorkflowError, match='workflow_input_value_or_project_binding_invalid'):
        save(application, project_id, workflow, expected_revision=document.revision)


def test_CLI_and_Web_use_the_same_document_and_new_review_after_semantic_edit(tmp_path):
    import json
    from typer.testing import CliRunner
    from igem_drylab.software.cli import app as cli
    application=ApplicationService(tmp_path)
    project=application.store.project(application.create_project('CLI graph metadata')['id'])
    workflow=Workflow.model_validate({'id':'cli-graph','name':'No science executed','nodes':[
        {'id':name,'label':name.upper(),'tool_id':'workflow.gather','inputs':{'results':{'kind':'literal','value':[]}},'depends_on':deps}
        for name,deps in [('a',[]),('b',['a']),('c',['a'])]]})
    proposal=application.planning.custom(project.id,workflow,'Software workflow review')
    runner=CliRunner()
    prefix=['--data-dir',str(tmp_path),'--json','workflow']
    created=runner.invoke(cli,[*prefix,'draft',proposal.id])
    assert created.exit_code==0,created.output
    document=json.loads(created.output)
    assert document['workflow']['nodes'][1]['depends_on']==['a']
    repeated=runner.invoke(cli,[*prefix,'draft',proposal.id])
    assert json.loads(repeated.output)==document
    rejected=runner.invoke(cli,[*prefix,'edit',proposal.id,'--project',project.id,'--upstream','c','--downstream','a'])
    assert rejected.exit_code==2
    assert json.loads(rejected.output)['code']=='workflow_cycle'
    assert application.workflow_documents.get(project.id,proposal.id).semantic_revision==1
    removed=runner.invoke(cli,[*prefix,'edit',proposal.id,'--project',project.id,'--remove','c'])
    assert removed.exit_code==0,removed.output
    changed=json.loads(removed.output)
    assert changed['semantic_revision']==2 and [n['id'] for n in changed['workflow']['nodes']]==['a','b']
    reviewed=runner.invoke(cli,[*prefix,'review-draft',proposal.id,'--project',project.id])
    assert reviewed.exit_code==0,reviewed.output
    reviewed=json.loads(reviewed.output)
    assert reviewed['status']=='proposed' and reviewed['id']!=proposal.id
    assert reviewed['workflow']==changed['workflow']
    assert application.store.runs(project.id)==[]

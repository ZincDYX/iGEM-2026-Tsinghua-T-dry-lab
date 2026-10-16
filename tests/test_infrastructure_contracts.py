"""Infrastructure behavior only; no scientific calculator or external model."""
import json
import pytest
from igem_drylab.workflow.models import Workflow, WorkflowNode, NodeInput, MapSpec
from igem_drylab.workflow.plugins import PluginManager
from igem_drylab.workflow.store import WorkflowStore
from igem_drylab.workflow.tools import WorkflowTools


def test_shared_source_hash_is_computed_once_per_review_but_never_reused_across_reviews(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from hashlib import sha256
    from igem_drylab.workflow import engine
    source=tmp_path/'fixture.py'
    source.write_bytes(b'SOFTWARE_FIXTURE_ONE')
    monkeypatch.setattr(engine.inspect,'getsourcefile',lambda handler:str(source))
    calls=[]
    monkeypatch.setattr(engine,'sha256',lambda raw:calls.append(raw) or sha256(raw))
    definition=SimpleNamespace(handler=object(),implementation_files=())
    files,hashes={},{}
    for _ in range(10):
        assert engine.WorkflowEngine._implementation_hash(definition,files,hashes)==sha256(source.read_bytes()).hexdigest()
    assert len(calls)==1
    source.write_bytes(b'SOFTWARE_FIXTURE_TWO')
    assert engine.WorkflowEngine._implementation_hash(definition,{}, {})==sha256(source.read_bytes()).hexdigest()
    assert len(calls)==2


def test_dependency_closure_includes_bindings_maps_and_explicit_fanin_without_reordering():
    nodes = [WorkflowNode(id='root', label='root', tool_id='fixture'),
             WorkflowNode(id='left', label='left', tool_id='fixture', inputs={'item':NodeInput(node_id='root')}),
             WorkflowNode(id='right', label='right', tool_id='fixture', map=MapSpec(items=NodeInput(node_id='root'))),
             WorkflowNode(id='join', label='join', tool_id='fixture', depends_on=['left','right']),
             WorkflowNode(id='independent', label='independent', tool_id='fixture')]
    workflow = Workflow(id='fixture', name='software only', nodes=nodes)
    assert workflow.required_nodes('join') == {'root','left','right','join'}
    assert workflow.required_nodes('left') == {'root','left'}
    assert workflow.required_nodes() == {node.id for node in nodes}
    assert [node.id for node in workflow.nodes] == ['root','left','right','join','independent']


def test_plugin_inventory_retains_default_enabled_disabled_and_explicit_enabled(tmp_path):
    store=WorkflowStore(tmp_path/'ledger.sqlite')
    manager=PluginManager(tmp_path/'plugins',store,WorkflowTools())
    with store.connection() as db:
        for digest in ('default','disabled','enabled'):
            db.execute('INSERT INTO plugins VALUES(?,?)',(digest,json.dumps({'hash':digest,'manifest':{'name':digest}})))
        db.executemany('INSERT INTO plugin_enabled VALUES(?,?)',[('disabled',0),('enabled',1)])
    assert manager.installed() == [
        {'hash':'default','manifest':{'name':'default'},'enabled':True},
        {'hash':'disabled','manifest':{'name':'disabled'},'enabled':False},
        {'hash':'enabled','manifest':{'name':'enabled'},'enabled':True}]


@pytest.mark.parametrize('function,arguments,expected',[
    ('m1_compute_features',{'sequence':'fixture'}, {'sequence':'fixture','forbidden_amino_acid_motifs':[]}),
    ('m1_validate_construct_sequence',{'construct_id':'fixture','ordered_part_ids':[],'part_sequences':{},'require_sequence_evidence':False},
     {'construct_id':'fixture','ordered_part_ids':[],'part_sequences':{},'require_sequence_evidence':False}),
    ('m2_calculate_geometry',{'reference_pdb':'a','model_pdb':'b','reference_chain':'A','model_chain':'B',
      'core_residues':[],'pocket_residues':[],'clash_cutoff_angstrom':0},
     {'reference_pdb':'a','model_pdb':'b','reference_chain':'A','model_chain':'B',
      'core_residues':[],'pocket_residues':[],'clash_cutoff_angstrom':0}),
    ('audit_external_tool_deployment',{'config_path':'fixture','budget_bytes':None},
     {'config_path':'fixture','budget_bytes':None}),
])
def test_mcp_forwarding_preserves_false_zero_empty_values_and_optional_omission(monkeypatch,function,arguments,expected):
    from igem_drylab.mcp import server
    captured=[]
    monkeypatch.setattr(server,'_call_local',lambda name,payload:captured.append(payload) or {'fixture':True})
    assert getattr(server,function)(**arguments) == {'fixture':True}
    assert captured == [expected]

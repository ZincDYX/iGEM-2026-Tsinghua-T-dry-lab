"""DAG/ledger protocol tests; no authentic predictor is imitated."""
import pytest

from igem_drylab.workflow.builtins import builtin_tools, recommend
from igem_drylab.workflow.engine import WorkflowEngine
from igem_drylab.workflow.models import Project, SequenceRecord
from igem_drylab.workflow.store import WorkflowStore


@pytest.mark.integration
def test_original_method_fanout_cheap_veto_and_persistent_missing_evidence(tmp_path):
    project = Project(id="p", name="Explicit software fixture", sequences=[
        SequenceRecord(id="bad", sequence="LLLLLLLLLLLL", role="enzyme_ligand_linker"),
        SequenceRecord(id="short", sequence="GSGSGSGSGSGS", role="enzyme_ligand_linker"),
        SequenceRecord(id="long", sequence="GSTSSGGGGGSGGSGGSGGS", role="scaffold_linker"),
        SequenceRecord(id="untyped", sequence="GSAD")])
    store = WorkflowStore(tmp_path / "ledger.sqlite")
    engine = WorkflowEngine(store, builtin_tools(), tmp_path / "artifacts", max_workers=2)
    workflow = recommend(project, "m1_sequence_checks")
    decisions = next(node for node in workflow.nodes if node.id == "m1_decisions")
    assert decisions.dependencies() == {"m1_fields", "m1_iupred2a", "m1_seg", "m1_jpred", "m1_signalp", "m1_deeptmhmm", "m1_tango", "m1_pscore", "m1_catgranule",'m1_fuzdrop'}
    assert workflow.nodes[-1].dependencies() == {"m1_decisions"}
    run_id = engine.create(project, workflow)
    result = engine.run(run_id)
    assert result["status"] == "succeeded", result["nodes"]
    rows = next(row for row in result["nodes"] if row["id"] == "m1_decisions")["output"]["items"]
    assert [row["verdict"] for row in rows] == ["reject", "blocked", "blocked", "blocked"]
    predictor = next(row for row in result["nodes"] if row["id"] == "m1_iupred2a")["output"]["items"]
    assert predictor[0]["tool_status"] == "not_eligible"
    assert predictor[1]["tool_status"] == "not_configured"
    assert rows[2]["precheck"]["features"]["length"] == 20
    assert len(rows[1]["steps"]) == 5
    reopened = WorkflowStore(tmp_path / "ledger.sqlite").run(run_id)
    assert next(row for row in reopened["nodes"] if row["id"] == "m1_decisions")["output"]["items"] == rows


@pytest.mark.data_contract
def test_m1_screen_rejects_unregistered_file_bearing_observations(tmp_path):
    from igem_drylab.workflow.m1_checks import M1DecisionInput, decision, precheck, m1_workflow
    from igem_drylab.workflow.tools import NodeContext
    definition = m1_workflow().nodes[0].inputs
    payload = M1DecisionInput(item=SequenceRecord(id="x", sequence="GSGSGSGS", role="enzyme_ligand_linker"),
        feature_definitions=definition["feature_definitions"].value, rules=definition["rules"].value)
    context = NodeContext(run_id="r", node_id="n", work_dir=tmp_path)
    payload.prechecks = [precheck(payload, context)]
    with pytest.raises(ValueError, match="registered_upstream"):
        decision(payload, context)


@pytest.mark.data_contract
def test_construct_context_uses_declared_parts_not_arbitrary_substrings_and_retains_DNA_gaps(tmp_path):
    from igem_drylab.workflow.m1_checks import M1ConstructContextInput,bind_construct_contexts,m1_workflow
    definitions=m1_workflow(aggregation_exclusion_reference='user test exclusion').nodes[0].inputs
    payload=M1ConstructContextInput(constructs=[dict(id='fusion',parts=[
        dict(id='named_IDR',kind='idr',sequence='GSGS'),dict(id='tag',kind='tag',sequence='GG')],
        localization_context='cytosolic',sequence_source_ref='synthetic-source')],
        sequences=[dict(id='fusion',sequence='GSGSGG',role='full_fusion'),dict(id='unbound',sequence='SGSG',role='idr')],
        feature_definitions=definitions['feature_definitions'].value,rules=definitions['rules'].value)
    result=bind_construct_contexts(payload)['items'][0]
    assert [(p['part_id'],p['start_aa'],p['end_aa']) for p in result['part_bindings']]==[('named_IDR',1,4),('tag',5,6)]
    assert result['sequence_qc']['status']=='blocked'
    assert set(result['sequence_qc']['missing_inputs'])=={'sequenced_coding_dna','wetlab_forbidden_restriction_site_list'}
    assert result['fusion_screen']['verdict']=='blocked'
    assert 'SignalP_full_fusion_output' in result['fusion_screen']['missing_required_evidence']
    # Matching length or a coincidental substring never manufactures a part.
    assert len(result['part_bindings'])==2
    payload.sequences[0].sequence='GGGSGG'
    mismatched=bind_construct_contexts(payload)['items'][0]
    assert mismatched['fusion_screen'] is None
    assert mismatched['missing']==['declared_parts_do_not_match_registered_complete_construct']


@pytest.mark.integration
def test_construct_context_is_a_real_durable_DAG_predecessor_without_predictor_defaults(tmp_path):
    from igem_drylab.workflow.m1_checks import m1_workflow
    from igem_drylab.pipeline.config import ConstructDefinition
    project=Project(id='p',name='synthetic explicit source',sequences=[
        SequenceRecord(id='fusion',sequence='GSGSGG',role='full_fusion'),
        SequenceRecord(id='part',sequence='GSGS',role='enzyme_ligand_linker')])
    construct=ConstructDefinition(id='fusion',parts=[dict(id='p1',kind='enzyme_ligand_linker',sequence='GSGS'),
        dict(id='tag',kind='tag',sequence='GG')],localization_context='cytosolic',sequence_source_ref='synthetic')
    store=WorkflowStore(tmp_path/'ledger.sqlite')
    engine=WorkflowEngine(store,builtin_tools(),tmp_path/'artifacts',max_workers=2)
    workflow=m1_workflow(constructs=[construct],aggregation_exclusion_reference='synthetic excluded by fixture')
    node=next(n for n in workflow.nodes if n.id=='m1_decisions')
    assert 'm1_construct_contexts' in node.dependencies()
    result=engine.run(engine.create(project,workflow))
    assert result['status']=='succeeded',result
    bound=next(n for n in result['nodes'] if n['id']=='m1_construct_contexts')['output']['items'][0]
    assert bound['sequence_qc']['status']=='blocked' and bound['fusion_screen']['verdict']=='blocked'


@pytest.mark.integration
def test_construct_binding_real_stdio_transport_and_shared_implementation(tmp_path):
    import asyncio,sys
    from pathlib import Path
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters
    from igem_drylab.workflow.m1_checks import M1ConstructContextInput,bind_construct_contexts,m1_workflow
    inputs=m1_workflow().nodes[0].inputs
    request=M1ConstructContextInput(constructs=[],sequences=[],
        feature_definitions=inputs['feature_definitions'].value,rules=inputs['rules'].value)
    root=Path(__file__).resolve().parents[1]
    async def exercise():
        async with Client(StdioServerParameters(command=sys.executable,args=['-B','-m','igem_drylab.mcp.server'],
            cwd=root,env={'PYTHONPATH':str(root/'src')}),read_timeout_seconds=30) as client:
            result=await client.call_tool('igem.m1.bind_construct_contexts',{'payload':request.model_dump(mode='json')})
            assert not result.is_error
            assert result.structured_content['result']==bind_construct_contexts(request)
    asyncio.run(exercise())


@pytest.mark.data_contract
def test_native_context_reaches_part_screen_without_hiding_DNA_or_localization_gaps(tmp_path):
    from igem_drylab.fusion_tool_import import NativeFusionArtifact,FusionImportInput,import_fusion_tools
    from igem_drylab.workflow.m1_checks import (M1ConstructContextInput,bind_construct_contexts,
        screen_part_contexts,m1_workflow)
    from igem_drylab.constructs.linker_features import compute_sequence_features,screen_sequence_v3
    from hashlib import sha256
    sequence='GGGSSGGGSS';digest=sha256(sequence.encode()).hexdigest()
    sp=tmp_path/'signalp.txt';sp.write_text('# SignalP-6.0\n# ID\tPrediction\tOTHER\tSP(Sec/SPI)\tCS Position\nfixture\tOTHER\t0.99\t0.01\t\n')
    tm=tmp_path/'topologies.3line';tm.write_text('>fixture | GLOB\n'+sequence+'\nIIIIIIIIII\n')
    fusion=import_fusion_tools(FusionImportInput(sequence=sequence,artifacts=[
        NativeFusionArtifact(path=sp,format='signalp6_summary',tool_version='6.0',record_id='fixture'),
        NativeFusionArtifact(path=tm,format='deeptmhmm1_3line',tool_version='1.0',record_id='fixture')],
        reviewer='fixture',source_reference='synthetic_format_fixture_not_actual_job',output_dir=tmp_path/'import'))['fusion']
    inputs=m1_workflow(aggregation_exclusion_reference='explicit synthetic exclusion').nodes[0].inputs
    payload=M1ConstructContextInput(constructs=[dict(id='fusion',parts=[dict(id='source_part',kind='idr',sequence='GGGSS'),
        dict(id='tag',kind='tag',sequence='GGGSS')],localization_context='cytosolic',sequence_source_ref='synthetic')],
        sequences=[dict(id='fusion',sequence=sequence,role='full_fusion')],
        feature_definitions=inputs['feature_definitions'].value,rules=inputs['rules'].value,
        signalp_results=[dict(candidate_id='fusion',input_sequence_sha256=digest,parsed=fusion)])
    bound=bind_construct_contexts(payload)['items']
    features=compute_sequence_features('GGGSS',definitions=payload.feature_definitions,
        definitions_sha256=sha256(payload.feature_definitions.model_dump_json().encode()).hexdigest())
    screen=screen_sequence_v3(sequence='GGGSS',features=features,sequence_kind='idr',rules=payload.rules)
    contexts=screen_part_contexts(screen,'GGGSS',payload.rules,bound)
    assert len(contexts)==1
    assert [p['part_id'] for p in contexts[0]['part_occurrences']]==['source_part']
    assert 'SignalP_full_fusion_output' not in contexts[0]['screen']['missing_required_evidence']
    assert 'DeepTMHMM_full_fusion_output' not in contexts[0]['screen']['missing_required_evidence']
    assert contexts[0]['sequence_qc']['status']=='blocked'
    bound[0]['localization_context']='er_membrane'
    assert screen_part_contexts(screen,'GGGSS',payload.rules,bound)==[]

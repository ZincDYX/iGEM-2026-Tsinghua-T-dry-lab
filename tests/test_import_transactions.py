"""Actual parsers/store/API, independent record and ownership expectations.

Software format and approval tests only; no numerical solver runs here.
"""
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile
import pytest
from fastapi.testclient import TestClient
from igem_drylab.software.application import ApplicationService
from igem_drylab.software.dashboard import create_app
from igem_drylab.workflow.models import WorkflowError


def setup(tmp_path):
    application=ApplicationService(tmp_path/'workspace')
    project=application.create_project('Import acceptance')
    return application,project['id']


def test_ambiguous_fasta_revises_once_and_DNA_never_becomes_protein(tmp_path):
    app,project=setup(tmp_path)
    preview=app.imports.preview(project,[('design.fa',b'>design\nACGTACGT\n')])
    assert preview.items[0].records[0]['possible_molecule_types']==['DNA','protein']
    assert preview.items[0].issues[0].code=='molecule_type_required'
    with pytest.raises(WorkflowError,match='import_confirmation_required'):
        app.imports.commit(project,preview.id)
    assert not app.store.project(project).files
    # Restart the service: the original preview and immutable bytes survive.
    restarted=ApplicationService(app.data_dir)
    revised=restarted.imports.revise(project,preview.id,{'design.fa':{'molecule_type':'DNA'}})
    assert revised.items[0].records[0]['molecule_type']=='DNA'
    saved=restarted.imports.commit(project,preview.id)
    assert saved['revision']==2 and saved['sequences']==[]
    assert restarted.imports.commit(project,preview.id)['revision']==2
    assert restarted.imports.inspect(project,preview.id).state=='committed'


def test_duplicate_reuse_and_changed_revision_do_not_publish_partial_import(tmp_path):
    app,project=setup(tmp_path)
    source=('enzyme.faa',b'>e\nMKWVTFISLLFLFSSAYS\n')
    first=app.imports.preview(project,[source])
    saved=app.imports.commit(project,first.id)
    repeated=app.imports.preview(project,[source])
    assert repeated.items[0].duplicate_file_id==saved['files'][0]['id']
    with pytest.raises(WorkflowError,match='duplicate_import_choice_required'):
        app.imports.commit(project,repeated.id)
    reused=app.imports.commit(project,repeated.id,{'enzyme.faa':'reuse'})
    assert len(reused['files'])==1 and len(reused['sequences'])==1
    stale=app.imports.preview(project,[('other.faa',b'>other\nMKLLV\n')])
    current=app.store.project(project)
    app.store.save_project(current,current.revision)
    with pytest.raises(WorkflowError,match='project_revision_conflict'):
        app.imports.commit(project,stale.id)
    assert len(app.store.project(project).files)==1
    reviewed=app.imports.revise(project,stale.id,{},app.store.project(project).revision)
    assert reviewed.expected_revision==app.store.project(project).revision
    assert len(app.imports.commit(project,stale.id)['files'])==2


def test_BCIF_preserves_auth_label_insertion_and_never_calls_Bfactor_confidence(tmp_path):
    from test_r12_bcif_display import fixture_bytes
    app,project=setup(tmp_path)
    preview=app.imports.preview(project,[('model.bcif',fixture_bytes()),('sequence.faa',b'>real-source-id\nA\n')])
    structure=preview.items[0].records[0]
    assert structure['chains']==[
        {'model':str(model),'auth_chain':'B','label_chain':'X','coordinate_sequence':'A',
            'sequence_scope':'observed residues only; missing residues not inferred'} for model in (7,8)]
    assert structure['residue_identity_preview'][0]['auth_number']=='12'
    assert structure['residue_identity_preview'][0]['label_number']=='1'
    assert structure['residue_identity_preview'][0]['insertion']=='A'
    assert structure['confidence_semantics'] is None
    import struct
    # The independent IHM fixture encodes coordinates as IEEE Float32. Compare
    # that exact source value, not the pre-encoding Python Float64 literal.
    assert structure['coordinate_preview'][0]['x']==struct.unpack('<f',struct.pack('<f',11.123456789))[0]
    assert len(preview.proposed_links)==2
    assert all(link['status']=='proposed_not_scientific_approval' for link in preview.proposed_links)


def test_full_csv_shape_is_checked_beyond_preview_and_null_not_zero(tmp_path):
    app,project=setup(tmp_path)
    raw=b'time,value,replicate,censoring\n'+b'0,1,A,observed\n'*15+b'1,2,A,observed,WRONG\n'
    with pytest.raises(WorkflowError,match='table_row_budget_or_shape_invalid'):
        app.imports.preview(project,[('data.csv',raw)])
    good=app.imports.preview(project,[('data.csv',b'time,value,replicate,censoring\n0,,A,below_LOD\n1,0,B,observed\n')])
    mapped=app.imports.revise(project,good.id,{'data.csv':{'column_mapping':{
        'time':{'role':'time','unit':'h'},'value':{'role':'value','unit':'uM'},
        'replicate':{'role':'replicate'},'censoring':{'role':'censoring'}}}})
    table=mapped.items[0].records[0]
    assert table['row_count']==2
    assert table['row_preview'][0]['value']=='' and table['row_preview'][1]['value']=='0'
    assert table['columns'][1]['mapping']['unit']=='uM'


def test_zip_and_folder_use_same_records_with_no_uploaded_code_execution(tmp_path):
    app,project=setup(tmp_path)
    marker=tmp_path/'NOT_EXECUTED'
    source=[('study/enzyme.faa',b'>e\nMKWVTFISLLFLFSSAYS\n'),
        ('study/user.py',f'open({str(marker)!r},"w").write("wrong")'.encode())]
    folder=app.imports.preview(project,source)
    stream=BytesIO()
    with ZipFile(stream,'w') as archive:
        for name,raw in source: archive.writestr(name,raw)
    zipped=app.imports.preview(project,[('study.zip',stream.getvalue())])
    assert [(i.filename,i.semantic_type,i.records) for i in folder.items]==[(i.filename,i.semantic_type,i.records) for i in zipped.items]
    assert zipped.items[1].semantic_type=='EvidenceAttachment'
    assert not marker.exists()


def test_text_content_detects_FASTA_without_reinterpreting_uploaded_scripts(tmp_path):
    app,project=setup(tmp_path)
    view=app.imports.preview(project,[('data.txt',b'>source\nACGT\n'),('script.py',b'>source\nACGT\n')])
    assert view.items[0].detected_format=='FASTA'
    assert view.items[0].issues[0].code=='molecule_type_required'
    assert view.items[1].semantic_type=='EvidenceAttachment'


def test_project_config_relative_file_binds_without_manual_hash_and_no_M4_defaults_run(tmp_path):
    app,project=setup(tmp_path)
    config={'schema_version':'project-config-v1','config':{'inputs':{'protein_fasta':'proteins.faa','enzymes':[],'scaffolds':[],'linkers':[]},
        'execution':{'mode':'real','allow_assumptions':False},'prepared_through':'m1','run':{'output_dir':'outputs'}}}
    preview=app.imports.preview(project,[('study/project.json',json.dumps(config).encode()),
        ('study/proteins.faa',b'>e\nMKWVTFISLLFLFSSAYS\n')])
    item=preview.items[0]
    assert not item.issues
    assert item.proposed_links[0]['file_id']==preview.items[1].file['id']
    saved=app.imports.commit(project,preview.id)
    assert saved['scientific_project']['config']['prepared_through']=='m1'
    assert saved['scientific_project']['config']['inputs']['protein_fasta'].startswith('asset:')
    assert all(file['sha256'] for file in saved['scientific_project']['evidence_files'])
    assert app.store.project(project).scientific_project is not None
    # No job, no implicit M4 execution or approval exists as a result of import.
    with app.store.connection() as db: assert db.execute('SELECT COUNT(*) FROM runs').fetchone()[0]==0


def test_missing_dependency_can_be_added_without_reupload_or_reparse_original(tmp_path,monkeypatch):
    app,project=setup(tmp_path)
    config={'schema_version':'project-config-v1','config':{'inputs':{'protein_fasta':'proteins.faa','enzymes':[],'scaffolds':[],'linkers':[]},
        'execution':{'mode':'real','allow_assumptions':False},'prepared_through':'m1'}}
    preview=app.imports.preview(project,[('study/project.json',json.dumps(config).encode())])
    original_id=preview.items[0].file['id']
    assert preview.items[0].issues[0].code=='missing_transaction_dependency'
    assert app.imports.pending(project)==[preview.id]
    # Independently count actual parser calls: the unchanged immutable config
    # is not reparsed. Dependency binding must nevertheless be reconsidered.
    called=[]
    original=app.imports.registry.parse
    def parse(path,options):
        called.append(path.name);return original(path,options)
    monkeypatch.setattr(app.imports.registry,'parse',parse)
    updated=app.imports.append(project,preview.id,[('study/proteins.faa',b'>e\nMKWVTFISLLFLFSSAYS\n')])
    assert called==['proteins.faa']
    assert updated.items[0].file['id']==original_id and not updated.items[0].issues
    assert app.imports.commit(project,preview.id)['scientific_project']['config']['prepared_through']=='m1'
    assert app.imports.pending(project)==[]


def test_CLI_uses_saved_import_molecule_confirmation_and_same_published_objects(tmp_path):
    from typer.testing import CliRunner
    from igem_drylab.software.cli import app as commands
    runner=CliRunner()
    workspace=tmp_path/'cli-workspace'
    prefix=['--data-dir',str(workspace),'--json']
    created=runner.invoke(commands,[*prefix,'project','create','--name','CLI import'])
    assert created.exit_code==0,created.output
    project=json.loads(created.output)['id']
    fasta=tmp_path/'design.fa';fasta.write_bytes(b'>design\nACGTACGT\n')
    imported=runner.invoke(commands,[*prefix,'import',str(fasta),'--project',project])
    assert imported.exit_code==2
    preview=json.loads(imported.output)
    confirmed=runner.invoke(commands,[*prefix,'import-review',preview['id'],'--project',project,'--file','design.fa','--molecule-type','DNA'])
    assert confirmed.exit_code==0,confirmed.output
    published=runner.invoke(commands,[*prefix,'import-commit',preview['id'],'--project',project])
    assert published.exit_code==0,published.output
    assert json.loads(published.output)['sequences']==[]
    reopened=ApplicationService(workspace)
    assert reopened.imports.inspect(project,preview['id']).state=='committed'


def test_registered_file_credentials_are_derived_not_user_entered_and_wrong_identity_rejected(tmp_path):
    from igem_drylab.compartments import ArtifactReference
    from igem_drylab.workflow.scientific_setup import fill_registered_file_hashes
    from hashlib import sha256
    app,project=setup(tmp_path)
    raw=b'original software format source'
    view=app.imports.preview(project,[('source.txt',raw)])
    schema=ArtifactReference.model_json_schema()
    reference={'path':view.items[0].file['path']}
    fill_registered_file_hashes(reference,schema,schema.get('$defs',{}),app.store,project)
    assert reference['sha256']==sha256(raw).hexdigest()
    reference['sha256']='0'*64
    with pytest.raises(WorkflowError,match='file_identity_changed'):
        fill_registered_file_hashes(reference,schema,schema.get('$defs',{}),app.store,project)
    with pytest.raises(WorkflowError,match='file_project_mismatch'):
        fill_registered_file_hashes({'path':view.items[0].file['path']},schema,schema.get('$defs',{}),app.store,'other')


def test_non_PS_canonical_archive_is_not_misclassified_and_configs_do_not_last_win(tmp_path):
    app,project=setup(tmp_path)
    stream=BytesIO()
    with ZipFile(stream,'w') as archive:
        archive.writestr('canonical_parameters.json',json.dumps({'not_a_PS_dataset':True}))
    view=app.imports.preview(project,[('ordinary.zip',stream.getvalue())])
    assert view.items[0].semantic_type=='UnclassifiedConfiguration'
    config=json.dumps({'schema_version':'project-config-v1','config':{'inputs':{'protein_fasta':'proteins.faa','enzymes':[],'scaffolds':[],'linkers':[]},
        'execution':{'mode':'real','allow_assumptions':False},'prepared_through':'m1'}}).encode()
    view=app.imports.preview(project,[('one.json',config),('two.json',config),('proteins.faa',b'>e\nMKLLV\n')])
    assert all(any(i.code=='multiple_project_configurations' for i in item.issues) for item in view.items[:2])
    with pytest.raises(WorkflowError,match='import_confirmation_required'): app.imports.commit(project,view.id)
    assert not app.store.project(project).files
    resolved=app.imports.revise(project,view.id,{'two.json':{'role':'evidence_attachment'}})
    assert resolved.items[1].semantic_type=='EvidenceAttachment'
    assert not resolved.items[0].issues
    assert app.imports.commit(project,view.id)['scientific_project'] is not None


@pytest.mark.parametrize('path',['../../outside.faa','/etc/passwd','C:/private/data.faa'])
def test_config_cannot_read_outside_this_transaction(tmp_path,path):
    app,project=setup(tmp_path)
    config={'schema_version':'project-config-v1','config':{'inputs':{'protein_fasta':path}}}
    with pytest.raises(WorkflowError,match='scientific_file_outside_authorized_workspace|disclosure_quarantined'):
        app.imports.preview(project,[('project.json',json.dumps(config).encode())])


def test_multipart_API_owns_transaction_and_original_GenBank_round_trips(tmp_path):
    app=create_app(data_dir=tmp_path/'workspace',session_token='software-test',discover_tools=False)
    source=(Path(__file__).parent/'fixtures/genbank/software_design.gb').read_bytes()
    headers={'X-FusionLab-Token':'software-test'}
    with TestClient(app) as client:
        p=client.post('/api/platform/projects',headers=headers,json={'project':{'id':'p','name':'GenBank task'}}).json()
        response=client.post('/api/platform/projects/p/imports',headers=headers,files=[('files',('original.gb',source,'text/plain'))])
        assert response.status_code==200,response.text
        preview=response.json()
        other=client.get(f"/api/platform/projects/not-p/imports/{preview['id']}",headers=headers)
        assert other.status_code==404
        result=client.post(f"/api/platform/projects/p/imports/{preview['id']}/commit",headers=headers,json={})
        assert result.status_code==200,result.text
        dataset=result.json()['datasets'][0]
        assert dataset['kind']=='genbank_design'
        original=client.get('/api/platform/files/'+dataset['file_id']+'?project_id=p',headers=headers)
        assert original.content==source
        from Bio import SeqIO
        from io import StringIO
        restored=list(SeqIO.parse(StringIO(original.text),'genbank'))
        assert str(restored[0].seq)=='ATGGCTGCTTAA'
        assert restored[0].features[0].qualifiers=={'organism':['synthetic construct']}
        assert restored[0].features[1].location.strand==-1
        assert restored[0].features[2].qualifiers['translation']==['MAA']
        assert 'translation' not in restored[0].features[3].qualifiers

"""Source-file binding through HTTP; software/parser inputs, no solver."""
import json
from pathlib import Path

import pytest
from test_r6_input_boundaries import api


TARGET = "MODEL        7\nATOM      1  CA  ALA B  12A     11.000  12.000  13.000  1.00 99.00           C\nENDMDL\n"
REFERENCE = "MODEL        9\nATOM      1  CA  ALA C  44B     10.000  12.000  13.000  1.00 88.00           C\nENDMDL\n"
RESIDUE = dict(model="7", chain="B", residue_number="12", insertion_code="A", residue_name="ALA")
REF_RESIDUE = dict(model="9", chain="C", residue_number="44", insertion_code="B", residue_name="ALA")


def setup(tmp_path, change=None):
    app, client = api(tmp_path)
    raw = dict(source_reference="EXPLICIT_SOFTWARE_PARSER_SOURCE_NOT_BIOLOGY", source_tool="PARSER_FIXTURE", source_tool_version="1",
        confidence_semantics="plddt", rows=[dict(residue=RESIDUE, reference_residue=REF_RESIDUE,
        full_fusion_position=17, region="enzyme", pocket=True, plddt=0)], overlays=[dict(
        source_reference="EXPLICIT_ORIGINAL_TRANSFORM", source_tool="PARSER_FIXTURE", source_tool_version="1",
        direction="reference_to_target", coordinate_unit="angstrom", convention="row_major_column_vector_xyz1",
        matrix=[[1,0,0,1],[0,1,0,0],[0,0,1,0],[0,0,0,1]])])
    if change:
        change(raw)
    original = json.dumps(raw, indent=1)
    files=[]
    for name, content in [('target.pdb',TARGET),('reference.pdb',REFERENCE),('fusion.fasta','>FULL_FUSION\n'+'A'*20+'\n'),('source.json',original)]:
        route = '/imports/display-file' if name.endswith('.pdb') else '/imports/preview'
        result = client.post('/api/platform'+route+'?filename='+name, content=content.encode()) if name.endswith('.pdb') else client.post('/api/platform'+route,json=dict(filename=name,content=content))
        assert result.status_code == 200,result.text
        files.append(result.json()['file'])
    project = client.post('/api/platform/projects',json={'project':dict(id='p',name='ANNOTATION_SOFTWARE_ONLY',files=files)}).json()
    body = dict(project_id='p', expected_revision=project['revision'], target_file_id=files[0]['id'],
        reference_file_id=files[1]['id'], sequence_file_id=files[2]['id'], sequence_id='FULL_FUSION',source_file_id=files[3]['id'])
    return app,client,project,body,files,original


def test_binding_without_hash_input_keeps_original_and_needs_explicit_confirmation(tmp_path):
    app,client,project,body,files,original = setup(tmp_path)
    result = client.post('/api/platform/imports/structure-annotations',json=body)
    assert result.status_code == 200,result.text
    preview = result.json()
    assert preview['kind'] == 'structure_annotations' and preview['file']['name'] == 'source.linked.json'
    assert client.get('/api/platform/projects/p').json() == project
    with app.state.platform_store.connection() as db:
        row = db.execute('SELECT * FROM file_assets WHERE id=?',(preview['file']['id'],)).fetchone()
    assert row['project_id'] is None
    linked = json.loads(Path(row['path']).read_bytes())
    assert linked['target_sha256'] == files[0]['sha256']
    assert linked['fusion_sequence_file_sha256'] == files[2]['sha256']
    assert linked['rows'][0]['reference_sha256'] == files[1]['sha256']
    assert linked['rows'][0]['plddt'] == 0 and linked['rows'][0]['full_fusion_position'] == 17
    assert linked['overlays'][0]['matrix'] == json.loads(original)['overlays'][0]['matrix']
    assert client.get('/api/platform/files/'+files[3]['id']+'?project_id=p').content == original.encode()
    assert client.get('/api/platform/files/'+preview['file']['id']+'?project_id=p').status_code == 403
    saved = client.post('/api/platform/projects',json={'project':{**project,'files':[*project['files'],preview['file']]},'expected_revision':project['revision']})
    assert saved.status_code == 200,saved.text
    meta = client.get('/api/platform/files/'+files[0]['id']+'/structure-annotations?project_id=p').json()
    assert meta['annotations'][0]['plddt'] == 0 and meta['annotations'][0]['reference_file_id'] == files[1]['id']
    assert meta['fusion_sequence_id'] == 'FULL_FUSION' and meta['mapping_status'] == 'source_registered_not_scientific_approval'
    again = client.post('/api/platform/imports/structure-annotations',json={**body,'expected_revision':saved.json()['revision']})
    assert again.status_code == 200 and again.json()['file']['id'] == preview['file']['id']
    assert client.get('/api/platform/projects/p').json()['scientific_project'] is None


@pytest.mark.parametrize('fault',['target_hash','reference_hash','sequence_hash','position','sequence_id','model','transform','source','confidence'])
def test_conflicting_or_invalid_scientific_source_is_not_repaired(tmp_path, fault):
    def change(raw):
        if fault == 'target_hash': raw['target_sha256']='f'*64
        elif fault == 'reference_hash': raw['rows'][0]['reference_sha256']='f'*64
        elif fault == 'sequence_hash': raw['fusion_sequence_file_sha256']='f'*64
        elif fault == 'position': raw['rows'][0]['full_fusion_position']=21
        elif fault == 'model': raw['rows'][0]['residue']={**RESIDUE,'model':'8'}
        elif fault == 'transform': raw['overlays'][0]['matrix'][0][0]=2
        elif fault == 'source': raw['source_reference']=''
        elif fault == 'confidence': raw['confidence_semantics']='not_provided'
    _,client,project,body,files,original = setup(tmp_path,change)
    if fault == 'sequence_id': body['sequence_id']='NONEXISTENT'
    result = client.post('/api/platform/imports/structure-annotations',json=body)
    assert result.status_code >= 400
    assert client.get('/api/platform/projects/p').json() == project
    assert client.get('/api/platform/files/'+files[3]['id']+'?project_id=p').content == original.encode()


@pytest.mark.parametrize('fault',['other_project','stale_revision','tampered_source','tampered_target'])
def test_binding_uses_grants_frozen_bytes_and_saved_revision(tmp_path, fault):
    app,client,project,body,files,_ = setup(tmp_path)
    if fault == 'other_project':
        other=client.post('/api/platform/projects',json={'project':dict(id='other',name='OTHER')}).json()
        body.update(project_id='other',expected_revision=other['revision'])
    elif fault == 'stale_revision': body['expected_revision']+=1
    else:
        file_id=files[3 if fault == 'tampered_source' else 0]['id']
        with app.state.platform_store.connection() as db:
            path=Path(db.execute('SELECT path FROM file_assets WHERE id=?',(file_id,)).fetchone()[0])
        path.write_bytes(b'changed')
    result=client.post('/api/platform/imports/structure-annotations',json=body)
    assert result.status_code in {403,409},result.text


def test_different_linked_annotation_is_not_silently_replaced(tmp_path):
    _,client,project,body,files,original = setup(tmp_path)
    preview=client.post('/api/platform/imports/structure-annotations',json=body).json()
    saved=client.post('/api/platform/projects',json={'project':{**project,'files':[*project['files'],preview['file']]},'expected_revision':project['revision']}).json()
    changed=json.loads(original)
    changed['rows'][0]['plddt']=42
    source=client.post('/api/platform/imports/preview',json=dict(filename='changed-source.json',content=json.dumps(changed))).json()['file']
    current=client.post('/api/platform/projects',json={'project':{**saved,'files':[*saved['files'],source]},'expected_revision':saved['revision']}).json()
    result=client.post('/api/platform/imports/structure-annotations',json={**body,'expected_revision':current['revision'],'source_file_id':source['id']})
    assert result.status_code == 409,result.text
    assert result.json()['detail']['code'] == 'structure_annotations_already_linked'
    assert client.get('/api/platform/projects/p').json() == current
    meta=client.get('/api/platform/files/'+files[0]['id']+'/structure-annotations?project_id=p').json()
    assert meta['annotation_file_id'] == preview['file']['id'] and meta['annotations'][0]['plddt'] == 0

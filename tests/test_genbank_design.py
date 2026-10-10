"""Annotated design retention/ownership oracle; no translation or numerical model."""
from fastapi.testclient import TestClient
from pathlib import Path

from igem_drylab.software.dashboard import create_app


SOURCE = (Path(__file__).parent/'fixtures/genbank/software_design.gb').read_text(encoding='utf-8')


def imported(client, content=SOURCE, project_id='p'):
    response = client.post('/api/platform/imports/preview', json={'filename':'design.gb','content':content})
    assert response.status_code == 200, response.text
    preview = response.json()
    project = {'id':project_id,'name':'Software fixture','files':[preview['file']],**preview['patch']}
    response = client.post('/api/platform/projects',json={'project':project})
    assert response.status_code == 200, response.text
    return response.json(), preview


def test_original_dna_full_annotations_strand_fuzzy_positions_and_missing_translation(tmp_path):
    client = TestClient(create_app(data_dir=tmp_path, deployment_mode='development'))
    project, preview = imported(client)
    assert [row['sequence'] for row in project['sequences']] == ['MAA']
    design = project['datasets'][0]
    assert design['records'][0]['untranslated_cds_count'] == 1
    page = client.get(f"/api/platform/projects/p/designs/{design['id']}")
    assert page.status_code == 200, page.text
    page = page.json()
    assert page['nucleotide_fragment'] == 'ATGGCTGCTTAA'
    assert page['annotations']['references'][0]['title'] == 'Independent metadata test'
    gene = page['features'][1]
    assert gene['parts'] == [{'start':'<0','start_kind':'BeforePosition','end':'9','end_kind':'ExactPosition','strand':-1,'ref':None,'ref_db':None}]
    assert gene['qualifiers']['gene'] == ['reverse_fixture']
    assert page['features'][2]['translation_status'] == 'matches_source_translation'
    missing = page['features'][3]
    assert missing['translation_status'] == 'missing_source_translation'
    assert [(p['start'],p['end']) for p in missing['parts']] == [('0','3'),('6','9')]
    assert missing['linked_sequence_id'] is None
    exported = client.get(f"/api/platform/files/{preview['file']['id']}?project_id=p")
    # Independent byte oracle proves every original field survives export,
    # not a write/read comparison using the same GenBank parser.
    assert exported.content == SOURCE.encode()
    page = client.get(f"/api/platform/projects/p/designs/{design['id']}?feature_offset=2&limit=1").json()
    assert len(page['features']) == 1 and page['features'][0]['feature_index'] == 2


def test_dna_only_import_is_retained_without_synthetic_protein_and_ownership_is_enforced(tmp_path):
    client = TestClient(create_app(data_dir=tmp_path, deployment_mode='development'))
    dna_only = SOURCE.replace('                     /translation="MAA"\n','')
    project, preview = imported(client, dna_only)
    assert project['sequences'] == []
    assert project['datasets'][0]['records'][0]['untranslated_cds_count'] == 2
    client.post('/api/platform/projects',json={'project':{'id':'other','name':'Other'}})
    design_id = project['datasets'][0]['id']
    assert client.get(f'/api/platform/projects/other/designs/{design_id}').status_code == 404
    assert client.get(f"/api/platform/files/{preview['file']['id']}?project_id=other").status_code == 403
    assert client.get(f'/api/platform/projects/p/designs/{design_id}?nucleotide_offset=12').status_code == 422


def test_edited_protein_is_not_mistaken_for_edited_dna(tmp_path):
    client = TestClient(create_app(data_dir=tmp_path, deployment_mode='development'))
    project, preview = imported(client)
    project['sequences'][0]['sequence'] = 'MMM'
    saved = client.post('/api/platform/projects', json={'project':project,'expected_revision':project['revision']})
    assert saved.status_code == 200, saved.text
    page = client.get(f"/api/platform/projects/p/designs/{project['datasets'][0]['id']}").json()
    assert page['features'][2]['translation_status'] == 'project_protein_differs_from_source'
    assert client.get(f"/api/platform/files/{preview['file']['id']}?project_id=p").content == SOURCE.encode()


def test_contig_only_source_retains_annotations_without_inventing_bases(tmp_path):
    client = TestClient(create_app(data_dir=tmp_path, deployment_mode='development'))
    source = SOURCE.replace('ORIGIN\n        1 atggctgctt aa\n', 'CONTIG      join(OTHER.1:1..12)\n')
    project, preview = imported(client, source)
    page = client.get(f"/api/platform/projects/p/designs/{project['datasets'][0]['id']}")
    assert page.status_code == 200, page.text
    assert page.json()['nucleotide_fragment'] is None
    assert page.json()['annotations']['contig'] == 'join(OTHER.1:1..12)'
    assert client.get(f"/api/platform/files/{preview['file']['id']}?project_id=p").content == source.encode()

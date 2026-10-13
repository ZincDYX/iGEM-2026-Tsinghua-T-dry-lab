"""Collection transport only; no predictor or scientific calculation runs."""
from io import BytesIO
from zipfile import ZipFile

import pytest
import yaml

from igem_drylab.software.input_collection import collection_options
from igem_drylab.software.application import ApplicationService
from igem_drylab.software.parsers import ParserRegistry
from igem_drylab.workflow.models import WorkflowError


def test_collection_binds_declared_role_and_localization_not_repeated_outputs(tmp_path):
    files=[('study/FILE_MANIFEST.json', b'{}'),
        ('study/run/project_source_inputs.yaml', yaml.safe_dump({'inputs':{
            'protein_fasta':'../sequences.fasta', 'sequence_roles':{'opaque':'full_fusion'},
            'constructs':[{'id':'opaque', 'localization_context':'er_anchored'}]}}).encode()),
        ('study/sequences.fasta', b'>opaque\nMAGSGS\n'),
        ('study/raw/input.fasta', b'>opaque\nMAGSGS\n')]
    options=collection_options(files)
    registry=ParserRegistry()
    for name, raw in files[2:]:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        parsed=registry.parse(path,options[name])
        if name=='study/sequences.fasta':
            assert parsed.patch['sequences'][0]['localization_context']=='er_anchored'
            assert parsed.patch['sequences'][0]['role']=='full_fusion'
        else:
            assert not parsed.patch['sequences']
            assert parsed.records[0]['sequence']=='MAGSGS'


def test_complete_collection_capacity_preserves_more_than_256_originals(tmp_path):
    raw=BytesIO()
    with ZipFile(raw,'w') as archive:
        for index in range(300): archive.writestr(f'evidence/{index}.md', 'Original')
    app=ApplicationService(tmp_path/'workspace');project=app.create_project('capacity')
    preview=app.imports.preview(project['id'],[('collection.zip',raw.getvalue())])
    assert len(preview.items)==300
    result=app.imports.commit(project['id'],preview.id)
    assert len(result['files'])==300


def test_same_sequence_with_changed_localization_requires_explicit_revision(tmp_path):
    app=ApplicationService(tmp_path/'workspace');project=app.create_project('context')
    first=app.imports.preview(project['id'],[('first.faa',b'>opaque\nMAGSGS\n')])
    app.imports.commit(project['id'],first.id)
    second=app.imports.preview(project['id'],[('second.faa',b'>opaque\nMAGSGS\n')],
        options={'second.faa':{'localization_context':'er_anchored'}})
    with pytest.raises(WorkflowError,match='sequence_conflict'):
        app.imports.commit(project['id'],second.id,{'second.faa':'new_version'})
    assert app.store.project(project['id']).sequences[0].localization_context=='cytosolic'

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


def test_protein_genbank_is_not_misclassified_as_DNA_or_inferred_CDS(tmp_path):
    from Bio import SeqIO
    from Bio.Seq import Seq
    from Bio.SeqRecord import SeqRecord
    record=SeqRecord(Seq('MAGSGS'),id='opaque',annotations={'molecule_type':'protein'})
    path=tmp_path/'protein.gb';SeqIO.write(record,path,'genbank')
    parsed=ParserRegistry().parse(path,{'role':'idr'})
    assert parsed.semantic_type=='SequenceCollection'
    assert parsed.records[0]['molecule_type']=='protein' and parsed.patch['sequences'][0]['role']=='idr'
    assert not ParserRegistry().parse(path,{'bind_sequences':False}).patch['sequences']


def test_secondround_import_owns_sequences_and_retains_original_workbook_cells(tmp_path):
    from hashlib import sha256
    from igem_drylab.software.input_collection import prepare_collection
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    def inline(column,row,value):
        return f'<c r="{column}{row}" t="inlineStr"><is><t>{value}</t></is></c>'
    header=''.join(inline(c,3,v) for c,v in zip('ABC',['candidate_id','amino_acid_sequence','sequence_sha256']))
    rows=''.join('<row r="'+str(i)+'">'+''.join(inline(c,i,v) for c,v in zip('ABC',
        [identifier,sequence,sha256(sequence.encode()).hexdigest()]))+'</row>'
        for i,(identifier,sequence) in enumerate([('new','GSGS'),('reference','MAGSGS')],4))
    workbook=BytesIO()
    with ZipFile(workbook,'w') as archive:
        archive.writestr('xl/worksheets/sheet1.xml',f'<worksheet xmlns="{ns}"><sheetData><row r="3">{header}</row>{rows}</sheetData></worksheet>')
    files=[('second/01_sequences/new_idr_library_120.fasta',b'>new\nGSGS\n'),
        ('second/02_analysis/original.xlsx',workbook.getvalue()),
        ('second/01_sequences/priority.fasta',b'>new\nGSGS\n'),
        ('second/01_sequences/full_fusion.fasta',b'>fusion\nMAGSGSGS\n')]
    expanded,options=prepare_collection(files)
    derived='second/derived/old_reference_IDRs_from_workbook.fasta'
    assert len(expanded)==len(files)+1
    assert dict(expanded)[derived]==b'>reference\nMAGSGS\n'
    assert options[files[0][0]]['role']=='idr'
    assert not options[files[2][0]]['bind_sequences'] and not options[files[3][0]]['bind_sequences']
    path=tmp_path/'library.fasta';path.write_bytes(files[0][1])
    parsed=ParserRegistry().parse(path,options[files[0][0]])
    assert parsed.records[0]['source_records'][0]['row']=='4'
    assert parsed.records[0]['source_records'][0]['sequence_column']=='B'
    with pytest.raises(ValueError,match='FASTA_workbook_sequence_mismatch'):
        prepare_collection([(files[0][0],b'>new\nSGSG\n'),*files[1:]])

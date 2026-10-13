"""Bind declared collection sequences without treating repeated evidence as inputs.

All original files remain in the import transaction. Configuration declarations
own role/localization; filenames never determine the protein identity. This
reads data only, and never runs scripts supplied in an archive.
"""
import json
import posixpath
from pathlib import PurePosixPath

import yaml


def _workbook_sequences(raw):
    """Read explicit literal sequence/source columns, never formulas or scores."""
    from io import BytesIO
    from zipfile import ZipFile
    import xml.etree.ElementTree as ET
    from hashlib import sha256
    from igem_drylab.workflow.binary_import import validate_archive_members
    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with ZipFile(BytesIO(raw)) as archive:
        validate_archive_members(archive.infolist())
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared = [''.join(node.itertext()) for node in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        def cells(row):
            result = {}
            for cell in row:
                if cell.find('s:f', ns) is not None:
                    continue  # a cached formula value is not an original sequence
                value = cell.find('s:v', ns)
                value = value.text if value is not None else ''
                if cell.get('t') == 's': value = shared[int(value)]
                elif cell.get('t') == 'inlineStr': value = ''.join(cell.find('s:is', ns).itertext())
                result[''.join(c for c in cell.get('r') if c.isalpha())] = value
            return result
        records = []
        for name in archive.namelist():
            if not name.startswith('xl/worksheets/') or not name.endswith('.xml'):
                continue
            columns = None
            for row in ET.fromstring(archive.read(name)).findall('s:sheetData/s:row', ns):
                values = cells(row)
                if {'candidate_id', 'amino_acid_sequence', 'sequence_sha256'} <= set(values.values()):
                    columns = {value: key for key, value in values.items()}; continue
                if columns is None or not values.get(columns['candidate_id']):
                    continue
                sequence = values.get(columns['amino_acid_sequence'])
                if not sequence or set(sequence)-set('ACDEFGHIKLMNPQRSTVWY') or sha256(sequence.encode()).hexdigest() != values.get(columns['sequence_sha256']):
                    raise ValueError('collection_workbook_literal_sequence_identity_mismatch')
                records.append(dict(id=values[columns['candidate_id']], sequence=sequence,
                    sheet_xml=name, row=row.get('r'), sequence_column=columns['amino_acid_sequence']))
        return records


def prepare_collection(files):
    """The supplied second-round format: exact library + workbook references.

    Retain priority subsets, fusion constructs and historical analysis as
    attachments. Those are not duplicate IDRs or reviewed prediction policies.
    """
    from Bio import SeqIO
    from io import StringIO
    files = list(files)
    options = collection_options(files)
    sources = dict(files)
    libraries = [name for name in sources if name.endswith('/01_sequences/new_idr_library_120.fasta')]
    for library in libraries:
        root = PurePosixPath(library).parent.parent.as_posix()
        workbooks = [name for name in sources if name.startswith(root+'/02_analysis/') and name.endswith('.xlsx')]
        if len(workbooks) != 1:
            raise ValueError('secondround_requires_one_original_sequence_workbook')
        workbook = workbooks[0]
        originals = {row.id: str(row.seq) for row in SeqIO.parse(StringIO(sources[library].decode()), 'fasta')}
        records = _workbook_sequences(sources[workbook])
        reviewed, metadata = {}, {}
        for row in records:
            identifier, sequence = row['id'], row['sequence']
            if identifier in reviewed and reviewed[identifier] != sequence:
                raise ValueError('secondround_conflicting_workbook_sequences')
            if identifier in originals and originals[identifier] != sequence:
                raise ValueError('secondround_FASTA_workbook_sequence_mismatch')
            reviewed[identifier] = sequence
            metadata.setdefault(identifier, dict(role='idr', source_records=[]))['source_records'].append(
                dict(workbook=workbook, **{k: row[k] for k in ('sheet_xml', 'row', 'sequence_column')}))
        if set(originals)-set(reviewed):
            raise ValueError('secondround_library_sequence_missing_from_workbook')
        for name in sources:
            if name.startswith(root+'/'):
                options[name] = dict(role='evidence_attachment', bind_sequences=False)
                if PurePosixPath(name).suffix.lower() in {'.fasta', '.fa', '.faa'}:
                    options[name]['molecule_type'] = 'protein'
        options[library] = dict(role='idr', molecule_type='protein', bind_sequences=True, sequence_metadata=metadata)
        references = {identifier: seq for identifier, seq in reviewed.items() if identifier not in originals}
        if references:
            name = root+'/derived/old_reference_IDRs_from_workbook.fasta'
            raw = ''.join(f'>{identifier}\n{sequence}\n' for identifier, sequence in references.items()).encode()
            if name in sources:
                if sources[name] != raw:
                    raise ValueError('secondround_derived_reference_filename_conflict')
            else:
                files.append((name, raw))
            options[name] = dict(role='idr', molecule_type='protein', bind_sequences=True, sequence_metadata=metadata)
    return files, options


def collection_options(files):
    sources = dict(files)
    markers = [name for name in sources if name.endswith('/run/project_source_inputs.yaml')]
    if len(markers) != 1 or not any(name.endswith('/FILE_MANIFEST.json') for name in sources):
        return {}
    primary = markers[0]
    root = PurePosixPath(primary).parent.parent.as_posix()
    options = {name: {'role': 'evidence_attachment'} for name in sources
               if PurePosixPath(name).suffix.lower() in {'.json', '.yaml', '.yml', '.csv', '.tsv'}}
    metadata = {}
    authoritative = set()
    for name in (primary, root+'/run/project_linker_candidates.yaml'):
        if name not in sources:
            continue
        config = yaml.safe_load(sources[name])
        inputs = config['inputs']
        contexts = {row['id']: row.get('localization_context', 'cytosolic')
                    for row in inputs.get('constructs', [])}
        for identifier, role in inputs.get('sequence_roles', {}).items():
            metadata[identifier] = dict(role=role, localization_context=contexts.get(identifier, 'cytosolic'))
        fasta = posixpath.normpath(posixpath.join(posixpath.dirname(name), inputs['protein_fasta']))
        if fasta not in sources:
            raise ValueError('collection_declared_fasta_missing')
        authoritative.add(fasta)
        options[name] = {'role': 'project_config'} if name == primary else {'role': 'evidence_attachment'}
    # Additional original designs are explicit records, not filename guesses.
    expanded = root+'/M1/expanded_designs/additional_unique_proteins.fasta'
    if expanded in sources:
        authoritative.add(expanded)
        rows = json.loads(sources[root+'/M1/expanded_designs/source_records.json'])
        original = yaml.safe_load(sources[primary])['inputs']
        from Bio import SeqIO
        from io import StringIO
        fixed = {row.id: str(row.seq) for row in SeqIO.parse(
            StringIO(sources[root+'/M1/inputs/fixed_components_from_project.fasta'].decode()), 'fasta')}
        # This exact component is supplied by the collection, not identified
        # from a construct filename or an arbitrary hydrophobic cutoff.
        anchors = [fixed['ER_anchor']] if 'ER_anchor' in fixed else []
        for row in rows:
            identifier = row.get('record_id') or row.get('id')
            if identifier:
                sequence = row['sequence']
                metadata.setdefault(identifier, dict(role='full_fusion', localization_context=
                    'er_anchored' if any(anchor in sequence for anchor in anchors) else 'cytosolic'))
    # Baselines and components have no M1 candidate role unless declared.
    for name in sources:
        if PurePosixPath(name).suffix.lower() in {'.fasta', '.fa', '.faa', '.fna'}:
            options[name] = dict(molecule_type='DNA' if name.endswith('selected_CDS_from_DNA.fasta') else 'protein',
                bind_sequences=name in authoritative, sequence_metadata=metadata, role='reference')
    return options

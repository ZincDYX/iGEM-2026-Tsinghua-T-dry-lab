"""Bind declared collection sequences without treating repeated evidence as inputs.

All original files remain in the import transaction. Configuration declarations
own role/localization; filenames never determine the protein identity. This
reads data only, and never runs scripts supplied in an archive.
"""
import json
import posixpath
from pathlib import PurePosixPath

import yaml


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

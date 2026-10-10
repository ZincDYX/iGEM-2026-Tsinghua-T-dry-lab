"""GenBank design references and views; original annotated bytes are canonical."""
from io import StringIO
from typing import Any, Literal

from Bio import SeqIO
from Bio.Seq import UndefinedSequenceError
from Bio.SeqFeature import Reference, SimpleLocation, CompoundLocation
from pydantic import Field

from .models import Contract, SequenceRecord, WorkflowError


class CDSProteinBinding(Contract):
    record_index: int = Field(ge=0)
    feature_index: int = Field(ge=0)
    sequence_id: str | None
    source_protein_id: str | None


class GenBankRecordRef(Contract):
    record_index: int = Field(ge=0)
    record_id: str
    nucleotide_count: int
    feature_count: int
    untranslated_cds_count: int


class GenBankDesign(Contract):
    kind: Literal['genbank_design'] = 'genbank_design'
    id: str
    name: str
    file_id: str
    records: list[GenBankRecordRef]
    cds_proteins: list[CDSProteinBinding]


class GenBankFeatureView(Contract):
    feature_index: int
    type: str
    location: str | None
    parts: list[dict[str, Any]]
    qualifiers: dict[str, list[str]]
    linked_sequence_id: str | None
    translation_status: str


class GenBankPage(Contract):
    design_id: str
    file_id: str
    record_index: int
    record_id: str
    record_count: int
    description: str
    molecule_type: str
    annotations: dict[str, Any]
    dbxrefs: list[str]
    nucleotide_count: int
    nucleotide_start_1based: int
    nucleotide_fragment: str | None
    feature_offset: int
    feature_total: int
    features: list[GenBankFeatureView]
    export_scope: Literal['unchanged_original_annotated_genbank'] = 'unchanged_original_annotated_genbank'


def import_design(content):
    records = list(SeqIO.parse(StringIO(content), 'genbank'))
    if not records:
        raise WorkflowError('genbank_contains_no_records')
    summaries, bindings, proteins = [], [], {}
    for record_index, record in enumerate(records):
        if record.annotations.get('molecule_type', '').upper() not in {'DNA', 'RNA', 'MRNA', 'TRNA', 'RRNA', 'SS-DNA', 'DS-DNA', 'SS-RNA', 'DS-RNA'}:
            raise WorkflowError('genbank_design_requires_nucleotide_records')
        missing = 0
        for feature_index, feature in enumerate(record.features):
            if feature.type != 'CDS':
                continue
            source_id = feature.qualifiers.get('protein_id', [None])[0]
            translation = feature.qualifiers.get('translation', [None])[0]
            protein_id = None
            if translation:
                from igem_drylab.constructs.linker_features import normalize_amino_acid_sequence
                protein_id = source_id or f'{record.id}_CDS_{feature_index}'
                sequence = normalize_amino_acid_sequence(translation)
                if protein_id in proteins and proteins[protein_id].sequence != sequence:
                    raise WorkflowError('genbank_duplicate_protein_id_has_different_translation')
                proteins[protein_id] = SequenceRecord(id=protein_id, sequence=sequence)
            else:
                missing += 1  # Never translate DNA or invent a missing protein.
            bindings.append(CDSProteinBinding(record_index=record_index, feature_index=feature_index,
                source_protein_id=source_id, sequence_id=protein_id))
        summaries.append(GenBankRecordRef(record_index=record_index, record_id=record.id,
            nucleotide_count=len(record.seq), feature_count=len(record.features), untranslated_cds_count=missing))
    return summaries, bindings, list(proteins.values())


def source_annotation(value):
    if isinstance(value, Reference):
        return {key: source_annotation(item) for key, item in vars(value).items()}
    if isinstance(value, (SimpleLocation, CompoundLocation)):
        return {'notation': str(value), 'strand': value.strand}
    if isinstance(value, dict):
        return {key: source_annotation(item) for key, item in value.items()}
    if isinstance(value, list):
        return [source_annotation(item) for item in value]
    return value


def design_page(content, design, sequences, record_index, feature_offset, limit, nucleotide_offset):
    records = SeqIO.parse(StringIO(content), 'genbank')
    record = next((item for index, item in enumerate(records) if index == record_index), None)
    if record is None:
        raise WorkflowError('genbank_record_not_found', status_code=404)
    if nucleotide_offset >= len(record.seq):
        raise WorkflowError('genbank_nucleotide_offset_out_of_range')
    bindings = {item.feature_index: item for item in design.cds_proteins if item.record_index == record_index}
    current = {item.id: item.sequence for item in sequences}
    features = []
    for index in range(feature_offset, min(feature_offset+limit, len(record.features))):
        feature = record.features[index]
        binding = bindings.get(index)
        sequence_id = binding.sequence_id if binding else None
        translation = feature.qualifiers.get('translation', [None])[0]
        status = 'not_a_cds'
        if feature.type == 'CDS':
            if not translation:
                status = 'missing_source_translation'
            elif sequence_id is None or sequence_id not in current:
                status = 'source_translation_not_linked'
            else:
                status = 'matches_source_translation' if current[sequence_id] == ''.join(translation.split()).upper() else 'project_protein_differs_from_source'
        parts = []
        for part in feature.location.parts if feature.location else []:
            # Preserve fuzzy position type/text, remote references and strand.
            # Do not silently coerce uncertain positions into exact integers.
            parts.append(dict(start=str(part.start), start_kind=type(part.start).__name__,
                end=str(part.end), end_kind=type(part.end).__name__, strand=part.strand,
                ref=part.ref, ref_db=part.ref_db))
        features.append(GenBankFeatureView(feature_index=index, type=feature.type,
            location=str(feature.location) if feature.location else None, parts=parts,
            qualifiers=feature.qualifiers, linked_sequence_id=sequence_id, translation_status=status))
    try:
        fragment = str(record.seq[nucleotide_offset:nucleotide_offset+2000])
    except UndefinedSequenceError:
        fragment = None  # Contig-only records retain annotations, never invented bases.
    return GenBankPage(design_id=design.id, file_id=design.file_id, record_index=record_index,
        record_id=record.id, record_count=len(design.records), description=record.description,
        molecule_type=record.annotations.get('molecule_type', ''), annotations=source_annotation(record.annotations),
        dbxrefs=record.dbxrefs, nucleotide_count=len(record.seq), nucleotide_start_1based=nucleotide_offset+1,
        nucleotide_fragment=fragment,
        feature_offset=feature_offset, feature_total=len(record.features), features=features)

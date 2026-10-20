"""M1.0 construct assembly, ORF translation, and restriction-site QC."""

from __future__ import annotations

from hashlib import sha256
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .linker_features import normalize_amino_acid_sequence


_CODON_TABLE = {
    "TTT": "F", "TTC": "F", "TTA": "L", "TTG": "L", "TCT": "S", "TCC": "S", "TCA": "S", "TCG": "S",
    "TAT": "Y", "TAC": "Y", "TAA": "*", "TAG": "*", "TGT": "C", "TGC": "C", "TGA": "*", "TGG": "W",
    "CTT": "L", "CTC": "L", "CTA": "L", "CTG": "L", "CCT": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    "CAT": "H", "CAC": "H", "CAA": "Q", "CAG": "Q", "CGT": "R", "CGC": "R", "CGA": "R", "CGG": "R",
    "ATT": "I", "ATC": "I", "ATA": "I", "ATG": "M", "ACT": "T", "ACC": "T", "ACA": "T", "ACG": "T",
    "AAT": "N", "AAC": "N", "AAA": "K", "AAG": "K", "AGT": "S", "AGC": "S", "AGA": "R", "AGG": "R",
    "GTT": "V", "GTC": "V", "GTA": "V", "GTG": "V", "GCT": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "GAT": "D", "GAC": "D", "GAA": "E", "GAG": "E", "GGT": "G", "GGC": "G", "GGA": "G", "GGG": "G",
}
_COMPLEMENT = str.maketrans("ACGT", "TGCA")


class PartBoundary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    part_id: str
    occurrence: int = Field(ge=1)
    start_aa: int = Field(ge=1)
    end_aa: int = Field(ge=1)


class RestrictionSiteHit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enzyme: str
    motif: str
    strand: Literal["forward", "reverse"]
    start_nt: int = Field(ge=1)
    end_nt: int = Field(ge=1)


class ConstructSequenceQc(BaseModel):
    model_config = ConfigDict(extra="forbid")
    construct_id: str
    status: Literal["valid", "blocked", "invalid"]
    full_protein_sequence: str | None = None
    protein_sha256: str | None = None
    coding_dna_sha256: str | None = None
    part_boundaries: list[PartBoundary] = Field(default_factory=list)
    restriction_hits: list[RestrictionSiteHit] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)


def assemble_and_validate_construct(
    *,
    construct_id: str,
    ordered_part_ids: list[str],
    part_sequences: dict[str, str],
    coding_dna: str | None,
    forbidden_restriction_sites: dict[str, str] | None,
    require_sequence_evidence: bool,
) -> ConstructSequenceQc:
    """Assemble an exact protein sequence and compare it with the sequenced ORF."""

    errors: list[str] = []
    missing: list[str] = []
    normalized_parts: list[tuple[str, str]] = []
    for part_id in ordered_part_ids:
        sequence = part_sequences.get(part_id)
        if sequence is None:
            errors.append(f"part_sequence_not_found:{part_id}")
            continue
        try:
            normalized_parts.append((part_id, normalize_amino_acid_sequence(sequence)))
        except ValueError:
            errors.append(f"invalid_part_sequence:{part_id}")
    if not ordered_part_ids:
        errors.append("ordered_part_ids_are_required")
    if errors:
        return ConstructSequenceQc(construct_id=construct_id, status="invalid", errors=errors)

    full_sequence = "".join(sequence for _, sequence in normalized_parts)
    boundaries: list[PartBoundary] = []
    occurrences: dict[str, int] = {}
    cursor = 1
    for part_id, sequence in normalized_parts:
        occurrences[part_id] = occurrences.get(part_id, 0) + 1
        boundaries.append(PartBoundary(
            part_id=part_id,
            occurrence=occurrences[part_id],
            start_aa=cursor,
            end_aa=cursor + len(sequence) - 1,
        ))
        cursor += len(sequence)

    normalized_dna: str | None = None
    if coding_dna is None:
        if require_sequence_evidence:
            missing.append("sequenced_coding_dna")
    else:
        normalized_dna = "".join(coding_dna.split()).upper().replace("U", "T")
        if not normalized_dna or any(base not in "ACGT" for base in normalized_dna):
            errors.append("coding_dna_contains_non_acgt_base")
        elif len(normalized_dna) % 3:
            errors.append("coding_dna_length_is_not_a_multiple_of_three")
        else:
            translated = "".join(
                _CODON_TABLE[normalized_dna[index:index + 3]]
                for index in range(0, len(normalized_dna), 3)
            )
            if "*" in translated[:-1]:
                errors.append("coding_dna_contains_internal_stop_codon")
            translated = translated.removesuffix("*")
            if translated != full_sequence:
                errors.append("coding_dna_translation_does_not_match_assembled_protein")

    hits: list[RestrictionSiteHit] = []
    if forbidden_restriction_sites is None:
        if require_sequence_evidence:
            missing.append("wetlab_forbidden_restriction_site_list")
    elif normalized_dna is not None and not errors:
        try:
            hits = _restriction_hits(normalized_dna, forbidden_restriction_sites)
        except ValueError as exc:
            errors.append(str(exc))

    status = "invalid" if errors else ("blocked" if missing else "valid")
    return ConstructSequenceQc(
        construct_id=construct_id,
        status=status,
        full_protein_sequence=full_sequence,
        protein_sha256=sha256(full_sequence.encode("ascii")).hexdigest(),
        coding_dna_sha256=(sha256(normalized_dna.encode("ascii")).hexdigest() if normalized_dna else None),
        part_boundaries=boundaries,
        restriction_hits=hits,
        errors=errors,
        missing_inputs=missing,
    )


def _restriction_hits(dna: str, forbidden_sites: dict[str, str]) -> list[RestrictionSiteHit]:
    hits: list[RestrictionSiteHit] = []
    for enzyme, raw_motif in forbidden_sites.items():
        motif = "".join(raw_motif.split()).upper().replace("U", "T")
        if not motif or any(base not in "ACGT" for base in motif):
            raise ValueError(f"invalid_restriction_motif:{enzyme}")
        reverse = motif.translate(_COMPLEMENT)[::-1]
        for strand, query in (("forward", motif), ("reverse", reverse)):
            if strand == "reverse" and reverse == motif:
                continue
            start = dna.find(query)
            while start >= 0:
                hits.append(RestrictionSiteHit(
                    enzyme=enzyme,
                    motif=motif,
                    strand=strand,
                    start_nt=start + 1,
                    end_nt=start + len(query),
                ))
                start = dna.find(query, start + 1)
    return sorted(hits, key=lambda item: (item.start_nt, item.enzyme, item.strand))

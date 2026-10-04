"""M1 V3 sequence features and rule-based negative screening.

The equations and rule boundaries in this module follow the 2026-09-27
M1--M4 implementation contract. They are engineering screens, not measured
biophysical properties and not probabilities of LLPS or expression success.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from math import log2
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

STANDARD_AMINO_ACIDS = frozenset("ACDEFGHIKLMNPQRSTVWY")


class M1FeatureDefinitions(BaseModel):
    """Versioned residue sets and hydropathy scale used by every M1 run."""

    model_config = ConfigDict(extra="forbid")
    formula_version: str
    hydrophobic_residues: str
    aromatic_residues: str
    charged_residues: str
    polar_residues: str
    positive_residues: str = "KR"
    negative_residues: str = "DE"
    hydropathy_scale_name: str
    hydropathy_scale: dict[str, float]

    @model_validator(mode="after")
    def _validate_residue_definitions(self) -> "M1FeatureDefinitions":
        for name in (
            "hydrophobic_residues",
            "aromatic_residues",
            "charged_residues",
            "polar_residues",
            "positive_residues",
            "negative_residues",
        ):
            residues = set(getattr(self, name))
            if not residues or not residues <= STANDARD_AMINO_ACIDS:
                raise ValueError(f"{name} must be a non-empty subset of the 20 standard amino acids")
        if set(self.hydropathy_scale) != STANDARD_AMINO_ACIDS:
            raise ValueError("hydropathy_scale must define exactly the 20 standard amino acids")
        return self

    @classmethod
    def from_yaml(cls, path: Path) -> tuple["M1FeatureDefinitions", str]:
        raw = path.read_bytes()
        payload = yaml.safe_load(raw.decode("utf-8"))
        return cls.model_validate(payload), sha256(raw).hexdigest()


class M1V3Rules(BaseModel):
    """Audited M1 V3 hard-screen policy.

    Soft-risk directions are deliberately not encoded because the source
    document does not define every direction unambiguously.
    """

    model_config = ConfigDict(extra="forbid")
    rule_version: str
    linker_min_length: int = 5
    linker_max_length: int = 25
    scaffold_linker_min_length: int = 10
    max_hydrophobic_run_reject: int = 5
    idr_hydrophobic_fraction_reject: float = 0.35
    linker_hydrophobic_fraction_reject: float = 0.40
    idr_min_longest_disordered_run: int = 20
    idr_min_disorder_mean: float = 0.5
    idr_max_longest_folded_run: int = 10
    max_secondary_structure_fraction: float = 0.10
    disorder_boundary: float = 0.5


class SequenceFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")
    formula_version: str
    feature_definitions_sha256: str
    sequence_sha256: str
    length: int
    gs_fraction: float
    pro_fraction: float
    aromatic_fraction: float
    hydrophobic_fraction: float
    charged_fraction: float
    polar_fraction: float
    net_charge_proxy: float
    shannon_entropy: float
    top2_fraction: float
    max_hydrophobic_run: int
    mean_hydropathy: float
    forbidden_motifs: tuple[str, ...] = ()
    charge_blockiness: None = None
    multivalency_density: None = None

    @property
    def gly_ser_fraction(self) -> float:
        """Legacy alias; the contract field is ``gs_fraction``."""

        return self.gs_fraction

    @property
    def sequence_complexity(self) -> float:
        """Legacy alias; the contract field is ``shannon_entropy``."""

        return self.shannon_entropy

    @property
    def aggregation_risk_flag(self) -> bool:
        """Legacy convenience using the selected V3 linker hard boundaries."""

        return self.hydrophobic_fraction >= 0.40 or self.max_hydrophobic_run >= 5

    def as_dict(self) -> dict[str, object]:
        payload = self.model_dump(mode="json")
        payload.update(
            gly_ser_fraction=self.gs_fraction,
            sequence_complexity=self.shannon_entropy,
            aggregation_risk_flag=self.aggregation_risk_flag,
        )
        return payload


class DisorderEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: Literal["IUPred2A"] = "IUPred2A"
    tool_version: str
    source_file: Path
    input_sha256: str
    score_boundary: float = 0.5
    scores: list[float] = Field(min_length=1)
    disorder_mean: float
    disorder_fraction: float
    longest_disordered_run: int
    longest_folded_run: int


class SecondaryStructureEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: Literal["PSIPRED", "JPred"]
    tool_version: str
    source_file: Path
    input_sha256: str
    states: str
    ss_fraction: float
    longest_ss_run: int


class SegEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: Literal["SEG"] = "SEG"
    tool_version: str
    source_file: Path
    input_sha256: str
    sequence_length: int = Field(ge=1)
    low_complexity_positions: list[int] = Field(default_factory=list)
    low_complexity_fraction: float = Field(ge=0, le=1)


class ProtParamEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_name: Literal["Biopython ProtParam"] = "Biopython ProtParam"
    tool_version: str
    input_sha256: str
    molecular_weight_da: float = Field(gt=0)
    theoretical_pi: float = Field(ge=0, le=14)
    amino_acid_counts: dict[str, int]


class FusionToolEvidence(BaseModel):
    """Normalized, provenance-bearing observations from full-fusion tools."""

    model_config = ConfigDict(extra="forbid")
    input_sha256: str | None = None
    signalp_tool_version: str | None = None
    signalp_source_file: Path | None = None
    signal_peptide_with_clear_cleavage: bool | None = None
    deeptmhmm_tool_version: str | None = None
    deeptmhmm_source_file: Path | None = None
    transmembrane_helix_count: int | None = Field(default=None, ge=0)
    aggregation_tool: Literal["TANGO", "PASTA2"] | None = None
    aggregation_tool_version: str | None = None
    aggregation_source_file: Path | None = None
    continuous_high_aggregation_hotspots: int | None = Field(default=None, ge=0)
    restriction_source_file: Path | None = None
    forbidden_dna_sites: list[str] = Field(default_factory=list)


class M1ScreenResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    formula_version: str
    rule_version: str
    sequence_kind: Literal["idr", "enzyme_ligand_linker", "scaffold_linker", "rigid_linker", "full_fusion"]
    localization_context: Literal["cytosolic", "er_anchored"]
    features: SequenceFeatures
    disorder: DisorderEvidence | None = None
    secondary_structure: SecondaryStructureEvidence | None = None
    seg: SegEvidence | None = None
    protparam: ProtParamEvidence | None = None
    fusion_evidence: FusionToolEvidence | None = None
    verdict: Literal["pass", "review", "reject", "blocked"]
    hard_reject_reasons: list[str] = Field(default_factory=list)
    review_reasons: list[str] = Field(default_factory=list)
    missing_required_evidence: list[str] = Field(default_factory=list)
    rank_score: None = None
    rank_score_reason: str = "unavailable_without_reviewed_normalization_and_weight_sources"


# Backwards-compatible public name used by existing callers.
LinkerFeatures = SequenceFeatures


def normalize_amino_acid_sequence(sequence: str) -> str:
    normalized = "".join(sequence.split()).upper()
    if not normalized or any(residue not in STANDARD_AMINO_ACIDS for residue in normalized):
        raise ValueError("sequence must contain only the 20 standard amino-acid letters")
    return normalized


def compute_sequence_features(
    sequence: str,
    *,
    definitions: M1FeatureDefinitions,
    definitions_sha256: str,
    forbidden_motifs: tuple[str, ...] = (),
) -> SequenceFeatures:
    """Compute the explicit M1 feature definitions without hidden scoring."""

    normalized = normalize_amino_acid_sequence(sequence)
    length = len(normalized)
    counts = Counter(normalized)

    def fraction(residues: str) -> float:
        return sum(counts[residue] for residue in set(residues)) / length

    hydrophobic = frozenset(definitions.hydrophobic_residues)
    run = 0
    max_run = 0
    for residue in normalized:
        run = run + 1 if residue in hydrophobic else 0
        max_run = max(max_run, run)

    ordered_counts = sorted(counts.values(), reverse=True)
    entropy = -sum((count / length) * log2(count / length) for count in counts.values())
    net_charge = (
        sum(counts[item] for item in definitions.positive_residues)
        - sum(counts[item] for item in definitions.negative_residues)
    ) / length
    found = tuple(motif for motif in forbidden_motifs if motif and motif.upper() in normalized)
    return SequenceFeatures(
        formula_version=definitions.formula_version,
        feature_definitions_sha256=definitions_sha256,
        sequence_sha256=sha256(normalized.encode("ascii")).hexdigest(),
        length=length,
        gs_fraction=fraction("GS"),
        pro_fraction=fraction("P"),
        aromatic_fraction=fraction(definitions.aromatic_residues),
        hydrophobic_fraction=fraction(definitions.hydrophobic_residues),
        charged_fraction=fraction(definitions.charged_residues),
        polar_fraction=fraction(definitions.polar_residues),
        net_charge_proxy=net_charge,
        shannon_entropy=entropy,
        top2_fraction=sum(ordered_counts[:2]) / length,
        max_hydrophobic_run=max_run,
        mean_hydropathy=sum(definitions.hydropathy_scale[item] for item in normalized) / length,
        forbidden_motifs=found,
    )


def assess_linker(
    sequence: str,
    *,
    forbidden_motifs: tuple[str, ...] = (),
    definitions_path: Path | None = None,
) -> SequenceFeatures:
    """Compatibility wrapper that now uses the audited M1 V3 definitions."""

    path = definitions_path or _default_definitions_path()
    definitions, digest = M1FeatureDefinitions.from_yaml(path)
    return compute_sequence_features(
        sequence,
        definitions=definitions,
        definitions_sha256=digest,
        forbidden_motifs=forbidden_motifs,
    )


def parse_iupred2a_output(
    path: Path,
    *,
    tool_version: str,
    input_sha256: str,
    score_boundary: float = 0.5,
) -> DisorderEvidence:
    """Parse the standard whitespace IUPred2A per-residue output."""

    scores: list[float] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) < 3:
            raise ValueError(f"invalid IUPred2A row: {raw}")
        scores.append(float(fields[2]))
    if not scores:
        raise ValueError("IUPred2A output contains no per-residue scores")
    disordered = [score >= score_boundary for score in scores]
    return DisorderEvidence(
        tool_version=tool_version,
        source_file=path,
        input_sha256=input_sha256,
        score_boundary=score_boundary,
        scores=scores,
        disorder_mean=sum(scores) / len(scores),
        disorder_fraction=sum(disordered) / len(disordered),
        longest_disordered_run=_longest_boolean_run(disordered, True),
        longest_folded_run=_longest_boolean_run(disordered, False),
    )


def parse_secondary_structure_output(
    path: Path,
    *,
    tool_name: Literal["PSIPRED", "JPred"],
    tool_version: str,
    input_sha256: str,
) -> SecondaryStructureEvidence:
    """Parse PSIPRED SS2 rows or a JPred ``jnetpred:`` state line."""

    states: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("jnetpred:"):
            states.extend(
                char
                for char in line.split(":", 1)[1].replace(",", "").replace("-", "C").upper()
                if char in "CHE"
            )
            continue
        fields = line.split()
        if len(fields) >= 3 and fields[0].isdigit() and fields[2].upper() in {"C", "H", "E"}:
            states.append(fields[2].upper())
    if not states:
        raise ValueError("secondary-structure output contains no C/H/E states")
    structured = [state in {"H", "E"} for state in states]
    return SecondaryStructureEvidence(
        tool_name=tool_name,
        tool_version=tool_version,
        source_file=path,
        input_sha256=input_sha256,
        states="".join(states),
        ss_fraction=sum(structured) / len(structured),
        longest_ss_run=_longest_boolean_run(structured, True),
    )


def parse_seg_fasta(
    path: Path,
    *,
    tool_version: str,
    input_sha256: str,
    expected_length: int,
) -> SegEvidence:
    """Parse one SEG-masked FASTA record; lowercase or X marks low complexity."""

    records: list[str] = []
    current: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            if current:
                records.append("".join(current))
                current = []
            continue
        current.append(line)
    if current:
        records.append("".join(current))
    if len(records) != 1:
        raise ValueError("SEG output must contain exactly one FASTA record")
    masked = records[0]
    if len(masked) != expected_length:
        raise ValueError("SEG output length does not match the input sequence")
    positions = [index for index, residue in enumerate(masked, start=1) if residue.islower() or residue.upper() == "X"]
    return SegEvidence(
        tool_version=tool_version,
        source_file=path,
        input_sha256=input_sha256,
        sequence_length=expected_length,
        low_complexity_positions=positions,
        low_complexity_fraction=len(positions) / expected_length,
    )


def compute_protparam_evidence(sequence: str, *, input_sha256: str) -> ProtParamEvidence:
    """Calculate the M1 ProtParam cross-check locally with versioned Biopython."""

    try:
        import Bio
        from Bio.SeqUtils.ProtParam import ProteinAnalysis
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise RuntimeError("Biopython is required for ProtParam evidence") from exc
    normalized = normalize_amino_acid_sequence(sequence)
    analysis = ProteinAnalysis(normalized)
    return ProtParamEvidence(
        tool_version=Bio.__version__,
        input_sha256=input_sha256,
        molecular_weight_da=analysis.molecular_weight(),
        theoretical_pi=analysis.isoelectric_point(),
        amino_acid_counts=analysis.count_amino_acids(),
    )


def screen_sequence_v3(
    *,
    features: SequenceFeatures,
    sequence_kind: Literal["idr", "enzyme_ligand_linker", "scaffold_linker", "rigid_linker", "full_fusion"],
    rules: M1V3Rules,
    disorder: DisorderEvidence | None = None,
    secondary_structure: SecondaryStructureEvidence | None = None,
    seg: SegEvidence | None = None,
    protparam: ProtParamEvidence | None = None,
    fusion_evidence: FusionToolEvidence | None = None,
    full_fusion_sha256: str | None = None,
    localization_context: Literal["cytosolic", "er_anchored"] = "cytosolic",
    require_external_evidence: bool = True,
) -> M1ScreenResult:
    reject: list[str] = []
    review: list[str] = []
    missing: list[str] = []

    is_linker = sequence_kind not in {"idr", "full_fusion"}
    if is_linker and (features.length < rules.linker_min_length or features.length > rules.linker_max_length):
        reject.append("linker_length_outside_5_to_25")
    if sequence_kind == "scaffold_linker" and features.length < rules.scaffold_linker_min_length:
        reject.append("scaffold_major_module_linker_shorter_than_10")
    if sequence_kind != "full_fusion" and features.max_hydrophobic_run >= rules.max_hydrophobic_run_reject:
        reject.append("continuous_hydrophobic_run_at_least_5")
    if sequence_kind == "idr" and features.hydrophobic_fraction >= rules.idr_hydrophobic_fraction_reject:
        reject.append("idr_hydrophobic_fraction_at_least_0_35")
    if is_linker and features.hydrophobic_fraction >= rules.linker_hydrophobic_fraction_reject:
        reject.append("linker_hydrophobic_fraction_at_least_0_40")
    if features.forbidden_motifs:
        reject.append("forbidden_amino_acid_motif_present")

    if sequence_kind == "idr":
        if disorder is None:
            missing.append("IUPred2A_per_residue_output")
        elif disorder.input_sha256 != features.sequence_sha256:
            reject.append("IUPred2A_input_hash_mismatch")
        else:
            if disorder.longest_disordered_run < rules.idr_min_longest_disordered_run:
                reject.append("idr_longest_disordered_run_shorter_than_20")
            if disorder.disorder_mean < rules.idr_min_disorder_mean:
                reject.append("idr_disorder_mean_below_0_5")
            if disorder.longest_folded_run >= rules.idr_max_longest_folded_run:
                reject.append("idr_folded_run_at_least_10")
    if sequence_kind != "full_fusion":
        if secondary_structure is None:
            missing.append("PSIPRED_or_JPred_output")
        elif secondary_structure.input_sha256 != features.sequence_sha256:
            reject.append("secondary_structure_input_hash_mismatch")
        elif secondary_structure.ss_fraction >= rules.max_secondary_structure_fraction:
            if sequence_kind == "rigid_linker":
                review.append("rigid_linker_secondary_structure_requires_design_review")
            else:
                reject.append("secondary_structure_fraction_at_least_0_10")

        if seg is None:
            missing.append("SEG_output")
        elif seg.input_sha256 != features.sequence_sha256:
            reject.append("SEG_input_hash_mismatch")
        if protparam is None:
            missing.append("ProtParam_output")
        elif protparam.input_sha256 != features.sequence_sha256:
            reject.append("ProtParam_input_hash_mismatch")

    if fusion_evidence is None:
        missing.extend(
            [
                "SignalP_full_fusion_output",
                "DeepTMHMM_full_fusion_output",
                "TANGO_or_PASTA2_full_fusion_output",
            ]
        )
    else:
        if full_fusion_sha256 is None:
            missing.append("assembled_full_fusion_sequence_hash")
        elif fusion_evidence.input_sha256 is None:
            missing.append("full_fusion_tool_input_hash")
        elif fusion_evidence.input_sha256 != full_fusion_sha256:
            reject.append("full_fusion_tool_input_hash_mismatch")
        if fusion_evidence.signal_peptide_with_clear_cleavage is None:
            missing.append("SignalP_full_fusion_output")
        elif fusion_evidence.signal_peptide_with_clear_cleavage and localization_context == "cytosolic":
            reject.append("cytosolic_construct_has_clear_signal_peptide_cleavage")
        elif fusion_evidence.signal_peptide_with_clear_cleavage:
            review.append("er_anchored_construct_signal_peptide_requires_scenario_specific_review")
        if fusion_evidence.transmembrane_helix_count is None:
            missing.append("DeepTMHMM_full_fusion_output")
        elif fusion_evidence.transmembrane_helix_count >= 1 and localization_context == "cytosolic":
            reject.append("cytosolic_construct_has_transmembrane_helix")
        elif fusion_evidence.transmembrane_helix_count >= 1:
            review.append("er_anchored_construct_transmembrane_segment_requires_scenario_specific_review")
        if fusion_evidence.continuous_high_aggregation_hotspots is None:
            missing.append("TANGO_or_PASTA2_full_fusion_output")
        elif fusion_evidence.continuous_high_aggregation_hotspots >= 2:
            reject.append("multiple_continuous_high_aggregation_hotspots")
        if fusion_evidence.forbidden_dna_sites:
            reject.append("wetlab_forbidden_DNA_site_present")

    missing = list(dict.fromkeys(missing))
    if reject:
        verdict = "reject"
    elif require_external_evidence and missing:
        verdict = "blocked"
    elif review or missing:
        verdict = "review"
    else:
        verdict = "pass"
    return M1ScreenResult(
        formula_version=features.formula_version,
        rule_version=rules.rule_version,
        sequence_kind=sequence_kind,
        localization_context=localization_context,
        features=features,
        disorder=disorder,
        secondary_structure=secondary_structure,
        seg=seg,
        protparam=protparam,
        fusion_evidence=fusion_evidence,
        verdict=verdict,
        hard_reject_reasons=reject,
        review_reasons=review,
        missing_required_evidence=missing,
    )


def _longest_boolean_run(values: list[bool], target: bool) -> int:
    longest = 0
    current = 0
    for value in values:
        current = current + 1 if value is target else 0
        longest = max(longest, current)
    return longest


def _default_definitions_path() -> Path:
    return Path(__file__).resolve().parents[3] / "configs" / "m1_feature_definitions.yaml"

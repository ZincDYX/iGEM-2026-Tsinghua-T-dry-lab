from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator
from igem_drylab.parameters import ParameterRecord
from igem_drylab.constructs import ConstructRecord


DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[3] / "configs"


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default="demo-run", pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    output_dir: Path = Path("outputs")


class ExecutionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Controls whether fixture values may be used as non-scientific demonstrations."""

    mode: Literal["demo", "real"] = "demo"
    require_provenance: bool = True
    allow_assumptions: bool = False
    analysis_grade: Literal["formal_measured", "mechanistic_sensitivity"] = "formal_measured"


class StrictScientificConfig(BaseModel):
    """Reject misspelled or retired scientific settings rather than ignoring them."""

    model_config = ConfigDict(extra="forbid")


class ExperimentalContext(StrictScientificConfig):
    host: str | None = None
    strain: str | None = None
    temperature_c: float | None = None
    pH: float | None = None
    assay_system: str | None = None


class LigandConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    role: str
    sdf: Path | None = None


class EnzymeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    protein_id: str
    reaction_role: str
    structure_pdb: Path | None = None
    sequence_sha256: str | None = None


class ScaffoldConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    description: str
    oligomeric_state: int = Field(ge=1)
    structure_pdb: Path | None = None


class LinkerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    sequence: str
    source: str = "unknown"
    sequence_kind: Literal["idr", "enzyme_ligand_linker", "scaffold_linker", "rigid_linker"] = "enzyme_ligand_linker"


class OrderedPartConfig(StrictScientificConfig):
    id: str
    kind: Literal["protein", "idr", "enzyme_ligand_linker", "scaffold_linker", "rigid_linker", "tag"]
    sequence: str | None = None


class TruncationMapping(StrictScientificConfig):
    reference_accession: str
    deleted_reference_residues: list[int] = Field(min_length=1)
    reference_to_fusion: dict[int, int]
    source_reference: str


class ConstructDefinition(BaseModel):
    """A wet-lab construct description; no fusion topology is inferred by code."""

    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    model_config = ConfigDict(extra="forbid")
    components: list[str] = Field(default_factory=list)
    parts: list[OrderedPartConfig] = Field(default_factory=list)
    domain_order: list[str] = Field(default_factory=list)
    fusion_orientation: str | None = None
    linker_ids: list[str] = Field(default_factory=list)
    scaffold_id: str | None = None
    recruitment_tags: list[str] = Field(default_factory=list)
    enzyme_ids: list[str] = Field(default_factory=list)
    oc_n_terminal_truncation: bool | None = None
    experimental_baseline: bool = False
    coding_dna: str | None = None
    sequence_source_ref: str | None = None
    forbidden_restriction_sites: dict[str, str] | None = None
    idr_ids: list[str] = Field(default_factory=list)
    sequences: dict[str, str] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    oc_truncation_mapping: TruncationMapping | None = None

    @model_validator(mode="after")
    def _parts_contract(self) -> "ConstructDefinition":
        if not self.parts and not self.components:
            raise ValueError("construct_requires_ordered_parts_or_components")
        if self.parts and self.domain_order:
            raise ValueError("use_parts_or_domain_order_not_both")
        if len(self.linker_ids) > 1 and "linker" in self.domain_order:
            raise ValueError("multiple_linkers_require_explicit_part_ids")
        return self


class DesignConfig(StrictScientificConfig):
    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    protein_construct_ids: list[str] = Field(min_length=1)
    required_enzyme_ids: list[str] = Field(default_factory=list)
    host: str | None = None
    promoters: dict[str, str] = Field(default_factory=dict)
    integration_sites: dict[str, str] = Field(default_factory=dict)
    condition_id: str | None = None


class InputsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    protein_fasta: Path
    ligands: list[LigandConfig] = Field(default_factory=list)
    enzymes: list[EnzymeConfig]
    scaffolds: list[ScaffoldConfig]
    linkers: list[LinkerConfig]
    idr_id: str | None = None
    constructs: list[ConstructDefinition] = Field(default_factory=list)
    construct_records: list[ConstructRecord] = Field(default_factory=list)
    designs: list[DesignConfig] = Field(default_factory=list)


class ToolConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    mode: Literal["mock", "external"] = "mock"
    repo_path: Path | None = None
    command: str | None = None
    deployment_paths: list[Path] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class M1Config(StrictScientificConfig):
    top_n: int = Field(default=10, ge=1)
    forbidden_motifs: list[str] = Field(default_factory=list)
    feature_definitions_file: Path = DEFAULT_CONFIG_DIR / "m1_feature_definitions.yaml"
    rules_file: Path = DEFAULT_CONFIG_DIR / "m1_rules_v3.yaml"
    predictor_evidence_file: Path | None = None
    require_external_evidence_in_real_mode: bool = True


class M2Config(StrictScientificConfig):
    structure_metrics_file: Path | None = None


class AuthorNativeEnzymeScales(StrictScientificConfig):
    """Explicit nonphysical author-model enzyme scales for sensitivity runs."""

    ptr_scale: float = Field(ge=0)
    pt_scale: float = Field(ge=0)
    oc_scale: float = Field(ge=0)
    dmt_scale: float = Field(ge=0)
    source: Literal["published_author_model", "explicit_sensitivity_input"] = "published_author_model"
    interpretation: Literal["relative_enzyme_scale_not_measured_abundance"] = "relative_enzyme_scale_not_measured_abundance"


class M3Config(StrictScientificConfig):
    binding_model: Literal["independent", "hill"] = "independent"
    hill_coefficient: float | None = Field(default=None, gt=0)
    recruitment: list["RecruitmentConfig"] = Field(default_factory=list)
    recruitment_mode: Literal["finite_site", "legacy_independent_partition", "effective_ratio"] = "finite_site"
    slot_ratio_sh3_to_pdz: float | None = Field(default=None, ge=0)
    total_recruited_fraction: float | None = Field(default=None, ge=0, le=1)
    recruitment_bias_oc_vs_dmt: float = Field(default=1.0, ge=0)
    ptr_pt_phase_handling: Literal["dilute_only", "homogeneous_kp_1"] = "dilute_only"
    author_native_inputs: AuthorNativeEnzymeScales | None = None

    @model_validator(mode="after")
    def _effective_ratio_contract(self) -> "M3Config":
        if self.recruitment_mode == "effective_ratio" and (
            self.slot_ratio_sh3_to_pdz is None or self.total_recruited_fraction is None
        ):
            raise ValueError("effective_ratio_requires_slot_ratio_and_total_recruited_fraction")
        return self


class RecruitmentConfig(StrictScientificConfig):
    enzyme_id: str
    enzyme_total_parameter: str
    site_total_parameter: str
    kd_parameter: str
    hill_coefficient_parameter: str | None = None


class InitialStateConfig(StrictScientificConfig):
    concentration_unit: Literal["uM"] = "uM"
    x9: float = Field(ge=0)
    x10: float = Field(default=0, ge=0)
    x11: float = Field(default=0, ge=0)
    x13: float = Field(default=0, ge=0)
    x15: float = Field(default=0, ge=0)

    def as_tuple(self) -> tuple[float, float, float, float, float]:
        return self.x9, self.x10, self.x11, self.x13, self.x15


class FullNetworkInitialStateConfig(StrictScientificConfig):
    """Explicit 8--15 state for the audited full Galatea network."""

    concentration_unit: Literal["uM", "author_native"] = "uM"
    intracellular: dict[str, float]
    extracellular: dict[str, float] = Field(default_factory=lambda: {str(index): 0.0 for index in range(8, 16)})

    @model_validator(mode="after")
    def _complete_nonnegative_states(self) -> "FullNetworkInitialStateConfig":
        required = {str(index) for index in range(8, 16)}
        if set(self.intracellular) != required or set(self.extracellular) != required:
            raise ValueError("full_network_initial_state_requires_compounds_8_to_15")
        if any(value < 0 for value in [*self.intracellular.values(), *self.extracellular.values()]):
            raise ValueError("full_network_initial_state_must_be_nonnegative")
        return self


class InductionGateConfig(StrictScientificConfig):
    on_time: float = Field(ge=0)
    off_time: float | None = Field(default=None, gt=0)
    basal: float = Field(default=0, ge=0)
    induced: float = Field(default=1, ge=0)
    mode: Literal["step", "sigmoid"] = "step"
    transition_width: float = Field(default=0.25, gt=0)
    time_unit: Literal["h", "author_native_day_axis"] = "h"

    @model_validator(mode="after")
    def _validate_interval(self) -> "InductionGateConfig":
        if self.off_time is not None and self.off_time <= self.on_time:
            raise ValueError("off_time_must_be_greater_than_on_time")
        return self


class M4Config(StrictScientificConfig):
    target_product: str = "glabridin"
    t_end: float = Field(default=24.0, gt=0)
    initial_state: InitialStateConfig | None = None
    full_network_initial_state: FullNetworkInitialStateConfig | None = None
    reaction_network_file: Path | None = None
    steady_state_initial_guess_um: dict[str, float] | None = None
    pt_gate: InductionGateConfig | None = None
    oc_gate: InductionGateConfig | None = None
    dmt_gate: InductionGateConfig | None = None
    condition_id: str | None = None
    max_side_product_fraction_13: float = Field(default=0.35, ge=0, le=1)
    min_13_reduction: float = Field(default=0.05, ge=0, le=1)
    min_15_improvement: float = Field(default=0, ge=-1)
    min_productivity: float = Field(default=0, ge=0)
    enable_degradation: bool = False
    # The legacy reduced kernel remains for existing projects. New Galatea work
    # must explicitly opt into the audited full network rather than receiving a
    # silent interpretation of legacy five-state inputs.
    network_mode: Literal["markdown_steady_state", "legacy_reduced", "galatea_full_competitive", "published_reference"] = "markdown_steady_state"
    scenario_mode: Literal[
        "published_reference", "homogeneous_constitutive", "homogeneous_published_like_temporal",
        "galatea_spatial", "galatea_spatiotemporal_ablation"
    ] = "homogeneous_constitutive"
    unit_mode: Literal["physical", "author_native_sensitivity"] = "physical"
    author_native_time_label: Literal["author_native_day_axis"] = "author_native_day_axis"
    activity_mode: Literal["unity_assumption", "sensitivity_parameters"] = "unity_assumption"
    transport_access: Literal["dilute_phase", "cell_average"] = "dilute_phase"
    transport_enabled: bool = False
    transport_rate_parameter: str | None = None
    transport_outside_over_inside: dict[str, float] = Field(default_factory=lambda: {str(index): 0.0 for index in range(8, 16)})

    @model_validator(mode="after")
    def _scenario_contract(self) -> "M4Config":
        if self.network_mode == "published_reference" and self.scenario_mode != "published_reference":
            raise ValueError("published_reference_network_requires_published_reference_scenario")
        if self.scenario_mode == "published_reference" and self.network_mode != "published_reference":
            raise ValueError("published_reference_scenario_requires_published_reference_network")
        if self.network_mode == "legacy_reduced" and self.scenario_mode != "homogeneous_constitutive":
            raise ValueError("legacy_reduced_supports_only_homogeneous_constitutive")
        if self.network_mode == "markdown_steady_state" and self.scenario_mode != "homogeneous_constitutive":
            raise ValueError("markdown_steady_state_uses_the_original_constitutive_steady_equations")
        if self.steady_state_initial_guess_um is not None:
            if set(self.steady_state_initial_guess_um) != {str(index) for index in range(8, 16)} or any(value < 0 for value in self.steady_state_initial_guess_um.values()):
                raise ValueError("steady_state_initial_guess_requires_nonnegative_compounds_8_to_15")
        if self.network_mode == "galatea_full_competitive" and self.scenario_mode == "published_reference":
            raise ValueError("full_network_cannot_route_to_published_reference")
        if self.scenario_mode == "galatea_spatial" and self.dmt_gate is not None:
            raise ValueError("galatea_spatial_requires_constitutive_dmt_without_a_temporal_gate")
        if self.network_mode == "galatea_full_competitive" and self.full_network_initial_state is None:
            raise ValueError("full_network_requires_explicit_full_network_initial_state")
        if self.network_mode == "galatea_full_competitive" and self.reaction_network_file is None:
            raise ValueError("full_network_requires_reaction_network_file")
        if self.network_mode == "galatea_full_competitive" and self.full_network_initial_state is not None:
            expected = "author_native" if self.unit_mode == "author_native_sensitivity" else "uM"
            if self.full_network_initial_state.concentration_unit != expected:
                raise ValueError("full_network_initial_state_unit_must_match_m4_unit_mode")
        if self.unit_mode == "author_native_sensitivity" and self.network_mode != "galatea_full_competitive":
            raise ValueError("author_native_sensitivity_requires_galatea_full_competitive_network")
        if self.unit_mode == "author_native_sensitivity" and self.transport_enabled:
            raise ValueError("author_native_transport_is_not_supported; disable_transport")
        if self.unit_mode == "author_native_sensitivity":
            for gate in (self.pt_gate, self.oc_gate, self.dmt_gate):
                if gate is not None and gate.time_unit != "author_native_day_axis":
                    raise ValueError("author_native_sensitivity_gate_requires_author_native_day_axis")
        if self.scenario_mode == "homogeneous_published_like_temporal" and self.dmt_gate is None:
            raise ValueError("homogeneous_published_like_temporal_requires_dmt_gate")
        if set(self.transport_outside_over_inside) != {str(index) for index in range(8, 16)} or any(value < 0 for value in self.transport_outside_over_inside.values()):
            raise ValueError("transport_outside_over_inside_requires_nonnegative_compounds_8_to_15")
        return self


def canonical_m4_condition_id(config: M4Config) -> str | None:
    """Stable condition scope shared by M3/M4, MCP, agent and ProjectState."""
    if config.condition_id:
        return config.condition_id
    gates = (config.pt_gate, config.oc_gate, config.dmt_gate)
    if any(gate is None for gate in gates):
        return None
    def encode(name: str, gate: InductionGateConfig) -> str:
        return f"{name}[on={gate.on_time:g},off={gate.off_time},basal={gate.basal:g},induced={gate.induced:g},mode={gate.mode},width={gate.transition_width:g}]"
    return "|".join(encode(name, gate) for name, gate in zip(("pt", "oc", "dmt"), gates, strict=True))


class FitPlanConfig(StrictScientificConfig):
    parameter_name: str
    fixed_parameter_names: list[str] = Field(default_factory=list)
    bounds: tuple[float, float]
    observables: list[Literal["13", "15"]] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_plan(self) -> "FitPlanConfig":
        if self.bounds[0] >= self.bounds[1]:
            raise ValueError("fit_bounds_must_be_strictly_increasing")
        if len(set(self.fixed_parameter_names)) != len(self.fixed_parameter_names):
            raise ValueError("fixed_parameter_names_must_be_unique")
        if self.parameter_name in self.fixed_parameter_names:
            raise ValueError("fit_target_cannot_be_fixed")
        return self


class M5Config(StrictScientificConfig):
    wetlab_results_file: Path | None = None
    absolute_residual_tolerance: float = Field(default=0.0, ge=0)
    relative_residual_tolerance: float = Field(default=0.0, ge=0)
    discrepancy_threshold_configured: bool = False
    fit_plan: FitPlanConfig | None = None


class StagesConfig(StrictScientificConfig):
    m1_llps: M1Config = Field(default_factory=M1Config)
    m2_fusion: M2Config = Field(default_factory=M2Config)
    m3_concentration: M3Config = Field(default_factory=M3Config)
    m4_reaction: M4Config = Field(default_factory=M4Config)
    m5_feedback: M5Config = Field(default_factory=M5Config)


class ProjectConfig(StrictScientificConfig):
    run: RunConfig
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    experimental_context: ExperimentalContext = Field(default_factory=ExperimentalContext)
    inputs: InputsConfig
    tools: dict[str, ToolConfig] = Field(default_factory=dict)
    parameters: list[ParameterRecord] = Field(default_factory=list)
    stages: StagesConfig = Field(default_factory=StagesConfig)

    @model_validator(mode="after")
    def _validate_references(self) -> "ProjectConfig":
        def unique(items: list[object], label: str) -> None:
            values = [getattr(item, "id", getattr(item, "construct_id", None)) for item in items]
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate_{label}_id")
        unique(self.inputs.linkers, "linker"); unique(self.inputs.scaffolds, "scaffold"); unique(self.inputs.enzymes, "enzyme"); unique(self.inputs.constructs, "construct")
        unique(self.inputs.construct_records, "construct_record"); unique(self.inputs.designs, "design")
        approved_records = [record for record in self.inputs.construct_records if record.review_status == "approved"]
        definitions = [*self.inputs.constructs, *(ConstructDefinition.model_validate(record.candidate_definition()) for record in approved_records)]
        unique(definitions, "combined_construct")
        definitions_by_id = {item.id: item for item in definitions}
        for design in self.inputs.designs:
            if design.id in definitions_by_id or len(set(design.protein_construct_ids)) != len(design.protein_construct_ids):
                raise ValueError("duplicate_design_or_protein_id")
            if any(identifier not in definitions_by_id for identifier in design.protein_construct_ids):
                raise ValueError("design_references_unknown_protein_construct")
            enzymes = {enzyme for identifier in design.protein_construct_ids for enzyme in definitions_by_id[identifier].enzyme_ids}
            if not set(design.required_enzyme_ids) <= enzymes:
                raise ValueError("design_missing_required_enzyme_construct")
        ParameterRegistry = __import__("igem_drylab.parameters", fromlist=["ParameterRegistry"]).ParameterRegistry
        ParameterRegistry(self.parameters)
        linker_ids, scaffold_ids, enzyme_ids = {item.id for item in self.inputs.linkers}, {item.id for item in self.inputs.scaffolds}, {item.id for item in self.inputs.enzymes}
        for construct in self.inputs.constructs:
            embedded = set(construct.sequences) | {part.id for part in construct.parts}
            if any(item not in linker_ids | embedded for item in construct.linker_ids): raise ValueError("construct_references_unknown_linker")
            if construct.scaffold_id and construct.scaffold_id not in scaffold_ids: raise ValueError("construct_references_unknown_scaffold")
            if any(item not in enzyme_ids for item in construct.enzyme_ids): raise ValueError("construct_references_unknown_enzyme")
        if self.execution.mode == "real" and self.stages.m4_reaction.condition_id is None and any((self.stages.m4_reaction.initial_state, self.stages.m4_reaction.full_network_initial_state, self.stages.m4_reaction.steady_state_initial_guess_um, self.stages.m4_reaction.pt_gate, self.stages.m4_reaction.oc_gate, self.stages.m4_reaction.dmt_gate)):
            raise ValueError("real_mode_requires_explicit_condition_id")
        if self.stages.m4_reaction.unit_mode == "author_native_sensitivity":
            if self.stages.m3_concentration.recruitment_mode != "effective_ratio":
                raise ValueError("author_native_sensitivity_requires_effective_ratio_m3")
            if self.stages.m3_concentration.author_native_inputs is None:
                raise ValueError("author_native_sensitivity_requires_explicit_author_native_enzyme_scales")
        return self


def load_config(path: Path) -> ProjectConfig:
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    return _resolve_relative_paths(ProjectConfig.model_validate(raw), path.parent)


def _resolve_path(path: Path | None, base_dir: Path) -> Path | None:
    if path is None or path.is_absolute():
        return path
    return base_dir / path


def _resolve_relative_paths(config: ProjectConfig, base_dir: Path) -> ProjectConfig:
    config.inputs.protein_fasta = _resolve_path(config.inputs.protein_fasta, base_dir)  # type: ignore[assignment]
    for ligand in config.inputs.ligands:
        ligand.sdf = _resolve_path(ligand.sdf, base_dir)  # type: ignore[assignment]
    for enzyme in config.inputs.enzymes:
        enzyme.structure_pdb = _resolve_path(enzyme.structure_pdb, base_dir)  # type: ignore[assignment]
    for scaffold in config.inputs.scaffolds:
        scaffold.structure_pdb = _resolve_path(scaffold.structure_pdb, base_dir)  # type: ignore[assignment]
    for tool in config.tools.values():
        tool.repo_path = _resolve_path(tool.repo_path, base_dir)  # type: ignore[assignment]
        tool.deployment_paths = [
            path if path.is_absolute() else base_dir / path
            for path in tool.deployment_paths
        ]
    config.stages.m1_llps.feature_definitions_file = _resolve_path(
        config.stages.m1_llps.feature_definitions_file,
        base_dir,
    )  # type: ignore[assignment]
    config.stages.m1_llps.rules_file = _resolve_path(config.stages.m1_llps.rules_file, base_dir)  # type: ignore[assignment]
    config.stages.m1_llps.predictor_evidence_file = _resolve_path(
        config.stages.m1_llps.predictor_evidence_file,
        base_dir,
    )  # type: ignore[assignment]
    config.stages.m2_fusion.structure_metrics_file = _resolve_path(
        config.stages.m2_fusion.structure_metrics_file,
        base_dir,
    )  # type: ignore[assignment]
    config.stages.m4_reaction.reaction_network_file = _resolve_path(config.stages.m4_reaction.reaction_network_file, base_dir)  # type: ignore[assignment]
    config.stages.m5_feedback.wetlab_results_file = _resolve_path(config.stages.m5_feedback.wetlab_results_file, base_dir)  # type: ignore[assignment]
    if config.execution.mode == "real":
        required_files = [
            config.inputs.protein_fasta,
            config.stages.m1_llps.feature_definitions_file,
            config.stages.m1_llps.rules_file,
        ]
        required_files.extend(item.sdf for item in config.inputs.ligands if item.sdf is not None)
        required_files.extend(item.structure_pdb for item in [*config.inputs.enzymes, *config.inputs.scaffolds] if item.structure_pdb is not None)
        required_files.extend([config.stages.m2_fusion.structure_metrics_file, config.stages.m5_feedback.wetlab_results_file])
        required_files.append(config.stages.m4_reaction.reaction_network_file)
        missing = [str(item) for item in required_files if item is not None and not item.exists()]
        if missing:
            raise ValueError(f"real_mode_references_missing_file:{','.join(missing)}")
    fasta_ids = _fasta_ids(config.inputs.protein_fasta)
    if any(enzyme.sequence_sha256 for enzyme in config.inputs.enzymes):
        from hashlib import sha256
        from .stages import _read_fasta_sequences
        sequences = _read_fasta_sequences(config.inputs.protein_fasta)
        for enzyme in config.inputs.enzymes:
            if enzyme.sequence_sha256 and sha256(sequences.get(enzyme.protein_id, "").encode("ascii")).hexdigest() != enzyme.sequence_sha256:
                raise ValueError(f"enzyme_sequence_sha256_mismatch:{enzyme.id}")
    required_ids = {item.protein_id for item in config.inputs.enzymes}
    if config.inputs.idr_id is not None:
        required_ids.add(config.inputs.idr_id)
    embedded_ids = {identifier for item in config.inputs.constructs for identifier in item.sequences}
    embedded_ids.update(part.id for item in config.inputs.constructs for part in item.parts if part.sequence is not None)
    embedded_ids.update(identifier for record in config.inputs.construct_records if record.review_status == "approved" for identifier in record.sequences)
    absent = sorted(required_ids - fasta_ids - embedded_ids)
    if absent:
        raise ValueError(f"protein_id_missing_from_fasta:{','.join(absent)}")
    return config


def _fasta_ids(path: Path) -> set[str]:
    """Read FASTA header IDs for lightweight sequence-provenance validation."""
    if not path.exists():
        return set()
    return {
        line[1:].strip().split()[0]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith(">") and line[1:].strip()
    }

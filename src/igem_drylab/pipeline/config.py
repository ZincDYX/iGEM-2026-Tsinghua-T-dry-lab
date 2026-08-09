from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator
from igem_drylab.parameters import ParameterRecord
from igem_drylab.constructs import ConstructRecord


class RunConfig(BaseModel):
    id: str = "demo-run"
    output_dir: Path = Path("outputs")


class ExecutionConfig(BaseModel):
    """Controls whether fixture values may be used as non-scientific demonstrations."""

    mode: Literal["demo", "real"] = "demo"
    require_provenance: bool = True
    allow_assumptions: bool = False


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
    id: str
    name: str
    role: str
    sdf: Path | None = None


class EnzymeConfig(BaseModel):
    id: str
    protein_id: str
    reaction_role: str
    structure_pdb: Path | None = None


class ScaffoldConfig(BaseModel):
    id: str
    description: str
    oligomeric_state: int = Field(ge=1)
    structure_pdb: Path | None = None


class LinkerConfig(BaseModel):
    id: str
    sequence: str
    source: str = "unknown"


class ConstructDefinition(BaseModel):
    """A wet-lab construct description; no fusion topology is inferred by code."""

    id: str
    components: list[str] = Field(min_length=1)
    domain_order: list[str] = Field(default_factory=list)
    fusion_orientation: str | None = None
    linker_ids: list[str] = Field(default_factory=list)
    scaffold_id: str | None = None
    recruitment_tags: list[str] = Field(default_factory=list)
    enzyme_ids: list[str] = Field(default_factory=list)
    oc_n_terminal_truncation: bool | None = None

    @model_validator(mode="after")
    def _one_linker_contract(self) -> "ConstructDefinition":
        if len(self.linker_ids) > 1:
            raise ValueError("current_m1_contract_allows_exactly_one_linker_id")
        return self


class InputsConfig(BaseModel):
    protein_fasta: Path
    ligands: list[LigandConfig] = Field(default_factory=list)
    enzymes: list[EnzymeConfig]
    scaffolds: list[ScaffoldConfig]
    linkers: list[LinkerConfig]
    idr_id: str | None = None
    constructs: list[ConstructDefinition] = Field(default_factory=list)
    construct_records: list[ConstructRecord] = Field(default_factory=list)


class ToolConfig(BaseModel):
    enabled: bool = False
    mode: Literal["mock", "external"] = "mock"
    repo_path: Path | None = None
    command: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class M1Config(StrictScientificConfig):
    top_n: int = Field(default=10, ge=1)
    forbidden_motifs: list[str] = Field(default_factory=list)


class M2Config(StrictScientificConfig):
    structure_metrics_file: Path | None = None


class M3Config(StrictScientificConfig):
    binding_model: Literal["independent", "hill"] = "independent"
    hill_coefficient: float | None = Field(default=None, gt=0)
    recruitment: list["RecruitmentConfig"] = Field(default_factory=list)


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


class InductionGateConfig(StrictScientificConfig):
    on_time: float = Field(ge=0)
    off_time: float | None = Field(default=None, gt=0)
    basal: float = Field(default=0, ge=0)
    induced: float = Field(default=1, ge=0)
    mode: Literal["step", "sigmoid"] = "step"
    transition_width: float = Field(default=0.25, gt=0)
    time_unit: Literal["h"] = "h"

    @model_validator(mode="after")
    def _validate_interval(self) -> "InductionGateConfig":
        if self.off_time is not None and self.off_time <= self.on_time:
            raise ValueError("off_time_must_be_greater_than_on_time")
        return self


class M4Config(StrictScientificConfig):
    target_product: str = "glabridin"
    t_end: float = Field(default=24.0, gt=0)
    initial_state: InitialStateConfig | None = None
    pt_gate: InductionGateConfig | None = None
    oc_gate: InductionGateConfig | None = None
    dmt_gate: InductionGateConfig | None = None
    condition_id: str | None = None
    max_side_product_fraction_13: float = Field(default=0.35, ge=0, le=1)
    min_13_reduction: float = Field(default=0.05, ge=0, le=1)
    min_15_improvement: float = Field(default=0, ge=-1)
    min_productivity: float = Field(default=0, ge=0)
    enable_degradation: bool = False


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
        ParameterRegistry = __import__("igem_drylab.parameters", fromlist=["ParameterRegistry"]).ParameterRegistry
        ParameterRegistry(self.parameters)
        linker_ids, scaffold_ids, enzyme_ids = {item.id for item in self.inputs.linkers}, {item.id for item in self.inputs.scaffolds}, {item.id for item in self.inputs.enzymes}
        for construct in self.inputs.constructs:
            if any(item not in linker_ids for item in construct.linker_ids): raise ValueError("construct_references_unknown_linker")
            if construct.scaffold_id and construct.scaffold_id not in scaffold_ids: raise ValueError("construct_references_unknown_scaffold")
            if any(item not in enzyme_ids for item in construct.enzyme_ids): raise ValueError("construct_references_unknown_enzyme")
        if self.execution.mode == "real" and self.stages.m4_reaction.condition_id is None and any((self.stages.m4_reaction.initial_state, self.stages.m4_reaction.pt_gate, self.stages.m4_reaction.oc_gate, self.stages.m4_reaction.dmt_gate)):
            raise ValueError("real_mode_requires_explicit_condition_id")
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
    config.stages.m2_fusion.structure_metrics_file = _resolve_path(
        config.stages.m2_fusion.structure_metrics_file,
        base_dir,
    )  # type: ignore[assignment]
    config.stages.m5_feedback.wetlab_results_file = _resolve_path(config.stages.m5_feedback.wetlab_results_file, base_dir)  # type: ignore[assignment]
    return config

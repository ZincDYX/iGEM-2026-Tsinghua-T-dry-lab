from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field
from igem_drylab.parameters import ParameterRecord


class RunConfig(BaseModel):
    id: str = "demo-run"
    output_dir: Path = Path("outputs")
    random_seed: int = 42


class ExecutionConfig(BaseModel):
    """Controls whether fixture values may be used as non-scientific demonstrations."""

    mode: Literal["demo", "real"] = "demo"
    require_provenance: bool = True
    allow_assumptions: bool = False


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


class InputsConfig(BaseModel):
    protein_fasta: Path
    ligands: list[LigandConfig] = Field(default_factory=list)
    enzymes: list[EnzymeConfig]
    scaffolds: list[ScaffoldConfig]
    linkers: list[LinkerConfig]
    idr_id: str | None = None
    constructs: list[ConstructDefinition] = Field(default_factory=list)


class ToolConfig(BaseModel):
    enabled: bool = False
    mode: Literal["mock", "external"] = "mock"
    repo_path: Path | None = None
    command: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class M1Config(BaseModel):
    top_n: int = Field(default=10, ge=1)
    forbidden_motifs: list[str] = Field(default_factory=list)


class M2Config(BaseModel):
    activity_penalty_weight: float = Field(default=0.35, ge=0, le=1)
    clash_penalty_weight: float = Field(default=0.25, ge=0, le=1)
    structure_metrics_file: Path | None = None


class M3Config(BaseModel):
    binding_model: Literal["independent", "hill"] = "independent"
    hill_coefficient: float | None = Field(default=None, gt=0)


class M4Config(BaseModel):
    target_product: str = "glabridin"
    oc_first_weight: float = Field(default=0.60, ge=0, le=1)
    dmt_later_weight: float = Field(default=0.40, ge=0, le=1)
    docking_penalties_file: Path | None = None
    t_end: float = Field(default=24.0, gt=0)


class StagesConfig(BaseModel):
    m1_llps: M1Config = Field(default_factory=M1Config)
    m2_fusion: M2Config = Field(default_factory=M2Config)
    m3_concentration: M3Config = Field(default_factory=M3Config)
    m4_reaction: M4Config = Field(default_factory=M4Config)


class ProjectConfig(BaseModel):
    run: RunConfig
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    inputs: InputsConfig
    tools: dict[str, ToolConfig] = Field(default_factory=dict)
    parameters: list[ParameterRecord] = Field(default_factory=list)
    stages: StagesConfig = Field(default_factory=StagesConfig)


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
    config.stages.m4_reaction.docking_penalties_file = _resolve_path(
        config.stages.m4_reaction.docking_penalties_file,
        base_dir,
    )  # type: ignore[assignment]
    return config

from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field


class RunConfig(BaseModel):
    id: str = "demo-run"
    output_dir: Path = Path("outputs")
    random_seed: int = 42


class LigandConfig(BaseModel):
    id: str
    name: str
    role: str
    sdf: Path


class EnzymeConfig(BaseModel):
    id: str
    protein_id: str
    reaction_role: str
    structure_pdb: Optional[Path] = None


class ScaffoldConfig(BaseModel):
    id: str
    description: str
    oligomeric_state: int = Field(ge=1)
    structure_pdb: Optional[Path] = None


class LinkerConfig(BaseModel):
    id: str
    sequence: str
    source: str = "unknown"


class InputsConfig(BaseModel):
    protein_fasta: Path
    ligands: list[LigandConfig]
    enzymes: list[EnzymeConfig]
    scaffolds: list[ScaffoldConfig]
    linkers: list[LinkerConfig]


class ToolConfig(BaseModel):
    enabled: bool = False
    mode: Literal["mock", "external"] = "mock"
    repo_path: Optional[Path] = None
    command: Optional[str] = None
    extra: dict[str, Any] = Field(default_factory=dict)


class M1Config(BaseModel):
    top_n: int = Field(default=10, ge=1)
    min_llps_score: float = Field(default=0.45, ge=0, le=1)


class M2Config(BaseModel):
    activity_penalty_weight: float = Field(default=0.35, ge=0, le=1)
    clash_penalty_weight: float = Field(default=0.25, ge=0, le=1)


class M3Config(BaseModel):
    saturation_threshold: float = Field(default=0.70, ge=0, le=1)
    leakage_threshold: float = Field(default=0.35, ge=0, le=1)


class M4Config(BaseModel):
    target_product: str = "glabridin"
    oc_first_weight: float = Field(default=0.60, ge=0, le=1)
    dmt_later_weight: float = Field(default=0.40, ge=0, le=1)


class StagesConfig(BaseModel):
    m1_llps: M1Config = Field(default_factory=M1Config)
    m2_fusion: M2Config = Field(default_factory=M2Config)
    m3_concentration: M3Config = Field(default_factory=M3Config)
    m4_reaction: M4Config = Field(default_factory=M4Config)


class ProjectConfig(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    run: RunConfig
    inputs: InputsConfig
    tools: dict[str, ToolConfig] = Field(default_factory=dict)
    stages: StagesConfig = Field(default_factory=StagesConfig)


def load_config(path: Path) -> ProjectConfig:
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    config = ProjectConfig.model_validate(raw)
    return _resolve_relative_paths(config, path.parent)


def _resolve_path(path: Optional[Path], base_dir: Path) -> Optional[Path]:
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
    return config

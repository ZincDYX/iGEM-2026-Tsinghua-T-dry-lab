from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class StageOutput(BaseModel):
    stage: str
    directory: Path
    json_file: Path
    csv_file: Path
    record_count: int


class PipelineManifest(BaseModel):
    run_id: str
    run_dir: Path
    stages: list[StageOutput]


class M1Candidate(BaseModel):
    candidate_id: str
    scaffold_id: str
    linker_id: str
    idr_id: str
    llps_score: float = Field(ge=0, le=1)
    oligomeric_state: int = Field(ge=1)
    predicted_state: Literal["reject", "borderline", "promising"]
    adapter: str
    notes: str


class M2FusionAssessment(BaseModel):
    candidate_id: str
    scaffold_id: str
    linker_id: str
    enzyme_pair: str
    fusion_topology: str
    structure_model: str
    activity_risk: float = Field(ge=0, le=1)
    clash_risk: float = Field(ge=0, le=1)
    m2_score: float = Field(ge=0, le=1)
    recommended_for_m3: bool
    notes: str


class M3ConcentrationAssessment(BaseModel):
    candidate_id: str
    local_concentration_fold_change: float = Field(ge=0)
    binding_equilibrium_hint: str
    saturation_risk: float = Field(ge=0, le=1)
    leakage_risk: float = Field(ge=0, le=1)
    oc_dmt_colocalization_score: float = Field(ge=0, le=1)
    recommended_for_m4: bool
    notes: str


class M4ReactionPrediction(BaseModel):
    candidate_id: str
    target_product: str
    oc_first_feasibility: float = Field(ge=0, le=1)
    dmt_later_feasibility: float = Field(ge=0, le=1)
    predicted_relative_yield: float = Field(ge=0, le=1)
    bottleneck: str
    recommendation: Literal["drop", "iterate", "test"]
    notes: str

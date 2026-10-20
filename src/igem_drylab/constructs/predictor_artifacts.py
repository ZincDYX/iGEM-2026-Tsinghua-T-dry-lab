"""Typed M1 evidence loading shared by stage execution and input snapshots."""
import json
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from .linker_features import (DisorderEvidence, SecondaryStructureEvidence, SegEvidence,
    ProtParamEvidence, FusionToolEvidence)
from igem_drylab.m1_prioritization import PredictorScore


class PredictorArtifactRecord(BaseModel):
    model_config=ConfigDict(extra="forbid")
    disorder: DisorderEvidence | None = None
    secondary_structure: SecondaryStructureEvidence | None = None
    seg: SegEvidence | None = None
    protparam: ProtParamEvidence | None = None
    fusion: FusionToolEvidence | None = None
    predictor_scores: list[PredictorScore] = Field(default_factory=list)


def load_predictor_artifacts(path: Path) -> dict[str,PredictorArtifactRecord]:
    raw=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw,dict):
        raise ValueError("M1_predictor_artifacts_require_ID_keyed_object")
    def resolve(value):
        if isinstance(value,BaseModel):
            for name in type(value).model_fields:
                item=getattr(value,name)
                if isinstance(item,Path) and not item.is_absolute():
                    setattr(value,name,(path.parent/item).resolve())
                else:
                    resolve(item)
        elif isinstance(value,dict):
            for item in value.values():
                resolve(item)
        elif isinstance(value,list):
            for item in value:
                resolve(item)
    records={identifier:PredictorArtifactRecord.model_validate(item) for identifier,item in raw.items()}
    for record in records.values():
        resolve(record)
    return records

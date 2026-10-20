"""Explicit OC/DMT-only topology, backed by reviewed genetic/background absence."""
from hashlib import sha256
from pathlib import Path
from pydantic import BaseModel,ConfigDict,Field


class AbsenceEvidenceBinding(BaseModel):
    model_config=ConfigDict(extra="forbid",str_strip_whitespace=True)
    artifact: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewed_by: str = Field(min_length=1)


class VerifiedAbsenceRecord(BaseModel):
    model_config=ConfigDict(extra="forbid",str_strip_whitespace=True)
    construct_id: str
    condition_id: str
    host: str
    strain: str
    confirmed_absent_enzymes: dict[str,str]
    source_reference: str = Field(min_length=1)
    verification_method: str = Field(min_length=1)
    reviewed_by: str = Field(min_length=1)


def verify_absence_evidence(binding, *, construct_id,condition_id,host,strain):
    raw=binding.artifact.read_bytes()
    if sha256(raw).hexdigest()!=binding.sha256:
        raise ValueError("active_subnetwork_absence_artifact_hash_mismatch")
    record=VerifiedAbsenceRecord.model_validate_json(raw)
    expected=dict(construct_id=construct_id,condition_id=condition_id,host=host,strain=strain,reviewed_by=binding.reviewed_by)
    if any(getattr(record,key)!=value or not value for key,value in expected.items()):
        raise ValueError("active_subnetwork_absence_identity_or_condition_mismatch")
    if record.confirmed_absent_enzymes!={"PTR":"genetic_and_background_activity_absent","PT":"genetic_and_background_activity_absent"}:
        raise ValueError("active_subnetwork_requires_verified_PTR_PT_genetic_and_background_absence")
    return {**record.model_dump(mode="json"),"artifact_sha256":binding.sha256}

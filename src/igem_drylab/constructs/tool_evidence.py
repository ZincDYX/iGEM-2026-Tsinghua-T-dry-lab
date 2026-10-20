"""Verify tool artifacts at the M1 scientific trust boundary.

Hashes bind bytes and declarations, not an unforgeable claim of execution.
Automated records must be produced by the tool runner. Manual interpretations
remain explicitly manual and require a reviewer and reviewed observations.
"""
import json
from hashlib import sha256
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ToolEvidenceProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    origin: Literal["automated", "manual_review"]
    output_sha256: str
    record_file: Path
    record_sha256: str


def verify_artifact(provenance, source_file, tool_name, tool_version, input_sha256, observations):
    if provenance is None or source_file is None or not tool_version:
        return False
    if not source_file.is_file() or not provenance.record_file.is_file():
        return False
    if sha256(source_file.read_bytes()).hexdigest() != provenance.output_sha256:
        raise ValueError(f"{tool_name}_output_hash_mismatch")
    raw = provenance.record_file.read_bytes()
    if sha256(raw).hexdigest() != provenance.record_sha256:
        raise ValueError(f"{tool_name}_record_hash_mismatch")
    record = json.loads(raw)
    for key, expected in {"tool_name": tool_name, "tool_version": tool_version,
                          "input_sha256": input_sha256, "output_sha256": provenance.output_sha256}.items():
        if record.get(key) != expected:
            raise ValueError(f"{tool_name}_record_{key}_mismatch")
    if provenance.origin == "automated":
        return record.get("origin") == "automated" and record.get("returncode") == 0 and bool(record.get("command"))
    reviewed = (record.get("origin") == "manual_review" and bool(record.get("reviewer")) and
                bool(record.get("source_reference")) and record.get("decision") == "approved")
    if reviewed and record.get("reviewed_observations") != observations:
        raise ValueError(f"{tool_name}_summary_or_array_mismatch:reviewed_observations")
    return reviewed

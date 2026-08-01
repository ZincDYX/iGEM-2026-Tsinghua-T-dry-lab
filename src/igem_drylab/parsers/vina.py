from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field


class VinaPose(BaseModel):
    mode: int
    affinity_kcal_mol: float
    rmsd_lb: float | None = None
    rmsd_ub: float | None = None


class VinaResult(BaseModel):
    poses: list[VinaPose]
    best_affinity_kcal_mol: float
    source_file: Path


_POSE_RE = re.compile(
    r"^\s*(?P<mode>\d+)\s+(?P<affinity>[+-]?\d+(?:\.\d+)?)"
    r"(?:\s+(?P<rmsd_lb>[+-]?\d+(?:\.\d+)?))?"
    r"(?:\s+(?P<rmsd_ub>[+-]?\d+(?:\.\d+)?))?\s*$"
)


def parse_vina_output(path: Path) -> VinaResult:
    poses: list[VinaPose] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = _POSE_RE.match(line)
        if not match:
            continue
        poses.append(
            VinaPose(
                mode=int(match.group("mode")),
                affinity_kcal_mol=float(match.group("affinity")),
                rmsd_lb=_optional_float(match.group("rmsd_lb")),
                rmsd_ub=_optional_float(match.group("rmsd_ub")),
            )
        )
    if not poses:
        raise ValueError(f"No Vina pose table parsed from {path}")
    best = min(pose.affinity_kcal_mol for pose in poses)
    return VinaResult(poses=poses, best_affinity_kcal_mol=best, source_file=path)


def _optional_float(value: str | None) -> float | None:
    return None if value is None else float(value)

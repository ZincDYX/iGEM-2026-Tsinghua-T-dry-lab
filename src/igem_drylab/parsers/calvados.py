from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, Field


class CalvadosResult(BaseModel):
    source_dir: Path
    dense_phase_concentration: float | None = Field(default=None, ge=0)
    dilute_phase_concentration: float | None = Field(default=None, ge=0)
    enrichment_factor: float | None = Field(default=None, ge=0)
    saturation_concentration: float | None = Field(default=None, ge=0)
    rg_mean: float | None = Field(default=None, ge=0)
    llps_score: float = Field(ge=0, le=1)
    evidence_files: list[Path] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def parse_calvados_output(path: Path) -> CalvadosResult:
    """Parse common CALVADOS analysis artifacts.

    CALVADOS analysis layouts vary by workflow. This parser supports explicit
    summary JSON first, then falls back to density profile CSV estimates.
    """
    path = Path(path)
    if path.is_file() and path.suffix.lower() == ".json":
        return _parse_summary_json(path)
    if not path.is_dir():
        raise ValueError(f"CALVADOS output path must be a directory or JSON file: {path}")
    json_summary = _find_summary_json(path)
    if json_summary is not None:
        return _parse_summary_json(json_summary)
    density_csv = _find_density_csv(path)
    if density_csv is not None:
        return _parse_density_csv(path, density_csv)
    raise ValueError(f"No supported CALVADOS summary or density profile found under {path}")


def _parse_summary_json(path: Path) -> CalvadosResult:
    payload = json.loads(path.read_text(encoding="utf-8"))
    dense = _first_float(payload, "dense_phase_concentration", "dense_concentration", "c_dense")
    dilute = _first_float(payload, "dilute_phase_concentration", "dilute_concentration", "c_dilute")
    ef = _first_float(payload, "enrichment_factor", "partition_coefficient", "kp")
    if ef is None and dense is not None and dilute and dilute > 0:
        ef = dense / dilute
    csat = _first_float(payload, "saturation_concentration", "csat", "c_sat")
    rg = _first_float(payload, "rg_mean", "mean_rg", "radius_of_gyration")
    return CalvadosResult(
        source_dir=path.parent,
        dense_phase_concentration=dense,
        dilute_phase_concentration=dilute,
        enrichment_factor=ef,
        saturation_concentration=csat,
        rg_mean=rg,
        llps_score=_llps_score(enrichment_factor=ef, dense=dense, dilute=dilute),
        evidence_files=[path],
        notes=["parsed_summary_json"],
    )


def _parse_density_csv(source_dir: Path, path: Path) -> CalvadosResult:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig", newline="")))
    if not rows:
        raise ValueError(f"Empty CALVADOS density CSV: {path}")
    density_key = _pick_column(rows[0], ("density", "concentration", "rho", "protein_density"))
    if density_key is None:
        raise ValueError("Density CSV must contain density/concentration/rho column")
    values = np.asarray([float(row[density_key]) for row in rows if row.get(density_key, "") != ""], dtype=float)
    if values.size == 0:
        raise ValueError("Density CSV contains no numeric density values")
    dense = float(np.quantile(values, 0.90))
    dilute = float(np.quantile(values, 0.10))
    ef = dense / dilute if dilute > 0 else None
    return CalvadosResult(
        source_dir=source_dir,
        dense_phase_concentration=dense,
        dilute_phase_concentration=dilute,
        enrichment_factor=ef,
        llps_score=_llps_score(enrichment_factor=ef, dense=dense, dilute=dilute),
        evidence_files=[path],
        notes=["estimated_from_density_profile_quantiles"],
    )


def _find_summary_json(path: Path) -> Path | None:
    candidates = [
        item
        for item in path.rglob("*.json")
        if any(token in item.name.lower() for token in ("summary", "analysis", "phase", "calvados"))
    ]
    return sorted(candidates, key=lambda item: len(item.parts))[0] if candidates else None


def _find_density_csv(path: Path) -> Path | None:
    candidates = [
        item
        for item in path.rglob("*.csv")
        if any(token in item.name.lower() for token in ("density", "profile", "slab", "concentration"))
    ]
    return sorted(candidates, key=lambda item: len(item.parts))[0] if candidates else None


def _first_float(payload: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        if key in payload and payload[key] is not None:
            return float(payload[key])
    return None


def _pick_column(row: dict[str, str], names: tuple[str, ...]) -> str | None:
    lower = {key.lower(): key for key in row}
    for name in names:
        if name in lower:
            return lower[name]
    return None


def _llps_score(*, enrichment_factor: float | None, dense: float | None, dilute: float | None) -> float:
    if enrichment_factor is not None:
        return max(0.0, min(1.0, np.log10(max(enrichment_factor, 1.0)) / 3.0))
    if dense is not None and dilute is not None and dense > dilute:
        return 0.5
    return 0.0

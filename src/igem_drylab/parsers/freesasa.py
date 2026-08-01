from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, Field

from igem_drylab.structure_metrics import residue_sasa


class FreeSasaResidueArea(BaseModel):
    chain: str
    residue: int
    total: float = Field(ge=0)


class PocketSasaResult(BaseModel):
    model_sasa: float = Field(ge=0)
    reference_sasa: float = Field(gt=0)
    retention: float = Field(ge=0)
    loss_fraction: float = Field(ge=0)
    threshold_loss_fraction: float = Field(default=0.15, ge=0, le=1)
    passes: bool
    source: str


def parse_freesasa_json(path: Path) -> list[FreeSasaResidueArea]:
    """Parse common FreeSASA residue-area JSON shapes.

    FreeSASA command/API output varies by wrapper. This parser accepts:
    - {"residueAreas": {"A": {"42": {"total": 123.4}}}}
    - {"chains": {"A": {"residues": {"42": {"total": 123.4}}}}}
    - [{"chain": "A", "residue": 42, "total": 123.4}]
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [_coerce_area(item) for item in payload]
    if not isinstance(payload, dict):
        raise ValueError("FreeSASA JSON must be an object or list")
    residue_areas = payload.get("residueAreas")
    if isinstance(residue_areas, dict):
        return _parse_residue_area_map(residue_areas)
    chains = payload.get("chains")
    if isinstance(chains, dict):
        areas: list[FreeSasaResidueArea] = []
        for chain_id, chain_payload in chains.items():
            residues = chain_payload.get("residues", {}) if isinstance(chain_payload, dict) else {}
            for residue_id, area_payload in residues.items():
                areas.append(_area_from_nested(chain_id, residue_id, area_payload))
        return areas
    raise ValueError("Unsupported FreeSASA JSON shape")


def sum_residue_areas(areas: Iterable[FreeSasaResidueArea], *, chain: str, residues: Iterable[int]) -> float:
    residue_set = set(residues)
    return float(sum(area.total for area in areas if area.chain == chain and area.residue in residue_set))


def compute_pocket_sasa_retention(
    *,
    model_pdb: Path | None = None,
    reference_pdb: Path | None = None,
    model_json: Path | None = None,
    reference_json: Path | None = None,
    chain: str,
    residues: Iterable[int],
    threshold_loss_fraction: float = 0.15,
) -> PocketSasaResult:
    if not 0 <= threshold_loss_fraction <= 1:
        raise ValueError("threshold_loss_fraction must be between 0 and 1")
    if model_json and reference_json:
        model_sasa = sum_residue_areas(parse_freesasa_json(model_json), chain=chain, residues=residues)
        reference_sasa = sum_residue_areas(parse_freesasa_json(reference_json), chain=chain, residues=residues)
        source = "freesasa_json"
    elif model_pdb and reference_pdb:
        model_sasa = residue_sasa(model_pdb, chain=chain, residues=residues)
        reference_sasa = residue_sasa(reference_pdb, chain=chain, residues=residues)
        source = "freesasa_python_api"
    else:
        raise ValueError("Provide either model/reference JSON files or model/reference PDB files")
    if reference_sasa <= 0:
        raise ValueError("reference_sasa must be positive")
    retention = model_sasa / reference_sasa
    loss = max(0.0, 1.0 - retention)
    return PocketSasaResult(
        model_sasa=model_sasa,
        reference_sasa=reference_sasa,
        retention=retention,
        loss_fraction=loss,
        threshold_loss_fraction=threshold_loss_fraction,
        passes=loss <= threshold_loss_fraction,
        source=source,
    )


def _parse_residue_area_map(payload: dict[str, Any]) -> list[FreeSasaResidueArea]:
    areas: list[FreeSasaResidueArea] = []
    for chain_id, residues in payload.items():
        if not isinstance(residues, dict):
            continue
        for residue_id, area_payload in residues.items():
            areas.append(_area_from_nested(chain_id, residue_id, area_payload))
    return areas


def _area_from_nested(chain_id: str, residue_id: Any, payload: Any) -> FreeSasaResidueArea:
    total = payload.get("total", payload.get("Total", payload)) if isinstance(payload, dict) else payload
    return FreeSasaResidueArea(chain=str(chain_id), residue=_parse_residue_id(residue_id), total=float(total))


def _coerce_area(payload: dict[str, Any]) -> FreeSasaResidueArea:
    return FreeSasaResidueArea(
        chain=str(payload["chain"]),
        residue=_parse_residue_id(payload["residue"]),
        total=float(payload["total"]),
    )


def _parse_residue_id(value: Any) -> int:
    text = str(value)
    digits = "".join(character for character in text if character.isdigit() or character == "-")
    if not digits:
        raise ValueError(f"Cannot parse residue id: {value}")
    return int(digits)

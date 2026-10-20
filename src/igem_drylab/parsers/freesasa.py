from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Literal

from pydantic import BaseModel, Field

from igem_drylab.structure_metrics import residue_key, residue_sasa_areas


class FreeSasaResidueArea(BaseModel):
    chain: str
    residue: int
    total: float = Field(ge=0, allow_inf_nan=False)
    model_id: int = 1
    insertion: str = ""

    @property
    def identity(self) -> tuple[int, str, int, str]:
        return self.model_id, self.chain, self.residue, self.insertion


class SasaResidueSelection(BaseModel):
    model_id: int = 1
    chain: str
    residue: int
    insertion: str = Field(default="", max_length=1)

    @property
    def identity(self) -> tuple[int, str, int, str]:
        return self.model_id, self.chain, self.residue, self.insertion


class SasaResiduePair(BaseModel):
    reference: SasaResidueSelection
    model: SasaResidueSelection


class PocketSasaResult(BaseModel):
    model_sasa: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    reference_sasa: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    retention: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    loss_fraction: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    threshold_loss_fraction: float = Field(default=0.30, ge=0, le=1)
    status: Literal["valid", "insufficient_data"]
    same_configuration_verified: bool
    model_configuration_hash: str | None = None
    reference_configuration_hash: str | None = None
    passes: bool | None
    source: str
    missing_model_residues: list[SasaResidueSelection] = Field(default_factory=list)
    missing_reference_residues: list[SasaResidueSelection] = Field(default_factory=list)
    residue_mapping: list[SasaResiduePair] = Field(default_factory=list)
    reason: str | None = None


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
        return [area.model_copy(update={"model_id": int(payload.get("model_id", 1))}) for area in _parse_residue_area_map(residue_areas)]
    chains = payload.get("chains")
    if isinstance(chains, dict):
        areas: list[FreeSasaResidueArea] = []
        for chain_id, chain_payload in chains.items():
            residues = chain_payload.get("residues", {}) if isinstance(chain_payload, dict) else {}
            for residue_id, area_payload in residues.items():
                area = _area_from_nested(chain_id, residue_id, area_payload)
                areas.append(area.model_copy(update={"model_id": int(payload.get("model_id", 1))}))
        return areas
    raise ValueError("Unsupported FreeSASA JSON shape")


def _area_index(areas: Iterable[FreeSasaResidueArea]) -> dict[tuple[int, str, int, str], float]:
    result = {}
    for area in areas:
        if area.identity in result:
            raise ValueError(f"duplicate FreeSASA residue identity: {area.identity}")
        result[area.identity] = area.total
    return result


def sum_residue_areas(areas: Iterable[FreeSasaResidueArea], *, chain: str,
                     residues: Iterable[int | str], model_id: int | None = None) -> float:
    index = _area_index(areas)
    resolved_model = _select_model(index, model_id)
    keys = [(resolved_model, chain, *residue_key(value)) for value in residues]
    if not keys or len(set(keys)) != len(keys):
        raise ValueError("SASA selection must be nonempty and unique")
    missing = [key for key in keys if key not in index]
    if missing:
        raise ValueError(f"missing declared SASA residues: {missing}")
    return float(sum(index[key] for key in keys))


def _select_model(index: dict, model_id: int | None) -> int:
    models = sorted({key[0] for key in index})
    if model_id is None:
        if len(models) != 1:
            raise ValueError(f"select SASA model_id explicitly; available models: {models}")
        return models[0]
    return model_id


def compute_pocket_sasa_retention(
    *,
    model_pdb: Path | None = None,
    reference_pdb: Path | None = None,
    model_json: Path | None = None,
    reference_json: Path | None = None,
    chain: str,
    residues: Iterable[int | str],
    threshold_loss_fraction: float = 0.30,
    model_configuration_hash: str | None = None,
    reference_configuration_hash: str | None = None,
    model_id: int | None = None,
    reference_model_id: int | None = None,
    model_altloc: str | None = None,
    reference_altloc: str | None = None,
    residue_mapping: Iterable[SasaResiduePair | dict] | None = None,
) -> PocketSasaResult:
    if not 0 <= threshold_loss_fraction <= 1:
        raise ValueError("threshold_loss_fraction must be between 0 and 1")
    if model_json and reference_json:
        model_areas = parse_freesasa_json(model_json)
        reference_areas = parse_freesasa_json(reference_json)
        recorded_model = _recorded_configuration(model_json)
        recorded_reference = _recorded_configuration(reference_json)
        if recorded_model is not None or recorded_reference is not None:
            # Actual runner metadata is the configuration authority. Legacy
            # plain-area files still require explicitly supplied provenance.
            model_configuration_hash = recorded_model
            reference_configuration_hash = recorded_reference
        source = "freesasa_json"
        same_configuration = (
            model_configuration_hash is not None
            and reference_configuration_hash is not None
            and model_configuration_hash == reference_configuration_hash
        )
    elif model_pdb and reference_pdb:
        import freesasa
        parameters = freesasa.Parameters()
        model_id, model_values = residue_sasa_areas(model_pdb, model_id=model_id, altloc=model_altloc, parameters=parameters)
        reference_model_id, reference_values = residue_sasa_areas(reference_pdb, model_id=reference_model_id, altloc=reference_altloc, parameters=parameters)
        model_areas = [FreeSasaResidueArea(model_id=model_id, chain=c, residue=r, insertion=i, total=a) for (c, r, i), a in model_values.items()]
        reference_areas = [FreeSasaResidueArea(model_id=reference_model_id, chain=c, residue=r, insertion=i, total=a) for (c, r, i), a in reference_values.items()]
        source = "freesasa_python_api"
        # Both structures are evaluated by the same API call with the same
        # library defaults, so configuration identity is established here.
        same_configuration = True
    else:
        raise ValueError("Provide either model/reference JSON files or model/reference PDB files")
    model_index, reference_index = _area_index(model_areas), _area_index(reference_areas)
    declared = [residue_key(value) for value in residues]
    if residue_mapping is None:
        model_id = _select_model(model_index, model_id)
        reference_model_id = _select_model(reference_index, reference_model_id)
        pairs = [SasaResiduePair(
            reference=SasaResidueSelection(model_id=reference_model_id, chain=chain, residue=r, insertion=i),
            model=SasaResidueSelection(model_id=model_id, chain=chain, residue=r, insertion=i),
        ) for r, i in declared]
    else:
        pairs = [SasaResiduePair.model_validate(pair) for pair in residue_mapping]
    if not pairs or any(len({getattr(pair, side).identity for pair in pairs}) != len(pairs) for side in ("model", "reference")):
        raise ValueError("pocket SASA mapping must be nonempty and one-to-one")
    for side, selected_model in (("model", model_id), ("reference", reference_model_id)):
        side_models = {getattr(pair, side).model_id for pair in pairs}
        if len(side_models) != 1 or (selected_model is not None and side_models != {selected_model}):
            raise ValueError(f"{side} SASA mapping must select exactly one matching model")
    if declared and (len(pairs) != len(declared) or len(set(declared)) != len(declared) or {(pair.reference.residue, pair.reference.insertion) for pair in pairs if pair.reference.chain == chain} != set(declared)):
        raise ValueError("SASA mapping must cover every declared reference pocket residue exactly once")
    missing_model = [pair.model for pair in pairs if pair.model.identity not in model_index]
    missing_reference = [pair.reference for pair in pairs if pair.reference.identity not in reference_index]
    details = dict(threshold_loss_fraction=threshold_loss_fraction, same_configuration_verified=same_configuration,
                   model_configuration_hash=model_configuration_hash, reference_configuration_hash=reference_configuration_hash,
                   source=source, residue_mapping=pairs)
    if missing_model or missing_reference:
        return PocketSasaResult(**details, status="insufficient_data", passes=None,
            missing_model_residues=missing_model, missing_reference_residues=missing_reference,
            reason="Declared pocket residues are missing; no comparable SASA or retention is published.")
    model_sasa = float(sum(model_index[pair.model.identity] for pair in pairs))
    reference_sasa = float(sum(reference_index[pair.reference.identity] for pair in pairs))
    if reference_sasa <= 0:
        return PocketSasaResult(**details, model_sasa=model_sasa, reference_sasa=reference_sasa,
                                status="insufficient_data", passes=None, reason="Reference SASA is zero; retention is undefined.")
    retention = model_sasa / reference_sasa
    loss = max(0.0, 1.0 - retention)
    return PocketSasaResult(
        model_sasa=model_sasa,
        reference_sasa=reference_sasa,
        retention=retention,
        loss_fraction=loss,
        **details,
        status="valid" if same_configuration else "insufficient_data",
        passes=retention >= 1.0 - threshold_loss_fraction if same_configuration else None,
    )


def _recorded_configuration(path: Path) -> str | None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "sasa_configuration" not in payload:
        return None
    configuration = payload["sasa_configuration"]
    required = {"algorithm", "probe_radius_angstrom", "n_points", "n_slices", "n_threads", "structure_options", "classifier"}
    if (not isinstance(configuration, dict) or not required.issubset(configuration)
            or payload.get("tool_name") != "FreeSASA" or not payload.get("tool_version")):
        raise ValueError("incomplete recorded FreeSASA configuration")
    encoded = json.dumps(configuration, sort_keys=True, separators=(",", ":")).encode()
    if payload.get("sasa_configuration_sha256") != sha256(encoded).hexdigest():
        raise ValueError("recorded FreeSASA configuration hash mismatch")
    return sha256(json.dumps({"version": payload["tool_version"], "configuration": configuration},
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()


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
    number, insertion = residue_key(residue_id)
    return FreeSasaResidueArea(chain=str(chain_id), residue=number, insertion=insertion, total=float(total))


def _coerce_area(payload: dict[str, Any]) -> FreeSasaResidueArea:
    number, insertion = residue_key(payload["residue"])
    if insertion and payload.get("insertion", insertion) != insertion:
        raise ValueError("conflicting SASA residue insertion codes")
    return FreeSasaResidueArea(
        chain=str(payload["chain"]),
        residue=number,
        insertion=payload.get("insertion", insertion),
        model_id=payload.get("model_id", 1),
        total=float(payload["total"]),
    )

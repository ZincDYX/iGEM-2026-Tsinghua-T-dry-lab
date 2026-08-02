from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, Field


class StructurePredictionSummary(BaseModel):
    candidate_id: str
    source: str
    model_file: Path | None = None
    confidence_file: Path | None = None
    pae_file: Path | None = None
    plddt_file: Path | None = None
    ranking_score: float | None = None
    confidence_score: float | None = Field(default=None, ge=0)
    ptm: float | None = Field(default=None, ge=0, le=1)
    iptm: float | None = Field(default=None, ge=0, le=1)
    mean_plddt: float | None = Field(default=None, ge=0, le=100)
    mean_interdomain_pae: float | None = Field(default=None, ge=0)
    has_clash: bool | None = None
    chain_pair_iptm: list[list[float]] | None = None
    chain_pair_pae_min: list[list[float]] | None = None
    raw_keys: list[str] = Field(default_factory=list)


def parse_structure_prediction_output(path: Path, *, candidate_id: str | None = None) -> StructurePredictionSummary:
    """Parse common ColabFold, AF3, Boltz, Chai, and ABCFold confidence outputs.

    ABCFold is an orchestrator, so this parser scans its output directory for
    AF3-style JSON, Boltz confidence JSON/NPZ, or Chai scores JSON/NPZ.
    """
    path = Path(path)
    if path.is_file():
        return _parse_single_file(path, candidate_id=candidate_id or path.stem)
    files = [item for item in path.rglob("*") if item.is_file()]
    colabfold_ranking = _pick_colabfold_ranking(files)
    confidence_json = _pick_confidence_json(files)
    scores_npz = _pick_npz(files, prefixes=("scores",))
    pae_npz = _pick_npz(files, prefixes=("pae",))
    plddt_npz = _pick_npz(files, prefixes=("plddt",))
    model_file = _pick_model_file(files)
    if colabfold_ranking is not None:
        summary = _parse_colabfold_ranking(colabfold_ranking, candidate_id=candidate_id or path.name)
        return summary.model_copy(update={"model_file": model_file})
    if confidence_json is not None:
        summary = _parse_confidence_json(confidence_json, candidate_id=candidate_id or path.name)
        return summary.model_copy(
            update={
                "model_file": model_file,
                "pae_file": pae_npz,
                "plddt_file": plddt_npz,
                "mean_interdomain_pae": summary.mean_interdomain_pae or _mean_npz_array(pae_npz),
                "mean_plddt": summary.mean_plddt or _normalize_plddt(_mean_npz_array(plddt_npz)),
            }
        )
    if scores_npz is not None:
        summary = _parse_scores_npz(scores_npz, candidate_id=candidate_id or path.name)
        return summary.model_copy(update={"model_file": model_file, "pae_file": pae_npz, "plddt_file": plddt_npz})
    raise ValueError(f"No supported structure prediction confidence output found under {path}")


def _parse_single_file(path: Path, *, candidate_id: str) -> StructurePredictionSummary:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _parse_confidence_json(path, candidate_id=candidate_id)
    if suffix == ".npz":
        return _parse_scores_npz(path, candidate_id=candidate_id)
    raise ValueError(f"Unsupported structure prediction file: {path}")


def _parse_confidence_json(path: Path, *, candidate_id: str) -> StructurePredictionSummary:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list) and payload:
        payload = payload[0]
    if not isinstance(payload, dict):
        raise ValueError("Confidence JSON must be an object")
    source = _infer_source_from_json(path, payload)
    chain_pair_iptm = _as_float_matrix(_first_present(payload, "chain_pair_iptm", "pair_chains_iptm", "per_chain_pair_iptm"))
    chain_pair_pae_min = _as_float_matrix(payload.get("chain_pair_pae_min"))
    mean_plddt = _first_present(payload, "mean_plddt", "complex_plddt", "plddt")
    if mean_plddt is None and isinstance(payload.get("atom_plddts"), list):
        mean_plddt = float(np.mean(payload["atom_plddts"]))
    return StructurePredictionSummary(
        candidate_id=candidate_id,
        source=source,
        confidence_file=path,
        ranking_score=_optional_float(payload.get("ranking_score")),
        confidence_score=_optional_float(_first_present(payload, "confidence_score", "aggregate_score")),
        ptm=_optional_float(_first_present(payload, "ptm", "pTM")),
        iptm=_optional_float(_first_present(payload, "iptm", "iPTM", "protein_iptm")),
        mean_plddt=_normalize_plddt(_optional_float(mean_plddt)),
        mean_interdomain_pae=_matrix_off_diagonal_mean(chain_pair_pae_min),
        has_clash=_optional_bool(_first_present(payload, "has_clash", "has_inter_chain_clashes")),
        chain_pair_iptm=chain_pair_iptm,
        chain_pair_pae_min=chain_pair_pae_min,
        raw_keys=sorted(str(key) for key in payload.keys()),
    )


def _parse_colabfold_ranking(path: Path, *, candidate_id: str) -> StructurePredictionSummary:
    """Parse ``ranking_debug.json`` emitted by ColabFold/AlphaFold2.

    This file reports confidence per model.  It does not contain chain-boundary
    information, so this parser deliberately leaves ``mean_interdomain_pae``
    empty. Calculate a chain-pair PAE block separately when chain ranges are
    known.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("ColabFold ranking_debug.json must be an object")
    order = payload.get("order", [])
    model_name = order[0] if isinstance(order, list) and order else None
    if not isinstance(model_name, str):
        for key in ("iptm", "ptm", "plddts", "ranking_confidence"):
            values = payload.get(key)
            if isinstance(values, dict) and values:
                model_name = next(iter(values))
                break
    if not isinstance(model_name, str):
        raise ValueError("Could not identify a ranked ColabFold model")
    return StructurePredictionSummary(
        candidate_id=candidate_id,
        source="colabfold_af2_multimer",
        confidence_file=path,
        ranking_score=_mapping_value(payload.get("ranking_confidence"), model_name),
        ptm=_mapping_value(payload.get("ptm"), model_name),
        iptm=_mapping_value(payload.get("iptm"), model_name),
        mean_plddt=_normalize_plddt(_mapping_value(payload.get("plddts"), model_name)),
        raw_keys=sorted(str(key) for key in payload.keys()),
    )


def _parse_scores_npz(path: Path, *, candidate_id: str) -> StructurePredictionSummary:
    with np.load(path, allow_pickle=True) as data:
        keys = list(data.files)
        payload = {key: data[key] for key in keys}
        return StructurePredictionSummary(
            candidate_id=candidate_id,
            source="chai_or_npz_scores",
            confidence_file=path,
            confidence_score=_np_scalar(payload.get("aggregate_score")),
            ptm=_np_scalar(payload.get("ptm")),
            iptm=_np_scalar(payload.get("iptm")),
            mean_plddt=_normalize_plddt(_np_mean(payload.get("plddt"))),
            has_clash=_np_bool(payload.get("has_inter_chain_clashes")),
            chain_pair_iptm=_np_matrix(payload.get("per_chain_pair_iptm")),
            raw_keys=sorted(keys),
        )


def _pick_confidence_json(files: list[Path]) -> Path | None:
    ranked = sorted(
        [item for item in files if item.suffix.lower() == ".json" and any(token in item.name.lower() for token in ("summary_confidences", "confidence", "scores"))],
        key=lambda item: (0 if "summary_confidences" in item.name.lower() else 1, len(item.parts)),
    )
    return ranked[0] if ranked else None


def _pick_colabfold_ranking(files: list[Path]) -> Path | None:
    matches = [item for item in files if item.name.lower() == "ranking_debug.json"]
    return sorted(matches, key=lambda item: len(item.parts))[0] if matches else None


def _pick_npz(files: list[Path], *, prefixes: tuple[str, ...]) -> Path | None:
    matches = [
        item
        for item in files
        if item.suffix.lower() == ".npz" and any(item.name.lower().startswith(prefix) for prefix in prefixes)
    ]
    return sorted(matches, key=lambda item: len(item.parts))[0] if matches else None


def _pick_model_file(files: list[Path]) -> Path | None:
    matches = [item for item in files if item.suffix.lower() in {".cif", ".pdb"}]
    return sorted(matches, key=lambda item: len(item.parts))[0] if matches else None


def _infer_source_from_json(path: Path, payload: dict[str, Any]) -> str:
    name = path.name.lower()
    keys = set(payload)
    if "summary_confidences" in name or "ranking_score" in keys or "atom_plddts" in keys:
        return "alphafold3_or_abcfold_af3"
    if "confidence_score" in keys or "complex_plddt" in keys or "pair_chains_iptm" in keys:
        return "boltz_or_abcfold_boltz"
    if "aggregate_score" in keys or "per_chain_pair_iptm" in keys:
        return "chai_or_abcfold_chai"
    return "generic_structure_prediction"


def _first_present(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mapping_value(value: Any, key: str) -> float | None:
    if isinstance(value, dict):
        return _optional_float(value.get(key))
    return _optional_float(value)


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _normalize_plddt(value: float | None) -> float | None:
    if value is None:
        return None
    return value * 100 if 0 <= value <= 1 else value


def _as_float_matrix(value: Any) -> list[list[float]] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        rows = []
        for outer in sorted(value, key=lambda x: int(x) if str(x).isdigit() else str(x)):
            inner = value[outer]
            if isinstance(inner, dict):
                rows.append([float(inner[key]) for key in sorted(inner, key=lambda x: int(x) if str(x).isdigit() else str(x))])
        return rows
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError):
        return None
    if array.ndim == 3 and array.shape[0] == 1:
        array = array[0]
    if array.ndim != 2:
        return None
    return array.tolist()


def _matrix_off_diagonal_mean(matrix: list[list[float]] | None) -> float | None:
    if not matrix:
        return None
    array = np.asarray(matrix, dtype=float)
    if array.ndim != 2 or array.shape[0] != array.shape[1] or array.shape[0] < 2:
        return None
    mask = ~np.eye(array.shape[0], dtype=bool)
    return float(array[mask].mean())


def _mean_npz_array(path: Path | None) -> float | None:
    if path is None:
        return None
    with np.load(path, allow_pickle=True) as data:
        if not data.files:
            return None
        return _np_mean(data[data.files[0]])


def _np_scalar(value: Any) -> float | None:
    if value is None:
        return None
    array = np.asarray(value)
    if array.size == 0:
        return None
    return float(array.reshape(-1)[0])


def _np_mean(value: Any) -> float | None:
    if value is None:
        return None
    array = np.asarray(value, dtype=float)
    if array.size == 0:
        return None
    return float(array.mean())


def _np_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(np.asarray(value).any())


def _np_matrix(value: Any) -> list[list[float]] | None:
    if value is None:
        return None
    return _as_float_matrix(np.asarray(value, dtype=float))

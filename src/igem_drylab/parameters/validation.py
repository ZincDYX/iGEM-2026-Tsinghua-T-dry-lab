"""Deterministic evidence normalization and compatibility checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import ParameterRecord

UNIT_ALIASES = {
    "um": "uM", "\u03bcm": "uM", "\u00b5m": "uM", "mm": "mM", "m": "M",
    "min": "min", "mins": "min", "hr": "h", "hrs": "h", "hour": "h", "hours": "h",
}
_CONCENTRATION_TO_M = {"M": 1.0, "mM": 1e-3, "uM": 1e-6, "nM": 1e-9}
_TIME_TO_SECONDS = {"s": 1.0, "min": 60.0, "h": 3600.0}


@dataclass(frozen=True)
class Compatibility:
    level: str
    reasons: tuple[str, ...]


def normalize_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    cleaned = unit.strip().replace("\u03bc", "u").replace("\u00b5", "u")
    return UNIT_ALIASES.get(cleaned.lower(), cleaned)


def convert_value(value: float, from_unit: str, to_unit: str) -> float:
    """Convert only compatible, explicitly requested concentration/time units.

    Kinetic-rate units are deliberately excluded: their dimensional meaning has
    to be declared by the model rather than guessed from a text string.
    """
    source, target = normalize_unit(from_unit), normalize_unit(to_unit)
    for table in (_CONCENTRATION_TO_M, _TIME_TO_SECONDS):
        if source in table and target in table:
            return value * table[source] / table[target]
    raise ValueError(f"Cannot safely convert '{from_unit}' to '{to_unit}'")


def parameter_from_evidence(
    *, parameter_id: str, name: str, value: float | str, unit: str | None,
    source: dict[str, Any], parameter_type: str = "other", **identity: str | None,
) -> ParameterRecord:
    """Create an *extracted* candidate only; this function cannot approve evidence."""
    return ParameterRecord(
        parameter_id=parameter_id, name=name, value=value, unit=normalize_unit(unit),
        parameter_type=parameter_type, source_type="literature", doi=source.get("doi"),
        source_reference=source.get("title") or source.get("record_id"),
        evidence_text=source.get("evidence") or source.get("evidence_text"),
        evidence_location=source.get("evidence_location"), review_status="extracted",
        validation_flags=["requires_identity_and_human_review"], **identity,
    )


def identity_compatibility(
    record: ParameterRecord, *, enzyme_id: str | None = None,
    substrate_id: str | None = None, product_id: str | None = None,
    host: str | None = None, mutant_allowed: bool = False,
) -> Compatibility:
    reasons: list[str] = []
    for label, expected, observed in (
        ("enzyme", enzyme_id, record.enzyme_id),
        ("substrate", substrate_id, record.substrate_id),
        ("product", product_id, record.product_id),
    ):
        if expected and observed and expected != observed:
            return Compatibility("incompatible", (f"{label}_mismatch",))
        if expected and not observed:
            reasons.append(f"{label}_not_reported")
    if host and record.conditions.get("host") and record.conditions["host"] != host:
        return Compatibility("incompatible", ("host_mismatch",))
    if record.conditions.get("mutant") and not mutant_allowed:
        return Compatibility("incompatible", ("mutant_not_accepted",))
    return Compatibility("exact" if not reasons else "weak", tuple(reasons))


def condition_compatibility(
    record: ParameterRecord, *, host: str | None = None, temperature_c: float | None = None,
) -> Compatibility:
    """Classify stated assay-condition agreement without silently correcting it."""
    observed_host = record.conditions.get("host")
    if host and observed_host and observed_host != host:
        return Compatibility("incompatible", ("host_mismatch",))
    reasons: list[str] = []
    observed_temperature = record.conditions.get("temperature_c")
    if temperature_c is not None and isinstance(observed_temperature, (int, float)):
        delta = abs(float(observed_temperature) - temperature_c)
        if delta > 5:
            return Compatibility("incompatible", ("temperature_difference_gt_5C",))
        if delta > 2:
            reasons.append("temperature_difference_gt_2C")
    elif temperature_c is not None:
        reasons.append("temperature_not_reported")
    return Compatibility("exact" if not reasons else "weak", tuple(reasons))

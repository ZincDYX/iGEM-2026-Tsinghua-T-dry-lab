"""Explicit dimension and unit conversion rules used by the resolver."""

from __future__ import annotations

import math

from .requirements import ParameterRequirement

_CONCENTRATION = {"M": 1e6, "mM": 1e3, "uM": 1.0, "nM": 1e-3}
_RATE_TO_PER_HOUR = {"1/h": 1.0, "h^-1": 1.0, "h-1": 1.0, "1/min": 60.0, "1/s": 3600.0, "s^-1": 3600.0}
_CONCENTRATION_RATE_TO_UM_PER_HOUR = {"uM/h": 1.0, "mM/h": 1e3, "M/h": 1e6}
_DIMENSIONLESS = {"1", "dimensionless", None}
_VOLUME_TO_LITRE = {"L": 1., "mL": 1e-3, "uL": 1e-6, "µL": 1e-6, "μL": 1e-6}


def canonicalize_unit(unit: str | None) -> str | None:
    """Normalize accepted micro-molar spellings before dimension validation."""
    return {"µM": "uM", "μM": "uM", "碌M": "uM"}.get(unit, unit)


def normalize_concentration(value: float, unit: str | None) -> float:
    """Convert a declared concentration to the production canonical unit (uM)."""
    unit = canonicalize_unit(unit)
    if unit not in _CONCENTRATION:
        raise ValueError(f"unsupported_concentration_unit:{unit}")
    return float(value) * _CONCENTRATION[unit]


def normalize_for_requirement(value: float, unit: str | None, requirement: ParameterRequirement) -> float:
    """Return a canonical numeric value or raise; never infer dimensions."""
    unit = canonicalize_unit(unit)
    if requirement.dimension == "dimensionless":
        if unit not in _DIMENSIONLESS:
            raise ValueError(f"dimension_mismatch:{unit}:expected_dimensionless")
        return value
    tables = {"concentration": _CONCENTRATION, "rate": _RATE_TO_PER_HOUR, "concentration_rate": _CONCENTRATION_RATE_TO_UM_PER_HOUR, "volume": _VOLUME_TO_LITRE,
        "molar_energy":{"J/mol":1.0,"kJ/mol":1000.0,"kcal/mol":4184.0}}
    table = tables[requirement.dimension]
    if unit not in table:
        raise ValueError(f"dimension_mismatch:{unit}:expected_{requirement.dimension}")
    canonical = value * table[unit]
    if requirement.canonical_unit in {"uM", "1/h", "uM/h", "L", "J/mol"}:
        return canonical
    raise ValueError(f"unsupported_canonical_unit:{requirement.canonical_unit}")


def validate_requirement_value(value: float, unit: str | None, requirement: ParameterRequirement) -> float:
    """Shared normalization, finiteness, and physical-bound validation."""
    canonical = normalize_for_requirement(value, unit, requirement)
    if not math.isfinite(canonical):
        raise ValueError("nonfinite_value")
    if requirement.minimum is not None and (
        canonical < requirement.minimum
        or (canonical == requirement.minimum and not requirement.minimum_inclusive)
    ):
        raise ValueError("physical_lower_bound_violation")
    if requirement.maximum is not None and canonical > requirement.maximum:
        raise ValueError("physical_upper_bound_violation")
    return canonical

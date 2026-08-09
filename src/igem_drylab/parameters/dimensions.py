"""Explicit dimension and unit conversion rules used by the resolver."""

from __future__ import annotations

from .requirements import ParameterRequirement

_CONCENTRATION = {"M": 1e6, "mM": 1e3, "uM": 1.0, "nM": 1e-3}
_RATE_TO_PER_HOUR = {"1/h": 1.0, "h^-1": 1.0, "h-1": 1.0, "1/min": 60.0, "1/s": 3600.0, "s^-1": 3600.0}
_DIMENSIONLESS = {"1", "dimensionless", None}


def normalize_concentration(value: float, unit: str | None) -> float:
    """Convert a declared concentration to the production canonical unit (uM)."""
    if unit not in _CONCENTRATION:
        raise ValueError(f"unsupported_concentration_unit:{unit}")
    return float(value) * _CONCENTRATION[unit]


def normalize_for_requirement(value: float, unit: str | None, requirement: ParameterRequirement) -> float:
    """Return a canonical numeric value or raise; never infer dimensions."""
    if requirement.dimension == "dimensionless":
        if unit not in _DIMENSIONLESS:
            raise ValueError(f"dimension_mismatch:{unit}:expected_dimensionless")
        return value
    table = _CONCENTRATION if requirement.dimension == "concentration" else _RATE_TO_PER_HOUR
    if unit not in table:
        raise ValueError(f"dimension_mismatch:{unit}:expected_{requirement.dimension}")
    canonical = value * table[unit]
    if requirement.canonical_unit in {"uM", "1/h"}:
        return canonical
    raise ValueError(f"unsupported_canonical_unit:{requirement.canonical_unit}")

"""Explicit dimension and unit conversion rules used by the resolver."""

from __future__ import annotations

from .requirements import ParameterRequirement

_CONCENTRATION = {"M": 1e6, "mM": 1e3, "uM": 1.0, "nM": 1e-3}
_RATE = {"1/s": 1.0, "1/min": 1 / 60, "1/h": 1 / 3600, "h^-1": 1 / 3600, "h-1": 1 / 3600}
_DIMENSIONLESS = {"1", "dimensionless", None}


def normalize_for_requirement(value: float, unit: str | None, requirement: ParameterRequirement) -> float:
    """Return a canonical numeric value or raise; never infer dimensions."""
    if requirement.dimension == "dimensionless":
        if unit not in _DIMENSIONLESS:
            raise ValueError(f"dimension_mismatch:{unit}:expected_dimensionless")
        return value
    table = _CONCENTRATION if requirement.dimension == "concentration" else _RATE
    if unit not in table:
        raise ValueError(f"dimension_mismatch:{unit}:expected_{requirement.dimension}")
    canonical = value * table[unit]
    if requirement.canonical_unit == "uM" or requirement.canonical_unit == "1/s":
        return canonical
    raise ValueError(f"unsupported_canonical_unit:{requirement.canonical_unit}")

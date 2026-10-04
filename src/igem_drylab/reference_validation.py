"""Numerical-table identity criteria, not biological acceptance thresholds."""
from decimal import Decimal

import numpy as np


def source_precision_verdict(calculated, source, *, source_cells=None, expected_discrepancies=()):
    """Compare concentrations at the precision retained in the source values.

    Nonzero source text allows half its last retained decimal unit plus a
    floating-point floor. Numeric Excel cells have no declared decimal precision
    and allow only storage/arithmetic precision; zeros use the same strict floor.
    No solver or biological tolerance is inflated to force a passing verdict.
    """
    calculated, source = np.asarray(calculated,float),np.asarray(source,float)
    if calculated.shape != source.shape or calculated.ndim != 2 or calculated.shape[1]<2:
        raise ValueError("reference_table_shape_mismatch")
    if not np.all(np.isfinite(calculated)) or not np.all(np.isfinite(source)):
        raise ValueError("reference_table_values_must_be_finite")
    scale=max(float(np.max(np.abs(source[:,1:]))),np.finfo(float).tiny)
    arithmetic_floor=64*np.finfo(float).eps*scale
    cells=np.asarray(source_cells,dtype=object) if source_cells is not None else np.asarray(source,dtype=object)
    if cells.shape!=source.shape:
        raise ValueError("reference_source_cell_shape_mismatch")
    tolerance=np.asarray([[0.5*10.**Decimal(value).as_tuple().exponent
                            if isinstance(value,str) and float(value)!=0 else 0.
                            for value in row] for row in cells[:,1:]])+arithmetic_floor
    difference=np.abs(calculated[:,1:]-source[:,1:])
    violations=int(np.count_nonzero(difference>tolerance))
    time_floor=64*np.finfo(float).eps*max(float(np.max(np.abs(source[:,0]))),1.)
    time_aligned=bool(np.all(np.abs(calculated[:,0]-source[:,0])<=time_floor))
    matched=violations==0 and time_aligned
    verdict="reproduced_within_retained_source_precision" if matched else (
        "expected_documentation_code_contradiction" if expected_discrepancies else "not_reproduced_within_retained_source_precision")
    return {"verdict":verdict,"source_precision_match":matched,"concentration_cells_outside_precision":violations,
            "time_aligned":time_aligned,"expected_discrepancies":list(expected_discrepancies),
            "comparison_space":"source-concentration-columns; time checked separately",
            "acceptance_criterion":"source_text_half_last_decimal_unit_plus_64_machine_eps; numeric_or_zero_cells_only_machine_floor",
            "precision_scope":"text_rounding_or_numeric_storage_identity; not_verified_scientific_reporting_precision",
            "scope":"published_simulation_output_identity_not_independent_experimental_validation"}

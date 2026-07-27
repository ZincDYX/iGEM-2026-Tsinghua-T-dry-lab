import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

# Basic constraints + normalization and validation helpers
# Default constraints file path can be provided by caller; otherwise use built-in defaults

@dataclass
class MetricConstraint:
    name: str
    units: List[str]
    target_unit: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    decimal_policy: Optional[str] = None  # e.g., 'percent_to_fraction'


def _default_constraints() -> Dict[str, Any]:
    # Conservative defaults; caller can override by passing constraints dict
    return {
        "co2_conversion": {"units": ["%", "fraction", None], "target_unit": "fraction", "min": 0.0, "max": 1.0, "decimal_policy": "percent_to_fraction"},
        "methanol_selectivity": {"units": ["%", "fraction", None], "target_unit": "fraction", "min": 0.0, "max": 1.0, "decimal_policy": "percent_to_fraction"},
        "methanol_yield": {"units": ["%", "fraction", None], "target_unit": "fraction", "min": 0.0, "max": 1.0, "decimal_policy": "percent_to_fraction"},
        "temperature": {"units": ["C", "K", None], "target_unit": "C", "min": -50.0, "max": 500.0},
        "pressure": {"units": ["bar", "MPa", None], "target_unit": "bar", "min": 0.0, "max": 500.0},
    }


def load_constraints(path: Optional[str] = None) -> Dict[str, Any]:
    if not path:
        return _default_constraints()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return _default_constraints()


def _to_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        if isinstance(val, str):
            v = val.strip().replace(',', '')
            if v.endswith('%'):
                v = v[:-1]
            return float(v)
        return float(val)
    except Exception:
        return None


def _norm_unit_token(unit: Optional[str]) -> Optional[str]:
    if unit is None:
        return None
    u = str(unit).strip().replace('?', '')
    u = u.replace('degC', 'C').replace('celsius', 'C').replace('Kelvin', 'K')
    u = u.replace('bar(a)', 'bar').replace('bars', 'bar')
    u = u.replace('mpa', 'MPa').replace('Mpa', 'MPa')
    u = u.replace('%', '%')
    if u.lower() in ('c', 'degc'): return 'C'
    if u in ('K',): return 'K'
    if u.lower() in ('bar',): return 'bar'
    if u in ('MPa',): return 'MPa'
    if u in ('%',): return '%'
    if u.lower() in ('fraction','ratio'): return 'fraction'
    return unit


def normalize_value_unit(metric: str, value: Any, unit: Optional[str], constraints: Dict[str, Any]) -> Tuple[Optional[float], Optional[str], List[str]]:
    """Return (normalized_value, normalized_unit, violations)"""
    c = constraints.get(metric, {})
    target = c.get('target_unit')
    min_v = c.get('min'); max_v = c.get('max')
    policy = c.get('decimal_policy')

    v = _to_float(value)
    u = _norm_unit_token(unit)
    violations: List[str] = []

    # Unit normalization for known metrics
    if metric in ('co2_conversion', 'methanol_selectivity', 'methanol_yield'):
        # normalize to fraction [0,1]
        if u == '%' or (u is None and isinstance(value, str) and str(value).strip().endswith('%')):
            if v is not None:
                v = v / 100.0
            u = 'fraction'
        elif policy == 'percent_to_fraction' and u in (None, 'fraction') and v is not None and v > 1.0 and v <= 100.0:
            # looks like percent but unit missing; convert
            v = v / 100.0
            u = 'fraction'
        else:
            u = 'fraction' if u in (None, 'fraction') else u
    elif metric in ('temperature',):
        # target: C
        if u == 'K' and v is not None:
            v = v - 273.15
            u = 'C'
        elif u in (None, 'C'):
            u = 'C'
    elif metric in ('pressure',):
        # target: bar
        if u == 'MPa' and v is not None:
            v = v * 10.0
            u = 'bar'
        elif u in (None, 'bar'):
            u = 'bar'

    # Range check
    if v is None:
        violations.append('value_unparsable')
    else:
        if min_v is not None and v < float(min_v):
            violations.append('below_min')
        if max_v is not None and v > float(max_v):
            violations.append('above_max')

    # Unit check
    allowed = c.get('units') or []
    if allowed and u not in allowed and u is not None:
        violations.append('unit_not_allowed')

    # Target unit check
    if target and u != target:
        # we normalized above; if?????????????
        violations.append('not_target_unit')

    return v, (target or u), violations


def validate_cross_relations(norm: Dict[str, Tuple[Optional[float], Optional[str]]]) -> List[str]:
    """Simple cross-metric checks; return violations codes"""
    viols: List[str] = []
    sel = norm.get('methanol_selectivity', (None, None))[0]
    conv = norm.get('co2_conversion', (None, None))[0]
    yld = norm.get('methanol_yield', (None, None))[0]
    for name, v in (('sel', sel), ('conv', conv), ('yld', yld)):
        if v is not None and (v < 0 or v > 1):
            viols.append(f'{name}_out_of_fraction')
    # yield should not exceed conversion approximately
    if yld is not None and conv is not None and yld > conv + 1e-6:
        viols.append('yield_exceeds_conversion')
    return viols


def compute_confidence(metric_violations: List[str], cross_violations: List[str], corrected_rounds: int) -> float:
    base = 1.0 if not metric_violations and not cross_violations else 0.6 if corrected_rounds > 0 else 0.3
    # More violations reduce confidence a bit
    penal = 0.05 * (len(metric_violations) + len(cross_violations))
    return max(0.0, min(1.0, base - penal))

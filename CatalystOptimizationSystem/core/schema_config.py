import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ASCII_ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


def normalize_identifier(name: str) -> str:
    name = (name or "").strip().replace(" ", "_")
    return "".join(ch for ch in name if ch in ASCII_ALLOWED).lower()


def ensure_metric_identifiers(names: Iterable[str]) -> List[str]:
    out = []
    for name in names:
        normalized = normalize_identifier(name)
        if not normalized or any(ord(ch) > 127 for ch in name):
            raise ValueError(f"metric names must be ASCII identifiers: {name}")
        out.append(normalized)
    return out


def load_schema(path: Optional[str | Path]) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    if "metrics" not in schema or not isinstance(schema["metrics"], list):
        raise ValueError("schema must contain a metrics list")
    schema["metric_names"] = ensure_metric_identifiers([m["name"] for m in schema["metrics"]])
    return schema


def schema_metric_names(schema: Optional[Dict[str, Any]]) -> List[str]:
    if not schema:
        return []
    return list(schema.get("metric_names") or [m["name"] for m in schema.get("metrics", [])])


def schema_constraints(schema: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    if not schema:
        return {}
    return {
        metric["name"]: {
            **metric.get("constraints", {}),
            "type": metric.get("type") or metric.get("constraints", {}).get("type", "numeric"),
        }
        for metric in schema.get("metrics", [])
    }


def schema_prompt(schema: Optional[Dict[str, Any]], metrics: List[str]) -> str:
    if not schema:
        return ""
    instructions = schema.get("prompt", {}).get("instructions", [])
    lines = [
        "Follow the extraction schema.",
        "Extract raw values and raw units exactly as stated in the text.",
        "Do not convert units; downstream Python code handles normalization.",
        "Return null for value, unit, and evidence when a metric is not explicitly reported.",
        "Include a short evidence string for every non-null value.",
        "Inside each record, use flat JSON keys exactly matching the requested metric names.",
    ]
    for item in instructions:
        item = str(item).strip()
        if item and item not in lines:
            lines.append(item)
    lines.append("Requested metrics: " + ", ".join(metrics))
    details = []
    by_name = {m["name"]: m for m in schema.get("metrics", [])}
    for name in metrics:
        meta = by_name.get(name, {})
        desc = meta.get("description", "")
        typ = meta.get("type") or meta.get("constraints", {}).get("type") or "numeric"
        target = meta.get("constraints", {}).get("target_unit")
        aliases = meta.get("aliases") or []
        alias_text = f" aliases={aliases}" if aliases else ""
        if desc or target or typ != "numeric":
            details.append(f"- {name}: type={typ}; {desc} target_unit={target}{alias_text}")
    if details:
        lines.append("Metric definitions:\n" + "\n".join(details))
    return "\n".join(lines)


def _is_missing_token(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        token = value.strip().lower()
        return token in {
            "",
            "-",
            "/",
            "—",
            "na",
            "n/a",
            "none",
            "null",
            "not reported",
            "not provided",
            "unreported",
            "missing",
            "无",
            "未报告",
            "未提供",
            "未直接测定",
            "不适用",
        }
    return False


def _to_float(value: Any) -> Optional[float]:
    if _is_missing_token(value):
        return None
    try:
        if isinstance(value, str):
            v = value.strip().replace(",", "")
            if v.endswith("%"):
                v = v[:-1]
            return float(v)
        return float(value)
    except Exception:
        return None


def _looks_like_numeric_series(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not re.search(r"\d", text):
        return False
    return bool(re.search(r"\d\s*(?:-|–|~|～|至|to|,|;|；)\s*\d", text, flags=re.IGNORECASE))


def _normalize_unit_token(unit: Optional[str]) -> Optional[str]:
    if unit is None:
        return None
    u = str(unit).strip()
    if _is_missing_token(u):
        return None
    u = u.replace("掳C", "C").replace("°C", "C").replace("℃", "C").replace("degC", "C").replace("celsius", "C")
    u = u.replace("Kelvin", "K").replace("kelvin", "K")
    u = u.replace("bar(a)", "bar").replace("bars", "bar")
    u = u.replace("mpa", "MPa").replace("Mpa", "MPa")
    u = u.replace("µ", "μ").replace("ug", "μg").replace("uM", "μM").replace("uL", "μL")
    u = u.replace("μmol min-1 mg-1", "μmol/min/mg")
    u = u.replace("μmol/min/mg protein", "μmol/min/mg")
    u = u.replace("units per mg protein", "U/mg")
    if u.lower() in ("c", "degc"):
        return "C"
    if u in ("K", "C", "MPa", "%"):
        return u
    if u in ("μM", "mM", "nM", "M", "mg/L", "μg/mL", "mg/mL", "μg", "mg", "μL", "mL"):
        return u
    if u in ("h", "hr", "hrs", "hour", "hours"):
        return "h"
    if u in ("min", "mins", "minute", "minutes"):
        return "min"
    if u in ("s", "sec", "second", "seconds"):
        return "s"
    if u in ("U", "U/mL", "U/mg", "μmol/min", "μmol/min/mg", "mg/g DW", "mg/g DCW", "OD600", "rpm"):
        return u
    if u.lower() == "bar":
        return "bar"
    if u.lower() in ("fraction", "ratio"):
        return "fraction"
    if u.lower() in ("ph", "ph unit", "ph units"):
        return "pH"
    return u


def normalize_value_unit_from_schema(
    metric: str,
    value: Any,
    unit: Optional[str],
    constraints: Dict[str, Dict[str, Any]],
) -> Tuple[Optional[Any], Optional[str], List[str]]:
    cfg = constraints.get(metric, {})
    field_type = cfg.get("type", "numeric")
    target = cfg.get("target_unit")
    allowed = cfg.get("units") or []
    min_v = cfg.get("min")
    max_v = cfg.get("max")
    policy = cfg.get("decimal_policy")

    u = _normalize_unit_token(unit)
    violations: List[str] = []

    if _is_missing_token(value) and u is None:
        return None, None, []

    if field_type in {"text", "categorical", "boolean"}:
        v = None if _is_missing_token(value) else str(value).strip()
        if field_type == "boolean" and v is not None:
            lower = v.lower()
            if lower in {"yes", "true", "1", "是", "yes/true"}:
                v = "yes"
            elif lower in {"no", "false", "0", "否", "no/false"}:
                v = "no"
        if allowed and v is not None and v not in allowed:
            violations.append("value_not_allowed")
        return v, u, violations

    v = _to_float(value)

    if v is None and _looks_like_numeric_series(value):
        return None, (target or u), []

    if policy == "percent_to_fraction":
        if u == "%" or (u is None and isinstance(value, str) and str(value).strip().endswith("%")):
            if v is not None:
                v = v / 100.0
            u = "fraction"
        elif u in (None, "fraction") and v is not None and 1.0 < v <= 100.0:
            v = v / 100.0
            u = "fraction"
        elif u is None:
            u = "fraction"

    for conversion in cfg.get("conversions", []):
        if u == conversion.get("from") and target == conversion.get("to") and v is not None:
            factor = conversion.get("factor")
            offset = conversion.get("offset", 0)
            if factor is not None:
                v = v * float(factor) + float(offset)
                u = target

    if u is None and target:
        u = target

    if v is None:
        violations.append("value_unparsable")
    else:
        if min_v is not None and v < float(min_v):
            violations.append("below_min")
        if max_v is not None and v > float(max_v):
            violations.append("above_max")

    if allowed and u not in allowed and u is not None:
        violations.append("unit_not_allowed")
    if target and u != target:
        violations.append("not_target_unit")
    return v, (target or u), violations


def validate_cross_relations_from_schema(
    norm: Dict[str, Tuple[Optional[Any], Optional[str], List[str]]],
    schema: Optional[Dict[str, Any]],
) -> List[str]:
    if not schema:
        return []
    violations = []
    for relation in schema.get("cross_relations", []):
        if relation.get("type") != "lte":
            continue
        left = relation.get("left")
        right = relation.get("right")
        lv = norm.get(left, (None, None, []))[0]
        rv = norm.get(right, (None, None, []))[0]
        tolerance = float(relation.get("tolerance", 0))
        if lv is not None and rv is not None and lv > rv + tolerance:
            violations.append(relation.get("name") or f"{left}_gt_{right}")
    return violations

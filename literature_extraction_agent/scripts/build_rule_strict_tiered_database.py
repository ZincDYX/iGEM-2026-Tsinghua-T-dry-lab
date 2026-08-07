from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "essay" / "final_structured_database_high_recall.csv"
DEFAULT_OUT = ROOT / "essay" / "rule_strict_tiered_database.csv"
DEFAULT_SUMMARY = ROOT / "essay" / "rule_strict_tiered_database_summary.json"

RESULT_METRICS = {
    "glabridin_titer",
    "glabridin_yield",
    "substrate_conversion",
    "enzyme_activity",
    "specific_activity",
    "relative_activity",
    "kcat",
    "km",
    "critical_phase_concentration",
    "llps_state",
}

NUMERIC_METRICS = RESULT_METRICS - {"llps_state"}
LOW_SIGNAL_PRODUCTS = {"", "product", "main product", "compound"}
LOW_SIGNAL_HOSTS = {"", "host", "strain"}

NEGATIVE_TITLE_TERMS = [
    "editorial",
    "obesity",
    "rheumatoid arthritis",
    "neuropathic pain",
    "alcohol consumption",
]
NEGATIVE_EVIDENCE_TERMS = [
    "references",
    "copyright",
    "creative commons",
    "license",
    "bar =",
    "scale bar",
    "stained with",
]
RESULT_WORDS = [
    "titer", "titre", "yield", "production", "produced", "reached", "achieved",
    "conversion", "activity", "specific activity", "relative activity", "kcat",
    "km", "phase separation", "condensate", "droplet",
]
TITER_UNITS = {
    "mg/l", "g/l", "ug/l", "ng/l", "mg/ml", "mg/g", "g/kg", "mg/kg",
    "gdcw/l", "mg/gdcw", "mg/g dcw", "mg/l/h", "g/l/h",
}
PERCENT_UNITS = {"%", "percent", "mol%", "wt%", "v/v", "w/v"}
ACTIVITY_UNITS = {"u/mg", "u/ml", "u/mgprotein", "u", "%", "fold"}
ADDITION_WORDS = [
    "added", "supplemented", "medium", "media", "substrate", "iptg",
    "glucose", "xylose", "acetate", "p-coumaric", "kac", "nacl", "buffer",
    "fed", "feeding", "containing",
]


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def numlike(value: str) -> bool:
    value = norm(value)
    return bool(re.search(r"\d", value)) and not re.fullmatch(r"[+-]?\d{4}", value)


def metric_value(row: dict[str, str], metric: str) -> tuple[str, str, str]:
    return norm(row.get(f"{metric}_value", "")), norm(row.get(f"{metric}_unit", "")), norm(row.get(f"{metric}_evidence", ""))


def has_result_language(evidence: str, metric: str) -> bool:
    low = evidence.lower()
    if metric in {"kcat", "km", "critical_phase_concentration", "llps_state"}:
        return True
    return any(word in low for word in RESULT_WORDS)


def near_value_text(evidence: str, value: str, window: int = 90) -> str:
    low = evidence.lower()
    value_low = re.escape(norm(value).lower())
    patterns = [value_low]
    if "±" in value or "+/-" in value or "¡à" in value.lower():
        first = re.split(r"±|\+/-|¡à", norm(value), maxsplit=1)[0].strip()
        if first:
            patterns.append(re.escape(first.lower()))
    for pat in patterns:
        m = re.search(pat, low)
        if m:
            start = max(0, m.start() - window)
            end = min(len(low), m.end() + window)
            return low[start:end]
    return low[: min(len(low), window * 2)]


def metric_specific_reject(metric: str, value: str, unit: str, evidence: str) -> str:
    unit_low = norm(unit).lower()
    low = evidence.lower()
    near = near_value_text(evidence, value)
    if metric == "glabridin_titer":
        if unit_low not in TITER_UNITS:
            return f"titer_bad_unit:{unit}"
        if not any(word in near for word in ["titer", "titre", "production", "produced", "reached", "achieved", "yield of", "level of"]):
            return "titer_no_result_word_near_value"
        if any(word in near for word in ADDITION_WORDS) and not any(word in near for word in ["titer", "titre", "produced", "production reached", "achieved"]):
            return "titer_near_addition_or_medium"
        if re.search(r"\b(?:iptg|kac|nacl|glucose|xylose|acetate|p-coumaric acid)\b", near) and not re.search(r"\b(?:titer|titre|produced|production|reached|achieved)\b", near):
            return "titer_likely_substrate_or_additive"
    elif metric == "glabridin_yield":
        if unit_low and unit_low not in PERCENT_UNITS and unit_low not in TITER_UNITS and unit_low != "fold":
            return f"yield_bad_unit:{unit}"
        if not any(word in near for word in ["yield", "conversion", "produced", "production", "reached", "achieved"]):
            return "yield_no_result_word_near_value"
    elif metric == "substrate_conversion":
        if unit_low and unit_low not in PERCENT_UNITS:
            return f"conversion_bad_unit:{unit}"
        if not any(word in near for word in ["conversion", "converted", "yield"]):
            return "conversion_no_result_word_near_value"
    elif metric in {"enzyme_activity", "specific_activity", "relative_activity"}:
        if unit_low and unit_low not in ACTIVITY_UNITS:
            return f"activity_bad_unit:{unit}"
        if not any(word in near for word in ["activity", "specific activity", "relative activity", "u/mg", "u/ml"]):
            return "activity_no_result_word_near_value"
    elif metric in {"kcat", "km"}:
        if metric == "kcat" and not any(word in low for word in ["kcat", "k_cat", "turnover"]):
            return "kcat_not_in_evidence"
        if metric == "km" and not any(word in low for word in ["km", "k_m", "michaelis"]):
            return "km_not_in_evidence"
    return ""


def is_bad_context(row: dict[str, str], evidence: str) -> str:
    title_low = norm(row.get("title", "")).lower()
    low = evidence.lower()
    for term in NEGATIVE_TITLE_TERMS:
        if term in title_low:
            return f"negative_title:{term}"
    for term in NEGATIVE_EVIDENCE_TERMS:
        if term in low:
            return f"negative_evidence:{term}"
    if len(evidence) < 35:
        return "short_evidence"
    return ""


def strict_tier(row: dict[str, str], metric: str, value: str, unit: str, evidence: str) -> tuple[str, str]:
    product = norm(row.get("main_product_name_value", ""))
    host = norm(row.get("expression_host_value", ""))
    system = norm(row.get("reaction_system_type_value", ""))
    data_source = norm(row.get("data_source_type_value", ""))
    quality = norm(row.get("quality_label", ""))
    bad = is_bad_context(row, evidence)
    if bad:
        return "", bad
    if metric in NUMERIC_METRICS and not numlike(value):
        return "", "missing_numeric_value"
    if metric in {"glabridin_titer", "glabridin_yield", "substrate_conversion", "enzyme_activity", "specific_activity", "relative_activity", "kcat", "km"} and not unit:
        if metric not in {"substrate_conversion", "glabridin_yield", "relative_activity"}:
            return "", "missing_unit"
    metric_reject = metric_specific_reject(metric, value, unit, evidence)
    if metric_reject:
        return "", metric_reject
    if not has_result_language(evidence, metric):
        return "", "no_result_language"

    has_product = product.lower() not in LOW_SIGNAL_PRODUCTS
    has_host = host.lower() not in LOW_SIGNAL_HOSTS or bool(system)
    high_quality = quality in {"high", "medium"} or data_source in {"table", "figure", "text"}
    is_review_or_table = data_source == "table" or "review" in norm(row.get("title", "")).lower()

    if metric in {"critical_phase_concentration", "llps_state"}:
        if "phase" in evidence.lower() or "condensate" in evidence.lower() or "droplet" in evidence.lower():
            return "strict_A_llps", ""
        return "strict_C_llps_candidate", ""
    if has_product and has_host and high_quality:
        return ("strict_A_review_table" if is_review_or_table else "strict_A_primary_like"), ""
    if has_product and high_quality:
        return ("strict_B_review_table" if is_review_or_table else "strict_B_product_result"), ""
    if has_host and metric in {"glabridin_titer", "glabridin_yield", "substrate_conversion", "enzyme_activity", "specific_activity", "relative_activity"}:
        return "strict_C_host_result", ""
    return "strict_C_result_only", ""


def signature(row: dict[str, str], metric: str, value: str, unit: str, evidence: str) -> str:
    raw = "|".join([
        norm(row.get("doi", "")).lower(),
        metric,
        norm(row.get("main_product_name_value", "")).lower(),
        norm(row.get("expression_host_value", "")).lower(),
        value.lower(),
        unit.lower(),
        evidence[:220].lower(),
    ])
    return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--excluded", type=Path, default=ROOT / "essay" / "rule_strict_tiered_database_excluded.csv")
    args = parser.parse_args()

    rows_out: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    fieldnames: list[str] = []
    seen: set[str] = set()
    with args.input.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        extra = ["rule_strict_id", "rule_strict_tier", "rule_strict_reason", "rule_strict_source"]
        out_fields = fieldnames + [x for x in extra if x not in fieldnames]
        excluded_fields = out_fields + ["exclude_reason"]
        for row in reader:
            metric = norm(row.get("structured_metric", ""))
            if metric not in RESULT_METRICS:
                continue
            value, unit, evidence = metric_value(row, metric)
            tier, reason = strict_tier(row, metric, value, unit, evidence)
            rid = signature(row, metric, value, unit, evidence)
            out_row = dict(row)
            out_row["rule_strict_id"] = rid
            out_row["rule_strict_tier"] = tier
            out_row["rule_strict_reason"] = reason or "accepted"
            out_row["rule_strict_source"] = "rule_from_high_recall_structured"
            if not tier:
                out_row["exclude_reason"] = reason
                excluded.append(out_row)
                continue
            if rid in seen:
                out_row["exclude_reason"] = "duplicate"
                excluded.append(out_row)
                continue
            seen.add(rid)
            rows_out.append(out_row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows_out)
    with args.excluded.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=excluded_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(excluded)

    by_tier: dict[str, int] = {}
    by_metric: dict[str, int] = {}
    by_source: dict[str, int] = {}
    dois: set[str] = set()
    products: dict[str, int] = {}
    hosts: dict[str, int] = {}
    for row in rows_out:
        by_tier[row["rule_strict_tier"]] = by_tier.get(row["rule_strict_tier"], 0) + 1
        by_metric[row.get("structured_metric", "")] = by_metric.get(row.get("structured_metric", ""), 0) + 1
        by_source[row.get("data_source_type_value", "")] = by_source.get(row.get("data_source_type_value", ""), 0) + 1
        doi = norm(row.get("doi", "")).lower()
        if doi:
            dois.add(doi)
        prod = norm(row.get("main_product_name_value", ""))
        host = norm(row.get("expression_host_value", ""))
        if prod:
            products[prod] = products.get(prod, 0) + 1
        if host:
            hosts[host] = hosts.get(host, 0) + 1

    summary = {
        "accepted_rows": len(rows_out),
        "excluded_rows": len(excluded),
        "unique_dois": len(dois),
        "by_rule_strict_tier": dict(sorted(by_tier.items())),
        "by_structured_metric": dict(sorted(by_metric.items())),
        "by_data_source_type": dict(sorted(by_source.items())),
        "top_products": sorted(products.items(), key=lambda x: -x[1])[:25],
        "top_hosts": sorted(hosts.items(), key=lambda x: -x[1])[:25],
        "output": str(args.out),
        "excluded_output": str(args.excluded),
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

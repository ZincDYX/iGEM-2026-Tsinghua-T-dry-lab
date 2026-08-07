from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from CatalystOptimizationSystem.core.constraints import compute_confidence
from CatalystOptimizationSystem.core.extractor import _flatten_record_rows, _normalize_records, _output_columns
from CatalystOptimizationSystem.core.schema_config import load_schema, schema_constraints, schema_metric_names
from CatalystOptimizationSystem.utils.config import DEFAULT_SCHEMA_JSON


DEFAULT_INPUT = ROOT / "essay" / "final_clean_database_all_pdfs.csv"
DEFAULT_OUT = ROOT / "essay" / "final_structured_database_high_recall.csv"
DEFAULT_SUMMARY = ROOT / "essay" / "final_structured_database_high_recall_summary.json"


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def source_type(section: str) -> str:
    section = (section or "").lower()
    if section == "table":
        return "table"
    if section == "figure":
        return "figure"
    if section == "methods_or_assay":
        return "method"
    if section == "supplementary":
        return "table"
    return "text"


def null_metric() -> dict[str, Any]:
    return {"value": None, "unit": None, "evidence": None}


def metric_obj(value: str, unit: str, evidence: str) -> dict[str, Any]:
    return {"value": value if value != "" else None, "unit": unit if unit != "" else None, "evidence": evidence if evidence else None}


def infer_product(evidence: str, title: str) -> str | None:
    text = f"{title} {evidence}".lower()
    products = [
        "glabridin", "naringenin", "taxifolin", "limonene", "taxadiene",
        "kaempferol", "quercetin", "eriodictyol", "pinocembrin",
        "anthocyanin", "anthocyanins", "lycopene", "astaxanthin",
        "beta-carotene", "¦ā-carotene", "β-carotene", "squalene",
        "resveratrol", "liquiritigenin", "apigenin", "xanthohumol",
        "phloretin", "carnosic acid", "menaquinone-7", "mk-7",
        "geranylgeraniol", "farnesene", "sclareol", "ferruginol",
    ]
    for product in products:
        if product in text:
            return product
    return None


def infer_host(evidence: str, title: str) -> str | None:
    text = f"{title} {evidence}".lower()
    hosts = [
        ("saccharomyces cerevisiae", "Saccharomyces cerevisiae"),
        ("s. cerevisiae", "S. cerevisiae"),
        ("yarrowia lipolytica", "Yarrowia lipolytica"),
        ("escherichia coli", "Escherichia coli"),
        ("e. coli", "E. coli"),
        ("corynebacterium glutamicum", "Corynebacterium glutamicum"),
        ("streptomyces albidoflavus", "Streptomyces albidoflavus"),
        ("streptomyces", "Streptomyces"),
        ("bacillus subtilis", "Bacillus subtilis"),
        ("pichia pastoris", "Pichia pastoris"),
        ("ogataea polymorpha", "Ogataea polymorpha"),
        ("y. lipolytica", "Y. lipolytica"),
    ]
    for needle, host in hosts:
        if needle in text:
            return host
    if "yeast" in text:
        return "yeast"
    return None


def is_concentration_unit(unit: str) -> bool:
    u = unit.lower()
    return u in {"um", "μm", "mm", "nm", "pm", "m", "mm", "um", "nm", "pm", "mg/l", "g/l", "mg/l", "ug/l", "ng/l", "mg/ml", "g/l", "mg/g"}


def is_time_unit(unit: str) -> bool:
    return unit.lower() in {"h", "hr", "hrs", "min", "s", "day", "days"}


def is_temperature_unit(unit: str) -> bool:
    return unit.lower() in {"c", "degc", "°c", "k"}


def put(record: dict[str, Any], metric: str, value: str, unit: str, evidence: str) -> None:
    if metric in record:
        record[metric] = metric_obj(value, unit, evidence)


def build_record(row: dict[str, str], metrics: list[str]) -> tuple[dict[str, Any], str]:
    record = {metric: null_metric() for metric in metrics}
    category = norm(row.get("metric_category", ""))
    value = norm(row.get("value", ""))
    unit = norm(row.get("unit", ""))
    evidence = norm(row.get("evidence", ""))
    title = norm(row.get("title", ""))
    low = evidence.lower()
    target_metric = "data_source_type"

    product = infer_product(evidence, title)
    host = infer_host(evidence, title)
    if product:
        put(record, "main_product_name", product, "", evidence)
    if host:
        put(record, "expression_host", host, "", evidence)
    put(record, "data_source_type", source_type(row.get("section_hint", "")), "", evidence)

    if category == "titer":
        target_metric = "glabridin_titer"
        put(record, target_metric, value, unit, evidence)
    elif category == "yield":
        target_metric = "glabridin_yield"
        put(record, target_metric, value, unit, evidence)
    elif category == "conversion":
        target_metric = "substrate_conversion"
        put(record, target_metric, value, unit, evidence)
    elif category == "activity":
        if unit.lower() in {"u/mg", "u/mgprotein"} or "specific activity" in low:
            target_metric = "specific_activity"
        elif unit == "%" or "relative activity" in low:
            target_metric = "relative_activity"
        else:
            target_metric = "enzyme_activity"
        put(record, target_metric, value, unit, evidence)
    elif category == "kinetics":
        if "kcat" in low or "k_cat" in low or unit.lower() in {"s^-1", "min^-1"}:
            target_metric = "kcat"
        elif "km" in low or "k_m" in low or unit.lower() in {"um", "mm", "nm", "μm"}:
            target_metric = "km"
        else:
            target_metric = "kinetic_efficiency"
        put(record, target_metric, value, unit, evidence)
    elif category == "llps":
        if is_concentration_unit(unit):
            target_metric = "critical_phase_concentration"
            put(record, target_metric, value, unit, evidence)
        elif is_time_unit(unit) and "frap" in low:
            target_metric = "frap_half_time"
            put(record, target_metric, value, unit, evidence)
        else:
            target_metric = "llps_state"
            put(record, target_metric, f"{value} {unit}".strip(), "", evidence)
        put(record, "phase_regulation_direction", "reported LLPS-related effect", "", evidence)
    elif category == "expression_or_fermentation":
        if "od600" in unit.lower() or "od600" in low:
            target_metric = "cell_density_od600"
            put(record, target_metric, value, unit, evidence)
        elif is_time_unit(unit):
            target_metric = "reaction_time"
            put(record, target_metric, value, unit, evidence)
        else:
            target_metric = "reaction_system_type"
            put(record, target_metric, "fermentation or expression system", "", evidence)
    elif category == "condition":
        if is_time_unit(unit):
            target_metric = "reaction_time"
        elif is_temperature_unit(unit):
            target_metric = "reaction_temperature"
        elif "ph" in low:
            target_metric = "reaction_ph"
        elif "od600" in unit.lower() or "od600" in low:
            target_metric = "cell_density_od600"
        elif is_concentration_unit(unit):
            if any(x in low for x in ["substrate", "p-coumaric", "glucose", "xylose", "acetate"]):
                target_metric = "substrate_concentration"
            elif any(x in low for x in ["nadph", "nadh", "atp", "iptg", "cofactor"]):
                target_metric = "cofactor_concentration"
            elif any(x in low for x in ["salt", "nacl", "kcl"]):
                target_metric = "llps_salt_concentration"
            else:
                target_metric = "substrate_concentration"
        else:
            target_metric = "reaction_system_type"
        put(record, target_metric, value, unit, evidence)
    else:
        if is_time_unit(unit):
            target_metric = "reaction_time"
        elif is_concentration_unit(unit):
            target_metric = "substrate_concentration"
        elif unit == "%":
            target_metric = "glabridin_yield" if "yield" in low else "substrate_conversion"
        put(record, target_metric, value, unit, evidence)

    return record, target_metric


def stable_signature(row: dict[str, str], target_metric: str) -> str:
    raw = "|".join([
        row.get("doi", "").lower(),
        target_metric,
        row.get("value", "").lower(),
        row.get("unit", "").lower(),
        row.get("evidence", "")[:220].lower(),
    ])
    return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--schema", type=Path, default=ROOT / DEFAULT_SCHEMA_JSON)
    parser.add_argument("--min-score", type=int, default=0)
    args = parser.parse_args()

    schema = load_schema(str(args.schema))
    metrics = schema_metric_names(schema)
    constraints = schema_constraints(schema)
    columns = _output_columns(metrics) + [
        "source_clean_record_id",
        "source_metric_category",
        "structured_metric",
        "quality_label",
        "source_score",
        "source_dataset",
    ]

    out_rows: list[dict[str, Any]] = []
    by_metric: dict[str, int] = {}
    by_category: dict[str, int] = {}
    doi_set: set[str] = set()

    with args.input.open("r", encoding="utf-8-sig", newline="") as f:
        for source_row in csv.DictReader(f):
            try:
                score = int(float(source_row.get("score", "0") or 0))
            except ValueError:
                score = 0
            if score < args.min_score:
                continue
            record, target_metric = build_record(source_row, metrics)
            norm_maps, metric_vios, cross_vios = _normalize_records([record], metrics, constraints, schema)
            confidence = compute_confidence(metric_vios, cross_vios, 0)
            rows = _flatten_record_rows(
                records=[record],
                norm_maps=norm_maps,
                metrics=metrics,
                pii=None,
                doi=norm(source_row.get("doi", "")),
                title=norm(source_row.get("title", "")),
                keyword="high_recall_structured_from_clean_evidence",
                schema=schema,
                selected_examples=[],
                corrected_rounds=0,
                confidence=confidence,
                text_chars=len(source_row.get("evidence", "") or ""),
                chunk_count=1,
                processed_chunks=1,
            )
            row = rows[0]
            row["article_key"] = f"doi:{norm(source_row.get('doi', '')).lower()}#evidence:{stable_signature(source_row, target_metric)}"
            row["source_clean_record_id"] = source_row.get("record_id", "")
            row["source_metric_category"] = source_row.get("metric_category", "")
            row["structured_metric"] = target_metric
            row["quality_label"] = source_row.get("quality_label", "")
            row["source_score"] = source_row.get("score", "")
            row["source_dataset"] = "final_clean_database_all_pdfs"
            out_rows.append(row)
            by_metric[target_metric] = by_metric.get(target_metric, 0) + 1
            by_category[source_row.get("metric_category", "")] = by_category.get(source_row.get("metric_category", ""), 0) + 1
            doi = norm(source_row.get("doi", "")).lower()
            if doi:
                doi_set.add(doi)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(out_rows)

    summary = {
        "input": str(args.input),
        "structured_rows": len(out_rows),
        "unique_dois": len(doi_set),
        "by_structured_metric": dict(sorted(by_metric.items())),
        "by_source_category": dict(sorted(by_category.items())),
        "output": str(args.out),
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

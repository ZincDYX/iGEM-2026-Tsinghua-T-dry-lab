from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "essay" / "high_recall_numeric_experimental_evidence.csv"
DEFAULT_OUT = ROOT / "essay" / "final_clean_database_10000.csv"
DEFAULT_EXCLUDED = ROOT / "essay" / "final_clean_database_10000_excluded.csv"
DEFAULT_SUMMARY = ROOT / "essay" / "final_clean_database_10000_summary.json"


LOW_VALUE_METRICS = {"microscopy_scale"}
HIGH_VALUE_METRICS = {"titer", "yield", "activity", "conversion", "kinetics", "llps"}


def norm_space(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def norm_unit(unit: str) -> str:
    u = norm_space(unit).replace(" ", "")
    low = u.lower()
    mapping = {
        "mg/l": "mg/L",
        "g/l": "g/L",
        "ug/l": "ug/L",
        "ng/l": "ng/L",
        "mg/g": "mg/g",
        "g/kg": "g/kg",
        "mg/kg": "mg/kg",
        "u/mg": "U/mg",
        "u/ml": "U/mL",
        "mM".lower(): "mM",
        "um": "uM",
        "mu*m": "uM",
        "nm": "nM",
        "pm": "pM",
        "percent": "%",
        "h": "h",
        "hr": "h",
        "hrs": "h",
        "min": "min",
        "day": "day",
        "days": "day",
        "c": "degC",
        "degc": "degC",
        "degreec": "degC",
        "od600": "OD600",
        "gdcw/l": "gDCW/L",
        "cells/ml": "cells/mL",
        "cfu/ml": "CFU/mL",
    }
    return mapping.get(low, u)


def parse_single_number(value: str) -> str:
    value = norm_space(value)
    if re.fullmatch(r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)", value):
        return value
    return ""


def quality_label(metric: str, score: int, unit: str) -> str:
    if metric in HIGH_VALUE_METRICS and score >= 35 and unit:
        return "high"
    if metric in HIGH_VALUE_METRICS and score >= 20:
        return "medium"
    if metric == "condition" and score >= 25:
        return "condition"
    return "candidate"


def exclude_reason(row: dict[str, str]) -> str:
    metric = row.get("metric_hint", "")
    evidence = norm_space(row.get("evidence", ""))
    if metric in LOW_VALUE_METRICS:
        return "low_value_microscopy_scale"
    if len(evidence) < 30:
        return "short_evidence"
    low = evidence.lower()
    if "references" in low and "doi" in low:
        return "reference_or_bibliography"
    if low.count("http") > 0:
        return "contains_url"
    return ""


def stable_id(row: dict[str, str]) -> str:
    raw = "|".join([
        row.get("doi", "").lower(),
        row.get("metric_category", ""),
        row.get("value", ""),
        row.get("unit", ""),
        row.get("evidence", "")[:220].lower(),
    ])
    return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--excluded", type=Path, default=DEFAULT_EXCLUDED)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()

    clean_rows: list[dict[str, str]] = []
    excluded_rows: list[dict[str, str]] = []
    seen: set[str] = set()
    raw_rows = 0
    duplicate_rows = 0

    with args.input.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for source_row in reader:
            raw_rows += 1
            reason = exclude_reason(source_row)
            value = norm_space(source_row.get("value_text", ""))
            unit = norm_unit(source_row.get("unit_text", ""))
            evidence = norm_space(source_row.get("evidence", ""))
            score_text = source_row.get("score", "0") or "0"
            try:
                score = int(float(score_text))
            except ValueError:
                score = 0
            row = {
                "record_id": "",
                "doi": norm_space(source_row.get("doi", "")),
                "title": norm_space(source_row.get("title", "")),
                "metric_category": norm_space(source_row.get("metric_hint", "")),
                "value": value,
                "unit": unit,
                "numeric_value": parse_single_number(value),
                "section_hint": norm_space(source_row.get("section_hint", "")),
                "score": str(score),
                "quality_label": quality_label(norm_space(source_row.get("metric_hint", "")), score, unit),
                "evidence": evidence,
                "rank": norm_space(source_row.get("rank", "")),
                "candidate_id": norm_space(source_row.get("candidate_id", "")),
                "text_file": norm_space(source_row.get("text_file", "")),
                "source_evidence_id": norm_space(source_row.get("evidence_id", "")),
            }
            row["record_id"] = stable_id(row)
            if reason:
                out = dict(row)
                out["exclude_reason"] = reason
                excluded_rows.append(out)
                continue
            dedupe_key = row["record_id"]
            if dedupe_key in seen:
                duplicate_rows += 1
                out = dict(row)
                out["exclude_reason"] = "duplicate"
                excluded_rows.append(out)
                continue
            seen.add(dedupe_key)
            clean_rows.append(row)

    fieldnames = [
        "record_id", "doi", "title", "metric_category", "value", "unit",
        "numeric_value", "section_hint", "score", "quality_label", "evidence",
        "rank", "candidate_id", "text_file", "source_evidence_id",
    ]
    excluded_fields = fieldnames + ["exclude_reason"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean_rows)
    with args.excluded.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=excluded_fields)
        writer.writeheader()
        writer.writerows(excluded_rows)

    by_metric: dict[str, int] = {}
    by_quality: dict[str, int] = {}
    doi_set: set[str] = set()
    for row in clean_rows:
        by_metric[row["metric_category"]] = by_metric.get(row["metric_category"], 0) + 1
        by_quality[row["quality_label"]] = by_quality.get(row["quality_label"], 0) + 1
        if row["doi"]:
            doi_set.add(row["doi"].lower())
    summary = {
        "source_rows": raw_rows,
        "clean_rows": len(clean_rows),
        "excluded_rows": len(excluded_rows),
        "duplicate_rows": duplicate_rows,
        "unique_dois": len(doi_set),
        "by_metric_category": dict(sorted(by_metric.items())),
        "by_quality_label": dict(sorted(by_quality.items())),
        "output": str(args.out),
        "excluded_output": str(args.excluded),
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

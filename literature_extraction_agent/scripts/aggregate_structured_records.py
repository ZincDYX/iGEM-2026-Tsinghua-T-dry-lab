from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "essay" / "final_structured_database_after_elsevier_pdf_expansion.csv"
DEFAULT_SCHEMA = ROOT / "CatalystOptimizationSystem" / "docs" / "schemas" / "glabridin_enzyme_catalysis.schema.json"
DEFAULT_OUT = ROOT / "essay" / "aggregated_clean_experimental_database.csv"
DEFAULT_LONG = ROOT / "essay" / "aggregated_clean_experimental_database_long.csv"
DEFAULT_EXCLUDED = ROOT / "essay" / "aggregated_clean_experimental_database_excluded.csv"
DEFAULT_SUMMARY = ROOT / "essay" / "aggregated_clean_experimental_database_summary.json"

HIGH_RECALL_KEYWORD = "high_recall_structured_from_clean_evidence"

RESULT_METRICS = {
    "glabridin_titer",
    "glabridin_yield",
    "glabridin_concentration",
    "glabridin_selectivity",
    "substrate_conversion",
    "enzyme_activity",
    "specific_activity",
    "relative_activity",
    "kinetic_efficiency",
    "kcat",
    "km",
    "critical_phase_concentration",
    "frap_half_time",
    "droplet_dissolution_time",
    "catalytic_efficiency_fold_change",
    "llps_state",
}

CONDITION_METRICS = {
    "reaction_temperature",
    "reaction_ph",
    "reaction_time",
    "buffer_type",
    "buffer_concentration",
    "substrate_concentration",
    "enzyme_concentration",
    "enzyme_amount",
    "cofactor",
    "cofactor_concentration",
    "cosubstrate",
    "cosubstrate_concentration",
    "reaction_volume",
    "cell_density_od600",
    "llps_scaffold_concentration",
    "llps_salt_concentration",
}

IDENTITY_METRICS = {
    "enzyme_name",
    "enzyme_mutant",
    "enzyme_source_species",
    "expression_host",
    "substrate_name",
    "substrate_id",
    "main_product_name",
    "main_product_id",
    "byproduct_name",
    "reaction_system_type",
    "is_whole_cell",
    "llps_component",
    "llps_trigger",
    "phase_regulation_direction",
    "data_source_type",
}

LOW_VALUE_PRODUCTS = {"", "product", "main product", "compound"}
LOW_VALUE_HOSTS = {"", "host", "strain"}


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def load_metrics(path: Path) -> list[str]:
    schema = json.loads(path.read_text(encoding="utf-8"))
    return [m["name"] for m in schema.get("metrics", []) if isinstance(m, dict) and m.get("name")]


def metric_value(row: dict[str, str], metric: str) -> tuple[str, str, str]:
    return (
        norm(row.get(f"{metric}_value", "")),
        norm(row.get(f"{metric}_unit", "")),
        norm(row.get(f"{metric}_evidence", "")),
    )


def has_metric(row: dict[str, str], metric: str) -> bool:
    value, unit, evidence = metric_value(row, metric)
    return bool(value or unit or evidence)


def metric_score(row: dict[str, str]) -> int:
    try:
        return int(float(row.get("source_score", "") or 0))
    except ValueError:
        return 0


def quality_rank(row: dict[str, str]) -> int:
    q = norm(row.get("quality_label", "")).lower()
    if q == "high":
        return 4
    if q == "medium":
        return 3
    if q == "condition":
        return 2
    if q == "candidate":
        return 1
    return 2 if row.get("keyword") != HIGH_RECALL_KEYWORD else 0


def best_row(rows: list[dict[str, str]], metric: str) -> dict[str, str] | None:
    candidates = [r for r in rows if has_metric(r, metric)]
    if not candidates:
        return None
    candidates.sort(
        key=lambda r: (
            quality_rank(r),
            metric_score(r),
            len(metric_value(r, metric)[2]),
            bool(metric_value(r, metric)[0]),
        ),
        reverse=True,
    )
    return candidates[0]


def first_evidence(row: dict[str, str], metrics: list[str]) -> str:
    structured = norm(row.get("structured_metric", ""))
    if structured:
        evidence = metric_value(row, structured)[2]
        if evidence:
            return evidence
    for metric in list(RESULT_METRICS) + list(CONDITION_METRICS) + list(IDENTITY_METRICS):
        if metric in metrics:
            evidence = metric_value(row, metric)[2]
            if evidence:
                return evidence
    for metric in metrics:
        evidence = metric_value(row, metric)[2]
        if evidence:
            return evidence
    return ""


def evidence_key(row: dict[str, str], metrics: list[str]) -> str:
    doi = norm(row.get("doi", "")).lower()
    evidence = first_evidence(row, metrics).lower()
    evidence = re.sub(r"\s+", " ", evidence)
    if not evidence:
        evidence = norm(row.get("article_key", "")).lower()
    digest = hashlib.sha1(evidence[:1200].encode("utf-8", errors="ignore")).hexdigest()[:16]
    return f"{doi}|{digest}"


def put_metric(out: dict[str, str], row: dict[str, str], metric: str) -> None:
    value, unit, evidence = metric_value(row, metric)
    if not (value or unit or evidence):
        return
    for suffix, source_value in [
        ("value", value),
        ("unit", unit),
        ("evidence", evidence),
        ("norm_value", norm(row.get(f"{metric}_norm_value", ""))),
        ("norm_unit", norm(row.get(f"{metric}_norm_unit", ""))),
        ("violations", norm(row.get(f"{metric}_violations", ""))),
        ("confidence", norm(row.get(f"{metric}_confidence", ""))),
    ]:
        key = f"{metric}_{suffix}"
        if source_value and not out.get(key):
            out[key] = source_value


def copy_best_context(out: dict[str, str], rows: list[dict[str, str]], metrics: list[str]) -> None:
    for metric in metrics:
        if metric in RESULT_METRICS:
            continue
        row = best_row(rows, metric)
        if row:
            put_metric(out, row, metric)


def result_rows_for_group(rows: list[dict[str, str]], metrics: list[str]) -> list[tuple[dict[str, str], str]]:
    result_rows: list[tuple[dict[str, str], str]] = []
    seen: set[str] = set()
    for row in rows:
        structured = norm(row.get("structured_metric", ""))
        candidate_metrics = [structured] if structured in RESULT_METRICS else [m for m in metrics if m in RESULT_METRICS]
        for metric in candidate_metrics:
            if metric not in RESULT_METRICS or not has_metric(row, metric):
                continue
            value, unit, evidence = metric_value(row, metric)
            key = "|".join([metric, value.lower(), unit.lower(), evidence[:260].lower()])
            if key in seen:
                continue
            seen.add(key)
            result_rows.append((row, metric))
    result_rows.sort(key=lambda item: (quality_rank(item[0]), metric_score(item[0])), reverse=True)
    return result_rows


def has_result(row: dict[str, str], metrics: list[str]) -> bool:
    return any(has_metric(row, metric) for metric in metrics if metric in RESULT_METRICS)


def clean_level(row: dict[str, str], metrics: list[str]) -> tuple[str, str]:
    result_metric = norm(row.get("primary_result_metric", ""))
    result_value = norm(row.get("primary_result_value", ""))
    result_unit = norm(row.get("primary_result_unit", ""))
    product = norm(row.get("main_product_name_value", "")).lower()
    host = norm(row.get("expression_host_value", "")).lower()
    evidence = norm(row.get("primary_result_evidence", "")).lower()
    quality = norm(row.get("aggregation_quality", ""))

    if not result_metric:
        return "", "no_primary_result_metric"
    if result_metric != "llps_state" and not re.search(r"\d", result_value):
        return "", "primary_result_has_no_numeric_value"
    if result_metric in {"glabridin_titer", "enzyme_activity", "specific_activity", "kcat", "km"} and not result_unit:
        return "", "primary_result_missing_unit"
    if len(evidence) < 30:
        return "", "short_primary_evidence"
    if "references" in evidence and "doi" in evidence:
        return "", "reference_like_evidence"

    has_product = product not in LOW_VALUE_PRODUCTS
    has_host = host not in LOW_VALUE_HOSTS or bool(norm(row.get("reaction_system_type_value", "")))
    has_condition = any(has_metric(row, m) for m in metrics if m in CONDITION_METRICS)

    if result_metric in {"critical_phase_concentration", "llps_state", "frap_half_time", "droplet_dissolution_time"}:
        if any(t in evidence for t in ["phase", "condensate", "droplet", "coacervate", "frap"]):
            return "A_llps", ""
        return "C_llps_candidate", ""
    if quality in {"high", "medium", "llm"} and has_product and has_host:
        return "A_complete", ""
    if has_product and has_condition:
        return "B_product_condition", ""
    if has_product or has_host:
        return "C_partial_context", ""
    return "D_result_only", ""


def aggregate_full_row(row: dict[str, str], metrics: list[str]) -> dict[str, str] | None:
    result_metrics = [m for m in metrics if m in RESULT_METRICS and has_metric(row, m)]
    if not result_metrics:
        return None
    primary = result_metrics[0]
    for preferred in ["glabridin_titer", "glabridin_yield", "substrate_conversion", "enzyme_activity", "specific_activity", "critical_phase_concentration", "llps_state"]:
        if preferred in result_metrics:
            primary = preferred
            break
    out = base_output(row, source_mode="llm_or_existing_multi_metric")
    for metric in metrics:
        put_metric(out, row, metric)
    value, unit, evidence = metric_value(row, primary)
    out["primary_result_metric"] = primary
    out["primary_result_value"] = value
    out["primary_result_unit"] = unit
    out["primary_result_evidence"] = evidence
    out["aggregation_quality"] = "llm"
    out["source_row_count"] = "1"
    out["source_article_keys"] = norm(row.get("article_key", ""))
    return out


def base_output(row: dict[str, str], *, source_mode: str) -> dict[str, str]:
    return {
        "aggregate_record_id": "",
        "doi": norm(row.get("doi", "")),
        "pii": norm(row.get("pii", "")),
        "title": norm(row.get("title", "")),
        "schema_id": norm(row.get("schema_id", "")),
        "source_mode": source_mode,
        "source_keywords": norm(row.get("keyword", "")),
        "source_row_count": "",
        "source_article_keys": "",
        "source_quality_labels": "",
        "source_scores": "",
        "primary_result_metric": "",
        "primary_result_value": "",
        "primary_result_unit": "",
        "primary_result_evidence": "",
        "aggregation_quality": "",
        "clean_level": "",
        "exclude_reason": "",
    }


def aggregate_high_recall_group(rows: list[dict[str, str]], metrics: list[str]) -> list[dict[str, str]]:
    outputs: list[dict[str, str]] = []
    if not rows:
        return outputs
    context_rows = rows
    for result_row, result_metric in result_rows_for_group(rows, metrics):
        out = base_output(result_row, source_mode="aggregated_high_recall_evidence_group")
        copy_best_context(out, context_rows, metrics)
        put_metric(out, result_row, result_metric)
        value, unit, evidence = metric_value(result_row, result_metric)
        out["primary_result_metric"] = result_metric
        out["primary_result_value"] = value
        out["primary_result_unit"] = unit
        out["primary_result_evidence"] = evidence
        labels = sorted({norm(r.get("quality_label", "")) for r in rows if norm(r.get("quality_label", ""))})
        scores = sorted({str(metric_score(r)) for r in rows if metric_score(r)}, key=lambda x: int(x), reverse=True)
        keywords = sorted({norm(r.get("keyword", "")) for r in rows if norm(r.get("keyword", ""))})
        article_keys = [norm(r.get("article_key", "")) for r in rows if norm(r.get("article_key", ""))]
        out["source_row_count"] = str(len(rows))
        out["source_article_keys"] = "; ".join(article_keys[:20])
        out["source_quality_labels"] = "; ".join(labels)
        out["source_scores"] = "; ".join(scores[:10])
        out["source_keywords"] = "; ".join(keywords)
        if any(q in {"high", "medium"} for q in labels):
            out["aggregation_quality"] = "high" if "high" in labels else "medium"
        elif "condition" in labels:
            out["aggregation_quality"] = "condition_linked"
        else:
            out["aggregation_quality"] = "candidate"
        outputs.append(out)
    return outputs


def stable_record_id(row: dict[str, str]) -> str:
    raw = "|".join([
        norm(row.get("doi", "")).lower(),
        norm(row.get("primary_result_metric", "")).lower(),
        norm(row.get("primary_result_value", "")).lower(),
        norm(row.get("primary_result_unit", "")).lower(),
        norm(row.get("main_product_name_value", "")).lower(),
        norm(row.get("expression_host_value", "")).lower(),
        norm(row.get("enzyme_name_value", "")).lower(),
        norm(row.get("substrate_name_value", "")).lower(),
        norm(row.get("reaction_time_value", "")).lower(),
        norm(row.get("reaction_temperature_value", "")).lower(),
        norm(row.get("reaction_ph_value", "")).lower(),
        norm(row.get("primary_result_evidence", ""))[:300].lower(),
    ])
    return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]


def write_long_table(path: Path, rows: list[dict[str, str]], metrics: list[str]) -> None:
    fields = [
        "aggregate_record_id",
        "doi",
        "title",
        "clean_level",
        "source_mode",
        "primary_result_metric",
        "metric",
        "metric_role",
        "value",
        "unit",
        "evidence",
        "aggregation_quality",
        "source_scores",
        "source_article_keys",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            for metric in metrics:
                value, unit, evidence = metric_value(row, metric)
                if not (value or unit or evidence):
                    continue
                if metric == row.get("primary_result_metric"):
                    role = "primary_result"
                elif metric in RESULT_METRICS:
                    role = "other_result"
                elif metric in CONDITION_METRICS:
                    role = "condition"
                else:
                    role = "identity_context"
                writer.writerow({
                    "aggregate_record_id": row.get("aggregate_record_id", ""),
                    "doi": row.get("doi", ""),
                    "title": row.get("title", ""),
                    "clean_level": row.get("clean_level", ""),
                    "source_mode": row.get("source_mode", ""),
                    "primary_result_metric": row.get("primary_result_metric", ""),
                    "metric": metric,
                    "metric_role": role,
                    "value": value,
                    "unit": unit,
                    "evidence": evidence,
                    "aggregation_quality": row.get("aggregation_quality", ""),
                    "source_scores": row.get("source_scores", ""),
                    "source_article_keys": row.get("source_article_keys", ""),
                })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--long-out", type=Path, default=DEFAULT_LONG)
    parser.add_argument("--excluded", type=Path, default=DEFAULT_EXCLUDED)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()

    metrics = load_metrics(args.schema)
    with args.input.open("r", encoding="utf-8-sig", newline="") as f:
        input_rows = list(csv.DictReader(f))

    high_recall_groups: dict[str, list[dict[str, str]]] = {}
    aggregate_candidates: list[dict[str, str]] = []
    skipped_source_rows = 0
    for row in input_rows:
        if norm(row.get("keyword", "")) == HIGH_RECALL_KEYWORD or norm(row.get("structured_metric", "")):
            high_recall_groups.setdefault(evidence_key(row, metrics), []).append(row)
        else:
            out = aggregate_full_row(row, metrics)
            if out:
                aggregate_candidates.append(out)
            else:
                skipped_source_rows += 1

    for group_rows in high_recall_groups.values():
        aggregate_candidates.extend(aggregate_high_recall_group(group_rows, metrics))

    out_rows: list[dict[str, str]] = []
    excluded_rows: list[dict[str, str]] = []
    seen: set[str] = set()
    duplicate_rows = 0
    for row in aggregate_candidates:
        level, reason = clean_level(row, metrics)
        row["clean_level"] = level
        row["exclude_reason"] = reason
        row["aggregate_record_id"] = stable_record_id(row)
        if not level:
            excluded_rows.append(row)
            continue
        if row["aggregate_record_id"] in seen:
            duplicate_rows += 1
            dup = dict(row)
            dup["exclude_reason"] = "duplicate_after_aggregation"
            excluded_rows.append(dup)
            continue
        seen.add(row["aggregate_record_id"])
        out_rows.append(row)

    metric_fields: list[str] = []
    for metric in metrics:
        for suffix in ["value", "unit", "evidence", "norm_value", "norm_unit", "violations", "confidence"]:
            metric_fields.append(f"{metric}_{suffix}")
    base_fields = [
        "aggregate_record_id", "doi", "pii", "title", "schema_id", "source_mode",
        "source_keywords", "source_row_count", "source_article_keys",
        "source_quality_labels", "source_scores", "primary_result_metric",
        "primary_result_value", "primary_result_unit", "primary_result_evidence",
        "aggregation_quality", "clean_level",
    ]
    fields = base_fields + metric_fields
    excluded_fields = fields + ["exclude_reason"]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(out_rows)
    with args.excluded.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=excluded_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(excluded_rows)
    write_long_table(args.long_out, out_rows, metrics)

    by_level: dict[str, int] = {}
    by_primary: dict[str, int] = {}
    by_source_mode: dict[str, int] = {}
    dois: set[str] = set()
    for row in out_rows:
        by_level[row["clean_level"]] = by_level.get(row["clean_level"], 0) + 1
        by_primary[row["primary_result_metric"]] = by_primary.get(row["primary_result_metric"], 0) + 1
        by_source_mode[row["source_mode"]] = by_source_mode.get(row["source_mode"], 0) + 1
        if row.get("doi"):
            dois.add(row["doi"].lower())
    summary = {
        "input_rows": len(input_rows),
        "skipped_source_rows_without_result": skipped_source_rows,
        "high_recall_evidence_groups": len(high_recall_groups),
        "aggregate_candidates_before_cleaning": len(aggregate_candidates),
        "clean_aggregated_records": len(out_rows),
        "excluded_aggregated_records": len(excluded_rows),
        "duplicates_removed_after_aggregation": duplicate_rows,
        "unique_dois": len(dois),
        "by_clean_level": dict(sorted(by_level.items())),
        "by_primary_result_metric": dict(sorted(by_primary.items())),
        "by_source_mode": dict(sorted(by_source_mode.items())),
        "output": str(args.out),
        "long_output": str(args.long_out),
        "excluded_output": str(args.excluded),
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

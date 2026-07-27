from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "essay" / "aggregated_analysis_ready_database.csv"
DEFAULT_OUT = ROOT / "essay" / "optimized_experimental_database.csv"
DEFAULT_CORE = ROOT / "essay" / "optimized_core_experimental_database.csv"
DEFAULT_REVIEW = ROOT / "essay" / "optimized_review_queue.csv"
DEFAULT_LONG = ROOT / "essay" / "optimized_experimental_database_long.csv"
DEFAULT_SUMMARY = ROOT / "essay" / "optimized_experimental_database_summary.json"

RESULT_METRICS = {
    "glabridin_titer", "glabridin_yield", "glabridin_concentration",
    "glabridin_selectivity", "substrate_conversion", "enzyme_activity",
    "specific_activity", "relative_activity", "kinetic_efficiency",
    "kcat", "km", "critical_phase_concentration", "frap_half_time",
    "droplet_dissolution_time", "catalytic_efficiency_fold_change",
    "llps_state",
}
CONDITION_METRICS = {
    "reaction_temperature", "reaction_ph", "reaction_time",
    "substrate_concentration", "cofactor_concentration",
    "cosubstrate_concentration", "cell_density_od600",
    "llps_scaffold_concentration", "llps_salt_concentration",
}
IDENTITY_METRICS = {
    "enzyme_name", "enzyme_mutant", "enzyme_source_species",
    "expression_host", "substrate_name", "main_product_name",
    "reaction_system_type", "llps_component", "llps_trigger",
    "phase_regulation_direction", "data_source_type",
}

TITER_TO_MG_L = {
    "mg/l": 1.0,
    "mg l-1": 1.0,
    "mg·l-1": 1.0,
    "g/l": 1000.0,
    "g l-1": 1000.0,
    "ug/l": 0.001,
    "µg/l": 0.001,
    "μg/l": 0.001,
    "ng/l": 0.000001,
    "mg/ml": 1000.0,
}
TIME_TO_H = {"h": 1.0, "hr": 1.0, "hrs": 1.0, "min": 1 / 60, "s": 1 / 3600, "day": 24.0, "days": 24.0}


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def low(value: str) -> str:
    return norm(value).lower()


def clean_html(value: str) -> str:
    return norm(re.sub(r"<[^>]+>", " ", str(value or "")))


def metric_value(row: dict[str, str], metric: str) -> tuple[str, str, str]:
    return norm(row.get(f"{metric}_value", "")), norm(row.get(f"{metric}_unit", "")), norm(row.get(f"{metric}_evidence", ""))


def has_metric(row: dict[str, str], metric: str) -> bool:
    value, unit, evidence = metric_value(row, metric)
    return bool(value or unit or evidence)


def parse_numeric(value: str) -> tuple[str, str, str, str]:
    text = norm(value)
    if not text:
        return "", "", "", ""
    qualifier = ""
    if text.startswith((">", "<", "≥", "≤", "~", "≈")):
        qualifier = text[0]
    cleaned = text.replace(",", "")
    nums = re.findall(r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)", cleaned)
    if not nums:
        return "", "", "", qualifier
    if len(nums) >= 2 and re.search(r"\d\s*(?:-|to|–|—)\s*\d", cleaned, re.I):
        return nums[0], nums[0], nums[1], qualifier or "range"
    return nums[0], nums[0], nums[0], qualifier


def canonical_unit(unit: str) -> str:
    u = low(unit).replace(" ", "")
    mapping = {
        "mg/l": "mg/L", "mgl-1": "mg/L", "mg·l-1": "mg/L",
        "g/l": "g/L", "gl-1": "g/L",
        "ug/l": "ug/L", "µg/l": "ug/L", "μg/l": "ug/L",
        "ng/l": "ng/L",
        "mg/ml": "mg/mL",
        "u/mg": "U/mg", "u/ml": "U/mL",
        "percent": "%", "%": "%",
        "h": "h", "hr": "h", "hrs": "h", "min": "min", "s": "s",
        "day": "day", "days": "day",
        "c": "C", "°c": "C", "degc": "C",
        "mm": "mM", "um": "uM", "µm": "uM", "μm": "uM", "nm": "nM",
        "od600": "OD600",
    }
    return mapping.get(u, norm(unit))


def normalize_numeric(metric: str, value: str, unit: str) -> tuple[str, str, str, str, str]:
    num, vmin, vmax, qualifier = parse_numeric(value)
    unit_norm = canonical_unit(unit)
    numeric_norm = num
    unit_converted = unit_norm
    if not num:
        return "", "", "", unit_norm, qualifier
    try:
        x = float(num)
        u = low(unit)
        if metric in {"glabridin_titer", "glabridin_concentration"} and u in TITER_TO_MG_L:
            numeric_norm = f"{x * TITER_TO_MG_L[u]:.6g}"
            unit_converted = "mg/L"
        elif metric == "reaction_time" and u in TIME_TO_H:
            numeric_norm = f"{x * TIME_TO_H[u]:.6g}"
            unit_converted = "h"
    except ValueError:
        pass
    return numeric_norm, vmin, vmax, unit_converted, qualifier


def canonical_host(host: str) -> tuple[str, str]:
    text = clean_html(host)
    l = text.lower()
    if any(x in l for x in ["saccharomyces cerevisiae", "s. cerevisiae", "by474", "invsc", "cEN.PK".lower()]):
        return "Saccharomyces cerevisiae", "yeast"
    if any(x in l for x in ["pichia pastoris", "komagataella phaffii", "k. phaffii", "p. pastoris", "ogataea polymorpha"]):
        return "Pichia/Komagataella/Ogataea yeast", "yeast"
    if "yarrowia lipolytica" in l or "y. lipolytica" in l:
        return "Yarrowia lipolytica", "yeast"
    if "yeast" in l:
        return "yeast", "yeast"
    if any(x in l for x in ["escherichia coli", "e. coli", "bl21", "dh5", "top10"]):
        return "Escherichia coli", "bacteria"
    if "bacillus subtilis" in l:
        return "Bacillus subtilis", "bacteria"
    if "bacillus" in l:
        return "Bacillus", "bacteria"
    if "corynebacterium glutamicum" in l:
        return "Corynebacterium glutamicum", "bacteria"
    if "streptomyces" in l:
        return "Streptomyces", "bacteria"
    if "nicotiana" in l or "arabidopsis" in l or "plant" in l:
        return text or "", "plant"
    return text, "unknown" if not text else "other"


def canonical_product(product: str, title: str, evidence: str) -> tuple[str, str]:
    text = clean_html(product)
    all_text = f"{text} {title} {evidence}".lower()
    product_map = [
        ("glabridin", "glabridin", "isoflavonoid"),
        ("liquiritigenin", "liquiritigenin", "flavonoid"),
        ("naringenin", "naringenin", "flavonoid"),
        ("taxifolin", "taxifolin", "flavonoid"),
        ("kaempferol", "kaempferol", "flavonoid"),
        ("quercetin", "quercetin", "flavonoid"),
        ("resveratrol", "resveratrol", "stilbene"),
        ("pinocembrin", "pinocembrin", "flavonoid"),
        ("apigenin", "apigenin", "flavonoid"),
        ("eriodictyol", "eriodictyol", "flavonoid"),
        ("isoflav", "isoflavonoid", "isoflavonoid"),
        ("flavonoid", "flavonoid", "flavonoid"),
        ("limonene", "limonene", "terpenoid"),
        ("lycopene", "lycopene", "isoprenoid"),
        ("carotene", "carotene", "isoprenoid"),
        ("astaxanthin", "astaxanthin", "isoprenoid"),
        ("squalene", "squalene", "isoprenoid"),
        ("taxadiene", "taxadiene", "terpenoid"),
        ("amorpha", "amorpha-4,11-diene", "terpenoid"),
        ("farnesene", "farnesene", "terpenoid"),
        ("isoprene", "isoprene", "isoprenoid"),
        ("menaquinone", "menaquinone", "isoprenoid"),
    ]
    for needle, canonical, family in product_map:
        if needle in all_text:
            return canonical if not text else text, family
    if any(x in all_text for x in ["condensate", "droplet", "phase separation", "coacervate"]):
        return text, "llps_system"
    if any(x in all_text for x in ["natural product", "specialized metabolite", "secondary metabolite"]):
        return text, "natural_product"
    return text, "unknown" if not text else "other"


def relevance(row: dict[str, str], host_group: str, product_family: str) -> tuple[int, str]:
    text = " ".join([
        low(row.get("title", "")),
        low(row.get("primary_result_evidence", "")),
        low(row.get("main_product_name_value", "")),
        low(row.get("llps_state_value", "")),
        low(row.get("llps_component_value", "")),
        low(row.get("reaction_system_type_value", "")),
    ])
    score = 0
    tags: list[str] = []
    if product_family in {"isoflavonoid", "flavonoid", "stilbene"}:
        score += 4
        tags.append("flavonoid_or_isoflavonoid")
    if product_family in {"terpenoid", "isoprenoid", "natural_product"}:
        score += 3
        tags.append("natural_product_or_isoprenoid")
    if host_group == "yeast":
        score += 3
        tags.append("yeast_host")
    if any(x in text for x in ["phase separation", "condensate", "droplet", "coacervate", "llps", "membraneless"]):
        score += 5
        tags.append("llps_related")
    if any(x in text for x in ["metabolic engineering", "heterologous", "biosynthesis", "cell factory", "pathway"]):
        score += 2
        tags.append("metabolic_engineering")
    if any(x in text for x in ["titer", "yield", "production", "conversion", "activity"]):
        score += 1
        tags.append("experimental_result")
    return score, ";".join(dict.fromkeys(tags))


def completeness(row: dict[str, str]) -> int:
    score = 0
    checks = [
        ("primary_result_value", 20),
        ("primary_result_unit", 10),
        ("primary_result_evidence", 15),
        ("main_product_name_value", 15),
        ("expression_host_value", 15),
        ("reaction_time_value", 8),
        ("reaction_temperature_value", 6),
        ("reaction_ph_value", 6),
        ("substrate_name_value", 5),
    ]
    for key, points in checks:
        if norm(row.get(key, "")):
            score += points
    return min(score, 100)


def database_tier(row: dict[str, str], score: int, complete: int) -> str:
    level = row.get("clean_level", "")
    metric = row.get("primary_result_metric", "")
    if level.startswith("A_") and score >= 5 and complete >= 60:
        return "core"
    if level.startswith("A_") and metric in {"llps_state", "critical_phase_concentration"}:
        return "llps_core"
    if score >= 4 and complete >= 45:
        return "silver"
    if level.startswith("C_") or complete < 45 or score < 3:
        return "review"
    return "silver"


def dedupe_key(row: dict[str, str]) -> str:
    parts = [
        row.get("doi", "").lower(),
        row.get("canonical_product", "").lower(),
        row.get("canonical_host", "").lower(),
        row.get("primary_result_metric", "").lower(),
        row.get("primary_result_numeric_normalized", "").lower() or row.get("primary_result_value", "").lower(),
        row.get("primary_result_unit_normalized", "").lower(),
        row.get("reaction_time_value", "").lower(),
        row.get("reaction_temperature_value", "").lower(),
        row.get("reaction_ph_value", "").lower(),
        row.get("substrate_concentration_value", "").lower(),
    ]
    return hashlib.sha1("|".join(parts).encode("utf-8", errors="ignore")).hexdigest()[:16]


def row_rank(row: dict[str, str]) -> tuple[int, int, int]:
    tier_rank = {"core": 4, "llps_core": 4, "silver": 3, "review": 1}.get(row.get("database_tier", ""), 0)
    return tier_rank, int(row.get("completeness_score", "0") or 0), int(row.get("project_relevance_score", "0") or 0)


def build_long(path: Path, rows: list[dict[str, str]], source_fields: list[str]) -> None:
    metric_names = []
    for field in source_fields:
        if field.endswith("_value"):
            metric = field[:-6]
            if f"{metric}_evidence" in source_fields:
                metric_names.append(metric)
    fields = [
        "optimized_record_id", "database_tier", "doi", "title", "canonical_product",
        "product_family", "canonical_host", "host_group", "primary_result_metric",
        "metric", "metric_role", "value", "unit", "evidence", "project_relevance_tags",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            for metric in metric_names:
                value, unit, evidence = metric_value(row, metric)
                if not (value or unit or evidence):
                    continue
                if metric == row.get("primary_result_metric"):
                    role = "primary_result"
                elif metric in RESULT_METRICS:
                    role = "other_result"
                elif metric in CONDITION_METRICS:
                    role = "condition"
                elif metric in IDENTITY_METRICS:
                    role = "identity_context"
                else:
                    role = "other"
                writer.writerow({
                    "optimized_record_id": row.get("optimized_record_id", ""),
                    "database_tier": row.get("database_tier", ""),
                    "doi": row.get("doi", ""),
                    "title": row.get("title", ""),
                    "canonical_product": row.get("canonical_product", ""),
                    "product_family": row.get("product_family", ""),
                    "canonical_host": row.get("canonical_host", ""),
                    "host_group": row.get("host_group", ""),
                    "primary_result_metric": row.get("primary_result_metric", ""),
                    "metric": metric,
                    "metric_role": role,
                    "value": value,
                    "unit": unit,
                    "evidence": evidence,
                    "project_relevance_tags": row.get("project_relevance_tags", ""),
                })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--core-out", type=Path, default=DEFAULT_CORE)
    parser.add_argument("--review-out", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--long-out", type=Path, default=DEFAULT_LONG)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        source_fields = list(reader.fieldnames or [])
        source_rows = list(reader)

    optimized: list[dict[str, str]] = []
    for row in source_rows:
        row = dict(row)
        title = clean_html(row.get("title", ""))
        evidence = norm(row.get("primary_result_evidence", ""))
        product, product_family = canonical_product(row.get("main_product_name_value", ""), title, evidence)
        host, host_group = canonical_host(row.get("expression_host_value", ""))
        metric = row.get("primary_result_metric", "")
        numeric, vmin, vmax, unit_norm, qualifier = normalize_numeric(metric, row.get("primary_result_value", ""), row.get("primary_result_unit", ""))
        rel_score, rel_tags = relevance(row, host_group, product_family)
        comp = completeness(row)
        row.update({
            "title_clean": title,
            "canonical_product": product,
            "product_family": product_family,
            "canonical_host": host,
            "host_group": host_group,
            "primary_result_numeric": parse_numeric(row.get("primary_result_value", ""))[0],
            "primary_result_numeric_min": vmin,
            "primary_result_numeric_max": vmax,
            "primary_result_numeric_qualifier": qualifier,
            "primary_result_numeric_normalized": numeric,
            "primary_result_unit_normalized": unit_norm,
            "project_relevance_score": str(rel_score),
            "project_relevance_tags": rel_tags,
            "completeness_score": str(comp),
        })
        row["database_tier"] = database_tier(row, rel_score, comp)
        row["optimized_record_id"] = dedupe_key(row)
        optimized.append(row)

    best_by_key: dict[str, dict[str, str]] = {}
    duplicate_rows = 0
    for row in optimized:
        key = row["optimized_record_id"]
        if key not in best_by_key:
            best_by_key[key] = row
            continue
        duplicate_rows += 1
        if row_rank(row) > row_rank(best_by_key[key]):
            best_by_key[key] = row
    deduped = list(best_by_key.values())
    deduped.sort(key=lambda r: (r.get("database_tier") != "core", r.get("database_tier") != "llps_core", -int(r.get("project_relevance_score", "0") or 0), r.get("doi", "")))

    extra_fields = [
        "optimized_record_id", "title_clean", "canonical_product", "product_family",
        "canonical_host", "host_group", "primary_result_numeric",
        "primary_result_numeric_min", "primary_result_numeric_max",
        "primary_result_numeric_qualifier", "primary_result_numeric_normalized",
        "primary_result_unit_normalized", "project_relevance_score",
        "project_relevance_tags", "completeness_score", "database_tier",
    ]
    fields = extra_fields + [f for f in source_fields if f not in extra_fields]

    core_rows = [r for r in deduped if r.get("database_tier") in {"core", "llps_core", "silver"}]
    review_rows = [r for r in deduped if r.get("database_tier") == "review"]

    for path, rows in [(args.out, deduped), (args.core_out, core_rows), (args.review_out, review_rows)]:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    build_long(args.long_out, deduped, source_fields)

    by_tier: dict[str, int] = {}
    by_product_family: dict[str, int] = {}
    by_host_group: dict[str, int] = {}
    by_metric: dict[str, int] = {}
    dois: set[str] = set()
    for row in deduped:
        by_tier[row["database_tier"]] = by_tier.get(row["database_tier"], 0) + 1
        by_product_family[row["product_family"]] = by_product_family.get(row["product_family"], 0) + 1
        by_host_group[row["host_group"]] = by_host_group.get(row["host_group"], 0) + 1
        by_metric[row["primary_result_metric"]] = by_metric.get(row["primary_result_metric"], 0) + 1
        if row.get("doi"):
            dois.add(row["doi"].lower())
    summary = {
        "input": str(args.input),
        "input_rows": len(source_rows),
        "optimized_rows": len(deduped),
        "duplicates_removed": duplicate_rows,
        "core_rows": len(core_rows),
        "review_rows": len(review_rows),
        "unique_dois": len(dois),
        "by_database_tier": dict(sorted(by_tier.items())),
        "by_product_family": dict(sorted(by_product_family.items())),
        "by_host_group": dict(sorted(by_host_group.items())),
        "by_primary_result_metric": dict(sorted(by_metric.items())),
        "output": str(args.out),
        "core_output": str(args.core_out),
        "review_output": str(args.review_out),
        "long_output": str(args.long_out),
    }
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

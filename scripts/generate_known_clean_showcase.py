from __future__ import annotations

import csv
import html
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ESSAY = ROOT / "essay"
SRC = ESSAY / "optimized_experimental_database_with_supplementary_expanded160_union_evidence_aware_fulltext_pro_completed_si_rule_fieldbackfilled.csv"
OUT_CLEAN = ESSAY / "known_clean_database_for_showcase.csv"
OUT_CORE = ESSAY / "known_clean_core_records_for_analysis.csv"
OUT_SUMMARY = ESSAY / "known_clean_showcase_summary.json"
OUT_HTML = ESSAY / "known_clean_methodology_showcase_en.html"
PDF_PANEL_DIR = ESSAY / "pdf_figure_panels"
PDF_VERSION_PANELS = [
    {
        "id": "Appendix Fig. A",
        "title": "Nature-style vector PDF panel, version 1",
        "pdf": "nature_style_complete_vector_figure_pack_en.pdf",
        "prefix": "nature_complete_v1",
        "caption": "Earlier complete Nature-style vector figure pack, retained as a visual archive for comparison with the known-clean showcase report.",
    },
    {
        "id": "Appendix Fig. B",
        "title": "Nature-style vector PDF panel, version 2",
        "pdf": "nature_style_complete_vector_figure_pack_en_v2.pdf",
        "prefix": "nature_complete_v2",
        "caption": "Refined complete Nature-style vector figure pack, included alongside version 1 so that changes in layout, legend spacing and panel organization can be compared in the same HTML report.",
    },
]

UNKNOWN = {
    "",
    "unknown",
    "none",
    "null",
    "nan",
    "n/a",
    "na",
    "not specified",
    "not available",
    "unidentified",
    "not reported",
}

MORANDI = [
    "#9A7F87",
    "#B8A48A",
    "#7D95A8",
    "#9AAB8F",
    "#C1A3A8",
    "#A9A39A",
    "#D0B07D",
    "#8D9B96",
    "#B7A7C6",
    "#C0C5BA",
]
INK = "#252323"
MUTED = "#68625e"
GRID = "#DDD8D1"
PALE = "#F4F1ED"

BEST_FIELDS = [
    "best_product_family",
    "best_canonical_product",
    "best_host_group",
    "best_canonical_host",
    "best_enzyme_name_value",
    "best_enzyme_source_species_value",
    "best_expression_host_value",
    "best_substrate_name_value",
    "best_main_product_name_value",
    "best_reaction_system_type_value",
    "best_is_whole_cell_value",
    "best_llps_state_value",
    "best_llps_trigger_value",
    "best_reaction_temperature_value",
    "best_reaction_ph_value",
    "best_reaction_time_value",
    "best_substrate_concentration_value",
    "best_cell_density_od600_value",
]

EXPORT_FIELDS = [
    "optimized_record_id",
    "doi",
    "title_clean",
    "database_tier",
    "clean_level",
    "primary_result_metric",
    "primary_result_numeric_normalized",
    "primary_result_unit_normalized",
    "primary_result_value",
    "primary_result_unit",
    "primary_result_evidence",
    "best_product_family",
    "best_canonical_product",
    "best_host_group",
    "best_canonical_host",
    "best_enzyme_name_value",
    "best_enzyme_source_species_value",
    "best_expression_host_value",
    "best_substrate_name_value",
    "best_main_product_name_value",
    "best_reaction_system_type_value",
    "best_is_whole_cell_value",
    "best_llps_component_value",
    "best_llps_state_value",
    "best_llps_trigger_value",
    "best_reaction_temperature_value",
    "best_reaction_temperature_unit",
    "best_reaction_ph_value",
    "best_reaction_time_value",
    "best_reaction_time_unit",
    "best_substrate_concentration_value",
    "best_substrate_concentration_unit",
    "best_cell_density_od600_value",
    "source_mode",
    "source_keywords",
    "fulltext_pro_status",
    "llm_qc_status",
    "si_rule_backfill_methods",
    "si_rule_backfill_evidence",
    "fulltext_pro_evidence_summary",
]

PRODUCT_LABELS = {
    "flavonoid": "Flavonoid",
    "isoflavonoid": "Isoflavonoid",
    "isoprenoid": "Isoprenoid",
    "terpenoid": "Terpenoid",
    "stilbene": "Stilbene",
    "llps_system": "LLPS system",
    "natural_product": "Natural product",
    "phenylpropanoid": "Phenylpropanoid",
    "prenylflavonoid": "Prenylflavonoid",
    "other": "Other known",
}
HOST_LABELS = {
    "yeast": "Yeast",
    "bacteria": "Bacteria",
    "plant": "Plant",
    "mammalian": "Mammalian",
    "cell_free": "Cell-free",
    "cyanobacteria": "Cyanobacteria",
    "other": "Other known",
}
CLEAN_LABELS = {
    "A_complete": "A complete",
    "A_llps": "A LLPS",
    "B_product_condition": "B product-condition",
    "C_llps_candidate": "C LLPS candidate",
    "C_partial_context": "C partial-context",
    "D_result_only": "D result-only",
}
TIER_LABELS = {
    "core": "Core",
    "llps_core": "LLPS core",
    "silver": "Silver",
    "review": "Review-level",
}
METRIC_LABELS = {
    "glabridin_yield": "Yield",
    "glabridin_titer": "Titer",
    "glabridin_concentration": "Concentration",
    "enzyme_activity": "Enzyme activity",
    "specific_activity": "Specific activity",
    "relative_activity": "Relative activity",
    "substrate_conversion": "Conversion",
    "kinetic_efficiency": "kcat/Km",
    "critical_phase_concentration": "Ccrit",
    "catalytic_efficiency_fold_change": "Catalytic fold-change",
    "llps_state": "LLPS state",
    "km": "Km",
    "kcat": "kcat",
}


def clean(value: Any) -> str:
    return " ".join(str(value or "").replace("\u00a0", " ").strip().split())


def low(value: Any) -> str:
    return clean(value).lower()


def is_unknown(value: Any) -> bool:
    return low(value) in UNKNOWN


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def labelize(value: Any, mapping: dict[str, str] | None = None) -> str:
    text = clean(value)
    key = text.lower()
    if mapping and text in mapping:
        return mapping[text]
    if mapping and key in mapping:
        return mapping[key]
    return text.replace("_", " ").replace("-", " ").title() if text else "Unlabeled"


def short(value: Any, n: int = 30) -> str:
    text = clean(value)
    return text if len(text) <= n else text[: n - 1] + "..."


def parse_float(value: Any) -> float | None:
    text = clean(value)
    nums = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    if not nums:
        return None
    values = [float(x) for x in nums]
    return sum(values) / len(values)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def known_count(row: dict[str, str]) -> int:
    return sum(1 for field in BEST_FIELDS if not is_unknown(row.get(field)))


def traceable(row: dict[str, str]) -> bool:
    return (not is_unknown(row.get("doi")) or not is_unknown(row.get("title_clean"))) and not is_unknown(row.get("primary_result_evidence"))


def numeric_result(row: dict[str, str]) -> bool:
    if parse_float(row.get("primary_result_numeric_normalized")) is not None:
        return True
    return parse_float(row.get("primary_result_value")) is not None


def enrich_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for row in rows:
        r = dict(row)
        k = known_count(r)
        r["known_field_count"] = str(k)
        r["known_field_fraction"] = f"{k / len(BEST_FIELDS):.3f}"
        r["traceable_record"] = "yes" if traceable(r) else "no"
        r["numeric_result_record"] = "yes" if numeric_result(r) else "no"
        r["known_clean_inclusion_reason"] = ""
        out.append(r)
    return out


def is_showcase_known(row: dict[str, str]) -> bool:
    if not traceable(row) or not numeric_result(row):
        return False
    if int(row.get("known_field_count") or 0) < 4:
        return False
    return True


def is_core_known(row: dict[str, str]) -> bool:
    if not is_showcase_known(row):
        return False
    clean_level = clean(row.get("clean_level"))
    if clean_level == "D_result_only":
        return False
    essential = [
        "best_product_family",
        "best_canonical_product",
        "best_host_group",
        "best_canonical_host",
        "best_main_product_name_value",
    ]
    return sum(1 for field in essential if not is_unknown(row.get(field))) >= 3


def counter(rows: list[dict[str, str]], field: str, mapping: dict[str, str] | None = None) -> Counter[str]:
    c: Counter[str] = Counter()
    for row in rows:
        if not is_unknown(row.get(field)):
            c[labelize(row.get(field), mapping)] += 1
    return c


def top_items(c: Counter[str], n: int = 8) -> list[tuple[str, int]]:
    return [(k, v) for k, v in c.most_common(n) if v > 0]


def without_other(items: list[tuple[str, int]]) -> list[tuple[str, int]]:
    return [(name, value) for name, value in items if name.lower() not in {"other", "other known"}]


def normalize_system(value: Any) -> str:
    k = low(value).replace("-", "_").replace(" ", "_")
    if not k or k in UNKNOWN:
        return ""
    if "whole" in k:
        return "Whole-cell"
    if "cell_free" in k:
        return "Cell-free"
    if "purified" in k:
        return "Purified enzyme"
    if "in_vivo" in k:
        return "In vivo"
    if "in_vitro" in k:
        return "In vitro"
    if "fermentation" in k:
        return "Fermentation"
    return labelize(value)


def titer_mg_l(row: dict[str, str]) -> float | None:
    metric = low(row.get("primary_result_metric"))
    if "titer" not in metric and "concentration" not in metric:
        return None
    unit = low(row.get("primary_result_unit_normalized") or row.get("primary_result_unit")).replace(" ", "")
    value = parse_float(row.get("primary_result_numeric_normalized") or row.get("primary_result_value"))
    if value is None:
        return None
    if unit in {"mg/l", "mgl-1", "mg·l-1"}:
        return value if 1e-9 < value < 1e8 else None
    if unit in {"g/l", "gl-1", "g·l-1"}:
        value *= 1000
        return value if 1e-9 < value < 1e8 else None
    return None


def temperature_c(row: dict[str, str]) -> float | None:
    v = parse_float(row.get("best_reaction_temperature_value"))
    return v if v is not None and 0 < v <= 100 else None


def ph_value(row: dict[str, str]) -> float | None:
    v = parse_float(row.get("best_reaction_ph_value"))
    return v if v is not None and 1 <= v <= 14 else None


def time_h(row: dict[str, str]) -> float | None:
    v = parse_float(row.get("best_reaction_time_value"))
    if v is None:
        return None
    unit = low(row.get("best_reaction_time_unit"))
    if "day" in unit or unit == "d":
        v *= 24
    elif "min" in unit:
        v /= 60
    elif unit in {"s", "sec", "second", "seconds"}:
        v /= 3600
    return v if 0 < v <= 10000 else None


def svg_bar(items: list[tuple[str, int]], title: str, width: int = 900, color: str = MORANDI[2]) -> str:
    if not items:
        return '<p class="empty">No known records available.</p>'
    left, right, top, bar_h, gap = 210, 70, 24, 22, 9
    height = top + len(items) * (bar_h + gap) + 18
    max_v = max(v for _, v in items) or 1
    plot_w = width - left - right
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">', f'<title>{esc(title)}</title>']
    for i, (name, value) in enumerate(items):
        y = top + i * (bar_h + gap)
        w = max(2, plot_w * value / max_v)
        parts.append(f'<text class="axis" x="{left-10}" y="{y+15}" text-anchor="end">{esc(short(name, 28))}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="2.5" fill="{color}"></rect>')
        parts.append(f'<text class="value" x="{left+w+8:.1f}" y="{y+15}">{value:,}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_coverage(rows: list[dict[str, str]], width: int = 920) -> str:
    labels = [
        ("Product family", "best_product_family"),
        ("Canonical product", "best_canonical_product"),
        ("Host group", "best_host_group"),
        ("Canonical host", "best_canonical_host"),
        ("Expression host", "best_expression_host_value"),
        ("Main product", "best_main_product_name_value"),
        ("Substrate", "best_substrate_name_value"),
        ("Reaction system", "best_reaction_system_type_value"),
        ("Temperature", "best_reaction_temperature_value"),
        ("pH", "best_reaction_ph_value"),
        ("Reaction time", "best_reaction_time_value"),
        ("Enzyme name", "best_enzyme_name_value"),
        ("Enzyme source", "best_enzyme_source_species_value"),
    ]
    total = len(rows)
    items = [(label, sum(1 for r in rows if not is_unknown(r.get(field)))) for label, field in labels]
    left, right, top, bar_h, gap = 190, 100, 22, 20, 8
    height = top + len(items) * (bar_h + gap) + 20
    plot_w = width - left - right
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Known field coverage">', "<title>Known field coverage</title>"]
    for i, (name, known) in enumerate(items):
        y = top + i * (bar_h + gap)
        pct = known / total if total else 0
        w = plot_w * pct
        parts.append(f'<text class="axis" x="{left-10}" y="{y+14}" text-anchor="end">{esc(name)}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{plot_w}" height="{bar_h}" rx="2.5" fill="{GRID}"></rect>')
        parts.append(f'<rect x="{left}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="2.5" fill="{MORANDI[3]}"></rect>')
        parts.append(f'<text class="value" x="{left+plot_w+8}" y="{y+14}">{pct*100:.1f}%</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_hist(values: list[float], title: str, unit: str, bins: int = 16, width: int = 900, log10: bool = False, markers: list[tuple[float, str]] | None = None) -> str:
    vals = [math.log10(v) if log10 and v > 0 else v for v in values if v is not None and math.isfinite(v) and (not log10 or v > 0)]
    if not vals:
        return '<p class="empty">No numeric values available.</p>'
    lo, hi = min(vals), max(vals)
    if abs(hi - lo) < 1e-9:
        hi = lo + 1
    step = (hi - lo) / bins
    counts = [0] * bins
    for v in vals:
        idx = min(bins - 1, max(0, int((v - lo) / step)))
        counts[idx] += 1
    left, right, top, bottom = 58, 24, 24, 46
    height = 265
    plot_w = width - left - right
    plot_h = height - top - bottom
    max_c = max(counts) or 1
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">', f'<title>{esc(title)}</title>']
    parts.append(f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="{INK}" stroke-width="1"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="{INK}" stroke-width="1"/>')
    bar_w = plot_w / bins * 0.78
    for i, c in enumerate(counts):
        h = plot_h * c / max_c
        x = left + i * plot_w / bins + (plot_w / bins - bar_w) / 2
        y = top + plot_h - h
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="{MORANDI[0]}" rx="2"></rect>')
    ticks = [lo, (lo + hi) / 2, hi]
    for t in ticks:
        x = left + (t - lo) / (hi - lo) * plot_w
        label = f"{10**t:.2g}" if log10 else f"{t:.3g}"
        parts.append(f'<text class="axis" x="{x:.1f}" y="{height-20}" text-anchor="middle">{esc(label)}</text>')
    parts.append(f'<text class="axis" x="{left+plot_w/2}" y="{height-4}" text-anchor="middle">{esc(unit)}</text>')
    parts.append(f'<text class="axis" x="18" y="{top+plot_h/2}" transform="rotate(-90 18 {top+plot_h/2})" text-anchor="middle">Count</text>')
    if markers:
        for raw_v, label in markers:
            if log10 and raw_v > 0:
                v = math.log10(raw_v)
            else:
                v = raw_v
            if lo <= v <= hi:
                x = left + (v - lo) / (hi - lo) * plot_w
                parts.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{top+plot_h}" stroke="{MORANDI[5]}" stroke-width="1.5"/>')
                parts.append(f'<text class="value" x="{x+5:.1f}" y="{top+13}">{esc(label)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_sankey(summary: dict[str, int], width: int = 980, height: int = 300) -> str:
    stages = [
        ("Candidate records", summary["all_rows"]),
        ("Traceable numeric records", summary["traceable_numeric_rows"]),
        ("Known-clean records", summary["known_clean_rows"]),
        ("Core analysis records", summary["core_known_rows"]),
    ]
    max_v = stages[0][1] or 1
    x_positions = [40, 300, 560, 820]
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Traceable database construction flow">', "<title>Traceable database construction flow</title>"]
    y_mid = height / 2
    prev_right = None
    prev_h = None
    for i, (label, value) in enumerate(stages):
        h = max(18, 210 * value / max_v)
        x = x_positions[i]
        y = y_mid - h / 2
        if i > 0 and prev_right is not None and prev_h is not None:
            h1 = prev_h
            h2 = h
            x1 = prev_right
            x2 = x
            y1a, y1b = y_mid - h1 / 2, y_mid + h1 / 2
            y2a, y2b = y_mid - h2 / 2, y_mid + h2 / 2
            c1 = x1 + 80
            c2 = x2 - 80
            path = f"M{x1},{y1a} C{c1},{y1a} {c2},{y2a} {x2},{y2a} L{x2},{y2b} C{c2},{y2b} {c1},{y1b} {x1},{y1b} Z"
            parts.append(f'<path d="{path}" fill="{MORANDI[i]}" opacity="0.28"></path>')
        parts.append(f'<rect x="{x}" y="{y:.1f}" width="34" height="{h:.1f}" fill="{MORANDI[i % len(MORANDI)]}" stroke="{INK}" stroke-width="0.6"></rect>')
        parts.append(f'<text class="value" x="{x+44}" y="{y_mid-7}">{value:,}</text>')
        parts.append(f'<text class="axis" x="{x+44}" y="{y_mid+12}">{esc(label)}</text>')
        prev_right = x + 34
        prev_h = h
    parts.append("</svg>")
    return "\n".join(parts)


def svg_method_flow(width: int = 980, height: int = 260) -> str:
    nodes = [
        ("Literature pool", "Scopus / WOS / Open full text"),
        ("Dynamic ICL", "Example retrieval by field and domain"),
        ("LLM extraction", "Multi-record JSON schema"),
        ("Rule checks", "Units, ranges, non-zero constraints"),
        ("Evidence-aware QC", "Full text, SI/data, DOI consensus"),
        ("Traceable DB", "DOI, title, evidence, confidence layer"),
    ]
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Methodology flow">', "<title>Methodology flow</title>"]
    box_w, box_h = 138, 70
    gap = (width - 2 * 30 - len(nodes) * box_w) / (len(nodes) - 1)
    y = 78
    for i, (title, subtitle) in enumerate(nodes):
        x = 30 + i * (box_w + gap)
        parts.append(f'<rect x="{x:.1f}" y="{y}" width="{box_w}" height="{box_h}" rx="4" fill="{PALE}" stroke="{MORANDI[i % len(MORANDI)]}" stroke-width="2"></rect>')
        parts.append(f'<text class="value" x="{x+box_w/2:.1f}" y="{y+27}" text-anchor="middle">{esc(title)}</text>')
        wrapped = subtitle if len(subtitle) < 26 else subtitle[:25] + "..."
        parts.append(f'<text class="axis" x="{x+box_w/2:.1f}" y="{y+50}" text-anchor="middle">{esc(wrapped)}</text>')
        if i < len(nodes) - 1:
            x1 = x + box_w
            x2 = x + box_w + gap - 10
            parts.append(f'<line x1="{x1+6:.1f}" y1="{y+box_h/2}" x2="{x2:.1f}" y2="{y+box_h/2}" stroke="{MUTED}" stroke-width="1.2"></line>')
            parts.append(f'<path d="M{x2:.1f},{y+box_h/2} l-6,-4 v8 z" fill="{MUTED}"></path>')
    parts.append("</svg>")
    return "\n".join(parts)


def metric_name(row: dict[str, str]) -> str:
    return labelize(row.get("primary_result_metric"), METRIC_LABELS)


def generate_summary(all_rows: list[dict[str, str]], clean_rows: list[dict[str, str]], core_rows: list[dict[str, str]]) -> dict[str, Any]:
    traceable_numeric = [r for r in all_rows if traceable(r) and numeric_result(r)]
    unique_dois = len({low(r.get("doi")) for r in clean_rows if not is_unknown(r.get("doi"))})
    source_methods: Counter[str] = Counter()
    for row in clean_rows:
        methods = [m for m in clean(row.get("si_rule_backfill_methods")).split(";") if m]
        if not methods:
            methods = [clean(row.get("source_mode")) or "original_extraction"]
        for m in methods:
            source_methods[m] += 1
    coverage = {
        field: {
            "known": sum(1 for r in clean_rows if not is_unknown(r.get(field))),
            "unknown": sum(1 for r in clean_rows if is_unknown(r.get(field))),
        }
        for field in BEST_FIELDS
    }
    titer_values = [v for r in core_rows if (v := titer_mg_l(r)) is not None]
    temperatures = [v for r in core_rows if (v := temperature_c(r)) is not None]
    phs = [v for r in core_rows if (v := ph_value(r)) is not None]
    times = [v for r in core_rows if (v := time_h(r)) is not None]
    summary = {
        "input": str(SRC),
        "known_clean_output": str(OUT_CLEAN),
        "core_known_output": str(OUT_CORE),
        "html_output": str(OUT_HTML),
        "all_rows": len(all_rows),
        "traceable_numeric_rows": len(traceable_numeric),
        "known_clean_rows": len(clean_rows),
        "core_known_rows": len(core_rows),
        "known_clean_unique_dois": unique_dois,
        "coverage": coverage,
        "top_product_families": dict(top_items(counter(clean_rows, "best_product_family", PRODUCT_LABELS), 12)),
        "top_named_product_families": dict(without_other(top_items(counter(clean_rows, "best_product_family", PRODUCT_LABELS), 12))),
        "top_host_groups": dict(top_items(counter(clean_rows, "best_host_group", HOST_LABELS), 8)),
        "top_reaction_systems": dict(top_items(Counter(normalize_system(r.get("best_reaction_system_type_value")) for r in clean_rows if normalize_system(r.get("best_reaction_system_type_value"))), 10)),
        "quality_levels": dict(top_items(counter(clean_rows, "clean_level", CLEAN_LABELS), 8)),
        "database_tiers": dict(top_items(counter(clean_rows, "database_tier", TIER_LABELS), 8)),
        "source_methods": dict(source_methods.most_common(12)),
        "numeric_distributions": {
            "titer_mg_l_n": len(titer_values),
            "titer_mg_l_median": statistics.median(titer_values) if titer_values else None,
            "temperature_c_n": len(temperatures),
            "temperature_c_median": statistics.median(temperatures) if temperatures else None,
            "ph_n": len(phs),
            "ph_median": statistics.median(phs) if phs else None,
            "time_h_n": len(times),
            "time_h_median": statistics.median(times) if times else None,
        },
    }
    return summary


def fig_section(fig_id: str, title: str, svg: str, caption: str) -> str:
    return f"""
    <section class="figure" id="{esc(fig_id)}">
      <h2>{esc(title)}</h2>
      <div class="svg-wrap">{svg}</div>
      <p class="caption"><strong>{esc(fig_id)}.</strong> {esc(caption)}</p>
    </section>
    """


def pdf_panel_appendix() -> str:
    sections = []
    for version in PDF_VERSION_PANELS:
        images = sorted(PDF_PANEL_DIR.glob(f"{version['prefix']}-*.png"), key=lambda p: int(re.search(r"-(\d+)\.png$", p.name).group(1)) if re.search(r"-(\d+)\.png$", p.name) else 0)
        if not images:
            continue
        cards = []
        for image in images:
            match = re.search(r"-(\d+)\.png$", image.name)
            page_no = match.group(1) if match else "?"
            rel = f"pdf_figure_panels/{image.name}"
            cards.append(
                f"""
                <figure class="pdf-page">
                  <img src="{esc(rel)}" alt="{esc(version['title'])}, page {esc(page_no)}">
                  <figcaption>{esc(version['id'])}.{esc(page_no)} Page {esc(page_no)} from <a href="{esc(version['pdf'])}">{esc(version['pdf'])}</a>.</figcaption>
                </figure>
                """
            )
        sections.append(
            f"""
            <section class="pdf-version">
              <h2>{esc(version['title'])}</h2>
              <p class="caption"><strong>{esc(version['id'])}.</strong> {esc(version['caption'])}</p>
              <div class="pdf-page-grid">
                {''.join(cards)}
              </div>
            </section>
            """
        )
    if not sections:
        return ""
    return f"""
    <section class="pdf-appendix" id="pdf-figure-archive">
      <h2>Previously generated PDF figure panels</h2>
      <p class="subtitle">The two earlier PDF-panel versions are embedded below as rendered page figures, while the original vector PDFs remain linked from each page caption.</p>
      {''.join(sections)}
    </section>
    """


def generate_html(all_rows: list[dict[str, str]], clean_rows: list[dict[str, str]], core_rows: list[dict[str, str]], summary: dict[str, Any]) -> str:
    product_items = without_other(top_items(counter(clean_rows, "best_product_family", PRODUCT_LABELS), 12))[:10]
    host_items = top_items(counter(clean_rows, "best_host_group", HOST_LABELS), 8)
    system_items = top_items(Counter(normalize_system(r.get("best_reaction_system_type_value")) for r in clean_rows if normalize_system(r.get("best_reaction_system_type_value"))), 9)
    clean_items = top_items(counter(clean_rows, "clean_level", CLEAN_LABELS), 8)
    tier_items = top_items(counter(clean_rows, "database_tier", TIER_LABELS), 8)
    metric_items = top_items(Counter(metric_name(r) for r in clean_rows if metric_name(r) != "Unlabeled"), 10)
    source_items = top_items(Counter(m for r in clean_rows for m in ([x for x in clean(r.get("si_rule_backfill_methods")).split(";") if x] or [clean(r.get("source_mode")) or "original_extraction"])), 10)
    titer_values = [v for r in core_rows if (v := titer_mg_l(r)) is not None]
    temperatures = [v for r in core_rows if (v := temperature_c(r)) is not None]
    phs = [v for r in core_rows if (v := ph_value(r)) is not None]
    times = [v for r in core_rows if (v := time_h(r)) is not None]
    median_titer = statistics.median(titer_values) if titer_values else None
    geom_titer = math.exp(sum(math.log(v) for v in titer_values if v > 0) / len([v for v in titer_values if v > 0])) if titer_values else None
    median_text = f"{median_titer:.2g} mg/L" if median_titer else "not available"
    geom_text = f"{geom_titer:.2g} mg/L" if geom_titer else "not available"

    methodology_points = [
        "Traceable records retain DOI, title, result value, unit and sentence-level evidence, so each chart can be audited back to literature context.",
        "Dynamic ICL retrieves field- and domain-matched examples before each LLM call instead of using a fixed five-example prompt, improving transfer across product families and LLPS cases.",
        "Multi-pass quality control combines schema validation, unit and range constraints, full-text/SI re-checking, Pro-model completion, and conservative DOI-level consensus propagation.",
        "The final analysis separates known-clean records from high-recall candidates, making downstream visualization robust without deleting the broader evidence reservoir.",
    ]
    methodology_html = "".join(f"<li>{esc(x)}</li>" for x in methodology_points)

    css = f"""
    <style>
      :root {{
        --ink: {INK};
        --muted: {MUTED};
        --paper: #fbfaf8;
        --panel: {PALE};
        --grid: {GRID};
      }}
      body {{
        margin: 0;
        font-family: Arial, Helvetica, sans-serif;
        color: var(--ink);
        background: var(--paper);
      }}
      main {{
        max-width: 1220px;
        margin: 0 auto;
        padding: 34px 38px 54px;
      }}
      h1 {{
        font-size: 30px;
        line-height: 1.18;
        margin: 0 0 10px;
        letter-spacing: 0;
      }}
      h2 {{
        font-size: 18px;
        margin: 0 0 12px;
      }}
      h3 {{
        font-size: 15px;
        margin: 0 0 8px;
      }}
      p, li {{
        font-size: 13px;
        line-height: 1.55;
      }}
      .subtitle {{
        color: var(--muted);
        max-width: 900px;
        margin: 0 0 22px;
      }}
      .metrics {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
        margin: 18px 0 24px;
      }}
      .metric {{
        border-top: 3px solid {MORANDI[2]};
        background: var(--panel);
        padding: 12px 14px;
      }}
      .metric .value {{
        display: block;
        font-size: 22px;
        font-weight: 700;
      }}
      .metric .label {{
        display: block;
        color: var(--muted);
        font-size: 12px;
        margin-top: 4px;
      }}
      .grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 18px;
        align-items: start;
      }}
      .figure {{
        break-inside: avoid;
        margin: 0 0 22px;
        background: transparent;
      }}
      .svg-wrap {{
        width: 100%;
        overflow: hidden;
      }}
      svg {{
        width: 100%;
        height: auto;
        display: block;
      }}
      .axis {{
        fill: var(--muted);
        font-size: 12px;
      }}
      .value {{
        fill: var(--ink);
        font-size: 12px;
        font-weight: 700;
      }}
      .caption {{
        margin: 8px 0 0;
        color: var(--muted);
        font-size: 12px;
      }}
      .method {{
        display: grid;
        grid-template-columns: 1.15fr 0.85fr;
        gap: 20px;
        border-top: 1px solid var(--grid);
        padding-top: 16px;
        margin: 18px 0 24px;
      }}
      .method ul {{
        margin: 0;
        padding-left: 18px;
      }}
      .table-wrap {{
        overflow-x: auto;
      }}
      .pdf-appendix {{
        margin-top: 22px;
        border-top: 1px solid var(--grid);
        padding-top: 20px;
      }}
      .pdf-version {{
        margin: 0 0 26px;
      }}
      .pdf-page-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        align-items: start;
      }}
      .pdf-page {{
        margin: 0;
        break-inside: avoid;
      }}
      .pdf-page img {{
        display: block;
        width: 100%;
        height: auto;
        border: 1px solid var(--grid);
        background: #fff;
      }}
      .pdf-page figcaption {{
        margin-top: 6px;
        color: var(--muted);
        font-size: 11px;
        line-height: 1.4;
      }}
      .pdf-page a {{
        color: inherit;
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
      }}
      th, td {{
        text-align: left;
        border-bottom: 1px solid var(--grid);
        padding: 7px 8px;
        vertical-align: top;
      }}
      th {{
        color: var(--muted);
        font-weight: 700;
      }}
      .empty {{
        color: var(--muted);
        font-size: 12px;
      }}
      @media (max-width: 860px) {{
        main {{ padding: 24px 18px; }}
        .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
        .grid, .method, .pdf-page-grid {{ grid-template-columns: 1fr; }}
      }}
      @media print {{
        body {{ background: white; }}
        main {{ max-width: none; padding: 20px; }}
        .figure {{ page-break-inside: avoid; }}
      }}
    </style>
    """

    figures = [
        fig_section(
            "Fig. 1",
            "Traceable database construction",
            svg_sankey(summary),
            "The database is filtered from all extracted candidates into traceable numeric records, known-clean records and a stricter core analysis layer. The retained layers preserve DOI/title and evidence text rather than forcing every field to be non-null.",
        ),
        fig_section(
            "Fig. 2",
            "Known-field coverage",
            svg_coverage(clean_rows),
            "Known-clean records show high coverage for host and system descriptors, while enzyme provenance and fine-grained condition fields remain deliberately sparse when direct evidence is absent.",
        ),
        fig_section(
            "Fig. 3a",
            "Product families",
            svg_bar(product_items, "Product family distribution", color=MORANDI[0]),
            "Flavonoid, isoprenoid and terpenoid records dominate the known subset, while isoflavonoid-related records remain comparatively under-represented, supporting the novelty of an isoflavonoid-focused project.",
        ),
        fig_section(
            "Fig. 3b",
            "Expression host groups",
            svg_bar(host_items, "Host group distribution", color=MORANDI[2]),
            "Yeast and bacterial systems account for most known host annotations, providing a practical design space for comparing prokaryotic and eukaryotic engineering strategies.",
        ),
        fig_section(
            "Fig. 3c",
            "Reaction system types",
            svg_bar(system_items, "Reaction system distribution", color=MORANDI[3]),
            "Whole-cell, in vivo, fermentation, cell-free and purified-enzyme records are separated to avoid conflating production experiments with biochemical assays.",
        ),
        fig_section(
            "Fig. 4a",
            "Quality-control levels",
            svg_bar(clean_items, "Clean level distribution", color=MORANDI[4]),
            "Quality tiers expose how much of the database is complete, product-condition linked, partial-context, LLPS-specific or result-only evidence.",
        ),
        fig_section(
            "Fig. 4b",
            "Database tiers",
            svg_bar(tier_items, "Database tier distribution", color=MORANDI[6]),
            "The tiering scheme separates core project-relevant records from broader silver and review-level evidence, allowing strict analysis and high-recall exploration to coexist.",
        ),
        fig_section(
            "Fig. 4c",
            "Evidence and completion methods",
            svg_bar(source_items, "Evidence method distribution", color=MORANDI[7]),
            "The final known fields originate from original extraction, dynamic ICL-assisted LLM extraction, full-text Pro completion, SI/data consensus and conservative DOI-level consensus.",
        ),
        fig_section(
            "Fig. 5a",
            "Titer distribution",
            svg_hist(titer_values, "Titer distribution", f"log10(mg/L); median={median_text}, geometric mean={geom_text}", log10=True, markers=[(0.5, "0.5 mg/L"), (5, "5 mg/L")]),
            "Titer values span orders of magnitude, so the log-scale view is the appropriate summary for positioning the project baseline and target yield.",
        ),
        fig_section(
            "Fig. 5b",
            "Temperature distribution",
            svg_hist(temperatures, "Reaction temperature distribution", "deg C", bins=14),
            "Known reaction and cultivation temperatures cluster around common microbial operating conditions, especially the yeast and bacterial ranges.",
        ),
        fig_section(
            "Fig. 5c",
            "pH distribution",
            svg_hist(phs, "Reaction pH distribution", "pH", bins=13),
            "Known pH values concentrate near neutral conditions, providing a useful reference interval for enzyme and LLPS-compatible assay design.",
        ),
        fig_section(
            "Fig. 5d",
            "Reaction time distribution",
            svg_hist(times, "Reaction time distribution", "hours", bins=16, log10=True),
            "Reaction and fermentation times cover short enzyme assays through longer production runs, supporting separate interpretation of activity and titer records.",
        ),
        fig_section(
            "Fig. 6",
            "Dynamic ICL and multi-pass QC workflow",
            svg_method_flow(),
            "The extraction agent uses dynamically matched ICL examples, schema-constrained JSON extraction and successive validation/backfill passes. This creates a traceable database rather than a one-shot prompt output.",
        ),
    ]

    rows_for_table = [
        ("All extracted candidate records", f"{summary['all_rows']:,}"),
        ("Traceable numeric records", f"{summary['traceable_numeric_rows']:,}"),
        ("Known-clean records", f"{summary['known_clean_rows']:,}"),
        ("Core analysis records", f"{summary['core_known_rows']:,}"),
        ("Unique DOIs in known-clean layer", f"{summary['known_clean_unique_dois']:,}"),
        ("Median titer", median_text),
        ("Geometric mean titer", geom_text),
    ]
    table_html = "".join(f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in rows_for_table)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Known-clean traceable literature database showcase</title>
  {css}
</head>
<body>
<main>
  <h1>Known-clean traceable literature database for LLPS-guided enzyme and metabolic engineering</h1>
  <p class="subtitle">This report uses only the fields that are explicitly known or conservatively completed. It emphasizes traceability, dynamic in-context learning and multi-pass quality control as the core dry-lab contribution.</p>
  <div class="metrics">
    <div class="metric"><span class="value">{summary['all_rows']:,}</span><span class="label">extracted candidates</span></div>
    <div class="metric"><span class="value">{summary['known_clean_rows']:,}</span><span class="label">known-clean records</span></div>
    <div class="metric"><span class="value">{summary['core_known_rows']:,}</span><span class="label">core analysis records</span></div>
    <div class="metric"><span class="value">{summary['known_clean_unique_dois']:,}</span><span class="label">traceable DOIs</span></div>
  </div>
  <section class="method">
    <div>
      <h2>Methodological contribution</h2>
      <ul>{methodology_html}</ul>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Layer or statistic</th><th>Value</th></tr></thead>
        <tbody>{table_html}</tbody>
      </table>
    </div>
  </section>
  <div class="grid">
    {''.join(figures)}
  </div>
  {pdf_panel_appendix()}
</main>
</body>
</html>
"""


def main() -> int:
    rows = enrich_rows(read_rows(SRC))
    clean_rows = []
    for row in rows:
        if is_showcase_known(row):
            row["known_clean_inclusion_reason"] = "traceable_numeric_record_with_at_least_four_known_best_fields"
            clean_rows.append(row)
    core_rows = []
    for row in clean_rows:
        if is_core_known(row):
            row["known_clean_inclusion_reason"] = "core_analysis_record_with_non_result_only_context_and_product_or_host_identity"
            core_rows.append(row)

    export_fields = EXPORT_FIELDS + ["known_field_count", "known_field_fraction", "traceable_record", "numeric_result_record", "known_clean_inclusion_reason"]
    write_rows(OUT_CLEAN, clean_rows, export_fields)
    write_rows(OUT_CORE, core_rows, export_fields)
    summary = generate_summary(rows, clean_rows, core_rows)
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_HTML.write_text(generate_html(rows, clean_rows, core_rows, summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Wrote: {OUT_CLEAN}")
    print(f"Wrote: {OUT_CORE}")
    print(f"Wrote: {OUT_SUMMARY}")
    print(f"Wrote: {OUT_HTML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

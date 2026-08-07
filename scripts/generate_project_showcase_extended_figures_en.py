# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import html
import json
import math
import re
import statistics
from collections import Counter
from pathlib import Path

import fulltext_pro_field_completion as ft


ROOT = ft.ROOT
SRC = ft.DEFAULT_OUTPUT
OUT = ROOT / "essay" / "project_showcase_extended_figures_en.html"
SUMMARY_OUT = ROOT / "essay" / "project_showcase_extended_figures_en_summary.json"

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
}

PRODUCT_FAMILIES = ["flavonoid", "isoprenoid", "terpenoid", "stilbene", "isoflavonoid", "llps_system"]
PRODUCT_LABELS = {
    "flavonoid": "Flavonoid",
    "isoprenoid": "Isoprenoid",
    "terpenoid": "Terpenoid",
    "stilbene": "Stilbene",
    "isoflavonoid": "Isoflavonoid",
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

COLORS = ["#2f6fbb", "#31a354", "#f39c12", "#b65fcf", "#d95f5f", "#1f9fb4", "#6c7a89", "#8d6e63"]


def clean(value: object) -> str:
    return " ".join(str(value or "").replace("\u00a0", " ").strip().split())


def low(value: object) -> str:
    return clean(value).lower()


def is_unknown(value: object) -> bool:
    return low(value) in UNKNOWN


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def labelize(value: object, mapping: dict[str, str] | None = None) -> str:
    text = clean(value)
    k = text.lower()
    if mapping and k in mapping:
        return mapping[k]
    return text.replace("_", " ").replace("-", " ").title() if text else "Unlabeled"


def short(value: str, limit: int = 26) -> str:
    value = clean(value)
    return value if len(value) <= limit else value[: limit - 1] + "..."


def parse_number(value: object) -> float | None:
    text = clean(value).replace("−", "-")
    matches = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    if not matches:
        return None
    vals = [float(x) for x in matches]
    if not vals:
        return None
    return sum(vals) / len(vals)


def percentile(values: list[float], x: float) -> float:
    return 100 * sum(1 for v in values if v <= x) / len(values) if values else 0.0


def median(values: list[float]) -> float:
    return statistics.median(values) if values else float("nan")


def quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return float("nan")
    pos = (len(sorted_values) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return sorted_values[lo]
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def fmt(value: float, digits: int = 2) -> str:
    if not math.isfinite(value):
        return "NA"
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    if abs(value) >= 10:
        return f"{value:,.1f}"
    return f"{value:,.{digits}f}"


def read_rows() -> list[dict[str, str]]:
    with SRC.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def counter_known(rows: list[dict[str, str]], field: str, mapping: dict[str, str] | None = None) -> Counter[str]:
    c: Counter[str] = Counter()
    for row in rows:
        value = row.get(field, "")
        if is_unknown(value):
            continue
        c[labelize(value, mapping)] += 1
    return c


def normalize_system(value: object) -> str:
    k = low(value).replace("-", "_").replace(" ", "_")
    if not k or k in UNKNOWN:
        return ""
    if k in {"whole_cell", "whole_cell_system", "wholecell"}:
        return "Whole-cell"
    if k in {"in_vivo", "invivo"}:
        return "In vivo"
    if k in {"in_vitro", "invitro"}:
        return "In vitro"
    if k in {"cell_free", "cellfree"}:
        return "Cell-free"
    if "purified" in k and "enzyme" in k:
        return "Purified enzyme"
    if "fermentation" in k:
        return "Fermentation"
    if "batch" in k:
        return "Batch"
    return labelize(value)


def temperature_c(row: dict[str, str]) -> float | None:
    value = parse_number(row.get("best_reaction_temperature_value"))
    if value is None or not (10 <= value <= 80):
        return None
    return value


def ph_value(row: dict[str, str]) -> float | None:
    value = parse_number(row.get("best_reaction_ph_value"))
    if value is None or not (1 <= value <= 14):
        return None
    return value


def reaction_time_h(row: dict[str, str]) -> float | None:
    value = parse_number(row.get("best_reaction_time_value"))
    if value is None:
        return None
    unit = low(row.get("best_reaction_time_unit"))
    if "day" in unit or unit == "d":
        value *= 24
    elif "min" in unit:
        value /= 60
    elif unit in {"s", "sec", "secs", "second", "seconds"}:
        value /= 3600
    if not (0.001 <= value <= 10000):
        return None
    return value


def titer_mg_l(row: dict[str, str]) -> float | None:
    metric = low(row.get("primary_result_metric"))
    unit = low(row.get("primary_result_unit_normalized") or row.get("primary_result_unit")).replace(" ", "")
    value = parse_number(row.get("primary_result_numeric_normalized") or row.get("primary_result_value"))
    if value is None:
        return None
    if unit in {"mg/l", "mgl-1", "mgl−1"} and ("titer" in metric or "concentration" in metric):
        if 1e-6 <= value <= 1e7:
            return value
    return None


def km_um(row: dict[str, str]) -> float | None:
    unit = clean(row.get("km_norm_unit"))
    value = parse_number(row.get("km_norm_value") or row.get("km_value"))
    if value is None or unit not in {"μM", "uM", "µM"}:
        return None
    if 0.001 <= value <= 10000:
        return value
    return None


def specific_activity_u_mg(row: dict[str, str]) -> float | None:
    unit = low(row.get("specific_activity_norm_unit") or row.get("specific_activity_unit"))
    value = parse_number(row.get("specific_activity_norm_value") or row.get("specific_activity_value"))
    if value is None:
        return None
    if "u/mg" in unit or "units/mg" in unit:
        return value if 1e-6 <= value <= 1e6 else None
    if "nmol/min/mg" in unit:
        return value / 1000 if 1e-9 <= value / 1000 <= 1e6 else None
    if "μmole" in unit and "min" in unit and "mg" in unit:
        return value if 1e-6 <= value <= 1e6 else None
    return None


def kinetic_efficiency_m_inv_s(row: dict[str, str]) -> float | None:
    unit = low(row.get("kinetic_efficiency_norm_unit") or row.get("kinetic_efficiency_unit"))
    value = parse_number(row.get("kinetic_efficiency_norm_value") or row.get("kinetic_efficiency_value"))
    if value is None:
        return None
    unit_ascii = unit.replace("⁻", "-").replace("−", "-").replace("µ", "μ")
    if "mg/kg" in unit_ascii or unit_ascii in {"", "x"}:
        return None
    if "μm" in unit_ascii or "um" in unit_ascii:
        value *= 1e6
    elif "mm" in unit_ascii:
        value *= 1e3
    elif "m" in unit_ascii:
        value *= 1
    else:
        return None
    if "min" in unit_ascii:
        value /= 60
    return value if 1e-6 <= value <= 1e12 else None


def llps_fold(row: dict[str, str]) -> float | None:
    unit = low(row.get("catalytic_efficiency_fold_change_norm_unit") or row.get("catalytic_efficiency_fold_change_unit"))
    value = parse_number(row.get("catalytic_efficiency_fold_change_norm_value") or row.get("catalytic_efficiency_fold_change_value"))
    if value is None:
        return None
    if "fold" in unit or unit == "":
        return value if 0.01 <= value <= 10000 else None
    if "%" in unit:
        return value / 100 if value > 1 else value
    return None


def bar_chart(items: list[tuple[str, int]], title: str, color: str = COLORS[0], width: int = 980) -> str:
    if not items:
        return empty("No known data available.")
    left, right, top, bar_h, gap = 220, 80, 24, 28, 10
    height = top + len(items) * (bar_h + gap) + 20
    max_v = max(v for _, v in items) or 1
    plot_w = width - left - right
    out = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">', f"<title>{esc(title)}</title>"]
    for i, (name, value) in enumerate(items):
        y = top + i * (bar_h + gap)
        w = plot_w * value / max_v
        out.append(f'<text class="axis-label" x="{left - 12}" y="{y + 19}" text-anchor="end">{esc(short(name, 28))}</text>')
        out.append(f'<rect x="{left}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="3" fill="{color}" opacity="0.86"></rect>')
        out.append(f'<text class="value-label" x="{left + w + 8:.1f}" y="{y + 19}">{value:,}</text>')
    out.append("</svg>")
    return "\n".join(out)


def histogram(values: list[float], title: str, xlabel: str, bins: list[float], color: str = COLORS[0], width: int = 980, height: int = 360, markers: list[tuple[float, str, str]] | None = None, kde: bool = False) -> str:
    values = [v for v in values if math.isfinite(v)]
    if not values:
        return empty("No valid numeric data available.")
    markers = markers or []
    counts = [0 for _ in range(len(bins) - 1)]
    for v in values:
        for i in range(len(bins) - 1):
            if bins[i] <= v < bins[i + 1] or (i == len(bins) - 2 and v == bins[i + 1]):
                counts[i] += 1
                break
    left, right, top, bottom = 70, 28, 30, 58
    plot_w, plot_h = width - left - right, height - top - bottom
    max_y = max(counts) or 1
    x_min, x_max = bins[0], bins[-1]

    def sx(x: float) -> float:
        return left + (x - x_min) / (x_max - x_min) * plot_w

    def sy(y: float) -> float:
        return top + plot_h - y / max_y * plot_h

    out = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">', f"<title>{esc(title)}</title>"]
    for t in nice_ticks(x_min, x_max, 7):
        x = sx(t)
        out.append(f'<line class="grid" x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{top + plot_h}"></line>')
        out.append(f'<text class="axis-label" x="{x:.1f}" y="{height - 28}" text-anchor="middle">{fmt(t, 1)}</text>')
    for t in nice_ticks(0, max_y, 5):
        y = sy(t)
        out.append(f'<line class="grid" x1="{left}" x2="{left + plot_w}" y1="{y:.1f}" y2="{y:.1f}"></line>')
        out.append(f'<text class="axis-label" x="{left - 8}" y="{y + 4:.1f}" text-anchor="end">{int(t)}</text>')
    for i, count in enumerate(counts):
        x0, x1 = sx(bins[i]), sx(bins[i + 1])
        y = sy(count)
        out.append(f'<rect x="{x0 + 1:.1f}" y="{y:.1f}" width="{max(1, x1 - x0 - 2):.1f}" height="{top + plot_h - y:.1f}" fill="{color}" opacity="0.72"><title>{fmt(bins[i], 2)} to {fmt(bins[i+1], 2)}: {count:,}</title></rect>')
    if kde and len(values) > 2:
        xs = [x_min + (x_max - x_min) * i / 160 for i in range(161)]
        bw = max((x_max - x_min) / 45, 1.06 * statistics.pstdev(values) * (len(values) ** -0.2) if len(values) > 2 else 0.1)
        density = []
        for x in xs:
            d = sum(math.exp(-0.5 * ((x - v) / bw) ** 2) for v in values) / (len(values) * bw * math.sqrt(2 * math.pi))
            density.append(d)
        scale = max_y / max(density) if max(density) > 0 else 1
        path = " ".join(("M" if i == 0 else "L") + f" {sx(x):.1f},{sy(d * scale):.1f}" for i, (x, d) in enumerate(zip(xs, density)))
        out.append(f'<path d="{path}" fill="none" stroke="{COLORS[3]}" stroke-width="3"></path>')
    for x_val, label, marker_color in markers:
        if x_min <= x_val <= x_max:
            x = sx(x_val)
            out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{top + plot_h}" stroke="{marker_color}" stroke-width="2.4" stroke-dasharray="5 4"></line>')
            out.append(f'<text class="marker-label" x="{x + 5:.1f}" y="{top + 14}">{esc(label)}</text>')
    out.append(f'<text class="axis-label" x="{left + plot_w/2:.1f}" y="{height - 6}" text-anchor="middle">{esc(xlabel)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def nice_ticks(a: float, b: float, n: int) -> list[float]:
    if b <= a:
        return [a]
    raw = (b - a) / max(1, n - 1)
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    step = min([1, 2, 5, 10], key=lambda x: abs(x * mag - raw)) * mag
    start = math.ceil(a / step) * step
    ticks = []
    x = start
    while x <= b + step * 0.2:
        ticks.append(round(x, 6))
        x += step
    return ticks


def boxplot(groups: list[tuple[str, list[float]]], title: str, ylabel: str, width: int = 980, height: int = 430) -> str:
    groups = [(name, sorted(vals)) for name, vals in groups if vals]
    if not groups:
        return empty("No valid grouped titer data available.")
    all_vals = [v for _, vals in groups for v in vals]
    y_min, y_max = math.floor(min(all_vals)), math.ceil(max(all_vals))
    left, right, top, bottom = 72, 30, 30, 96
    plot_w, plot_h = width - left - right, height - top - bottom
    step = plot_w / len(groups)

    def sy(y: float) -> float:
        return top + plot_h - (y - y_min) / (y_max - y_min) * plot_h

    out = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">', f"<title>{esc(title)}</title>"]
    for t in nice_ticks(y_min, y_max, 7):
        y = sy(t)
        out.append(f'<line class="grid" x1="{left}" x2="{left + plot_w}" y1="{y:.1f}" y2="{y:.1f}"></line>')
        out.append(f'<text class="axis-label" x="{left - 8}" y="{y + 4:.1f}" text-anchor="end">{fmt(t, 1)}</text>')
    for i, (name, vals) in enumerate(groups):
        q1, med, q3 = quantile(vals, 0.25), quantile(vals, 0.5), quantile(vals, 0.75)
        lo, hi = quantile(vals, 0.05), quantile(vals, 0.95)
        x = left + step * (i + 0.5)
        bw = min(62, step * 0.55)
        out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{sy(lo):.1f}" y2="{sy(hi):.1f}" stroke="#475467" stroke-width="2"></line>')
        out.append(f'<rect x="{x - bw/2:.1f}" y="{sy(q3):.1f}" width="{bw:.1f}" height="{max(1, sy(q1)-sy(q3)):.1f}" fill="{COLORS[i % len(COLORS)]}" opacity="0.76"></rect>')
        out.append(f'<line x1="{x - bw/2:.1f}" x2="{x + bw/2:.1f}" y1="{sy(med):.1f}" y2="{sy(med):.1f}" stroke="#101828" stroke-width="2.5"></line>')
        out.append(f'<text class="axis-label rotate-label" transform="translate({x:.1f},{height - bottom + 18}) rotate(30)" text-anchor="start">{esc(name)}</text>')
        out.append(f'<text class="value-label" x="{x:.1f}" y="{sy(hi) - 7:.1f}" text-anchor="middle">n={len(vals)}</text>')
    out.append(f'<text class="axis-label" transform="translate(18,{top + plot_h/2:.1f}) rotate(-90)" text-anchor="middle">{esc(ylabel)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def llps_fold_chart(values: list[float], width: int = 980, height: int = 340) -> str:
    if not values:
        return empty("No valid LLPS fold-change data available.")
    logs = [math.log10(v) for v in values if v > 0]
    y_min, y_max = math.floor(min(logs)), math.ceil(max(logs))
    left, right, top, bottom = 82, 36, 30, 55
    plot_w, plot_h = width - left - right, height - top - bottom

    def sx(i: int) -> float:
        return left + (i + 0.5) * plot_w / len(logs)

    def sy(y: float) -> float:
        return top + plot_h - (y - y_min) / max(1e-9, y_max - y_min) * plot_h

    out = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="LLPS catalytic efficiency fold-change">', "<title>LLPS catalytic efficiency fold-change</title>"]
    for t in nice_ticks(y_min, y_max, 6):
        y = sy(t)
        out.append(f'<line class="grid" x1="{left}" x2="{left + plot_w}" y1="{y:.1f}" y2="{y:.1f}"></line>')
        out.append(f'<text class="axis-label" x="{left - 8}" y="{y + 4:.1f}" text-anchor="end">10^{fmt(t, 0)}</text>')
    for i, (v, logv) in enumerate(zip(values, logs)):
        x = sx(i)
        y = sy(logv)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{COLORS[i % len(COLORS)]}" opacity="0.86"><title>{fmt(v, 2)}-fold</title></circle>')
        out.append(f'<text class="axis-label" x="{x:.1f}" y="{height - 20}" text-anchor="middle">{i+1}</text>')
    out.append(f'<text class="axis-label" transform="translate(20,{top + plot_h/2:.1f}) rotate(-90)" text-anchor="middle">log10(fold-change)</text>')
    out.append("</svg>")
    return "\n".join(out)


def empty(message: str) -> str:
    return f'<div class="empty">{esc(message)}</div>'


def stat(label: str, value: str, note: str) -> str:
    return f'<div class="stat"><span>{esc(label)}</span><strong>{esc(value)}</strong><em>{esc(note)}</em></div>'


def section(title: str, visual: str, caption: str) -> str:
    return f'<section class="panel"><h2>{esc(title)}</h2>{visual}<p class="caption">{esc(caption)}</p></section>'


def grid3(items: list[tuple[str, str, str]]) -> str:
    return '<section class="grid three">' + "".join(section(title, visual, caption) for title, visual, caption in items) + "</section>"


def grid2(items: list[tuple[str, str, str]]) -> str:
    return '<section class="grid two">' + "".join(section(title, visual, caption) for title, visual, caption in items) + "</section>"


def css() -> str:
    return """
<style>
:root { --bg:#f3f6fb; --ink:#1f2937; --muted:#667085; --panel:#fff; --line:#d8e0ea; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font-family:Arial, Helvetica, sans-serif; }
main { width:min(1220px, calc(100% - 32px)); margin:0 auto; padding:32px 0 54px; }
.hero { background:linear-gradient(135deg,#fff 0%,#edf5ff 100%); border:1px solid var(--line); border-radius:14px; padding:34px; }
.eyebrow { margin:0 0 10px; color:#2f6fbb; font-weight:700; font-size:12px; letter-spacing:.08em; text-transform:uppercase; }
h1 { margin:0; font-size:40px; line-height:1.1; }
.lead { max-width:960px; color:var(--muted); line-height:1.6; font-size:17px; margin:14px 0 0; }
.stats { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin-top:24px; }
.stat, .panel { background:var(--panel); border:1px solid var(--line); border-radius:14px; box-shadow:0 8px 24px rgba(31,41,55,.06); }
.stat { padding:16px; }
.stat span, .stat em { display:block; color:var(--muted); font-style:normal; font-size:13px; }
.stat strong { display:block; font-size:28px; margin:8px 0 4px; }
.panel { padding:22px; margin-top:18px; }
.grid { display:grid; gap:18px; }
.grid .panel { margin-top:18px; }
.grid.two { grid-template-columns:repeat(2,minmax(0,1fr)); }
.grid.three { grid-template-columns:repeat(3,minmax(0,1fr)); }
h2 { margin:0 0 14px; font-size:21px; line-height:1.25; }
.caption { margin:14px 0 0; color:var(--muted); line-height:1.55; }
.chart { width:100%; height:auto; display:block; }
.axis-label,.value-label,.marker-label,.center-label { font-family:Arial, Helvetica, sans-serif; fill:var(--ink); }
.axis-label { font-size:13px; fill:#475467; }
.value-label { font-size:13px; font-weight:700; }
.marker-label { font-size:12px; font-weight:700; fill:#1f2937; }
.grid { stroke:#d8e0ea; stroke-width:1; }
.rotate-label { dominant-baseline:central; }
.empty { min-height:180px; display:flex; align-items:center; justify-content:center; color:var(--muted); border:1px dashed var(--line); border-radius:12px; }
footer { color:var(--muted); line-height:1.55; margin-top:22px; }
@media (max-width:980px) { .stats,.grid.two,.grid.three { grid-template-columns:1fr; } h1 { font-size:32px; } .hero,.panel { padding:18px; } }
</style>
"""


def build() -> tuple[str, dict[str, object]]:
    rows = read_rows()
    total = len(rows)

    product_counts = counter_known(rows, "best_product_family", PRODUCT_LABELS)
    host_group_counts = counter_known(rows, "best_host_group", HOST_LABELS)
    canonical_host_counts = counter_known(rows, "best_canonical_host")
    system_counts: Counter[str] = Counter()
    for r in rows:
        s = normalize_system(r.get("best_reaction_system_type_value"))
        if s:
            system_counts[s] += 1

    temps = [v for r in rows if (v := temperature_c(r)) is not None]
    phs = [v for r in rows if (v := ph_value(r)) is not None]
    times = [v for r in rows if (v := reaction_time_h(r)) is not None]
    titers = [v for r in rows if (v := titer_mg_l(r)) is not None]
    log_titers = [math.log10(v) for v in titers if v > 0]
    med_titer = median(titers)
    geom_titer = 10 ** statistics.mean(log_titers) if log_titers else float("nan")

    family_titers: list[tuple[str, list[float]]] = []
    for fam in PRODUCT_FAMILIES:
        vals = [math.log10(t) for r in rows if low(r.get("best_product_family")) == fam and (t := titer_mg_l(r)) is not None and t > 0]
        family_titers.append((PRODUCT_LABELS[fam], vals))
    family_titers.sort(key=lambda item: median(item[1]) if item[1] else -999, reverse=True)

    km_values = [v for r in rows if (v := km_um(r)) is not None]
    spec_values = [v for r in rows if (v := specific_activity_u_mg(r)) is not None]
    eff_values = [v for r in rows if (v := kinetic_efficiency_m_inv_s(r)) is not None]
    folds = [v for r in rows if (v := llps_fold(r)) is not None]
    triggers = Counter()
    for r in rows:
        trig = clean(r.get("best_llps_trigger_value"))
        if not is_unknown(trig):
            triggers[trig] += 1

    temp_30_37 = sum(1 for v in temps if abs(v - 30) <= 0.5 or abs(v - 37) <= 0.5)
    ph_neutral = sum(1 for v in phs if 6 <= v <= 7.5)
    low_start_pct = percentile(titers, 0.5)
    target_pct = percentile(titers, 5)
    llps_records = sum(
        1
        for r in rows
        if any(not is_unknown(r.get(f)) for f in ["best_llps_component_value", "best_llps_state_value", "best_llps_trigger_value"])
    )

    summary = {
        "total_records": total,
        "known_product_family": sum(product_counts.values()),
        "known_host_group": sum(host_group_counts.values()),
        "known_canonical_host": sum(canonical_host_counts.values()),
        "known_reaction_system": sum(system_counts.values()),
        "temperature_values": len(temps),
        "temperature_30_or_37_pct": temp_30_37 / len(temps) * 100 if temps else 0,
        "ph_values": len(phs),
        "ph_6_to_7_5_pct": ph_neutral / len(phs) * 100 if phs else 0,
        "time_values_h": len(times),
        "titer_values_mg_l": len(titers),
        "titer_median_mg_l": med_titer,
        "titer_geometric_mean_mg_l": geom_titer,
        "project_initial_0_5_mg_l_percentile": low_start_pct,
        "project_target_5_mg_l_percentile": target_pct,
        "km_values_filtered": len(km_values),
        "specific_activity_values_filtered": len(spec_values),
        "kinetic_efficiency_values_filtered": len(eff_values),
        "llps_fold_values": len(folds),
        "llps_evidence_records": llps_records,
    }

    titer_bins = [x / 2 for x in range(-12, 15)]  # -6 to 7 in 0.5 log units
    html_doc = [
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        "<title>Extended iGEM Database Figures</title>",
        css(),
        "</head><body><main>",
        "<section class=\"hero\">",
        "<p class=\"eyebrow\">Extended figures for project presentation</p>",
        "<h1>Known Evidence Patterns in the Literature-Derived Experimental Database</h1>",
        "<p class=\"lead\">These figures focus on recognized records only. Unknown fields are retained in the database but excluded from distribution plots so that the visual conclusions are based on explicit or full-text-supported evidence.</p>",
        "<div class=\"stats\">",
        stat("Structured records", f"{total:,}", "Current database rows"),
        stat("Titer records", f"{len(titers):,}", "Valid mg/L values"),
        stat("Median titer", f"{fmt(med_titer)} mg/L", "Observed central level"),
        stat("0.5 mg/L percentile", f"{low_start_pct:.1f}%", "Project starting point"),
        "</div></section>",
        grid3([
            ("Product Family Distribution", bar_chart(product_counts.most_common(12), "Product family distribution", COLORS[0]), "Flavonoids and terpenoid/isoprenoid-related families are among the most concentrated natural-product categories. Isoflavonoids are much less represented, supporting the novelty space of this project."),
            ("Expression Host Distribution", bar_chart(canonical_host_counts.most_common(12), "Expression host distribution", COLORS[1]), "The specific-host view highlights the dominance of Saccharomyces cerevisiae, Escherichia coli, and other commonly engineered chassis."),
            ("Reaction System Type Distribution", bar_chart(system_counts.most_common(12), "Reaction system type distribution", COLORS[2]), "Whole-cell, in vivo, in vitro, fermentation, and cell-free systems provide the main experimental settings for comparing pathway and enzyme performance."),
        ]),
        grid3([
            ("Reaction Temperature Histogram", histogram(temps, "Reaction temperature", "Temperature (°C)", list(range(10, 82, 2)), COLORS[0]), f"The most frequent working temperatures are 30°C and 37°C. Together they account for {temp_30_37 / len(temps) * 100:.1f}% of filtered temperature records, matching yeast and E. coli practice."),
            ("Reaction pH Histogram", histogram(phs, "Reaction pH", "pH", [x / 2 for x in range(2, 29)], COLORS[1]), f"pH values concentrate around the neutral window: pH 6.0-7.5 covers {ph_neutral / len(phs) * 100:.1f}% of filtered pH records."),
            ("Reaction Time Histogram", histogram([math.log10(v) for v in times], "Reaction time", "log10(hours)", [x / 4 for x in range(-12, 18)], COLORS[2]), f"Reaction time spans minutes to multi-day fermentations; the median is {fmt(median(times), 1)} hours after unit normalization."),
        ]),
        section(
            "Overall Titer Distribution With KDE",
            histogram(
                log_titers,
                "Overall titer distribution on log10 scale",
                "log10(titer, mg/L)",
                titer_bins,
                COLORS[0],
                markers=[
                    (math.log10(med_titer), f"Median {fmt(med_titer)} mg/L", "#101828"),
                    (math.log10(geom_titer), f"Geomean {fmt(geom_titer)} mg/L", "#b65fcf"),
                    (math.log10(0.5), "Project start 0.5 mg/L", "#d95f5f"),
                    (math.log10(5), "Target 5 mg/L", "#31a354"),
                ],
                kde=True,
            ),
            f"Natural-product heterologous titers span several orders of magnitude and are better read on a log scale. The project starting point of 0.5 mg/L lies at the {low_start_pct:.1f}th percentile, while 5 mg/L lies at the {target_pct:.1f}th percentile; the database median is {fmt(med_titer)} mg/L and the geometric mean is {fmt(geom_titer)} mg/L.",
        ),
        section(
            "Titer Boxplot by Product Family",
            boxplot(family_titers, "Titer by product family", "log10(titer, mg/L)"),
            "Titer distributions differ strongly across product families. In the current database, isoflavonoid records have a lower median than several broader natural-product classes, while LLPS-system records show a higher median among the selected groups.",
        ),
        grid3([
            ("Km Distribution", histogram([math.log10(v) for v in km_values], "Km values", "log10(Km, μM)", [x / 2 for x in range(-6, 9)], COLORS[0]), f"Km values are filtered to 0.001-10000 μM and plotted on log10 scale (n={len(km_values):,}). This gives a substrate-affinity landscape for enzyme-selection discussion."),
            ("Specific Activity Distribution", histogram([math.log10(v) for v in spec_values], "Specific activity", "log10(specific activity, U/mg)", [x / 2 for x in range(-8, 13)], COLORS[1]), f"Specific activity values are shown as U/mg or U/mg-equivalent records (n={len(spec_values):,}), supporting comparison between enzyme activity levels."),
            ("kcat/Km Catalytic Efficiency", histogram([math.log10(v) for v in eff_values], "Catalytic efficiency", "log10(kcat/Km, M^-1 s^-1)", [x / 2 for x in range(-2, 17)], COLORS[2]), f"kcat/Km values are converted where units permit conversion to M^-1 s^-1 (n={len(eff_values):,})."),
        ]),
        grid2([
            ("LLPS-Associated Catalytic Efficiency Fold-Change", llps_fold_chart(folds), f"Reported LLPS-associated fold-change values are sparse but informative (n={len(folds):,}). They support the qualitative claim that condensate regulation can produce strong catalytic effects, while also requiring careful case-level interpretation."),
            ("Reported LLPS Trigger Types", bar_chart(triggers.most_common(18), "LLPS trigger types", COLORS[4]), f"LLPS trigger annotations include stress, salt, glucose state, calcium, overexpression, DNA damage, and polymer/crowding conditions. The database contains {llps_records:,} records with at least one LLPS-specific field."),
        ]),
        "<footer><p>Generated from the full-text-completed database. Numeric plots use filtered, unit-normalized values and exclude unsupported or implausible entries.</p></footer>",
        "</main></body></html>",
    ]
    return "\n".join(html_doc), summary


def main() -> None:
    report, summary = build()
    OUT.write_text(report, encoding="utf-8")
    SUMMARY_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote: {OUT}")
    print(f"Wrote: {SUMMARY_OUT}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

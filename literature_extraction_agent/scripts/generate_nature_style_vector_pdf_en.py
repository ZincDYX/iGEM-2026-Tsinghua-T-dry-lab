# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
import math
import re
import statistics
import textwrap
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.gridspec import GridSpec
from matplotlib.path import Path as MplPath
from matplotlib.patches import Circle, PathPatch, Rectangle, Wedge

import fulltext_pro_field_completion as ft


ROOT = ft.ROOT
SRC = ft.DEFAULT_OUTPUT
OUT = ROOT / "essay" / "nature_style_complete_vector_figure_pack_en.pdf"
SUMMARY = ROOT / "essay" / "nature_style_complete_vector_figure_pack_en_summary.json"

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
TIER_LABELS = {
    "core": "Core",
    "llps_core": "LLPS core",
    "silver": "Silver",
    "review": "Review",
}
CLEAN_LABELS = {
    "A_complete": "A complete",
    "A_llps": "A LLPS",
    "B_product_condition": "B product-condition",
    "C_llps_candidate": "C LLPS candidate",
    "C_partial_context": "C partial context",
    "D_result_only": "D result-only",
}
METRIC_LABELS = {
    "glabridin_yield": "Yield",
    "glabridin_titer": "Titer",
    "glabridin_concentration": "Concentration",
    "enzyme_activity": "Enzyme activity",
    "specific_activity": "Specific activity",
    "substrate_conversion": "Conversion",
    "kinetic_efficiency": "kcat/Km",
    "relative_activity": "Relative activity",
    "critical_phase_concentration": "Ccrit",
    "llps_state": "LLPS state",
    "km": "Km",
    "kcat": "kcat",
}
PRODUCT_FAMILIES = ["flavonoid", "isoprenoid", "terpenoid", "stilbene", "isoflavonoid", "llps_system"]
STOPWORDS = {
    "the", "and", "for", "with", "from", "into", "that", "this", "were", "was", "are", "has", "have", "had",
    "using", "used", "via", "through", "between", "within", "under", "after", "before", "than", "study", "analysis",
    "effect", "effects", "based", "data", "result", "results", "table", "figure", "supplementary", "cell", "cells",
    "protein", "proteins", "enzyme", "enzymes", "reaction", "reactions", "metabolic", "metabolism", "biosynthesis",
    "activity", "expression", "production", "product", "products",
}

COLORS = {
    "blue": "#2C6BB2",
    "green": "#3A9D5D",
    "orange": "#E69F00",
    "purple": "#7B61A8",
    "red": "#C44E52",
    "cyan": "#4C9FAD",
    "gray": "#6B7280",
    "light": "#E7ECF3",
    "dark": "#202938",
}
PALETTE = ["#2C6BB2", "#3A9D5D", "#E69F00", "#7B61A8", "#C44E52", "#4C9FAD", "#6B7280", "#9C755F"]


def clean(value: object) -> str:
    return " ".join(str(value or "").replace("\u00a0", " ").strip().split())


def low(value: object) -> str:
    return clean(value).lower()


def is_unknown(value: object) -> bool:
    return low(value) in UNKNOWN


def labelize(value: object, mapping: dict[str, str] | None = None) -> str:
    text = clean(value)
    k = text.lower()
    if mapping and k in mapping:
        return mapping[k]
    return text.replace("_", " ").replace("-", " ").title() if text else "Unlabeled"


def parse_number(value: object) -> float | None:
    text = clean(value).replace("−", "-")
    matches = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    if not matches:
        return None
    values = [float(x) for x in matches]
    return sum(values) / len(values)


def read_rows() -> list[dict[str, str]]:
    with SRC.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def counter_known(rows: list[dict[str, str]], field: str, mapping: dict[str, str] | None = None) -> Counter[str]:
    out: Counter[str] = Counter()
    for row in rows:
        value = row.get(field, "")
        if not is_unknown(value):
            out[labelize(value, mapping)] += 1
    return out


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
    v = parse_number(row.get("best_reaction_temperature_value"))
    return v if v is not None and 10 <= v <= 80 else None


def ph_value(row: dict[str, str]) -> float | None:
    v = parse_number(row.get("best_reaction_ph_value"))
    return v if v is not None and 1 <= v <= 14 else None


def reaction_time_h(row: dict[str, str]) -> float | None:
    v = parse_number(row.get("best_reaction_time_value"))
    if v is None:
        return None
    unit = low(row.get("best_reaction_time_unit"))
    if "day" in unit or unit == "d":
        v *= 24
    elif "min" in unit:
        v /= 60
    elif unit in {"s", "sec", "secs", "second", "seconds"}:
        v /= 3600
    return v if 0.001 <= v <= 10000 else None


def titer_mg_l(row: dict[str, str]) -> float | None:
    metric = low(row.get("primary_result_metric"))
    unit = low(row.get("primary_result_unit_normalized") or row.get("primary_result_unit")).replace(" ", "")
    v = parse_number(row.get("primary_result_numeric_normalized") or row.get("primary_result_value"))
    if v is None:
        return None
    if unit in {"mg/l", "mgl-1", "mgl−1"} and ("titer" in metric or "concentration" in metric):
        return v if 1e-6 <= v <= 1e7 else None
    return None


def km_um(row: dict[str, str]) -> float | None:
    unit = clean(row.get("km_norm_unit"))
    v = parse_number(row.get("km_norm_value") or row.get("km_value"))
    if v is None or unit not in {"uM", "μM", "µM"}:
        return None
    return v if 0.001 <= v <= 10000 else None


def specific_activity_u_mg(row: dict[str, str]) -> float | None:
    unit = low(row.get("specific_activity_norm_unit") or row.get("specific_activity_unit"))
    v = parse_number(row.get("specific_activity_norm_value") or row.get("specific_activity_value"))
    if v is None:
        return None
    if "u/mg" in unit or "units/mg" in unit:
        return v if 1e-6 <= v <= 1e6 else None
    if "nmol/min/mg" in unit:
        converted = v / 1000
        return converted if 1e-9 <= converted <= 1e6 else None
    if "umole" in unit or "μmole" in unit:
        if "min" in unit and "mg" in unit:
            return v if 1e-6 <= v <= 1e6 else None
    return None


def kinetic_efficiency_m_inv_s(row: dict[str, str]) -> float | None:
    unit = low(row.get("kinetic_efficiency_norm_unit") or row.get("kinetic_efficiency_unit"))
    v = parse_number(row.get("kinetic_efficiency_norm_value") or row.get("kinetic_efficiency_value"))
    if v is None:
        return None
    u = unit.replace("⁻", "-").replace("−", "-").replace("µ", "u").replace("μ", "u")
    if "mg/kg" in u or u in {"", "x"}:
        return None
    if "um" in u:
        v *= 1e6
    elif "mm" in u:
        v *= 1e3
    elif "m" in u:
        v *= 1
    else:
        return None
    if "min" in u:
        v /= 60
    return v if 1e-6 <= v <= 1e12 else None


def llps_fold(row: dict[str, str]) -> float | None:
    unit = low(row.get("catalytic_efficiency_fold_change_norm_unit") or row.get("catalytic_efficiency_fold_change_unit"))
    v = parse_number(row.get("catalytic_efficiency_fold_change_norm_value") or row.get("catalytic_efficiency_fold_change_value"))
    if v is None:
        return None
    if "fold" in unit or unit == "":
        return v if 0.01 <= v <= 10000 else None
    if "%" in unit:
        converted = v / 100 if v > 1 else v
        return converted if 0.01 <= converted <= 10000 else None
    return None


def metric_name(row: dict[str, str]) -> str:
    metric = row.get("primary_result_metric") or row.get("schema_id") or ""
    if is_unknown(metric):
        return ""
    return labelize(metric, METRIC_LABELS)


def percentile(values: list[float], x: float) -> float:
    return 100 * sum(1 for v in values if v <= x) / len(values) if values else 0.0


def geom_mean(values: list[float]) -> float:
    logs = [math.log10(v) for v in values if v > 0]
    return 10 ** statistics.mean(logs) if logs else float("nan")


def setup_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.titlesize": 9.5,
            "axes.labelsize": 8.5,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "legend.fontsize": 7.2,
            "axes.linewidth": 0.65,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "figure.dpi": 300,
        }
    )


def panel(ax, letter: str, title: str) -> None:
    ax.text(-0.12, 1.08, letter, transform=ax.transAxes, fontsize=12, fontweight="bold", va="top", ha="left")
    ax.set_title(title, loc="left", pad=8, fontweight="bold")


def clean_axes(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(length=2.5, width=0.6)
    ax.grid(axis="x", color="#D8DEE9", lw=0.45, alpha=0.8)
    ax.set_axisbelow(True)


def barh(ax, counter: Counter[str], title: str, letter: str, n: int = 10, color: str = COLORS["blue"]) -> None:
    items = [(k, v) for k, v in counter.most_common(n) if k]
    names = [k for k, _ in items][::-1]
    vals = [v for _, v in items][::-1]
    ax.barh(names, vals, color=color, alpha=0.86, height=0.72)
    for y, v in enumerate(vals):
        ax.text(v + max(vals) * 0.015, y, f"{v:,}", va="center", fontsize=7.2)
    ax.set_xlabel("Records")
    panel(ax, letter, title)
    clean_axes(ax)


def coverage_plot(ax, rows: list[dict[str, str]]) -> None:
    fields = [
        ("Product family", "best_product_family"),
        ("Canonical product", "best_canonical_product"),
        ("Host group", "best_host_group"),
        ("Canonical host", "best_canonical_host"),
        ("Main product", "best_main_product_name_value"),
        ("Substrate", "best_substrate_name_value"),
        ("Enzyme", "best_enzyme_name_value"),
        ("System type", "best_reaction_system_type_value"),
        ("Whole-cell flag", "best_is_whole_cell_value"),
        ("Temperature", "best_reaction_temperature_value"),
        ("pH", "best_reaction_ph_value"),
        ("Reaction time", "best_reaction_time_value"),
        ("Substrate conc.", "best_substrate_concentration_value"),
        ("LLPS evidence", "best_llps_component_value"),
    ]
    total = len(rows)
    labels = [x[0] for x in fields][::-1]
    known = [sum(1 for r in rows if not is_unknown(r.get(f))) for _, f in fields][::-1]
    unknown = [total - k for k in known]
    y = np.arange(len(labels))
    ax.barh(y, known, color=COLORS["green"], alpha=0.86, label="Known")
    ax.barh(y, unknown, left=known, color=COLORS["light"], label="Unknown")
    ax.set_yticks(y, labels)
    ax.set_xlabel("Records")
    ax.legend(frameon=False, loc="lower right")
    panel(ax, "A", "Field coverage after full-text completion")
    clean_axes(ax)


def hist_plot(ax, values: list[float], bins, title: str, letter: str, xlabel: str, color: str, markers: list[tuple[float, str, str]] | None = None, kde: bool = False) -> None:
    values = [v for v in values if math.isfinite(v)]
    ax.hist(values, bins=bins, color=color, alpha=0.74, edgecolor="white", linewidth=0.35)
    if kde and len(values) > 5:
        xs = np.linspace(min(bins), max(bins), 250)
        arr = np.array(values)
        bw = max((max(bins) - min(bins)) / 55, 1.06 * arr.std(ddof=0) * (len(arr) ** -0.2))
        if bw > 0:
            den = np.exp(-0.5 * ((xs[:, None] - arr[None, :]) / bw) ** 2).sum(axis=1) / (len(arr) * bw * math.sqrt(2 * math.pi))
            scale = len(arr) * (bins[1] - bins[0])
            ax.plot(xs, den * scale, color=COLORS["purple"], lw=1.7, label="KDE")
    if markers:
        ymax = ax.get_ylim()[1]
        for x, label, c in markers:
            ax.axvline(x, color=c, lw=1.25, ls=(0, (4, 3)))
            ax.text(x, ymax * 0.92, label, rotation=90, ha="right", va="top", color=c, fontsize=6.8)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Records")
    panel(ax, letter, title)
    clean_axes(ax)


def product_host_bubble(ax, rows: list[dict[str, str]]) -> None:
    fams = [x for x, _ in counter_known(rows, "best_product_family", PRODUCT_LABELS).most_common(7) if x != "Other known"]
    hosts = [x for x, _ in counter_known(rows, "best_host_group", HOST_LABELS).most_common(7) if x != "Other known"]
    pairs: Counter[tuple[str, str]] = Counter()
    for r in rows:
        fam = labelize(r.get("best_product_family"), PRODUCT_LABELS)
        host = labelize(r.get("best_host_group"), HOST_LABELS)
        if fam in fams and host in hosts:
            pairs[(fam, host)] += 1
    vmax = max(pairs.values()) if pairs else 1
    for i, fam in enumerate(fams):
        for j, host in enumerate(hosts):
            val = pairs.get((fam, host), 0)
            if val:
                ax.scatter(i, j, s=20 + 420 * math.sqrt(val / vmax), color=COLORS["blue"], alpha=0.65)
                if val == vmax:
                    ax.text(i, j, f"{val:,}", ha="center", va="center", fontsize=7, color="white", fontweight="bold")
    ax.set_xticks(range(len(fams)), fams, rotation=35, ha="right")
    ax.set_yticks(range(len(hosts)), hosts)
    ax.set_xlim(-0.7, len(fams) - 0.3)
    ax.set_ylim(-0.7, len(hosts) - 0.3)
    panel(ax, "A", "Known product-family by host matrix")
    ax.grid(color="#D8DEE9", lw=0.45)
    ax.spines[:].set_visible(False)


def upset_plot(ax, rows: list[dict[str, str]]) -> None:
    sets = [
        ("Product", lambda r: not is_unknown(r.get("best_product_family")) or not is_unknown(r.get("best_canonical_product"))),
        ("Host", lambda r: not is_unknown(r.get("best_host_group")) or not is_unknown(r.get("best_canonical_host"))),
        ("Enzyme", lambda r: not is_unknown(r.get("best_enzyme_name_value"))),
        ("Substrate", lambda r: not is_unknown(r.get("best_substrate_name_value"))),
        ("Main product", lambda r: not is_unknown(r.get("best_main_product_name_value"))),
        ("Conditions", lambda r: any(not is_unknown(r.get(f)) for f in ["best_reaction_temperature_value", "best_reaction_ph_value", "best_reaction_time_value"])),
        ("LLPS", lambda r: any(not is_unknown(r.get(f)) for f in ["best_llps_component_value", "best_llps_state_value", "best_llps_trigger_value"])),
    ]
    combos: Counter[tuple[int, ...]] = Counter()
    for r in rows:
        combo = tuple(1 if fn(r) else 0 for _, fn in sets)
        if any(combo):
            combos[combo] += 1
    items = combos.most_common(12)
    y = np.arange(len(items))
    vals = [v for _, v in items]
    ax.barh(y, vals, color=COLORS["orange"], alpha=0.82)
    ax.set_yticks(y, [""] * len(y))
    ax.invert_yaxis()
    ax.set_xlabel("Records")
    for yi, (combo, val) in enumerate(items):
        for j, bit in enumerate(combo):
            ax.scatter(-max(vals) * (0.36 - j * 0.045), yi, s=22, color=COLORS["green"] if bit else COLORS["light"], clip_on=False)
        ax.text(val + max(vals) * 0.015, yi, f"{val:,}", va="center", fontsize=7)
    for j, (name, _) in enumerate(sets):
        ax.text(-max(vals) * (0.36 - j * 0.045), len(items) + 0.25, name, rotation=55, ha="right", va="bottom", fontsize=6.7)
    panel(ax, "B", "Known-field co-occurrence")
    clean_axes(ax)


def evidence_chain(ax, rows: list[dict[str, str]], doi_count: int) -> None:
    total = len(rows)
    accepted = sum(1 for r in rows if low(r.get("fulltext_pro_status")) == "accepted")
    low_conf = sum(1 for r in rows if low(r.get("fulltext_pro_status")) == "low_confidence")
    product_host = sum(1 for r in rows if not is_unknown(r.get("best_product_family")) and not is_unknown(r.get("best_host_group")))
    nodes = [
        ("DOI sources", doi_count),
        ("Structured rows", total),
        ("Accepted full text", accepted),
        ("Low-confidence retained", low_conf),
        ("Product-host labeled", product_host),
    ]
    pos = {
        "DOI sources": (0.08, 0.52),
        "Structured rows": (0.36, 0.52),
        "Accepted full text": (0.66, 0.78),
        "Low-confidence retained": (0.66, 0.28),
        "Product-host labeled": (0.90, 0.52),
    }
    maxv = max(v for _, v in nodes)
    for a, b in [
        ("DOI sources", "Structured rows"),
        ("Structured rows", "Accepted full text"),
        ("Structured rows", "Low-confidence retained"),
        ("Accepted full text", "Product-host labeled"),
        ("Low-confidence retained", "Product-host labeled"),
    ]:
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        ax.plot([x1, x2], [y1, y2], color=COLORS["gray"], lw=1.2, alpha=0.45, transform=ax.transAxes)
    for i, (name, value) in enumerate(nodes):
        x, yv = pos[name]
        radius = 0.045 + 0.06 * math.sqrt(value / maxv)
        circ = Circle((x, yv), radius, color=PALETTE[i], alpha=0.86, transform=ax.transAxes)
        ax.add_patch(circ)
        ax.text(x, yv, f"{value:,}", ha="center", va="center", fontsize=7.2, color="white", fontweight="bold", transform=ax.transAxes)
        ax.text(x, yv - radius - 0.045, name, ha="center", va="top", fontsize=7.1, transform=ax.transAxes)
    ax.axis("off")
    panel(ax, "C", "Traceable evidence chain")


def family_boxplot(ax, rows: list[dict[str, str]]) -> None:
    groups = []
    for fam in PRODUCT_FAMILIES:
        vals = [math.log10(v) for r in rows if low(r.get("best_product_family")) == fam and (v := titer_mg_l(r)) is not None and v > 0]
        if vals:
            groups.append((PRODUCT_LABELS[fam], vals))
    groups.sort(key=lambda item: statistics.median(item[1]), reverse=True)
    data = [vals for _, vals in groups]
    labels = [name for name, _ in groups]
    bp = ax.boxplot(data, patch_artist=True, widths=0.62, showfliers=False)
    for i, box in enumerate(bp["boxes"]):
        box.set(facecolor=PALETTE[i % len(PALETTE)], alpha=0.65, linewidth=0.8)
    for med in bp["medians"]:
        med.set(color=COLORS["dark"], lw=1.4)
    for whisker in bp["whiskers"]:
        whisker.set(color=COLORS["gray"], lw=0.8)
    for cap in bp["caps"]:
        cap.set(color=COLORS["gray"], lw=0.8)
    ax.set_xticks(range(1, len(labels) + 1), labels, rotation=35, ha="right")
    ax.set_ylabel("log10(titer, mg/L)")
    panel(ax, "B", "Titer by product family")
    clean_axes(ax)


def trigger_group(name: str) -> str:
    k = low(name)
    if any(x in k for x in ["glucose", "starvation", "deprivation", "galactose"]):
        return "Nutrient or induction"
    if any(x in k for x in ["salt", "nacl", "peg", "crowding"]):
        return "Salt or crowding"
    if any(x in k for x in ["dna", "mms", "zeocin", "damage"]):
        return "DNA damage"
    if any(x in k for x in ["ca2", "calcium"]):
        return "Calcium"
    if any(x in k for x in ["overexpression", "expression"]):
        return "Overexpression"
    if any(x in k for x in ["hydrogen peroxide", "stress", "acetic", "zymolyase"]):
        return "Stress"
    if any(x in k for x in ["mismatch", "hydrophobic"]):
        return "Hydrophobic mismatch"
    return "Other reported trigger"


def sunburst(ax, rows: list[dict[str, str]]) -> None:
    fam_counts = counter_known(rows, "best_product_family", PRODUCT_LABELS)
    fams = [f for f, _ in fam_counts.most_common(7) if f != "Other known"]
    total = sum(fam_counts[f] for f in fams) or 1
    start = 90
    for i, fam in enumerate(fams):
        theta = 360 * fam_counts[fam] / total
        ax.add_patch(Wedge((0, 0), 1.0, start, start + theta, width=0.32, facecolor=PALETTE[i % len(PALETTE)], alpha=0.78, edgecolor="white", lw=0.7))
        host_counts: Counter[str] = Counter()
        for r in rows:
            if labelize(r.get("best_product_family"), PRODUCT_LABELS) == fam and not is_unknown(r.get("best_host_group")):
                host_counts[labelize(r.get("best_host_group"), HOST_LABELS)] += 1
        h_total = sum(host_counts.values()) or 1
        h_start = start
        for j, (host, hv) in enumerate(host_counts.most_common(4)):
            h_theta = theta * hv / h_total
            ax.add_patch(Wedge((0, 0), 1.36, h_start, h_start + h_theta, width=0.28, facecolor=PALETTE[(i + j + 1) % len(PALETTE)], alpha=0.50, edgecolor="white", lw=0.5))
            h_start += h_theta
        mid = math.radians(start + theta / 2)
        ax.text(1.55 * math.cos(mid), 1.55 * math.sin(mid), fam, ha="center", va="center", fontsize=6.8)
        start += theta
    ax.set_aspect("equal")
    ax.set_xlim(-1.82, 1.82)
    ax.set_ylim(-1.72, 1.72)
    ax.axis("off")
    panel(ax, "D", "Product-host hierarchy")


def wrapped(text: str, width: int = 78) -> str:
    return "\n".join(textwrap.fill(part, width=width) for part in text.split("\n"))


def add_page_title(fig, title: str, subtitle: str) -> None:
    fig.text(0.02, 0.985, title, ha="left", va="top", fontsize=13.5, fontweight="bold")
    fig.text(0.02, 0.957, subtitle, ha="left", va="top", fontsize=8.5, color=COLORS["gray"])


def add_figure_caption(fig, caption: str) -> None:
    fig.text(0.02, 0.020, wrapped(caption, 185), ha="left", va="bottom", fontsize=7.25, color=COLORS["dark"], linespacing=1.22)


def save_page(pdf: PdfPages, fig, caption: str) -> None:
    add_figure_caption(fig, caption)
    pdf.savefig(fig)
    plt.close(fig)


def sankey_flow(ax, rows: list[dict[str, str]]) -> None:
    columns = [
        ("Source", "source_mode", None),
        ("Product family", "best_product_family", PRODUCT_LABELS),
        ("Host group", "best_host_group", HOST_LABELS),
        ("Metric", "__metric__", METRIC_LABELS),
    ]
    allowed: list[set[str]] = []
    for _, field, mapping in columns:
        if field == "__metric__":
            cnt = Counter(metric_name(r) for r in rows if metric_name(r))
        else:
            cnt = counter_known(rows, field, mapping)
        allowed.append({name for name, _ in cnt.most_common(7)})
    paths: Counter[tuple[str, str, str, str]] = Counter()
    for r in rows:
        vals = [
            labelize(r.get("source_mode")),
            labelize(r.get("best_product_family"), PRODUCT_LABELS),
            labelize(r.get("best_host_group"), HOST_LABELS),
            metric_name(r),
        ]
        if not all(vals):
            continue
        vals = [v if v in allowed[i] else "Other known" for i, v in enumerate(vals)]
        if "Other known" in vals[1:3]:
            continue
        paths[tuple(vals)] += 1
    node_counts = [Counter() for _ in columns]
    link_counts: list[Counter[tuple[str, str]]] = [Counter(), Counter(), Counter()]
    for path, count in paths.items():
        for i, v in enumerate(path):
            node_counts[i][v] += count
        for i in range(3):
            link_counts[i][(path[i], path[i + 1])] += count
    xs = [0.06, 0.34, 0.62, 0.87]
    node_pos: list[dict[str, tuple[float, float, float]]] = []
    for col, cnt in enumerate(node_counts):
        items = cnt.most_common(8)
        total = sum(v for _, v in items) or 1
        gap = 0.018
        usable = 0.76 - gap * max(0, len(items) - 1)
        y_top = 0.84
        pos = {}
        for name, value in items:
            h = max(0.035, usable * value / total)
            pos[name] = (xs[col], y_top - h, h)
            y_top -= h + gap
        node_pos.append(pos)
    max_link = max((v for cnt in link_counts for v in cnt.values()), default=1)
    for i, cnt in enumerate(link_counts):
        for (a, b), value in cnt.most_common(70):
            if a not in node_pos[i] or b not in node_pos[i + 1]:
                continue
            x1, y1, h1 = node_pos[i][a]
            x2, y2, h2 = node_pos[i + 1][b]
            y_start, y_end = y1 + h1 / 2, y2 + h2 / 2
            path = MplPath(
                [(x1 + 0.105, y_start), ((x1 + x2) / 2, y_start), ((x1 + x2) / 2, y_end), (x2, y_end)],
                [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4],
            )
            ax.add_patch(PathPatch(path, transform=ax.transAxes, facecolor="none", edgecolor=PALETTE[i], lw=0.5 + 9 * math.sqrt(value / max_link), alpha=0.16))
    for c, (title, _, _) in enumerate(columns):
        ax.text(xs[c], 0.93, title, transform=ax.transAxes, fontsize=7.6, fontweight="bold")
        for name, (x, y, h) in node_pos[c].items():
            ax.add_patch(Rectangle((x, y), 0.105, h, transform=ax.transAxes, facecolor=PALETTE[c], alpha=0.78, edgecolor="white", lw=0.4))
            ax.text(x + 0.006, y + min(h - 0.004, 0.020), name[:15], transform=ax.transAxes, fontsize=6.2, color="white", va="top", fontweight="bold")
    ax.axis("off")
    panel(ax, "A", "Known source-product-host-metric flow")


def chord_plot(ax, rows: list[dict[str, str]]) -> None:
    fams = [x for x, _ in counter_known(rows, "best_product_family", PRODUCT_LABELS).most_common(6) if x != "Other known"]
    hosts = [x for x, _ in counter_known(rows, "best_host_group", HOST_LABELS).most_common(6) if x != "Other known"]
    nodes = fams + hosts
    edges: Counter[tuple[str, str]] = Counter()
    for r in rows:
        fam = labelize(r.get("best_product_family"), PRODUCT_LABELS)
        host = labelize(r.get("best_host_group"), HOST_LABELS)
        if fam in fams and host in hosts:
            edges[(fam, host)] += 1
    angles = {node: -math.pi / 2 + 2 * math.pi * i / len(nodes) for i, node in enumerate(nodes)}
    max_edge = max(edges.values()) if edges else 1
    radius = 1.0
    for (fam, host), value in edges.most_common(55):
        a1, a2 = angles[fam], angles[host]
        x1, y1 = radius * math.cos(a1), radius * math.sin(a1)
        x2, y2 = radius * math.cos(a2), radius * math.sin(a2)
        path = MplPath([(x1, y1), (0, 0), (x2, y2)], [MplPath.MOVETO, MplPath.CURVE3, MplPath.CURVE3])
        ax.add_patch(PathPatch(path, facecolor="none", edgecolor=COLORS["blue"], lw=0.35 + 7 * math.sqrt(value / max_edge), alpha=0.18))
    for node in nodes:
        a = angles[node]
        x, y = radius * math.cos(a), radius * math.sin(a)
        color = COLORS["green"] if node in fams else COLORS["orange"]
        ax.scatter([x], [y], s=130, color=color, alpha=0.88, zorder=3)
        ha = "left" if math.cos(a) >= 0 else "right"
        ax.text(1.18 * math.cos(a), 1.18 * math.sin(a), node, ha=ha, va="center", fontsize=6.7)
    ax.set_aspect("equal")
    ax.set_xlim(-1.42, 1.42)
    ax.set_ylim(-1.30, 1.30)
    ax.axis("off")
    panel(ax, "A", "Product-family and host chord diagram")


def network_plot(ax, rows: list[dict[str, str]]) -> None:
    fams = [x for x, _ in counter_known(rows, "best_product_family", PRODUCT_LABELS).most_common(6) if x != "Other known"]
    hosts = [x for x, _ in counter_known(rows, "best_host_group", HOST_LABELS).most_common(6) if x != "Other known"]
    metrics = [x for x, _ in Counter(metric_name(r) for r in rows if metric_name(r)).most_common(6)]
    pos = {}
    for i, name in enumerate(fams):
        pos[name] = (0.08, 0.84 - i * 0.13, COLORS["green"])
    for i, name in enumerate(hosts):
        pos[name] = (0.46, 0.84 - i * 0.13, COLORS["orange"])
    for i, name in enumerate(metrics):
        pos[name] = (0.80, 0.84 - i * 0.13, COLORS["purple"])
    e1: Counter[tuple[str, str]] = Counter()
    e2: Counter[tuple[str, str]] = Counter()
    for r in rows:
        fam = labelize(r.get("best_product_family"), PRODUCT_LABELS)
        host = labelize(r.get("best_host_group"), HOST_LABELS)
        metric = metric_name(r)
        if fam in fams and host in hosts:
            e1[(fam, host)] += 1
        if host in hosts and metric in metrics:
            e2[(host, metric)] += 1
    max_edge = max([1] + list(e1.values()) + list(e2.values()))
    for edges in [e1, e2]:
        for (a, b), value in edges.most_common(60):
            if a in pos and b in pos:
                x1, y1, _ = pos[a]
                x2, y2, _ = pos[b]
                ax.plot([x1, x2], [y1, y2], color=COLORS["gray"], lw=0.3 + 4.5 * math.sqrt(value / max_edge), alpha=0.22, transform=ax.transAxes)
    for name, (x, y, color) in pos.items():
        ax.scatter([x], [y], s=95, color=color, alpha=0.88, transform=ax.transAxes)
        ax.text(x + 0.035, y, name[:22], va="center", fontsize=6.8, transform=ax.transAxes)
    ax.axis("off")
    panel(ax, "B", "Known product-host-metric network")


def treemap_plot(ax, counter: Counter[str], title: str, letter: str) -> None:
    items = counter.most_common(14)
    total = sum(v for _, v in items) or 1
    y = 0.08
    row_height = 0.18
    idx = 0
    while idx < len(items):
        row = items[idx: idx + 4]
        row_total = sum(v for _, v in row) or 1
        x = 0.02
        for j, (name, value) in enumerate(row):
            w = 0.94 * value / row_total
            ax.add_patch(Rectangle((x, y), w, row_height, transform=ax.transAxes, facecolor=PALETTE[(idx + j) % len(PALETTE)], alpha=0.78, edgecolor="white", lw=0.8))
            ax.text(x + 0.012, y + row_height - 0.035, name[:20], transform=ax.transAxes, color="white", fontsize=6.7, fontweight="bold", va="top")
            ax.text(x + 0.012, y + 0.025, f"{value:,}", transform=ax.transAxes, color="white", fontsize=6.5, va="bottom")
            x += w
        y += row_height + 0.015
        idx += 4
    ax.axis("off")
    panel(ax, letter, title)


def word_cloud_plot(ax, rows: list[dict[str, str]]) -> None:
    words: Counter[str] = Counter()
    fields = ["title_clean", "title", "best_main_product_name_value", "best_substrate_name_value", "best_enzyme_name_value", "best_llps_component_value", "primary_result_metric"]
    for r in rows:
        blob = " ".join(r.get(f, "") for f in fields)
        for word in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", blob):
            w = word.lower().strip("-")
            if w not in STOPWORDS and len(w) >= 3:
                words[w] += 1
    items = words.most_common(60)
    if not items:
        ax.axis("off")
        return
    maxv = items[0][1]
    x, y = 0.03, 0.88
    for i, (word, value) in enumerate(items):
        size = 6 + 16 * math.sqrt(value / maxv)
        label = word.upper() if word in {"llps", "frap", "od600", "kcat"} else word.title()
        approx = 0.010 * len(label) * size / 8
        if x + approx > 0.96:
            x = 0.03 + (i % 4) * 0.015
            y -= 0.105
        if y < 0.06:
            break
        ax.text(x, y, label, fontsize=size, color=PALETTE[i % len(PALETTE)], alpha=0.90, transform=ax.transAxes)
        x += approx + 0.025
    ax.axis("off")
    panel(ax, "A", "Keyword cloud from known records")


def top_entities_table(ax, rows: list[dict[str, str]]) -> None:
    products = counter_known(rows, "best_canonical_product").most_common(12)
    hosts = counter_known(rows, "best_canonical_host").most_common(12)
    ax.axis("off")
    panel(ax, "B", "Top known products and hosts")
    y = 0.82
    ax.text(0.02, y, "Rank", fontweight="bold", fontsize=7.4, transform=ax.transAxes)
    ax.text(0.12, y, "Canonical product", fontweight="bold", fontsize=7.4, transform=ax.transAxes)
    ax.text(0.47, y, "n", fontweight="bold", fontsize=7.4, transform=ax.transAxes)
    ax.text(0.58, y, "Canonical host", fontweight="bold", fontsize=7.4, transform=ax.transAxes)
    ax.text(0.94, y, "n", fontweight="bold", fontsize=7.4, transform=ax.transAxes)
    for i in range(12):
        y = 0.76 - i * 0.055
        p, pv = products[i] if i < len(products) else ("", "")
        h, hv = hosts[i] if i < len(hosts) else ("", "")
        ax.text(0.02, y, str(i + 1), fontsize=7.1, transform=ax.transAxes)
        ax.text(0.12, y, p[:28], fontsize=7.1, transform=ax.transAxes)
        ax.text(0.47, y, f"{pv:,}" if pv != "" else "", fontsize=7.1, transform=ax.transAxes)
        ax.text(0.58, y, h[:28], fontsize=7.1, transform=ax.transAxes)
        ax.text(0.94, y, f"{hv:,}" if hv != "" else "", fontsize=7.1, transform=ax.transAxes)
        ax.plot([0.02, 0.98], [y - 0.022, y - 0.022], color="#E5E7EB", lw=0.45, transform=ax.transAxes)

def generate_pdf(rows: list[dict[str, str]]) -> dict[str, object]:
    total = len(rows)
    doi_count = len({low(r.get("doi")) for r in rows if not is_unknown(r.get("doi"))})
    temps = [v for r in rows if (v := temperature_c(r)) is not None]
    phs = [v for r in rows if (v := ph_value(r)) is not None]
    times = [v for r in rows if (v := reaction_time_h(r)) is not None]
    titers = [v for r in rows if (v := titer_mg_l(r)) is not None]
    log_titers = [math.log10(v) for v in titers if v > 0]
    med_titer = statistics.median(titers)
    geo_titer = geom_mean(titers)
    km_values = [v for r in rows if (v := km_um(r)) is not None]
    spec_values = [v for r in rows if (v := specific_activity_u_mg(r)) is not None]
    eff_values = [v for r in rows if (v := kinetic_efficiency_m_inv_s(r)) is not None]
    folds = [v for r in rows if (v := llps_fold(r)) is not None]
    triggers = Counter(trigger_group(r.get("best_llps_trigger_value")) for r in rows if not is_unknown(r.get("best_llps_trigger_value")))
    source_counter = counter_known(rows, "source_mode")
    tier_counter = counter_known(rows, "database_tier", TIER_LABELS)
    clean_counter = counter_known(rows, "clean_level", CLEAN_LABELS)
    metric_counter = Counter(metric_name(r) for r in rows if metric_name(r))
    system_counter: Counter[str] = Counter()
    for r in rows:
        s = normalize_system(r.get("best_reaction_system_type_value"))
        if s:
            system_counter[s] += 1

    with PdfPages(OUT) as pdf:
        fig = plt.figure(figsize=(11.2, 8.1), constrained_layout=False)
        add_page_title(fig, "Figure 1. Database coverage and major known categories", "Recognized records after cleaning, LLM quality control, and full-text or supplementary-material completion.")
        gs = GridSpec(2, 2, figure=fig, left=0.10, right=0.98, bottom=0.16, top=0.90, wspace=0.30, hspace=0.38)
        coverage_plot(fig.add_subplot(gs[0, :]), rows)
        barh(fig.add_subplot(gs[1, 0]), counter_known(rows, "best_product_family", PRODUCT_LABELS), "Product-family distribution", "B", 10, COLORS["blue"])
        barh(fig.add_subplot(gs[1, 1]), counter_known(rows, "best_host_group", HOST_LABELS), "Host-group distribution", "C", 9, COLORS["green"])
        save_page(pdf, fig, "Fig. 1 | Database coverage and major known categories. a, Field-level known/unknown coverage after rule-based cleaning, LLM quality control and full-text completion. b, Distribution of recognized product families. c, Distribution of recognized host groups. Unknown values are retained in the database but are shown separately or excluded from categorical counts.")

        fig = plt.figure(figsize=(11.2, 8.1), constrained_layout=False)
        add_page_title(fig, "Figure 2. Database source, quality and metric composition", "Full-atlas summary panels from the known-information visualization report.")
        gs = GridSpec(2, 2, figure=fig, left=0.08, right=0.98, bottom=0.16, top=0.90, wspace=0.34, hspace=0.42)
        barh(fig.add_subplot(gs[0, 0]), source_counter, "Source-mode distribution", "A", 10, COLORS["blue"])
        barh(fig.add_subplot(gs[0, 1]), tier_counter, "Database-tier distribution", "B", 10, COLORS["green"])
        barh(fig.add_subplot(gs[1, 0]), metric_counter, "Measured result metrics", "C", 12, COLORS["cyan"])
        barh(fig.add_subplot(gs[1, 1]), clean_counter, "Evidence-quality levels", "D", 10, COLORS["gray"])
        save_page(pdf, fig, "Fig. 2 | Source, quality and measurement composition of the database. a, Source mode for structured records. b, Curation tier distribution. c, Primary result metrics extracted from literature evidence. d, Evidence-quality labels used to distinguish complete records, partial-context records and result-only records.")

        fig = plt.figure(figsize=(11.2, 8.1), constrained_layout=False)
        add_page_title(fig, "Figure 3. Evidence relationships and database structure", "Known product-host intersections, co-occurring fields, traceable evidence flow, and hierarchical product-host organization.")
        gs = GridSpec(2, 2, figure=fig, left=0.07, right=0.98, bottom=0.16, top=0.90, wspace=0.32, hspace=0.40)
        product_host_bubble(fig.add_subplot(gs[0, 0]), rows)
        upset_plot(fig.add_subplot(gs[0, 1]), rows)
        evidence_chain(fig.add_subplot(gs[1, 0]), rows, doi_count)
        sunburst(fig.add_subplot(gs[1, 1]), rows)
        save_page(pdf, fig, "Fig. 3 | Relationship structure among known database fields. a, Bubble matrix of product-family and host-group intersections. b, UpSet-style co-occurrence of known fields in the same record. c, Evidence chain from DOI sources to structured rows and product-host-labelled records. d, Product-host hierarchy for recognized product families.")

        fig = plt.figure(figsize=(11.2, 8.1), constrained_layout=False)
        add_page_title(fig, "Figure 4. Atlas network, flow and part-to-whole views", "Additional database-atlas views translated from the English HTML report into vector panels.")
        gs = GridSpec(2, 2, figure=fig, left=0.06, right=0.98, bottom=0.16, top=0.90, wspace=0.28, hspace=0.38)
        sankey_flow(fig.add_subplot(gs[0, :]), rows)
        chord_plot(fig.add_subplot(gs[1, 0]), rows)
        network_plot(fig.add_subplot(gs[1, 1]), rows)
        save_page(pdf, fig, "Fig. 4 | Flow and graph representations of known evidence. a, Sankey-style flow connecting source mode, product family, host group and measured result metric. b, Chord diagram summarizing repeated product-family and host-group pairings. c, Network view linking product families, host groups and result metrics. Line width encodes record support.")

        fig = plt.figure(figsize=(11.2, 8.1), constrained_layout=False)
        add_page_title(fig, "Figure 5. Treemap, keyword and top-entity atlas panels", "Compact full-database overview panels for presentation and manuscript supplements.")
        gs = GridSpec(2, 2, figure=fig, left=0.06, right=0.98, bottom=0.16, top=0.90, wspace=0.30, hspace=0.40)
        treemap_plot(fig.add_subplot(gs[0, 0]), tier_counter, "Database-tier treemap", "A")
        treemap_plot(fig.add_subplot(gs[0, 1]), counter_known(rows, "best_product_family", PRODUCT_LABELS), "Product-family treemap", "B")
        word_cloud_plot(fig.add_subplot(gs[1, 0]), rows)
        top_entities_table(fig.add_subplot(gs[1, 1]), rows)
        save_page(pdf, fig, "Fig. 5 | Compact atlas summaries for known entries. a, Treemap of curation tiers. b, Treemap of recognized product families. c, Keyword cloud generated from titles and known extracted fields. d, Top canonical products and hosts by record count. These panels provide overview material for project display slides and supplementary database description.")

        fig = plt.figure(figsize=(11.2, 8.1), constrained_layout=False)
        add_page_title(fig, "Figure 6. Reaction-condition reference ranges", "Filtered numeric fields define commonly reported operating windows for engineered host and LLPS-related systems.")
        gs = GridSpec(2, 2, figure=fig, left=0.07, right=0.98, bottom=0.16, top=0.90, wspace=0.30, hspace=0.40)
        hist_plot(fig.add_subplot(gs[0, 0]), temps, np.arange(10, 82, 2), "Temperature", "A", "Temperature (deg C)", COLORS["blue"])
        hist_plot(fig.add_subplot(gs[0, 1]), phs, np.arange(1, 14.5, 0.5), "pH", "B", "pH", COLORS["green"])
        hist_plot(fig.add_subplot(gs[1, 0]), [math.log10(v) for v in times if v > 0], np.arange(-3, 4.6, 0.25), "Reaction time", "C", "log10(hours)", COLORS["orange"])
        barh(fig.add_subplot(gs[1, 1]), system_counter, "Reaction-system type", "D", 10, COLORS["purple"])
        save_page(pdf, fig, "Fig. 6 | Reaction-condition reference ranges. a, Temperature distribution after filtering implausible values. b, pH distribution. c, Reaction time distribution after conversion to hours and log10 transformation. d, Reaction-system type distribution. The 30 deg C and 37 deg C modes together account for 53.8% of temperature records; pH 6.0-7.5 accounts for 51.9% of pH records.")

        fig = plt.figure(figsize=(11.2, 8.1), constrained_layout=False)
        add_page_title(fig, "Figure 7. Titer benchmark landscape", "Titer values are plotted on log10 scale to compare project starting and target points with the literature-derived distribution.")
        gs = GridSpec(2, 2, figure=fig, left=0.07, right=0.98, bottom=0.16, top=0.90, wspace=0.30, hspace=0.45)
        hist_plot(
            fig.add_subplot(gs[0, :]),
            log_titers,
            np.arange(-6, 7.5, 0.5),
            "Overall titer distribution with KDE",
            "A",
            "log10(titer, mg/L)",
            COLORS["blue"],
            markers=[
                (math.log10(med_titer), f"Median {med_titer:.1f}", COLORS["dark"]),
                (math.log10(geo_titer), f"Geomean {geo_titer:.1f}", COLORS["purple"]),
                (math.log10(0.5), "Start 0.5", COLORS["red"]),
                (math.log10(5), "Target 5", COLORS["green"]),
            ],
            kde=True,
        )
        family_boxplot(fig.add_subplot(gs[1, 0]), rows)
        ax = fig.add_subplot(gs[1, 1])
        ax.axis("off")
        ax.text(0.00, 0.95, "Interpretable benchmark summary", fontsize=10, fontweight="bold", transform=ax.transAxes)
        text = (
            f"Valid titer records: {len(titers):,}\n"
            f"Median: {med_titer:.1f} mg/L\n"
            f"Geometric mean: {geo_titer:.1f} mg/L\n"
            f"0.5 mg/L percentile: {percentile(titers, 0.5):.1f}%\n"
            f"5 mg/L percentile: {percentile(titers, 5):.1f}%\n\n"
            "Interpretation: the starting titer is located in the lower tail of the literature distribution, while the 5 mg/L target is conservative relative to the database-wide median."
        )
        ax.text(0.00, 0.82, wrapped(text, 58), fontsize=8.1, va="top", linespacing=1.45, transform=ax.transAxes)
        panel(ax, "C", "")
        save_page(pdf, fig, "Fig. 7 | Literature-derived titer benchmark for project target setting. a, Histogram and kernel-density estimate of valid titer records on a log10(mg/L) scale, with median, geometric mean, 0.5 mg/L project starting point and 5 mg/L target marked. b, Product-family titer boxplots ordered by median. c, Numeric interpretation showing that 0.5 mg/L lies in the lower tail whereas 5 mg/L remains conservative relative to the database-wide median.")

        fig = plt.figure(figsize=(11.2, 8.1), constrained_layout=False)
        add_page_title(fig, "Figure 8. Enzyme-parameter landscape for OC/DMT candidate discussion", "Available kinetic and activity records provide background ranges; explicit OC/DMT/OMT enzyme labels are sparse and should not be over-interpreted as a grouped comparison.")
        gs = GridSpec(2, 3, figure=fig, left=0.07, right=0.98, bottom=0.16, top=0.90, wspace=0.32, hspace=0.46)
        hist_plot(fig.add_subplot(gs[0, 0]), [math.log10(v) for v in km_values], np.arange(-3, 4.5, 0.5), "Km distribution", "A", "log10(Km, uM)", COLORS["blue"])
        hist_plot(fig.add_subplot(gs[0, 1]), [math.log10(v) for v in spec_values], np.arange(-6, 6.5, 0.5), "Specific activity", "B", "log10(U/mg)", COLORS["green"])
        hist_plot(fig.add_subplot(gs[0, 2]), [math.log10(v) for v in eff_values], np.arange(-1, 12.5, 0.5), "Catalytic efficiency", "C", "log10(kcat/Km, M-1 s-1)", COLORS["orange"])
        ax = fig.add_subplot(gs[1, :])
        ax.axis("off")
        panel(ax, "D", "Use in project logic")
        enzyme_note = (
            f"Filtered records: Km n={len(km_values):,}, specific activity n={len(spec_values):,}, kcat/Km n={len(eff_values):,}.\n\n"
            "These panels define an activity-affinity landscape for evaluating candidate catalytic modules. "
            "The current database contains only a few explicitly labeled OC/DMT/OMT enzyme-name entries, "
            "so the figure is best used as a background distribution for SBD-triggered substrate recruitment and catalytic feasibility, "
            "not as a formal OC-versus-DMT statistical comparison."
        )
        ax.text(0.02, 0.78, wrapped(enzyme_note, 140), fontsize=8.8, va="top", linespacing=1.55, transform=ax.transAxes)
        save_page(pdf, fig, "Fig. 8 | Enzyme-parameter landscape for OC/DMT candidate discussion. a, Km distribution filtered to 0.001-10000 uM and shown on a log10 scale. b, Specific activity distribution in U/mg or U/mg-equivalent units. c, Catalytic efficiency distribution after conversion to M-1 s-1 where units permit. d, Interpretation note: these panels define a background activity-affinity landscape for SBD-triggered recruitment and catalytic feasibility, not a formal OC-versus-DMT comparison.")

        fig = plt.figure(figsize=(11.2, 8.1), constrained_layout=False)
        add_page_title(fig, "Figure 9. LLPS regulatory evidence and project-relevant signals", "LLPS-specific fields highlight reported triggers and catalytic-effect evidence for condensate-based regulation.")
        gs = GridSpec(2, 2, figure=fig, left=0.07, right=0.98, bottom=0.16, top=0.90, wspace=0.32, hspace=0.42)
        ax = fig.add_subplot(gs[0, 0])
        if folds:
            xs = np.arange(1, len(folds) + 1)
            ax.scatter(xs, np.log10(folds), s=55, color=COLORS["purple"], alpha=0.82)
            for x, v in zip(xs, folds):
                ax.text(x, math.log10(v) + 0.08, f"{v:g}x", ha="center", fontsize=7)
            ax.axhline(0, color=COLORS["gray"], lw=0.8, ls=(0, (3, 3)))
            ax.set_xlabel("Reported LLPS fold-change record")
            ax.set_ylabel("log10(fold-change)")
        else:
            ax.text(0.5, 0.5, "No fold-change values", ha="center", va="center")
        panel(ax, "A", "LLPS-associated catalytic effect")
        clean_axes(ax)
        barh(fig.add_subplot(gs[0, 1]), triggers, "LLPS trigger classes", "B", 10, COLORS["red"])
        barh(fig.add_subplot(gs[1, 0]), metric_counter, "Measured result metrics", "C", 12, COLORS["cyan"])
        barh(fig.add_subplot(gs[1, 1]), clean_counter, "Evidence-quality levels", "D", 10, COLORS["gray"])
        save_page(pdf, fig, "Fig. 9 | LLPS regulatory evidence and project-relevant signals. a, Reported LLPS-associated catalytic-efficiency fold-change records. b, Trigger classes for LLPS or condensate-related regulation, including nutrient or induction cues, DNA damage, stress, calcium, overexpression and salt/crowding. c, Measured result metrics represented in the database. d, Evidence-quality levels for the extracted records.")

    return {
        "output_pdf": str(OUT),
        "source_csv": str(SRC),
        "total_records": total,
        "unique_dois": doi_count,
        "temperature_records": len(temps),
        "temperature_30_or_37_pct": 100 * sum(1 for v in temps if abs(v - 30) <= 0.5 or abs(v - 37) <= 0.5) / len(temps) if temps else 0,
        "ph_records": len(phs),
        "ph_6_to_7_5_pct": 100 * sum(1 for v in phs if 6 <= v <= 7.5) / len(phs) if phs else 0,
        "time_records": len(times),
        "titer_records_mg_l": len(titers),
        "titer_median_mg_l": med_titer,
        "titer_geometric_mean_mg_l": geo_titer,
        "project_start_0_5_mg_l_percentile": percentile(titers, 0.5),
        "project_target_5_mg_l_percentile": percentile(titers, 5),
        "km_records_filtered": len(km_values),
        "specific_activity_records_filtered": len(spec_values),
        "kinetic_efficiency_records_filtered": len(eff_values),
        "llps_fold_change_records": len(folds),
        "trigger_classes": dict(triggers.most_common()),
    }


def main() -> None:
    setup_style()
    rows = read_rows()
    summary = generate_pdf(rows)
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Wrote: {OUT}")
    print(f"Wrote: {SUMMARY}")


if __name__ == "__main__":
    main()

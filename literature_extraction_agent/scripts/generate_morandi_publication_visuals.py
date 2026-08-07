# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import html
import json
import math
import re
import statistics
import textwrap
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyArrowPatch, PathPatch, Rectangle
from matplotlib.path import Path as MplPath


ROOT = Path(__file__).resolve().parents[1]
ESSAY = ROOT / "essay"
SRC = ESSAY / "optimized_experimental_database_with_supplementary_expanded160_union_evidence_aware_fulltext_pro_completed_si_rule_fieldbackfilled.csv"
FIG_DIR = ESSAY / "morandi_publication_figures"
OUT_HTML = ESSAY / "morandi_publication_visualization_report_en.html"
OUT_PDF = ESSAY / "morandi_publication_figure_pack_en.pdf"
SUMMARY = ESSAY / "morandi_publication_visualization_summary.json"

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
    "#9A7F87",  # mauve rose
    "#B8A48A",  # warm taupe
    "#7D95A8",  # dusty blue
    "#9AAB8F",  # sage
    "#C1A3A8",  # muted pink
    "#A9A39A",  # stone
    "#D0B07D",  # ochre
    "#8D9B96",  # blue green gray
    "#B7A7C6",  # muted lavender
    "#C0C5BA",  # pale sage
]
INK = "#232323"
MUTED = "#66615E"
PANEL = "#6B6763"
LIGHT = "#E4E0DA"
PALE = "#F3F1EE"

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
CLEAN_LABELS = {
    "A_complete": "A complete",
    "A_llps": "A LLPS",
    "B_product_condition": "B product-condition",
    "C_llps_candidate": "C LLPS candidate",
    "C_partial_context": "C partial context",
    "D_result_only": "D result-only",
}
TIER_LABELS = {
    "core": "Core",
    "llps_core": "LLPS core",
    "silver": "Silver",
    "review": "Review",
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
    "llps_state": "LLPS state",
    "km": "Km",
    "kcat": "kcat",
}
PRODUCT_FAMILIES = ["flavonoid", "isoprenoid", "terpenoid", "stilbene", "isoflavonoid", "llps_system"]


def clean(value: object) -> str:
    return " ".join(str(value or "").replace("\u00a0", " ").strip().split())


def low(value: object) -> str:
    return clean(value).lower()


def is_unknown(value: object) -> bool:
    return low(value) in UNKNOWN


def labelize(value: object, mapping: dict[str, str] | None = None) -> str:
    text = clean(value)
    key = text.lower()
    if mapping and key in mapping:
        return mapping[key]
    return text.replace("_", " ").replace("-", " ").title() if text else "Unlabeled"


def parse_number(value: object) -> float | None:
    text = clean(value)
    matches = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    if not matches:
        return None
    vals = [float(x) for x in matches]
    return sum(vals) / len(vals)


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


def metric_name(row: dict[str, str]) -> str:
    raw = low(row.get("primary_result_metric"))
    if not raw:
        return ""
    return METRIC_LABELS.get(raw, labelize(raw))


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
    if unit in {"mg/l", "mgl-1"} and ("titer" in metric or "concentration" in metric):
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
        v /= 1000
        return v if 1e-9 <= v <= 1e6 else None
    return None


def kinetic_efficiency_m_inv_s(row: dict[str, str]) -> float | None:
    unit = low(row.get("kinetic_efficiency_norm_unit") or row.get("kinetic_efficiency_unit"))
    v = parse_number(row.get("kinetic_efficiency_norm_value") or row.get("kinetic_efficiency_value"))
    if v is None:
        return None
    u = unit.replace("µ", "u").replace("μ", "u")
    if "um" in u:
        v *= 1e6
    elif "mm" in u:
        v *= 1e3
    elif "m" not in u:
        return None
    if "min" in u:
        v /= 60
    return v if 1e-6 <= v <= 1e12 else None


def llps_fold(row: dict[str, str]) -> float | None:
    for field in ["catalytic_efficiency_fold_change_norm_value", "catalytic_efficiency_fold_change_value"]:
        v = parse_number(row.get(field))
        if v is not None and 0.01 <= v <= 1e5:
            return v
    return None


def trigger_group(value: object) -> str:
    k = low(value)
    if not k or k in UNKNOWN:
        return ""
    if any(x in k for x in ["salt", "ionic", "nacl", "kcl"]):
        return "Salt / ionic strength"
    if any(x in k for x in ["ph", "acid", "alkaline"]):
        return "pH"
    if any(x in k for x in ["temperature", "heat", "cold"]):
        return "Temperature"
    if any(x in k for x in ["substrate", "ligand", "metabolite"]):
        return "Substrate / ligand"
    if any(x in k for x in ["light", "opto"]):
        return "Light"
    if any(x in k for x in ["concentration", "threshold"]):
        return "Concentration"
    return labelize(value)


def geom_mean(values: list[float]) -> float:
    vals = [v for v in values if v > 0]
    return 10 ** (sum(math.log10(v) for v in vals) / len(vals)) if vals else float("nan")


def percentile(values: list[float], x: float) -> float:
    vals = sorted(v for v in values if v > 0)
    if not vals:
        return float("nan")
    return 100 * sum(v <= x for v in vals) / len(vals)


def setup_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 8.4,
            "axes.titlesize": 9.2,
            "axes.labelsize": 8.2,
            "xtick.labelsize": 7.2,
            "ytick.labelsize": 7.2,
            "legend.fontsize": 7.0,
            "axes.linewidth": 0.65,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "figure.dpi": 300,
            "savefig.facecolor": "white",
        }
    )


def panel(ax, letter: str, title: str) -> None:
    ax.text(-0.10, 1.06, letter, transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom", ha="left", color=INK)
    ax.set_title(title, loc="left", pad=5, fontweight="bold", color=INK)


def box_axes(ax) -> None:
    for side in ["left", "right", "top", "bottom"]:
        ax.spines[side].set_visible(True)
        ax.spines[side].set_color(PANEL)
        ax.spines[side].set_linewidth(0.65)
    ax.tick_params(length=2.5, color=PANEL, labelcolor=INK)
    ax.grid(False)
    ax.set_facecolor("white")


def add_header(fig, title: str) -> None:
    fig.text(0.02, 0.985, title, ha="left", va="top", fontsize=13.2, fontweight="bold", color=INK)


def add_caption(fig, text: str) -> None:
    fig.text(0.025, 0.018, textwrap.fill(text, 178), ha="left", va="bottom", fontsize=7.2, color=INK, linespacing=1.18)


def save_figure(pdf: PdfPages, fig, name: str, caption: str) -> Path:
    add_caption(fig, caption)
    svg = FIG_DIR / f"{name}.svg"
    fig.savefig(svg, format="svg", bbox_inches="tight")
    pdf.savefig(fig)
    plt.close(fig)
    return svg


def short_tick(label: str, limit: int = 30) -> str:
    label = clean(label)
    return label if len(label) <= limit else label[: max(1, limit - 1)] + "."


def barh(ax, counter: Counter[str], letter: str, title: str, n: int, color: str, *, label_limit: int = 30) -> None:
    items = [(k, v) for k, v in counter.most_common(n) if k][::-1]
    labels = [short_tick(k, label_limit) for k, _ in items]
    values = [v for _, v in items]
    y = np.arange(len(items))
    ax.barh(y, values, color=color, edgecolor=PANEL, linewidth=0.25, height=0.64)
    ax.set_yticks(y, labels)
    ax.tick_params(axis="y", labelsize=6.7 if label_limit <= 24 else 7.0)
    ax.set_xlabel("Records")
    if values:
        off = max(values) * 0.015
        for yi, v in zip(y, values):
            ax.text(v + off, yi, f"{v:,}", va="center", fontsize=6.8, color=INK)
        ax.set_xlim(0, max(values) * 1.24)
    panel(ax, letter, title)
    box_axes(ax)


def hist(ax, values: list[float], bins, letter: str, title: str, xlabel: str, color: str, markers=None, kde=False) -> None:
    values = [v for v in values if math.isfinite(v)]
    ax.hist(values, bins=bins, color=color, edgecolor=PANEL, linewidth=0.25, rwidth=0.86)
    if kde and len(values) > 5:
        xs = np.linspace(min(bins), max(bins), 300)
        arr = np.asarray(values)
        width = bins[1] - bins[0]
        bw = max(width * 1.25, 1.06 * arr.std(ddof=0) * (len(arr) ** -0.2))
        den = np.exp(-0.5 * ((xs[:, None] - arr[None, :]) / bw) ** 2).sum(axis=1)
        den = den / (len(arr) * bw * math.sqrt(2 * math.pi))
        ax.plot(xs, den * len(arr) * width, color=MORANDI[0], lw=1.35)
    if markers:
        ymax = ax.get_ylim()[1]
        for x, label, color_m in markers:
            ax.axvline(x, color=color_m, lw=1.05)
            ax.text(x, ymax * 0.97, label, rotation=90, ha="right", va="top", fontsize=6.3, color=color_m)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Records")
    panel(ax, letter, title)
    box_axes(ax)


def donut(ax, counter: Counter[str], letter: str, title: str, n: int, *, legend_cols: int = 1) -> None:
    items = counter.most_common(n)
    other = sum(counter.values()) - sum(v for _, v in items)
    if other > 0:
        items.append(("Others", other))
    labels = [short_tick(k, 18) for k, _ in items]
    vals = [v for _, v in items]
    colors = MORANDI[: len(vals)]
    wedges, _ = ax.pie(vals, startangle=90, counterclock=False, colors=colors, wedgeprops={"width": 0.38, "edgecolor": "white", "linewidth": 0.6})
    total = sum(vals)
    ax.text(0, 0, f"Total:\n{total:,}", ha="center", va="center", fontsize=8, fontweight="bold", color=INK)
    for w, lab, val in zip(wedges, labels, vals):
        ang = math.radians((w.theta1 + w.theta2) / 2)
        x, y = 1.12 * math.cos(ang), 1.12 * math.sin(ang)
        if val / total >= 0.035:
            ax.text(x, y, f"{val:,}\n({val/total:.0%})", ha="center", va="center", fontsize=6.2, color=INK)
    ax.legend(
        wedges,
        labels,
        loc="center left",
        bbox_to_anchor=(0.78, 0.50),
        ncol=legend_cols,
        frameon=False,
        fontsize=5.9,
        handlelength=0.9,
        handletextpad=0.35,
        borderaxespad=0.0,
        labelspacing=0.32,
    )
    panel(ax, letter, title)
    box_axes(ax)
    ax.set_xticks([])
    ax.set_yticks([])


def coverage_panel(ax, rows: list[dict[str, str]]) -> None:
    fields = [
        ("Product family", "best_product_family"),
        ("Product", "best_canonical_product"),
        ("Host group", "best_host_group"),
        ("Host", "best_canonical_host"),
        ("Expression host", "best_expression_host_value"),
        ("System type", "best_reaction_system_type_value"),
        ("Whole-cell", "best_is_whole_cell_value"),
        ("Temperature", "best_reaction_temperature_value"),
        ("pH", "best_reaction_ph_value"),
        ("Time", "best_reaction_time_value"),
        ("Substrate", "best_substrate_name_value"),
        ("Substrate conc.", "best_substrate_concentration_value"),
        ("LLPS state", "best_llps_state_value"),
        ("LLPS trigger", "best_llps_trigger_value"),
    ][::-1]
    total = len(rows)
    known = [sum(1 for r in rows if not is_unknown(r.get(f))) for _, f in fields]
    unknown = [total - k for k in known]
    y = np.arange(len(fields))
    ax.barh(y, known, color=MORANDI[3], edgecolor=PANEL, linewidth=0.2, height=0.62, label="Known")
    ax.barh(y, unknown, left=known, color=LIGHT, edgecolor="white", linewidth=0.2, height=0.62, label="Unknown")
    ax.set_yticks(y, [x for x, _ in fields])
    ax.set_xlabel("Records")
    ax.legend(frameon=False, loc="lower right")
    panel(ax, "a", "Field coverage after completion")
    box_axes(ax)


def sankey_overview(ax, rows: list[dict[str, str]]) -> None:
    ax.set_axis_off()
    levels = [
        ("Source", counter_known(rows, "source_mode").most_common(4)),
        ("Product family", counter_known(rows, "best_product_family", PRODUCT_LABELS).most_common(4)),
        ("Host group", counter_known(rows, "best_host_group", HOST_LABELS).most_common(4)),
        ("Metric", Counter(metric_name(r) for r in rows if metric_name(r)).most_common(4)),
    ]
    xs = np.linspace(0.05, 0.95, len(levels))
    node_pos: list[dict[str, tuple[float, float, float]]] = []
    for li, (header, items) in enumerate(levels):
        total = sum(v for _, v in items) or 1
        heights = [max(0.035, 0.48 * v / total) for _, v in items]
        gap = 0.032
        y_top = 0.84
        pos = {}
        ax.text(xs[li], 0.93, header, ha="center", va="center", fontsize=8.7, fontweight="bold", color=INK)
        for idx, ((label, val), h) in enumerate(zip(items, heights)):
            y = y_top - sum(heights[:idx]) - gap * idx - h / 2
            rect = Rectangle((xs[li] - 0.018, y - h / 2), 0.036, h, facecolor=MORANDI[(li + idx) % len(MORANDI)], edgecolor=PANEL, linewidth=0.45)
            ax.add_patch(rect)
            ha = "right" if li == 0 else "left"
            tx = xs[li] - 0.025 if li == 0 else xs[li] + 0.025
            ax.text(tx, y, f"{short_tick(label, 24)}\n{val:,}", ha=ha, va="center", fontsize=6.2, color=INK)
            pos[label] = (xs[li], y, h)
        node_pos.append(pos)
    # Simple proportional links between adjacent dominant categories, computed from records.
    fields = [
        ("source_mode", None),
        ("best_product_family", PRODUCT_LABELS),
        ("best_host_group", HOST_LABELS),
        ("primary_result_metric", METRIC_LABELS),
    ]
    for li in range(len(fields) - 1):
        left_field, left_map = fields[li]
        right_field, right_map = fields[li + 1]
        pairs = Counter()
        for r in rows:
            a = metric_name(r) if left_field == "primary_result_metric" else labelize(r.get(left_field), left_map) if not is_unknown(r.get(left_field)) else ""
            b = metric_name(r) if right_field == "primary_result_metric" else labelize(r.get(right_field), right_map) if not is_unknown(r.get(right_field)) else ""
            if a in node_pos[li] and b in node_pos[li + 1]:
                pairs[(a, b)] += 1
        maxv = max(pairs.values()) if pairs else 1
        for (a, b), val in pairs.most_common(18):
            x0, y0, _ = node_pos[li][a]
            x1, y1, _ = node_pos[li + 1][b]
            path = MplPath([(x0 + 0.018, y0), ((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1), (x1 - 0.018, y1)], [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4])
            ax.add_patch(PathPatch(path, facecolor="none", edgecolor=MORANDI[li], alpha=0.16, lw=0.35 + 4.5 * val / maxv, capstyle="round"))
    panel(ax, "b", "Database curation flow")


def bubble_matrix(ax, rows: list[dict[str, str]], letter: str = "c") -> None:
    families = [k for k, _ in counter_known(rows, "best_product_family", PRODUCT_LABELS).most_common(6)]
    hosts = [k for k, _ in counter_known(rows, "best_host_group", HOST_LABELS).most_common(5)]
    pairs = Counter()
    for r in rows:
        f = labelize(r.get("best_product_family"), PRODUCT_LABELS) if not is_unknown(r.get("best_product_family")) else ""
        h = labelize(r.get("best_host_group"), HOST_LABELS) if not is_unknown(r.get("best_host_group")) else ""
        if f in families and h in hosts:
            pairs[(f, h)] += 1
    maxv = max(pairs.values()) if pairs else 1
    for i, f in enumerate(families):
        for j, h in enumerate(hosts):
            v = pairs.get((f, h), 0)
            if v:
                ax.scatter(i, j, s=18 + 680 * (v / maxv), color=MORANDI[(i + j) % len(MORANDI)], edgecolor=PANEL, linewidth=0.35, alpha=0.86)
                if v >= maxv * 0.18:
                    ax.text(i, j, f"{v:,}", ha="center", va="center", fontsize=5.7, color=INK)
    ax.set_xticks(range(len(families)), [short_tick(x, 16) for x in families], rotation=28, ha="right")
    ax.set_yticks(range(len(hosts)), [short_tick(x, 16) for x in hosts])
    ax.tick_params(axis="both", labelsize=6.5)
    panel(ax, letter, "Product-family by host matrix")
    box_axes(ax)


def evidence_chain(ax, rows: list[dict[str, str]], letter: str = "d") -> None:
    ax.set_axis_off()
    total = len(rows)
    dois = len({low(r.get("doi")) for r in rows if not is_unknown(r.get("doi"))})
    title_known = sum(1 for r in rows if not is_unknown(r.get("title")))
    product_known = sum(1 for r in rows if not is_unknown(r.get("best_product_family")))
    host_known = sum(1 for r in rows if not is_unknown(r.get("best_host_group")))
    result_known = sum(1 for r in rows if not is_unknown(r.get("primary_result_metric")))
    labels = [
        ("DOI", dois),
        ("Title", title_known),
        ("Product label", product_known),
        ("Host label", host_known),
        ("Result", result_known),
        ("Records", total),
    ]
    xs = np.linspace(0.06, 0.94, len(labels))
    for i, ((lab, val), x) in enumerate(zip(labels, xs)):
        ax.add_patch(Rectangle((x - 0.045, 0.44), 0.09, 0.16, facecolor=MORANDI[i % len(MORANDI)], edgecolor=PANEL, linewidth=0.5))
        ax.text(x, 0.54, lab, ha="center", va="center", fontsize=7.2, fontweight="bold", color=INK)
        ax.text(x, 0.48, f"{val:,}", ha="center", va="center", fontsize=7.0, color=INK)
        if i < len(labels) - 1:
            ax.add_patch(FancyArrowPatch((x + 0.05, 0.52), (xs[i + 1] - 0.05, 0.52), arrowstyle="-|>", mutation_scale=8, linewidth=0.7, color=MUTED))
    panel(ax, letter, "Traceable evidence chain")


def titer_box(ax, rows: list[dict[str, str]]) -> None:
    groups = []
    for fam in PRODUCT_FAMILIES:
        vals = [math.log10(v) for r in rows if low(r.get("best_product_family")) == fam and (v := titer_mg_l(r)) is not None and v > 0]
        if vals:
            groups.append((PRODUCT_LABELS[fam], vals))
    groups.sort(key=lambda x: statistics.median(x[1]), reverse=True)
    bp = ax.boxplot([v for _, v in groups], patch_artist=True, widths=0.54, showfliers=False)
    for i, patch in enumerate(bp["boxes"]):
        patch.set(facecolor=MORANDI[i % len(MORANDI)], edgecolor=PANEL, linewidth=0.55)
    for key in ["whiskers", "caps"]:
        for line in bp[key]:
            line.set(color=PANEL, linewidth=0.55)
    for med in bp["medians"]:
        med.set(color=INK, linewidth=1.1)
    ax.set_xticks(range(1, len(groups) + 1), [g[0] for g in groups], rotation=30, ha="right")
    ax.set_ylabel("log10(titer, mg/L)")
    panel(ax, "d", "Titer by product family")
    box_axes(ax)


def small_text_panel(ax, letter: str, title: str, lines: list[str]) -> None:
    ax.set_axis_off()
    panel(ax, letter, title)
    y = 0.84
    for i, line in enumerate(lines):
        ax.text(0.04, y, textwrap.fill(line, 58), transform=ax.transAxes, ha="left", va="top", fontsize=8.0 if i else 8.8, color=INK, fontweight="bold" if i == 0 else "normal")
        y -= 0.13 if i == 0 else 0.10


def fig1(rows: list[dict[str, str]], pdf: PdfPages) -> tuple[Path, str]:
    fig = plt.figure(figsize=(12.8, 8.0))
    add_header(fig, "Fig. 1 Overview of the literature-derived database")
    gs = GridSpec(2, 2, figure=fig, left=0.08, right=0.97, bottom=0.13, top=0.90, hspace=0.48, wspace=0.38)
    coverage_panel(fig.add_subplot(gs[0, 0]), rows)
    sankey_overview(fig.add_subplot(gs[0, 1]), rows)
    barh(fig.add_subplot(gs[1, :]), counter_known(rows, "best_product_family", PRODUCT_LABELS), "c", "Product families", 8, MORANDI[0], label_limit=30)
    cap = "Fig. 1 | Overview of the curated literature database. a, Coverage of key fields after full-text and SI/data-assisted completion. b, Curation flow from source mode to product family, host group and measured metric. c, Recognized product-family distribution."
    return save_figure(pdf, fig, "fig1_overview", cap), cap


def fig2(rows: list[dict[str, str]], pdf: PdfPages) -> tuple[Path, str]:
    temps = [v for r in rows if (v := temperature_c(r)) is not None]
    phs = [v for r in rows if (v := ph_value(r)) is not None]
    times = [v for r in rows if (v := reaction_time_h(r)) is not None and v > 0]
    fig = plt.figure(figsize=(12.4, 7.2))
    add_header(fig, "Fig. 2 Statistical analysis of extracted reaction conditions")
    gs = GridSpec(2, 2, figure=fig, left=0.08, right=0.97, bottom=0.15, top=0.87, hspace=0.50, wspace=0.40)
    hist(fig.add_subplot(gs[0, 0]), temps, np.arange(10, 82, 2), "a", "Temperature", "Temperature (°C)", MORANDI[2])
    hist(fig.add_subplot(gs[0, 1]), phs, np.arange(1, 14.5, 0.5), "b", "pH", "pH", MORANDI[3])
    hist(fig.add_subplot(gs[1, 0]), [math.log10(v) for v in times], np.arange(-3, 4.6, 0.25), "c", "Reaction time", "log10(hours)", MORANDI[6])
    barh(fig.add_subplot(gs[1, 1]), Counter(metric_name(r) for r in rows if metric_name(r)), "d", "Result metrics", 8, MORANDI[4], label_limit=26)
    mode_pct = 100 * sum(1 for v in temps if abs(v - 30) <= 0.5 or abs(v - 37) <= 0.5) / len(temps) if temps else 0
    ph_pct = 100 * sum(1 for v in phs if 6 <= v <= 7.5) / len(phs) if phs else 0
    cap = f"Fig. 2 | Reaction-condition and metric statistics. a-c, Distributions of temperature, pH and reaction time using uniform bin styling and no background grid. d, Measured result metrics. Temperatures near 30 deg C or 37 deg C account for {mode_pct:.1f}% of filtered temperature records, and pH 6.0-7.5 accounts for {ph_pct:.1f}% of filtered pH records."
    return save_figure(pdf, fig, "fig2_conditions_quality", cap), cap


def fig3(rows: list[dict[str, str]], pdf: PdfPages) -> tuple[Path, str]:
    titers = [v for r in rows if (v := titer_mg_l(r)) is not None and v > 0]
    log_titers = [math.log10(v) for v in titers]
    med = statistics.median(titers) if titers else float("nan")
    geo = geom_mean(titers)
    fig = plt.figure(figsize=(12.4, 7.4))
    add_header(fig, "Fig. 3 Titer benchmark landscape")
    gs = GridSpec(2, 2, figure=fig, left=0.07, right=0.98, bottom=0.14, top=0.88, hspace=0.50, wspace=0.32)
    hist(
        fig.add_subplot(gs[0, :]),
        log_titers,
        np.arange(-6, 7.5, 0.5),
        "a",
        "Overall titer distribution",
        "log10(titer, mg/L)",
        MORANDI[2],
        markers=[
            (math.log10(med), f"Median {med:.1f}", INK),
            (math.log10(geo), f"Geomean {geo:.1f}", MORANDI[0]),
            (math.log10(0.5), "0.5 mg/L", MORANDI[4]),
            (math.log10(5), "5 mg/L", MORANDI[3]),
        ],
        kde=True,
    )
    titer_box(fig.add_subplot(gs[1, 0]), rows)
    small_text_panel(
        fig.add_subplot(gs[1, 1]),
        "c",
        "Project benchmark interpretation",
        [
            "Benchmark values",
            f"Valid titer records: {len(titers):,}",
            f"Median titer: {med:.2f} mg/L",
            f"Geometric mean: {geo:.2f} mg/L",
            f"0.5 mg/L percentile: {percentile(titers, 0.5):.1f}%",
            f"5 mg/L percentile: {percentile(titers, 5):.1f}%",
            "The starting point is positioned in the lower tail of the literature distribution, while the target remains within a realistic optimization range.",
        ],
    )
    cap = "Fig. 3 | Literature-derived titer benchmark. a, Overall titer distribution on a log10(mg/L) axis with kernel-density estimate, median, geometric mean, project-start and project-target markers. b, Product-family titer boxplots sorted by median. c, Benchmark values used to justify the project target."
    return save_figure(pdf, fig, "fig3_titer_benchmark", cap), cap


def fig4(rows: list[dict[str, str]], pdf: PdfPages) -> tuple[Path, str]:
    km = [v for r in rows if (v := km_um(r)) is not None]
    spec = [v for r in rows if (v := specific_activity_u_mg(r)) is not None]
    eff = [v for r in rows if (v := kinetic_efficiency_m_inv_s(r)) is not None]
    folds = [v for r in rows if (v := llps_fold(r)) is not None]
    triggers = Counter(trigger_group(r.get("best_llps_trigger_value")) for r in rows if trigger_group(r.get("best_llps_trigger_value")))
    fig = plt.figure(figsize=(12.8, 9.0))
    add_header(fig, "Fig. 4 Enzyme-parameter and LLPS regulatory landscape")
    gs = GridSpec(3, 2, figure=fig, left=0.08, right=0.97, bottom=0.12, top=0.90, hspace=0.55, wspace=0.42)
    hist(fig.add_subplot(gs[0, 0]), [math.log10(v) for v in km], np.arange(-3, 4.5, 0.5), "a", "Km", "log10(Km, μM)", MORANDI[2])
    hist(fig.add_subplot(gs[0, 1]), [math.log10(v) for v in spec], np.arange(-6, 6.5, 0.5), "b", "Specific activity", "log10(U/mg)", MORANDI[3])
    hist(fig.add_subplot(gs[1, 0]), [math.log10(v) for v in eff], np.arange(-1, 12.5, 0.5), "c", "Catalytic efficiency", "log10(kcat/Km, M-1 s-1)", MORANDI[6])
    ax = fig.add_subplot(gs[1, 1])
    if folds:
        xs = np.arange(1, len(folds) + 1)
        ax.scatter(xs, [math.log10(v) for v in folds], s=38, color=MORANDI[0], edgecolor=PANEL, linewidth=0.35)
        ax.axhline(0, color=PANEL, lw=0.65)
    ax.set_xlabel("Reported record")
    ax.set_ylabel("log10(fold change)")
    panel(ax, "d", "LLPS catalytic effect")
    box_axes(ax)
    barh(fig.add_subplot(gs[2, 0]), triggers, "e", "LLPS trigger classes", 6, MORANDI[4], label_limit=28)
    bubble_matrix(fig.add_subplot(gs[2, 1]), rows, "f")
    cap = f"Fig. 4 | Enzyme and LLPS regulatory analysis. a-c, Filtered distributions of Km, specific activity and catalytic efficiency. d, Reported LLPS-associated catalytic fold-change values. e, Trigger classes for condensate or phase-separation regulation. f, Product-family and host-group intersections used to contextualize LLPS/enzyme-system design."
    return save_figure(pdf, fig, "fig4_enzyme_llps", cap), cap


def fig5(rows: list[dict[str, str]], pdf: PdfPages) -> tuple[Path, str]:
    product = counter_known(rows, "best_canonical_product").most_common(12)
    host = counter_known(rows, "best_canonical_host").most_common(12)
    terms = Counter()
    stop = {"the", "and", "with", "for", "from", "using", "production", "biosynthesis", "enzyme", "activity", "metabolic", "protein", "cell", "cells"}
    for r in rows:
        blob = " ".join([r.get("title", ""), r.get("best_main_product_name_value", ""), r.get("best_substrate_name_value", ""), r.get("best_llps_trigger_value", "")])
        for word in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", blob.lower()):
            if word not in stop:
                terms[word] += 1
    fig = plt.figure(figsize=(13.0, 8.0))
    add_header(fig, "Fig. 5 Research-frequency summaries")
    gs = GridSpec(2, 2, figure=fig, left=0.10, right=0.98, bottom=0.13, top=0.88, hspace=0.46, wspace=0.48)
    barh(fig.add_subplot(gs[0, 0]), Counter(dict(product)), "a", "Commonly extracted products", 12, MORANDI[0], label_limit=28)
    barh(fig.add_subplot(gs[0, 1]), Counter(dict(host)), "b", "Commonly used hosts", 10, MORANDI[2], label_limit=30)
    barh(fig.add_subplot(gs[1, :]), Counter({k.title(): v for k, v in terms.most_common(12)}), "c", "Frequent contextual terms", 12, MORANDI[3], label_limit=30)
    cap = "Fig. 5 | Research-frequency summaries. a, Most frequently extracted canonical products. b, Most frequently identified canonical hosts. c, Frequent contextual terms from titles and completed fields. Ranked bar charts are used instead of dense word-cloud panels for publication readability."
    return save_figure(pdf, fig, "fig5_research_frequency", cap), cap


def build_html(figures: list[tuple[Path, str]], summary: dict[str, object]) -> None:
    cards = []
    for svg_path, caption in figures:
        svg = svg_path.read_text(encoding="utf-8", errors="ignore")
        cards.append(
            f"""
            <section class="figure-card">
              <div class="svg-wrap">{svg}</div>
              <p class="caption">{html.escape(caption)}</p>
            </section>
            """
        )
    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Morandi Publication Visualization Report</title>
  <style>
    :root {{
      --ink: #232323;
      --muted: #66615e;
      --paper: #f7f5f1;
      --panel: #ffffff;
      --line: #bdb6ad;
    }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: Arial, Helvetica, sans-serif;
    }}
    main {{
      max-width: 1240px;
      margin: 0 auto;
      padding: 28px 22px 44px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      line-height: 1.15;
      letter-spacing: 0;
    }}
    .lead {{
      margin: 0 0 24px;
      color: var(--muted);
      max-width: 920px;
      line-height: 1.55;
    }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 22px;
    }}
    .meta div {{
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 10px 12px;
    }}
    .meta strong {{
      display: block;
      font-size: 20px;
      line-height: 1.2;
    }}
    .meta span {{
      color: var(--muted);
      font-size: 12px;
    }}
    .figure-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      margin: 18px 0 28px;
      padding: 12px 14px 14px;
    }}
    .svg-wrap svg {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .caption {{
      margin: 10px 4px 0;
      color: var(--ink);
      font-family: Georgia, 'Times New Roman', serif;
      font-size: 14px;
      line-height: 1.45;
    }}
    @media (max-width: 760px) {{
      main {{ padding: 20px 12px 34px; }}
      .meta {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      h1 {{ font-size: 23px; }}
    }}
  </style>
</head>
<body>
<main>
  <h1>Publication-style visualization of the literature-derived database</h1>
  <p class="lead">Figures were redrawn with a unified Morandi palette, fixed-width bar styling and clean panel backgrounds without dashed grid lines. The report uses the current field-completed database.</p>
  <div class="meta">
    <div><strong>{summary['total_records']:,}</strong><span>structured records</span></div>
    <div><strong>{summary['unique_dois']:,}</strong><span>traceable DOI sources</span></div>
    <div><strong>{summary['valid_titer_records']:,}</strong><span>valid titer records</span></div>
    <div><strong>{summary['si_text_dois']:,}</strong><span>SI/data text DOI coverage</span></div>
  </div>
  {''.join(cards)}
</main>
</body>
</html>
"""
    OUT_HTML.write_text(html_text, encoding="utf-8")


def generate() -> dict[str, object]:
    setup_style()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_rows()
    figures: list[tuple[Path, str]] = []
    with PdfPages(OUT_PDF) as pdf:
        figures.append(fig1(rows, pdf))
        figures.append(fig2(rows, pdf))
        figures.append(fig3(rows, pdf))
        figures.append(fig4(rows, pdf))
        figures.append(fig5(rows, pdf))
    titer_values = [v for r in rows if (v := titer_mg_l(r)) is not None and v > 0]
    si_text_manifest = ESSAY / "supplementary_current" / "supplementary_current_text_manifest.csv"
    si_dois = set()
    if si_text_manifest.exists():
        with si_text_manifest.open("r", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if r.get("status") == "cached" and not is_unknown(r.get("doi")):
                    si_dois.add(low(r.get("doi")))
    summary = {
        "source_csv": str(SRC),
        "output_html": str(OUT_HTML),
        "output_pdf": str(OUT_PDF),
        "figure_dir": str(FIG_DIR),
        "total_records": len(rows),
        "unique_dois": len({low(r.get("doi")) for r in rows if not is_unknown(r.get("doi"))}),
        "valid_titer_records": len(titer_values),
        "titer_median_mg_l": statistics.median(titer_values) if titer_values else None,
        "titer_geometric_mean_mg_l": geom_mean(titer_values) if titer_values else None,
        "project_start_0_5_mg_l_percentile": percentile(titer_values, 0.5),
        "project_target_5_mg_l_percentile": percentile(titer_values, 5),
        "si_text_dois": len(si_dois),
        "figures": [str(p) for p, _ in figures],
    }
    build_html(figures, summary)
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    summary = generate()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

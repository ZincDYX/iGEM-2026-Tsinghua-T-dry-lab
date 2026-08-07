from __future__ import annotations

import csv
import json
import math
import statistics
import textwrap
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyArrowPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
ESSAY = ROOT / "essay"
SRC = ESSAY / "project_conditioned_evidence_database.csv"
OUT = ESSAY / "modified_project_data_visualization_v6.pdf"
SUMMARY = ESSAY / "modified_project_data_visualization_v6_summary.json"

INK = "#2E2B28"
MUTED = "#706E6A"
LINE = "#DDD9D2"
PAPER = "#FBFAF7"
PALE = "#ECE8E0"
MAIN = "#9AAEBC"
MAIN_DARK = "#6F8798"
SECOND = "#C7BBA8"
ACCENT = "#C56A5A"
ACCENT_DARK = "#8F443B"

UNKNOWN = {"", "unknown", "none", "null", "nan", "n/a", "na", "not specified", "not available", "unidentified", "unlabeled"}
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


def setup_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 12.8,
            "axes.titlesize": 15.0,
            "axes.labelsize": 12.5,
            "xtick.labelsize": 11.2,
            "ytick.labelsize": 11.2,
            "legend.fontsize": 10.5,
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "figure.dpi": 300,
        }
    )


def clean(value: object) -> str:
    return " ".join(str(value or "").replace("\u00a0", " ").strip().split())


def low(value: object) -> str:
    return clean(value).lower()


def unknown(value: object) -> bool:
    return low(value) in UNKNOWN


def labelize(value: object, mapping: dict[str, str] | None = None) -> str:
    text = clean(value)
    if not text or unknown(text):
        return "Unlabeled"
    key = text.lower()
    if mapping and key in mapping:
        return mapping[key]
    return text.replace("_", " ").replace("-", " ").title()


def first_known(row: dict[str, str], *fields: str) -> str:
    for field in fields:
        value = clean(row.get(field, ""))
        if value and not unknown(value):
            return value
    return ""


def parse_number(value: object) -> float | None:
    import re

    text = clean(value).replace("−", "-")
    matches = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    if not matches:
        return None
    vals = [float(x) for x in matches]
    return sum(vals) / len(vals)


def read_rows() -> list[dict[str, str]]:
    with SRC.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def wrap(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def page_title(fig, title: str, subtitle: str = "") -> None:
    wrapped = wrap(title, 70)
    fig.text(0.052, 0.945, wrapped, ha="left", va="top", fontsize=22.0, fontweight="bold", color=INK, linespacing=1.08)
    if subtitle:
        y = 0.885 - 0.048 * wrapped.count("\n")
        fig.text(0.052, y, wrap(subtitle, 126), ha="left", va="top", fontsize=12.7, color=MUTED, linespacing=1.24)


def caption(fig, text: str) -> None:
    fig.text(0.052, 0.042, wrap(text, 154), ha="left", va="bottom", fontsize=10.8, color=INK, linespacing=1.2)


def clean_axes(ax, grid: bool = False) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(length=3, width=0.7, pad=5)
    if grid:
        ax.grid(axis="y", color=LINE, lw=0.55, alpha=0.65)
        ax.set_axisbelow(True)


def host_group(row: dict[str, str]) -> str:
    return labelize(first_known(row, "best_host_group", "host_group", "best_canonical_host", "canonical_host"), HOST_LABELS)


def product_family(row: dict[str, str]) -> str:
    return labelize(first_known(row, "best_product_family", "product_family"), PRODUCT_LABELS)


def canonical_product(row: dict[str, str]) -> str:
    return labelize(first_known(row, "best_canonical_product", "canonical_product", "best_main_product_name_value", "main_product_name_value"))


def is_true(row: dict[str, str], field: str) -> bool:
    return low(row.get(field)) in {"true", "1", "yes", "y"}


def is_glabridin(row: dict[str, str]) -> bool:
    product_fields = " ".join(
        clean(row.get(field, ""))
        for field in [
            "best_canonical_product",
            "canonical_product",
            "best_main_product_name_value",
            "main_product_name_value",
            "title_clean",
            "title",
        ]
    )
    return is_true(row, "is_project_glabridin_direct") or "glabridin" in low(product_fields)


def is_llps(row: dict[str, str]) -> bool:
    return is_true(row, "is_project_llps_related")


def is_llps_enzyme(row: dict[str, str]) -> bool:
    return is_true(row, "is_project_llps_enzyme")


def is_yeast(row: dict[str, str]) -> bool:
    return is_true(row, "is_project_yeast") or host_group(row) == "Yeast"


def is_flavonoid(row: dict[str, str]) -> bool:
    return is_true(row, "is_project_flavonoid_related") or product_family(row) in {"Flavonoid", "Isoflavonoid", "Pterocarpan", "Prenylflavonoid"}


def temperature_c(row: dict[str, str]) -> float | None:
    value = parse_number(first_known(row, "best_reaction_temperature_value", "reaction_temperature_norm_value", "reaction_temperature_value"))
    if value is None:
        return None
    return value if 10 <= value <= 80 else None


def ph_value(row: dict[str, str]) -> float | None:
    value = parse_number(first_known(row, "best_reaction_ph_value", "reaction_ph_norm_value", "reaction_ph_value"))
    if value is None:
        return None
    return value if 1 <= value <= 14 else None


def titer_mg_l(row: dict[str, str]) -> float | None:
    metric = low(row.get("primary_result_metric"))
    unit = low(first_known(row, "primary_result_unit_normalized", "primary_result_unit")).replace(" ", "")
    value = parse_number(first_known(row, "primary_result_numeric_normalized", "primary_result_value", "glabridin_titer_norm_value", "glabridin_titer_value"))
    if value is None:
        return None
    if unit in {"mg/l", "mgl-1", "mgl-1"} and ("titer" in metric or "concentration" in metric or "glabridin" in metric):
        return value if 1e-6 <= value <= 1e7 else None
    if "glabridin_titer" in metric and 1e-6 <= value <= 1e7:
        return value
    return None


def numeric_values(rows: list[dict[str, str]], fn) -> list[float]:
    out = []
    for row in rows:
        value = fn(row)
        if value is not None and math.isfinite(value):
            out.append(value)
    return out


def top_items(counter: Counter[str], n: int) -> list[tuple[str, int]]:
    return [(k, v) for k, v in counter.most_common(n) if k and k != "Unlabeled"]


def barh(ax, counter: Counter[str], highlights: set[str], n: int, xlabel: str = "Records") -> list[tuple[str, int]]:
    items = top_items(counter, n)[::-1]
    names = [x for x, _ in items]
    vals = [v for _, v in items]
    colors = [ACCENT if name in highlights else MAIN for name in names]
    bars = ax.barh(names, vals, height=0.56, color=colors, alpha=0.92)
    maxv = max(vals) if vals else 1
    ax.set_xlim(0, maxv * 1.30)
    for bar, name, val in zip(bars, names, vals):
        ax.text(
            val + maxv * 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{val:,}",
            va="center",
            fontsize=10.8,
            color=ACCENT_DARK if name in highlights else INK,
            fontweight="bold" if name in highlights else "normal",
        )
    ax.set_xlabel(xlabel)
    clean_axes(ax)
    return items


def normalized_hist_line(ax, values: list[float], bins: np.ndarray, color: str, label: str, lw: float) -> None:
    if not values:
        return
    counts, edges = np.histogram(values, bins=bins)
    if counts.max() > 0:
        counts = counts / counts.max()
    centers = (edges[:-1] + edges[1:]) / 2
    ax.plot(centers, counts, color=color, lw=lw, label=label)


def trigger_label(value: object) -> str:
    text = labelize(value)
    key = text.lower()
    if "ph" in key or "temperature" in key:
        return "pH/temp"
    if "substrate" in key or "ligand" in key:
        return "substrate/ligand"
    if "expression" in key or "nutrient" in key:
        return "expression/nutrient"
    if "threshold" in key:
        return "threshold"
    if "stress" in key or "damage" in key:
        return "stress/DNA"
    if "ionic" in key or "crowding" in key:
        return "ionic/crowding"
    if "reported" in key:
        return "other trigger"
    return text


def pct(part: int, whole: int) -> float:
    return 100.0 * part / whole if whole else 0.0


def page_1_database(pdf, rows: list[dict[str, str]]) -> None:
    fig = plt.figure(figsize=(14.4, 9.2), facecolor=PAPER)
    tier_counts = Counter(row.get("project_tier", "Unlabeled") for row in rows)
    title = "Project conclusions should come from conditioned evidence layers"
    subtitle = "The database remains broad, but claims for this iGEM system are restricted to yeast, flavonoid/glabridin and LLPS-enzyme tiers."
    page_title(fig, title, subtitle)
    ax = fig.add_axes([0.12, 0.19, 0.76, 0.56])
    order = [
        "Background | broad literature prior",
        "Tier 4 | transferable LLPS mechanism prior",
        "Tier 3 | LLPS-enzyme catalytic prior",
        "Tier 2 | yeast natural-product pathway prior",
        "Tier 1 | direct yeast-flavonoid/glabridin evidence",
    ]
    labels = ["Background", "Tier 4\nLLPS prior", "Tier 3\nLLPS-enzyme", "Tier 2\nYeast pathway", "Tier 1\nDirect evidence"]
    vals = [tier_counts.get(x, 0) for x in order]
    colors = [PALE, SECOND, MAIN, MAIN_DARK, ACCENT]
    ax.bar(labels, vals, color=colors, width=0.62, edgecolor="none")
    maxv = max(vals) if vals else 1
    for i, value in enumerate(vals):
        ax.text(i, value + maxv * 0.025, f"{value:,}", ha="center", va="bottom", fontsize=11.3, color=ACCENT_DARK if i == 4 else INK, fontweight="bold" if i == 4 else "normal")
    ax.annotate("decision layer", xy=(4, vals[-1]), xytext=(3.25, maxv * 0.83), color=ACCENT_DARK, fontsize=12.5, fontweight="bold", arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.7))
    ax.set_ylabel("Structured records")
    clean_axes(ax, grid=True)
    caption(fig, "Fig. 1 | Project-tier stratification. The accent bar marks records that are closest to the project; muted bars remain background priors for context and search-space design.")
    pdf.savefig(fig)
    plt.close(fig)


def page_2_host_product(pdf, rows: list[dict[str, str]]) -> None:
    fig = plt.figure(figsize=(14.4, 9.2), facecolor=PAPER)
    yeast_n = sum(1 for r in rows if is_yeast(r))
    glab_n = sum(1 for r in rows if is_glabridin(r))
    page_title(fig, "Yeast and Glabridin are the two anchors for transferring literature evidence", f"Yeast-associated records: {yeast_n:,}; Glabridin-linked records: {glab_n:,}. Other categories are kept as context, not the center of the design story.")
    gs = fig.add_gridspec(1, 2, left=0.10, right=0.92, bottom=0.20, top=0.70, wspace=0.38)
    ax1 = fig.add_subplot(gs[0, 0])
    hosts = Counter(host_group(r) for r in rows)
    barh(ax1, hosts, {"Yeast"}, 8)
    ax1.set_title("Expression host evidence", loc="left", fontweight="bold")
    ax2 = fig.add_subplot(gs[0, 1])
    products = Counter(product_family(r) for r in rows)
    highlights = {"Flavonoid", "Isoflavonoid", "LLPS system", "Prenylflavonoid"}
    barh(ax2, products, highlights, 8)
    ax2.set_title("Product-family evidence", loc="left", fontweight="bold")
    caption(fig, "Fig. 2 | Host and product-family distributions are filtered into a project-facing view. Yeast and flavonoid/isoflavonoid families are highlighted because they define the transfer path for glabridin biosynthesis.")
    pdf.savefig(fig)
    plt.close(fig)


def page_3_titer(pdf, rows: list[dict[str, str]]) -> None:
    fig = plt.figure(figsize=(14.4, 9.2), facecolor=PAPER)
    all_t = numeric_values(rows, titer_mg_l)
    yeast_rows = [r for r in rows if is_yeast(r)]
    yeast_flav = [r for r in rows if is_yeast(r) and is_flavonoid(r)]
    glab = [r for r in rows if is_glabridin(r)]
    llps_enzyme = [r for r in rows if is_llps_enzyme(r)]
    med = statistics.median(all_t) if all_t else float("nan")
    page_title(fig, "The 5 mg/L target is better judged against project-conditioned titers", "The full corpus gives the scale of natural-product production, while yeast-flavonoid and glabridin subsets define the most relevant feasibility benchmark.")
    ax = fig.add_axes([0.11, 0.23, 0.78, 0.49])
    groups = [
        ("All", all_t),
        ("Yeast", numeric_values(yeast_rows, titer_mg_l)),
        ("Yeast +\nflavonoid", numeric_values(yeast_flav, titer_mg_l)),
        ("Glabridin", numeric_values(glab, titer_mg_l)),
        ("LLPS-\nenzyme", numeric_values(llps_enzyme, titer_mg_l)),
    ]
    data = [[math.log10(v) for v in vals if v and v > 0] for _, vals in groups]
    positions = np.arange(len(groups))
    box = ax.boxplot(data, positions=positions, patch_artist=True, widths=0.52, showfliers=False)
    for patch, (name, _) in zip(box["boxes"], groups):
        key = name.replace("\n", " ")
        patch.set_facecolor(ACCENT if key in {"Yeast + flavonoid", "Glabridin"} else MAIN)
        patch.set_alpha(0.86 if key in {"Yeast + flavonoid", "Glabridin"} else 0.50)
        patch.set_edgecolor(INK)
        patch.set_linewidth(0.9)
    for key in ["whiskers", "caps", "medians"]:
        for item in box[key]:
            item.set_color(INK)
            item.set_linewidth(1.0)
    for value, text, color in [(0.5, "start 0.5 mg/L", ACCENT), (5.0, "target 5 mg/L", ACCENT_DARK)]:
        if value > 0:
            y = math.log10(value)
            ax.axhline(y, color=color, lw=1.7)
            ax.text(len(groups) - 0.55, y + 0.05, text, color=color, fontsize=11.0, fontweight="bold", ha="right", va="bottom")
    if math.isfinite(med) and med > 0:
        ax.text(0.02, 0.96, f"Full-corpus median: {med:.2g} mg/L", transform=ax.transAxes, va="top", fontsize=11.2, color=MUTED)
    ax.set_xticks(positions, [name for name, _ in groups])
    ax.set_ylabel("log10(titer, mg/L)")
    clean_axes(ax, grid=True)
    caption(fig, "Fig. 3 | Titer benchmark by relevance layer. Project markers at 0.5 and 5 mg/L turn the distribution into a design target rather than a generic histogram.")
    pdf.savefig(fig)
    plt.close(fig)


def page_4_conditions(pdf, rows: list[dict[str, str]]) -> None:
    fig = plt.figure(figsize=(14.4, 9.2), facecolor=PAPER)
    yeast_rows = [r for r in rows if is_yeast(r)]
    llps_rows = [r for r in rows if is_llps_enzyme(r)]
    temps = numeric_values(rows, temperature_c)
    phs = numeric_values(rows, ph_value)
    page_title(fig, "pH and temperature migrate as starting priors, not as finished optima", "The apparent 30 deg C and neutral pH preferences are partly host-driven; LLPS-enzyme performance must be re-measured after fusion and condensation.")
    gs = fig.add_gridspec(1, 2, left=0.10, right=0.92, bottom=0.20, top=0.70, wspace=0.30)
    ax1 = fig.add_subplot(gs[0, 0])
    bins_t = np.arange(10, 82, 2)
    normalized_hist_line(ax1, temps, bins_t, SECOND, "All", 1.8)
    normalized_hist_line(ax1, numeric_values(yeast_rows, temperature_c), bins_t, MAIN_DARK, "Yeast", 2.5)
    normalized_hist_line(ax1, numeric_values(llps_rows, temperature_c), bins_t, ACCENT, "LLPS-enzyme", 2.5)
    ax1.axvspan(28, 30, color=ACCENT, alpha=0.16)
    ax1.text(30.7, 0.82, "test around\n28-30 deg C", fontsize=10.9, color=ACCENT_DARK, fontweight="bold")
    ax1.set_xlabel("Temperature (deg C)")
    ax1.set_ylabel("Normalized density")
    ax1.set_title("Temperature prior", loc="left", fontweight="bold")
    ax1.legend(frameon=False, loc="upper right")
    clean_axes(ax1)
    ax2 = fig.add_subplot(gs[0, 1])
    bins_p = np.arange(1, 14.5, 0.5)
    normalized_hist_line(ax2, phs, bins_p, SECOND, "All", 1.8)
    normalized_hist_line(ax2, numeric_values(yeast_rows, ph_value), bins_p, MAIN_DARK, "Yeast", 2.5)
    normalized_hist_line(ax2, numeric_values(llps_rows, ph_value), bins_p, ACCENT, "LLPS-enzyme", 2.5)
    ax2.axvspan(6, 7.5, color=ACCENT, alpha=0.16)
    ax2.text(7.65, 0.82, "neutral\nwindow", fontsize=10.9, color=ACCENT_DARK, fontweight="bold")
    ax2.set_xlabel("pH")
    ax2.set_ylabel("Normalized density")
    ax2.set_title("pH prior", loc="left", fontweight="bold")
    ax2.legend(frameon=False, loc="upper right")
    clean_axes(ax2)
    caption(fig, "Fig. 4 | Condition priors are plotted as normalized curves to compare subsets without letting the largest category dominate. The project should start in the highlighted windows and then re-optimize for LLPS state and enzyme activity.")
    pdf.savefig(fig)
    plt.close(fig)


def page_5_llps_design(pdf, rows: list[dict[str, str]]) -> None:
    fig = plt.figure(figsize=(14.4, 9.2), facecolor=PAPER)
    high = [r for r in rows if low(r.get("llps_transferability_class")) == "high_transferability"]
    page_title(fig, "LLPS is useful only when trigger, partition and activity are co-designed", "The database separates transferable LLPS triggers from generic condensate biology, then maps likely defects to measurable design knobs.")
    gs = fig.add_gridspec(1, 2, left=0.16, right=0.94, bottom=0.20, top=0.70, wspace=0.40)
    ax1 = fig.add_subplot(gs[0, 0])
    triggers = Counter(trigger_label(r.get("llps_project_trigger_class")) for r in high if not unknown(r.get("llps_project_trigger_class")))
    barh(ax1, triggers, set(triggers.keys()), 8)
    ax1.set_title("High-transferability LLPS triggers", loc="left", fontweight="bold")
    ax2 = fig.add_subplot(gs[0, 1])
    risks: Counter[str] = Counter()
    actions: Counter[str] = Counter()
    for row in rows:
        for token in clean(row.get("defect_risk_tags")).split(";"):
            if token and not unknown(token):
                risks[labelize(token)] += 1
        for token in clean(row.get("design_action_tags")).split(";"):
            if token and not unknown(token):
                actions[labelize(token)] += 1
    selected = [
        ("Activity retention", risks.get("Activity Retention Risk", 0), actions.get("Compare Free Vs Llps Enzyme Kinetics", 0)),
        ("Partition selectivity", risks.get("Partition/Selectivity Risk", 0), actions.get("Measure Enzyme/Substrate/Product Partition", 0)),
        ("Fusion/linker", risks.get("Activity Retention Risk", 0), actions.get("Screen Linker/Fusion Orientation", 0)),
        ("Phase properties", risks.get("Partition/Selectivity Risk", 0), actions.get("Tune Condensate Polarity/Charge", 0)),
    ]
    y = np.arange(len(selected))
    risk_vals = [x[1] for x in selected]
    action_vals = [x[2] for x in selected]
    ax2.barh(y - 0.18, risk_vals, height=0.32, color=SECOND, label="risk evidence")
    ax2.barh(y + 0.18, action_vals, height=0.32, color=ACCENT, label="design-action evidence")
    ax2.set_yticks(y, [x[0] for x in selected])
    ax2.set_xlabel("Records")
    ax2.set_title("Defect-to-design evidence", loc="left", fontweight="bold")
    ax2.legend(frameon=False, loc="lower right")
    clean_axes(ax2)
    caption(fig, "Fig. 5 | LLPS trigger classes and design-risk evidence. This figure turns LLPS from a descriptive phenotype into a set of testable knobs: trigger choice, enzyme retention, partition and condensate material properties.")
    pdf.savefig(fig)
    plt.close(fig)


def page_6_rules(pdf, rows: list[dict[str, str]]) -> None:
    fig = plt.figure(figsize=(14.4, 9.2), facecolor=PAPER)
    page_title(fig, "The data-driven design rule is multi-objective, not simply 'make more condensate'", "An LLPS-enzyme system should maximize production while constraining catalytic activity, mass transfer, partitioning and host burden.")
    ax = fig.add_axes([0.055, 0.17, 0.89, 0.62])
    ax.axis("off")
    columns = ["Defect exposed by LLPS", "Measure in our system", "Optimization response"]
    x = [0.04, 0.36, 0.69]
    for xpos, col in zip(x, columns):
        ax.text(xpos, 0.94, col, transform=ax.transAxes, fontsize=13.6, fontweight="bold", color=INK)
    rules = [
        ("Activity loss", "free enzyme vs LLPS-enzyme Km, kcat/Km, specific activity", "change fusion site, linker and scaffold density"),
        ("Substrate/product mismatch", "partition coefficient for enzyme, substrate and product", "tune condensate polarity, charge and client motif"),
        ("Slow diffusion", "FRAP recovery, droplet size and time-course lag", "avoid over-stable or over-dense condensates"),
        ("Host burden", "growth, OD600, expression level and puncta count", "reduce induction strength or rebalance expression ratio"),
        ("No catalytic readout", "titer, conversion or activity absent", "keep as mechanism prior, not direct design proof"),
    ]
    for i, (a, b, c) in enumerate(rules):
        y = 0.82 - i * 0.145
        ax.add_patch(Rectangle((0.02, y - 0.052), 0.95, 0.103, transform=ax.transAxes, facecolor="white" if i % 2 else PALE, edgecolor=LINE, lw=0.7))
        ax.text(x[0], y, a, transform=ax.transAxes, va="center", fontsize=12.0, color=ACCENT_DARK, fontweight="bold")
        ax.text(x[1], y, wrap(b, 36), transform=ax.transAxes, va="center", fontsize=11.2, color=INK)
        ax.text(x[2], y, wrap(c, 36), transform=ax.transAxes, va="center", fontsize=11.2, color=INK)
        ax.add_patch(FancyArrowPatch((0.30, y), (0.34, y), transform=ax.transAxes, arrowstyle="-|>", mutation_scale=14, lw=1.15, color=ACCENT))
        ax.add_patch(FancyArrowPatch((0.63, y), (0.67, y), transform=ax.transAxes, arrowstyle="-|>", mutation_scale=14, lw=1.15, color=ACCENT))
    ax.text(0.50, 0.055, "Objective: maximize titer/conversion subject to activity retention, partition compatibility, droplet fluidity and host viability.", transform=ax.transAxes, ha="center", fontsize=13.0, color=ACCENT_DARK, fontweight="bold")
    caption(fig, "Fig. 6 | Design-rule table for an LLPS-enzyme glabridin system. The arrows show the intended reading order: LLPS-specific defect -> project measurement -> engineering response.")
    pdf.savefig(fig)
    plt.close(fig)


def page_7_traceability(pdf, rows: list[dict[str, str]]) -> None:
    fig = plt.figure(figsize=(14.4, 9.2), facecolor=PAPER)
    dois = {low(r.get("doi")) for r in rows if not unknown(r.get("doi"))}
    evidence_rows = sum(1 for r in rows if not unknown(r.get("primary_result_evidence")))
    tier13 = sum(1 for r in rows if str(r.get("project_tier", "")).startswith(("Tier 1", "Tier 2", "Tier 3")))
    page_title(fig, "Traceability makes the database usable as a design-support system", "Each row keeps DOI/title and evidence text, so a design recommendation can be audited back to the literature instead of becoming an opaque LLM answer.")
    ax = fig.add_axes([0.07, 0.22, 0.86, 0.47])
    ax.axis("off")
    nodes = [
        (f"{len(dois):,}", "unique DOI anchors"),
        (f"{len(rows):,}", "structured records"),
        (f"{evidence_rows:,}", "evidence-text rows"),
        (f"{tier13:,}", "Tier 1-3 project records"),
    ]
    xs = np.linspace(0.10, 0.90, len(nodes))
    for i, ((value, label), xpos) in enumerate(zip(nodes, xs)):
        color = ACCENT if i == len(nodes) - 1 else MAIN
        ax.add_patch(Rectangle((xpos - 0.095, 0.36), 0.19, 0.28, transform=ax.transAxes, facecolor="white", edgecolor=color, lw=2.0))
        ax.text(xpos, 0.55, value, transform=ax.transAxes, ha="center", va="center", fontsize=20.0, fontweight="bold", color=ACCENT_DARK if i == len(nodes) - 1 else INK)
        ax.text(xpos, 0.43, label, transform=ax.transAxes, ha="center", va="center", fontsize=11.8, color=MUTED)
        if i < len(nodes) - 1:
            ax.add_patch(FancyArrowPatch((xpos + 0.105, 0.50), (xs[i + 1] - 0.105, 0.50), transform=ax.transAxes, arrowstyle="-|>", mutation_scale=18, lw=1.7, color=ACCENT if i == 2 else MUTED))
    caption(fig, "Fig. 7 | Literature-to-record evidence chain. The same structure now supports the new QA module: retrieve relevant rows, summarize design advice and expose DOI/title/evidence provenance.")
    pdf.savefig(fig)
    plt.close(fig)


def generate() -> dict[str, object]:
    setup_style()
    rows = read_rows()
    with PdfPages(OUT) as pdf:
        page_1_database(pdf, rows)
        page_2_host_product(pdf, rows)
        page_3_titer(pdf, rows)
        page_4_conditions(pdf, rows)
        page_5_llps_design(pdf, rows)
        page_6_rules(pdf, rows)
        page_7_traceability(pdf, rows)
    summary = {
        "input_csv": str(SRC),
        "output_pdf": str(OUT),
        "pages": 7,
        "records": len(rows),
        "unique_dois": len({low(r.get("doi")) for r in rows if not unknown(r.get("doi"))}),
        "yeast_records": sum(1 for r in rows if is_yeast(r)),
        "glabridin_records": sum(1 for r in rows if is_glabridin(r)),
        "llps_records": sum(1 for r in rows if is_llps(r)),
        "style": "Morandi palette; one muted main color plus one project accent; conclusion-style page titles.",
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    summary = generate()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Wrote: {OUT}")


if __name__ == "__main__":
    main()

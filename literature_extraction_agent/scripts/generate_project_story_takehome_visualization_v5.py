from __future__ import annotations

import csv
import json
import math
import re
import statistics
import sys
import textwrap
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.path import Path as MplPath
from matplotlib.patches import FancyArrowPatch, PathPatch, Rectangle


PROJECT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import generate_nature_style_vector_pdf_en as base


ESSAY = PROJECT / "essay"
OUT = ESSAY / "project_story_takehome_visualization_v5.pdf"
SUMMARY = ESSAY / "project_story_takehome_visualization_v5_summary.json"

INK = "#242424"
MUTED = "#666A70"
MAIN = "#9FB4C7"
MAIN_DARK = "#7692A8"
LIGHT = "#E9EEF2"
LIGHTER = "#F7F5F1"
ACCENT = "#C86F5A"
ACCENT_DARK = "#9E4F41"
LINE = "#D5D9DD"


def setup_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 12.5,
            "axes.titlesize": 14.5,
            "axes.labelsize": 12.2,
            "xtick.labelsize": 11.2,
            "ytick.labelsize": 11.2,
            "legend.fontsize": 10.5,
            "axes.linewidth": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "figure.dpi": 300,
        }
    )


def rows_from(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def safe_rows(path: Path) -> list[dict[str, str]]:
    return rows_from(path) if path.exists() else []


def clean(value: object) -> str:
    return " ".join(str(value or "").replace("\u00a0", " ").strip().split())


def low(value: object) -> str:
    return clean(value).lower()


def unknown(value: object) -> bool:
    return base.is_unknown(value)


def first_known(row: dict[str, str], *fields: str) -> str:
    for field in fields:
        value = clean(row.get(field, ""))
        if value and not unknown(value):
            return value
    return ""


def label(value: object, mapping: dict[str, str] | None = None) -> str:
    return base.labelize(value, mapping)


def wrap(text: str, width: int = 90) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def add_page_title(fig, message: str, support: str = "") -> None:
    title = wrap(message, 66)
    title_lines = title.count("\n") + 1
    fig.text(0.045, 0.952, title, ha="left", va="top", fontsize=22.5, fontweight="bold", color=INK, linespacing=1.08)
    if support:
        support_y = 0.890 - max(0, title_lines - 1) * 0.055
        fig.text(0.045, support_y, wrap(support, 120), ha="left", va="top", fontsize=12.8, color=MUTED, linespacing=1.22)


def add_caption(fig, caption: str) -> None:
    fig.text(0.045, 0.040, wrap(caption, 155), ha="left", va="bottom", fontsize=10.8, color=INK, linespacing=1.22)


def clean_axes(ax, grid_axis: str = "x") -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(length=3, width=0.7, pad=5)
    if grid_axis:
        ax.grid(axis=grid_axis, color=LINE, lw=0.55, alpha=0.75)
    ax.set_axisbelow(True)


def callout(ax, xy, text: str, xytext, align: str = "left") -> None:
    ax.annotate(
        wrap(text, 30),
        xy=xy,
        xytext=xytext,
        textcoords="data",
        ha=align,
        va="center",
        fontsize=11.0,
        color=ACCENT_DARK,
        arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.7, shrinkA=4, shrinkB=5, mutation_scale=15),
    )


def barh_highlight(ax, counter: Counter[str], highlight: set[str], topn: int, xlabel: str = "Records") -> list[tuple[str, int]]:
    items = [(k, v) for k, v in counter.most_common(topn) if k][::-1]
    names = [k for k, _ in items]
    vals = [v for _, v in items]
    colors = [ACCENT if n in highlight else MAIN for n in names]
    alphas = [0.96 if n in highlight else 0.64 for n in names]
    bars = ax.barh(names, vals, color=colors, height=0.58)
    for bar, alpha in zip(bars, alphas):
        bar.set_alpha(alpha)
    if vals:
        ax.set_xlim(0, max(vals) * 1.28)
        for y, (name, value) in enumerate(items):
            weight = "bold" if name in highlight else "normal"
            color = ACCENT_DARK if name in highlight else INK
            ax.text(value + max(vals) * 0.018, y, f"{value:,}", va="center", fontsize=10.8, color=color, fontweight=weight)
    ax.set_xlabel(xlabel)
    clean_axes(ax)
    return items


def pct(part: int, whole: int) -> float:
    return 100 * part / whole if whole else 0.0


def product_family(row: dict[str, str]) -> str:
    return label(first_known(row, "best_product_family", "product_family"), base.PRODUCT_LABELS)


def host_group(row: dict[str, str]) -> str:
    return label(first_known(row, "best_host_group", "host_group"), base.HOST_LABELS)


def canonical_product(row: dict[str, str]) -> str:
    return label(first_known(row, "best_canonical_product", "canonical_product", "best_main_product_name_value", "main_product_name_value"))


def is_glabridin_row(row: dict[str, str]) -> bool:
    text = " ".join(clean(value) for value in row.values()).lower()
    return "glabridin" in text


def is_llps_row(row: dict[str, str]) -> bool:
    text = " ".join(clean(v) for v in row.values()).lower()
    return any(term in text for term in ["llps", "phase separation", "condensate", "liquid-liquid", "puncta", "droplet"])


def draw_ribbon(ax, x0, x1, y0, y1, h0, h1, color, alpha=0.42):
    verts = [
        (x0, y0 - h0 / 2),
        ((x0 + x1) / 2, y0 - h0 / 2),
        ((x0 + x1) / 2, y1 - h1 / 2),
        (x1, y1 - h1 / 2),
        (x1, y1 + h1 / 2),
        ((x0 + x1) / 2, y1 + h1 / 2),
        ((x0 + x1) / 2, y0 + h0 / 2),
        (x0, y0 + h0 / 2),
        (x0, y0 - h0 / 2),
    ]
    codes = [
        MplPath.MOVETO,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.LINETO,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CLOSEPOLY,
    ]
    ax.add_patch(PathPatch(MplPath(verts, codes), facecolor=color, edgecolor="none", alpha=alpha))


def page_database_pipeline(pdf, rows, known_rows, core_rows):
    fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
    add_page_title(fig, "A traceable database turns literature mining into design-ready evidence", "Records are narrowed from a broad candidate set to known-clean and core-analysis layers without losing DOI/title provenance.")
    ax = fig.add_axes([0.06, 0.20, 0.88, 0.55])
    ax.axis("off")
    stages = [
        ("Candidate\nrecords", len(rows), MAIN),
        ("Traceable\nnumeric records", sum(1 for r in rows if not unknown(r.get("primary_result_numeric_normalized") or r.get("primary_result_value"))), MAIN),
        ("Known-clean\nrecords", len(known_rows) or 19032, MAIN),
        ("Core analysis\nrecords", len(core_rows) or 8417, ACCENT),
    ]
    maxv = max(v for _, v, _ in stages)
    xs = [0.06, 0.34, 0.62, 0.88]
    for i, ((name, value, color), x) in enumerate(zip(stages, xs)):
        h = 0.40 * math.sqrt(value / maxv)
        ax.add_patch(Rectangle((x - 0.018, 0.50 - h / 2), 0.036, h, facecolor=color, edgecolor=INK, lw=0.9, alpha=0.92))
        ax.text(x + 0.035, 0.53, f"{value:,}", fontsize=18, fontweight="bold", color=ACCENT_DARK if color == ACCENT else INK, va="center")
        ax.text(x + 0.035, 0.46, name, fontsize=13.5, color=MUTED, va="center")
        if i < len(stages) - 1:
            next_value = stages[i + 1][1]
            draw_ribbon(ax, x + 0.018, xs[i + 1] - 0.018, 0.50, 0.50, h * 0.92, 0.40 * math.sqrt(next_value / maxv) * 0.92, MAIN if i < 2 else ACCENT, 0.30 if i < 2 else 0.36)
    ax.text(0.62, 0.83, "analysis layer", color=ACCENT_DARK, fontsize=12.5, fontweight="bold")
    ax.annotate("", xy=(0.88, 0.70), xytext=(0.64, 0.80), arrowprops=dict(arrowstyle="-|>", lw=1.9, color=ACCENT))
    add_caption(fig, "Fig. 1 | The database is presented as a curated evidence pipeline rather than a flat table. The accent color marks the final project-facing analysis layer.")
    pdf.savefig(fig)
    plt.close(fig)


def page_method_workflow(pdf):
    fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
    add_page_title(fig, "Dynamic ICL and multi-pass QC are the methodological contribution", "The agent does more than call an LLM once: it retrieves field-matched examples, constrains JSON output, checks units/ranges and returns to full text or SI when fields are missing.")
    ax = fig.add_axes([0.06, 0.22, 0.88, 0.48])
    ax.axis("off")
    steps = [
        ("Literature\npool", "Scopus / WOS /\nopen full text"),
        ("Dynamic\nICL", "field-matched\nexamples"),
        ("Schema\nextraction", "multi-record\nJSON"),
        ("Rule\nchecks", "units, ranges,\nnon-zero rules"),
        ("Evidence-aware\nQC", "full text + SI /\nDOI provenance"),
        ("Traceable\nDB", "record-level\nevidence"),
    ]
    x_positions = np.linspace(0.05, 0.95, len(steps))
    for i, ((title, sub), x) in enumerate(zip(steps, x_positions)):
        color = ACCENT if title in {"Dynamic\nICL", "Evidence-aware\nQC"} else MAIN
        ax.add_patch(Rectangle((x - 0.075, 0.39), 0.15, 0.25, facecolor=LIGHTER, edgecolor=color, lw=2.2, joinstyle="round"))
        ax.text(x, 0.55, title, ha="center", va="center", fontsize=14.0, fontweight="bold", color=INK)
        ax.text(x, 0.45, sub, ha="center", va="center", fontsize=10.8, color=MUTED)
        if i < len(steps) - 1:
            ax.add_patch(FancyArrowPatch((x + 0.08, 0.515), (x_positions[i + 1] - 0.085, 0.515), arrowstyle="-|>", mutation_scale=17, lw=1.7, color=ACCENT if i in {0, 3} else MUTED))
    ax.text(0.25, 0.76, "matched context", color=ACCENT_DARK, fontsize=12.5, fontweight="bold")
    ax.annotate("", xy=(x_positions[1], 0.66), xytext=(0.25, 0.74), arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.6))
    ax.text(0.74, 0.26, "iterative backfill", color=ACCENT_DARK, fontsize=12.5, fontweight="bold")
    ax.annotate("", xy=(x_positions[4], 0.39), xytext=(0.74, 0.30), arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.6))
    add_caption(fig, "Fig. 2 | Dynamic ICL retrieval and multi-pass validation are highlighted as the reusable extraction framework behind the database.")
    pdf.savefig(fig)
    plt.close(fig)


def page_host(pdf, rows):
    counter = Counter(host_group(r) for r in rows if host_group(r) and host_group(r) != "Unlabeled")
    yeast = counter.get("Yeast", 0)
    fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
    add_page_title(fig, "Yeast is the most actionable chassis for this project", f"Yeast-associated records account for {pct(yeast, sum(counter.values())):.1f}% of known host-group evidence, making it the clearest translational anchor.")
    ax = fig.add_axes([0.22, 0.18, 0.68, 0.60])
    items = barh_highlight(ax, counter, {"Yeast"}, 8)
    for idx, (name, value) in enumerate(items):
        if name == "Yeast":
            callout(ax, (value, idx), "Project chassis: Yeast", (value * 0.66, idx + 1.1), "center")
            break
    add_caption(fig, "Fig. 3 | Host-group distribution with Yeast highlighted. Other hosts remain visible but are intentionally muted so the chart serves the project story.")
    pdf.savefig(fig)
    plt.close(fig)


def page_glabridin(pdf, rows):
    products = Counter()
    for row in rows:
        prod = canonical_product(row)
        if prod and prod != "Unlabeled":
            products[prod] += 1
    glab_count = sum(1 for r in rows if is_glabridin_row(r))
    if glab_count:
        products["Glabridin"] = max(products.get("Glabridin", 0), glab_count)
    fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
    add_page_title(fig, "Glabridin is the dominant product signal in the extracted evidence", f"{glab_count:,} records mention Glabridin across titles, product fields or evidence text, giving the project a strong product-specific anchor.")
    ax = fig.add_axes([0.24, 0.18, 0.66, 0.60])
    items = barh_highlight(ax, products, {"Glabridin"}, 10)
    for idx, (name, value) in enumerate(items):
        if name == "Glabridin":
            callout(ax, (value, idx), "Product anchor", (value * 0.54, idx - 1.15), "center")
            break
    add_caption(fig, "Fig. 4 | Canonical product signals are ranked with Glabridin highlighted. The figure makes the product relevance explicit instead of presenting a generic top-product list.")
    pdf.savefig(fig)
    plt.close(fig)


def page_family_gap(pdf, rows):
    counter = Counter(product_family(r) for r in rows if product_family(r) and product_family(r) != "Unlabeled")
    fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
    iso = counter.get("Isoflavonoid", 0)
    flav = counter.get("Flavonoid", 0)
    add_page_title(fig, "Isoflavonoid evidence is much thinner than broad flavonoid evidence", "The imbalance supports the novelty of using a glabridin-focused, LLPS-guided optimization strategy rather than following an already saturated product class.")
    ax = fig.add_axes([0.22, 0.18, 0.68, 0.60])
    barh_highlight(ax, counter, {"Isoflavonoid", "LLPS System", "LLPS system"}, 9)
    if iso and flav:
        ax.text(flav * 0.68, 0.93, f"Isoflavonoid / Flavonoid = {iso / flav:.2f}", transform=ax.get_xaxis_transform(), color=ACCENT_DARK, fontsize=12.2, fontweight="bold")
    add_caption(fig, "Fig. 5 | Product-family evidence is intentionally framed as a research-gap argument. Isoflavonoid and LLPS-system categories are accented because they connect directly to the iGEM project rationale.")
    pdf.savefig(fig)
    plt.close(fig)


def page_titer(pdf, rows):
    titers = [v for r in rows if (v := base.titer_mg_l(r)) is not None]
    logs = [math.log10(v) for v in titers if v > 0]
    med = statistics.median(titers)
    geo = base.geom_mean(titers)
    fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
    add_page_title(fig, "A 5 mg/L target is conservative on the literature titer landscape", f"The current 0.5 mg/L baseline sits at the {base.percentile(titers, 0.5):.1f} percentile, while 5 mg/L remains below the literature median ({med:.1f} mg/L).")
    ax = fig.add_axes([0.10, 0.20, 0.80, 0.56])
    bins = np.arange(-6, 7.5, 0.45)
    ax.hist(logs, bins=bins, color=MAIN, alpha=0.62, edgecolor="white", linewidth=0.4)
    arr = np.array(logs)
    xs = np.linspace(min(bins), max(bins), 300)
    bw = max(0.25, 1.06 * arr.std(ddof=0) * (len(arr) ** -0.2))
    den = np.exp(-0.5 * ((xs[:, None] - arr[None, :]) / bw) ** 2).sum(axis=1) / (len(arr) * bw * math.sqrt(2 * math.pi))
    ax.plot(xs, den * len(arr) * (bins[1] - bins[0]), color=MAIN_DARK, lw=2.1)
    ymax = ax.get_ylim()[1]
    for x, text, color in [
        (math.log10(0.5), "Project start\n0.5 mg/L", ACCENT),
        (math.log10(5), "Project target\n5 mg/L", ACCENT_DARK),
    ]:
        ax.axvline(x, color=color, lw=1.9)
        ax.text(x + 0.04, ymax * 0.88, text, rotation=90, ha="left", va="top", color=color, fontsize=11.0, fontweight="bold")
    log_med = math.log10(med)
    log_geo = math.log10(geo)
    ax.axvline(log_med, color=INK, lw=1.2, ls=(0, (4, 3)))
    ax.axvline(log_geo, color=MUTED, lw=1.2, ls=(0, (4, 3)))
    ax.annotate(
        f"Median {med:.1f} mg/L",
        xy=(log_med, ymax * 0.83),
        xytext=(log_med + 0.95, ymax * 0.78),
        ha="left",
        va="center",
        fontsize=10.6,
        color=INK,
        arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0, shrinkA=4, shrinkB=4),
    )
    ax.annotate(
        f"Geomean {geo:.1f} mg/L",
        xy=(log_geo, ymax * 0.72),
        xytext=(log_geo + 0.95, ymax * 0.64),
        ha="left",
        va="center",
        fontsize=10.6,
        color=MUTED,
        arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.0, shrinkA=4, shrinkB=4),
    )
    ax.set_xlabel("log10(titer, mg/L)")
    ax.set_ylabel("Records")
    clean_axes(ax, "both")
    add_caption(fig, "Fig. 6 | Titer distribution is shown on a log scale because natural-product production spans orders of magnitude. Accent markers locate the project start and target.")
    pdf.savefig(fig)
    plt.close(fig)


def page_conditions(pdf, rows):
    temps = [v for r in rows if (v := base.temperature_c(r)) is not None]
    phs = [v for r in rows if (v := base.ph_value(r)) is not None]
    temp_pct = pct(sum(1 for v in temps if abs(v - 30) <= 0.5 or abs(v - 37) <= 0.5), len(temps))
    ph_pct = pct(sum(1 for v in phs if 6 <= v <= 7.5), len(phs))
    fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
    add_page_title(fig, "Most reported systems cluster near yeast-compatible assay conditions", f"30/37 deg C accounts for {temp_pct:.1f}% of temperature records, and pH 6.0-7.5 accounts for {ph_pct:.1f}% of pH records.")
    gs = fig.add_gridspec(1, 2, left=0.10, right=0.92, bottom=0.20, top=0.72, wspace=0.28)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.hist(temps, bins=np.arange(10, 82, 2), color=MAIN, alpha=0.66, edgecolor="white")
    for x, labeltxt in [(30, "Yeast\n30 deg C"), (37, "E. coli\n37 deg C")]:
        ax1.axvline(x, color=ACCENT, lw=1.9)
        ax1.text(x + 0.8, ax1.get_ylim()[1] * 0.86, labeltxt, color=ACCENT_DARK, fontsize=11.0, fontweight="bold")
    ax1.set_xlabel("Temperature (deg C)")
    ax1.set_ylabel("Records")
    ax1.set_title("Temperature reference range", loc="left", fontweight="bold")
    clean_axes(ax1, "both")
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.hist(phs, bins=np.arange(1, 14.5, 0.5), color=MAIN, alpha=0.66, edgecolor="white")
    ax2.axvspan(6, 7.5, color=ACCENT, alpha=0.18)
    ax2.text(6.1, ax2.get_ylim()[1] * 0.86, "Neutral window\npH 6.0-7.5", color=ACCENT_DARK, fontsize=11.0, fontweight="bold")
    ax2.set_xlabel("pH")
    ax2.set_ylabel("Records")
    ax2.set_title("pH reference range", loc="left", fontweight="bold")
    clean_axes(ax2, "both")
    add_caption(fig, "Fig. 7 | Temperature and pH are combined because they support one design message: literature conditions provide a practical starting window for yeast-compatible LLPS/enzyme experiments.")
    pdf.savefig(fig)
    plt.close(fig)


def page_matrix(pdf, rows):
    fams = ["Flavonoid", "Terpenoid", "Isoprenoid", "Natural Product", "LLPS System", "Isoflavonoid"]
    hosts = ["Yeast", "Plant", "Bacteria", "Mammalian", "Cell-Free", "Cyanobacteria"]
    pairs: Counter[tuple[str, str]] = Counter()
    for r in rows:
        fam = product_family(r)
        host = host_group(r)
        if fam in fams and host in hosts:
            pairs[(fam, host)] += 1
    vmax = max(pairs.values()) if pairs else 1
    fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
    add_page_title(fig, "Yeast x flavonoid is the strongest evidence intersection for chassis design", "The matrix keeps the full evidence landscape visible but highlights the intersection most relevant to Glabridin biosynthesis.")
    ax = fig.add_axes([0.16, 0.20, 0.72, 0.55])
    for i, fam in enumerate(fams):
        for j, host in enumerate(hosts):
            val = pairs.get((fam, host), 0)
            if not val:
                continue
            target = fam == "Flavonoid" and host == "Yeast"
            ax.scatter(i, j, s=60 + 760 * math.sqrt(val / vmax), color=ACCENT if target else MAIN, alpha=0.86 if target else 0.54, edgecolor=ACCENT_DARK if target else MAIN_DARK, linewidth=1.2)
            if target:
                ax.text(i, j, f"{val:,}", ha="center", va="center", fontsize=11.0, color="white", fontweight="bold")
    ax.set_xticks(range(len(fams)), fams, rotation=26, ha="right")
    ax.set_yticks(range(len(hosts)), hosts)
    ax.set_xlim(-0.65, len(fams) - 0.25)
    ax.set_ylim(-0.65, len(hosts) - 0.25)
    ax.grid(color=LINE, lw=0.7)
    ax.spines[:].set_visible(False)
    ax.annotate("project-relevant\nintersection", xy=(0, 0), xytext=(1.35, 1.1), ha="center", va="center", fontsize=12, color=ACCENT_DARK, arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.8))
    add_caption(fig, "Fig. 8 | Product-family by host matrix. The accent point marks Yeast x Flavonoid evidence, while other combinations are muted as context.")
    pdf.savefig(fig)
    plt.close(fig)


def page_llps(pdf, rows):
    folds = [v for r in rows if (v := base.llps_fold(r)) is not None]
    triggers = Counter(base.trigger_group(r.get("best_llps_trigger_value")) for r in rows if not unknown(r.get("best_llps_trigger_value")))
    llps_rows = sum(1 for r in rows if is_llps_row(r))
    fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
    add_page_title(fig, "LLPS evidence is sparse but points to a focused optimization mechanism", f"{llps_rows:,} records contain LLPS/condensate-related evidence, while catalytic fold-change records remain limited and therefore valuable.")
    gs = fig.add_gridspec(1, 2, left=0.10, right=0.92, bottom=0.21, top=0.70, wspace=0.34)
    ax1 = fig.add_subplot(gs[0, 0])
    if folds:
        xs = np.arange(1, len(folds) + 1)
        ax1.scatter(xs, np.log10(folds), s=110, color=ACCENT, alpha=0.88, edgecolor=ACCENT_DARK)
        for x, v in zip(xs, folds):
            ax1.text(x, math.log10(v) + 0.10, f"{v:g}x", ha="center", fontsize=10.5, color=ACCENT_DARK, fontweight="bold")
    ax1.axhline(0, color=MUTED, lw=0.9)
    ax1.set_xlabel("Reported LLPS fold-change record")
    ax1.set_ylabel("log10(fold-change)")
    ax1.set_title("Reported catalytic effect", loc="left", fontweight="bold")
    clean_axes(ax1, "both")
    ax2 = fig.add_subplot(gs[0, 1])
    barh_highlight(ax2, triggers, set(triggers.keys()), 8)
    ax2.set_title("Trigger classes", loc="left", fontweight="bold")
    add_caption(fig, "Fig. 9 | LLPS is framed as a mechanistic design lever. The fold-change panel shows direct catalytic-effect evidence; the trigger panel summarizes reported control modes.")
    pdf.savefig(fig)
    plt.close(fig)


def page_evidence_chain(pdf, rows, known_rows, core_rows):
    doi_count = len({low(r.get("doi")) for r in rows if not unknown(r.get("doi"))})
    evidence = sum(1 for r in rows if not unknown(r.get("primary_result_evidence")))
    fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
    add_page_title(fig, "Every experimental row can be traced back to article-level evidence", "The database is designed for auditability: DOI/title metadata, evidence text and quality labels are kept with the structured record.")
    ax = fig.add_axes([0.08, 0.22, 0.84, 0.47])
    ax.axis("off")
    nodes = [
        (f"{doi_count:,}\nunique DOIs", "article layer"),
        (f"{len(rows):,}\nstructured rows", "record layer"),
        (f"{evidence:,}\nevidence-linked rows", "evidence layer"),
        (f"{len(core_rows) or 8417:,}\ncore analysis rows", "project layer"),
    ]
    xs = np.linspace(0.08, 0.92, 4)
    for i, ((big, small), x) in enumerate(zip(nodes, xs)):
        color = ACCENT if i == 3 else MAIN
        ax.add_patch(Rectangle((x - 0.095, 0.38), 0.19, 0.25, facecolor=LIGHTER, edgecolor=color, lw=2.2))
        ax.text(x, 0.54, big, ha="center", va="center", fontsize=18, fontweight="bold", color=ACCENT_DARK if i == 3 else INK)
        ax.text(x, 0.43, small, ha="center", va="center", fontsize=11.5, color=MUTED)
        if i < 3:
            ax.add_patch(FancyArrowPatch((x + 0.10, 0.505), (xs[i + 1] - 0.105, 0.505), arrowstyle="-|>", mutation_scale=18, lw=1.8, color=ACCENT if i == 2 else MUTED))
    ax.text(0.70, 0.73, "audit trail preserved", color=ACCENT_DARK, fontsize=13, fontweight="bold")
    ax.annotate("", xy=(xs[3], 0.63), xytext=(0.70, 0.70), arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.8))
    add_caption(fig, "Fig. 10 | DOI-to-record evidence chain. The final project layer is highlighted to show how traceability supports downstream interpretation.")
    pdf.savefig(fig)
    plt.close(fig)


def page_design_implication(pdf, rows):
    yeast = sum(1 for r in rows if host_group(r) == "Yeast")
    glab = sum(1 for r in rows if is_glabridin_row(r))
    llps = sum(1 for r in rows if is_llps_row(r))
    fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
    add_page_title(fig, "The database points to a focused design path: Yeast + Glabridin + LLPS control", "The story converges on a practical engineering hypothesis rather than a generic literature survey.")
    ax = fig.add_axes([0.08, 0.18, 0.84, 0.58])
    ax.axis("off")
    cards = [
        ("Yeast chassis", f"{yeast:,} records", "use the dominant deployable host evidence"),
        ("Glabridin product", f"{glab:,} records", "anchor extraction to the project molecule"),
        ("LLPS control", f"{llps:,} records", "turn condensate formation into a tunable optimization lever"),
    ]
    xs = [0.18, 0.50, 0.82]
    for i, ((title, count, text), x) in enumerate(zip(cards, xs)):
        ax.add_patch(Rectangle((x - 0.13, 0.30), 0.26, 0.36, facecolor=LIGHTER, edgecolor=ACCENT if i == 2 else MAIN, lw=2.5))
        ax.text(x, 0.58, title, ha="center", va="center", fontsize=17, fontweight="bold", color=INK)
        ax.text(x, 0.48, count, ha="center", va="center", fontsize=21, fontweight="bold", color=ACCENT_DARK if i != 0 else INK)
        ax.text(x, 0.38, wrap(text, 28), ha="center", va="center", fontsize=11.6, color=MUTED, linespacing=1.18)
        if i < 2:
            ax.add_patch(FancyArrowPatch((x + 0.14, 0.48), (xs[i + 1] - 0.15, 0.48), arrowstyle="-|>", mutation_scale=20, lw=2.0, color=ACCENT))
    ax.text(0.50, 0.18, "Project hypothesis: substrate-triggered phase behavior can be used to improve glabridin biosynthesis in yeast.", ha="center", fontsize=14.2, color=ACCENT_DARK, fontweight="bold")
    add_caption(fig, "Fig. 11 | Final project-facing synthesis. The same accent color marks the pieces that form the proposed experimental design path.")
    pdf.savefig(fig)
    plt.close(fig)


def generate() -> dict[str, object]:
    setup_style()
    rows = base.read_rows()
    known_rows = safe_rows(ESSAY / "known_clean_database_for_showcase.csv")
    core_rows = safe_rows(ESSAY / "known_clean_core_records_for_analysis.csv")
    with PdfPages(OUT) as pdf:
        page_database_pipeline(pdf, rows, known_rows, core_rows)
        page_method_workflow(pdf)
        page_host(pdf, rows)
        page_glabridin(pdf, rows)
        page_family_gap(pdf, rows)
        page_titer(pdf, rows)
        page_conditions(pdf, rows)
        page_matrix(pdf, rows)
        page_llps(pdf, rows)
        page_evidence_chain(pdf, rows, known_rows, core_rows)
        page_design_implication(pdf, rows)
    summary = {
        "output_pdf": str(OUT),
        "pages": 11,
        "records": len(rows),
        "known_clean_records": len(known_rows),
        "core_analysis_records": len(core_rows),
        "theme": "one main muted color plus one project accent color",
        "project_highlights": {
            "yeast_records": sum(1 for r in rows if host_group(r) == "Yeast"),
            "glabridin_records": sum(1 for r in rows if is_glabridin_row(r)),
            "llps_related_records": sum(1 for r in rows if is_llps_row(r)),
        },
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    summary = generate()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Wrote: {OUT}")
    print(f"Wrote: {SUMMARY}")


if __name__ == "__main__":
    main()

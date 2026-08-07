from __future__ import annotations

import csv
import json
import math
import statistics
import sys
import textwrap
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyArrowPatch, Rectangle


PROJECT = Path(r"D:\文献抽取igem")
SCRIPTS = PROJECT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import generate_nature_style_vector_pdf_en as base


ESSAY = PROJECT / "essay"
OUT_CSV = ESSAY / "project_conditioned_evidence_database.csv"
OUT_SUMMARY = ESSAY / "project_conditioned_evidence_summary.json"
OUT_PDF = ESSAY / "project_conditioned_evidence_report_v1.pdf"

INK = "#262626"
MUTED = "#646970"
MAIN = "#9FB4C7"
MAIN_DARK = "#6F8EA6"
LIGHT = "#E8EEF2"
LIGHTER = "#F7F5F1"
ACCENT = "#C86F5A"
ACCENT_DARK = "#9E4F41"
LINE = "#D8DCE0"

UNKNOWN = base.UNKNOWN


def setup_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11.5,
            "axes.titlesize": 13.5,
            "axes.labelsize": 11.8,
            "xtick.labelsize": 10.5,
            "ytick.labelsize": 10.5,
            "legend.fontsize": 10.0,
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


def is_unknown(value: object) -> bool:
    return low(value) in UNKNOWN


def first_known(row: dict[str, str], *fields: str) -> str:
    for field in fields:
        value = clean(row.get(field, ""))
        if value and not is_unknown(value):
            return value
    return ""


def labelize(value: object, mapping: dict[str, str] | None = None) -> str:
    return base.labelize(value, mapping)


def row_text(row: dict[str, str], fields: list[str]) -> str:
    return " ".join(clean(row.get(field, "")) for field in fields).lower()


PRODUCT_FIELDS = [
    "title",
    "title_clean",
    "canonical_product",
    "best_canonical_product",
    "main_product_name_value",
    "best_main_product_name_value",
    "primary_result_evidence",
    "best_main_product_name_evidence",
]

LLPS_FIELDS = [
    "title",
    "title_clean",
    "best_llps_component_value",
    "best_llps_component_evidence",
    "best_llps_state_value",
    "best_llps_state_evidence",
    "best_llps_trigger_value",
    "best_llps_trigger_evidence",
    "primary_result_evidence",
]


def product_family(row: dict[str, str]) -> str:
    return labelize(first_known(row, "best_product_family", "product_family"), base.PRODUCT_LABELS)


def host_group(row: dict[str, str]) -> str:
    return labelize(first_known(row, "best_host_group", "host_group"), base.HOST_LABELS)


def canonical_product(row: dict[str, str]) -> str:
    return labelize(first_known(row, "best_canonical_product", "canonical_product", "best_main_product_name_value", "main_product_name_value"))


def system_type(row: dict[str, str]) -> str:
    return base.normalize_system(first_known(row, "best_reaction_system_type_value", "reaction_system_type_value"))


def metric_name(row: dict[str, str]) -> str:
    return base.metric_name(row)


def is_yeast(row: dict[str, str]) -> bool:
    text = row_text(row, ["best_canonical_host", "canonical_host", "best_expression_host_value", "expression_host_value", "title", "title_clean"])
    return host_group(row) == "Yeast" or "yeast" in text or "saccharomyces" in text


def is_glabridin_direct(row: dict[str, str]) -> bool:
    # Avoid schema_id/source keyword inflation; these fields can mention glabridin for every row.
    return "glabridin" in row_text(row, PRODUCT_FIELDS)


def is_isoflavonoid(row: dict[str, str]) -> bool:
    text = row_text(row, PRODUCT_FIELDS)
    family = product_family(row).lower()
    return family == "isoflavonoid" or "isoflavonoid" in text or "isoflavone" in text or "glabridin" in text


def is_flavonoid_related(row: dict[str, str]) -> bool:
    text = row_text(row, PRODUCT_FIELDS)
    family = product_family(row).lower()
    terms = ["flavonoid", "isoflavonoid", "isoflavone", "glabridin", "naringenin", "anthocyanin", "chalcone", "liquiritigenin"]
    return any(term in family for term in ["flavonoid", "isoflavonoid", "phenylpropanoid", "prenylflavonoid"]) or any(term in text for term in terms)


def is_natural_product(row: dict[str, str]) -> bool:
    family = product_family(row).lower()
    text = row_text(row, PRODUCT_FIELDS + ["primary_result_metric"])
    terms = ["flavonoid", "isoprenoid", "terpenoid", "stilbene", "alkaloid", "anthocyanin", "natural product", "biosynthesis", "titer", "yield"]
    return any(term in family for term in ["flavonoid", "isoprenoid", "terpenoid", "stilbene", "natural product", "phenylpropanoid"]) or any(term in text for term in terms)


def is_llps_related(row: dict[str, str]) -> bool:
    text = row_text(row, LLPS_FIELDS)
    terms = ["llps", "phase separation", "phase-separated", "condensate", "liquid-liquid", "droplet", "puncta", "foci", "granule", "scaffold", "colocalization", "channeling"]
    return any(term in text for term in terms) or not is_unknown(row.get("best_llps_component_value")) or not is_unknown(row.get("best_llps_state_value"))


def has_catalytic_readout(row: dict[str, str]) -> bool:
    metric = low(first_known(row, "primary_result_metric", "schema_id"))
    text = row_text(row, ["primary_result_evidence", "title", "title_clean"])
    terms = ["activity", "specific_activity", "enzyme_activity", "kcat", "km", "kinetic", "conversion", "yield", "titer", "catalytic", "product formation"]
    return any(term in metric for term in terms) or any(term in text for term in terms)


def has_enzyme_context(row: dict[str, str]) -> bool:
    text = row_text(row, ["best_enzyme_name_value", "enzyme_name_value", "title", "title_clean", "primary_result_evidence"])
    return bool(first_known(row, "best_enzyme_name_value", "enzyme_name_value")) or "enzyme" in text or "catalytic" in text


def has_controllable_trigger(row: dict[str, str]) -> bool:
    text = row_text(row, ["best_llps_trigger_value", "best_llps_trigger_evidence", "title", "title_clean", "primary_result_evidence"])
    return any(term in text for term in ["substrate", "ligand", "light", "temperature", "ph", "salt", "concentration", "inducible", "trigger"])


def project_trigger_class(row: dict[str, str]) -> str:
    if not is_llps_related(row):
        return "not_llps"
    text = row_text(row, ["best_llps_trigger_value", "best_llps_trigger_evidence", "title", "title_clean", "primary_result_evidence"])
    if any(term in text for term in ["substrate", "ligand", "client", "product"]):
        return "substrate/ligand responsive"
    if any(term in text for term in ["galactose", "glucose", "induction", "inducible", "nutrient", "starvation", "deprivation"]):
        return "expression or nutrient induction"
    if any(term in text for term in ["concentration", "dosage", "threshold", "overexpression", "expression level"]):
        return "concentration threshold"
    if any(term in text for term in ["ph", "temperature", "heat", "cold"]):
        return "pH or temperature"
    if any(term in text for term in ["salt", "nacl", "peg", "crowding", "calcium", "ca2"]):
        return "ionic strength or crowding"
    if any(term in text for term in ["dna", "damage", "mms", "zeocin", "stress", "hydrogen peroxide", "acetic", "zymolyase"]):
        return "stress/DNA-damage mechanism only"
    if is_llps_related(row):
        return "other reported trigger"
    return "not_llps"


def is_project_compatible_trigger(row: dict[str, str]) -> bool:
    return project_trigger_class(row) in {
        "substrate/ligand responsive",
        "expression or nutrient induction",
        "concentration threshold",
        "pH or temperature",
        "ionic strength or crowding",
    }


def project_flags(row: dict[str, str]) -> list[str]:
    flags: list[str] = []
    if is_yeast(row):
        flags.append("yeast")
    if is_flavonoid_related(row):
        flags.append("flavonoid_related")
    if is_isoflavonoid(row):
        flags.append("isoflavonoid_or_glabridin")
    if is_glabridin_direct(row):
        flags.append("glabridin_direct")
    if is_llps_related(row):
        flags.append("llps_related")
    if is_llps_related(row) and has_enzyme_context(row):
        flags.append("llps_enzyme")
    if is_natural_product(row):
        flags.append("natural_product")
    if has_catalytic_readout(row):
        flags.append("catalytic_readout")
    if is_project_compatible_trigger(row):
        flags.append("project_compatible_llps_trigger")
    return flags


def llps_transfer_score(row: dict[str, str]) -> tuple[int, str]:
    if not is_llps_related(row):
        return 0, "not_llps"
    score = 0
    if has_catalytic_readout(row):
        score += 2
    if has_enzyme_context(row):
        score += 2
    if system_type(row) in {"Whole-cell", "In vivo", "Fermentation"} or is_yeast(row):
        score += 2
    if is_natural_product(row):
        score += 2
    if is_yeast(row) or host_group(row) in {"Yeast", "Mammalian", "Plant"}:
        score += 1
    if base.llps_fold(row) is not None:
        score += 1
    if is_project_compatible_trigger(row):
        score += 2
    elif has_controllable_trigger(row):
        score += 1
    text = row_text(row, ["title", "title_clean", "primary_result_evidence"])
    if any(term in text for term in ["disease", "stress granule", "pathology"]) and not has_catalytic_readout(row):
        score -= 2
    if project_trigger_class(row) == "stress/DNA-damage mechanism only":
        score -= 1
    if not has_catalytic_readout(row):
        score -= 1
    if score >= 7:
        cls = "high_transferability"
    elif score >= 4:
        cls = "medium_transferability"
    else:
        cls = "low_transferability"
    return max(score, 0), cls


def project_tier(row: dict[str, str]) -> str:
    yeast = is_yeast(row)
    flav = is_flavonoid_related(row)
    iso = is_isoflavonoid(row)
    glab = is_glabridin_direct(row)
    llps = is_llps_related(row)
    catalytic = has_catalytic_readout(row)
    score, cls = llps_transfer_score(row)
    if yeast and (glab or iso or flav) and catalytic:
        return "Tier 1 | direct yeast-flavonoid/glabridin evidence"
    if yeast and is_natural_product(row):
        return "Tier 2 | yeast natural-product pathway prior"
    if llps and has_enzyme_context(row) and catalytic:
        return "Tier 3 | LLPS-enzyme catalytic prior"
    if llps and cls in {"high_transferability", "medium_transferability"}:
        return "Tier 4 | transferable LLPS mechanism prior"
    return "Background | broad literature prior"


def defect_tags(row: dict[str, str]) -> list[str]:
    tags: list[str] = []
    text = row_text(row, ["title", "title_clean", "primary_result_evidence", "best_llps_state_evidence", "best_llps_component_evidence"])
    metric = low(first_known(row, "primary_result_metric", "schema_id"))
    if is_llps_related(row):
        if any(term in metric + " " + text for term in ["activity", "kinetic", "kcat", "km", "relative activity", "specific activity"]):
            tags.append("activity-retention risk")
        if any(term in text for term in ["partition", "client", "selectivity", "localization", "colocalization"]):
            tags.append("partition/selectivity risk")
        if any(term in text for term in ["diffusion", "frap", "viscosity", "gel", "solid", "aggregate"]):
            tags.append("mass-transfer/fluidity risk")
        if any(term in text for term in ["toxicity", "growth", "burden", "in vivo", "whole-cell", "fermentation"]):
            tags.append("host-burden risk")
        if not has_catalytic_readout(row):
            tags.append("no catalytic readout")
    if is_yeast(row) and is_natural_product(row):
        tags.append("host-compatible prior")
    return tags or ["background prior only"]


def design_actions(row: dict[str, str]) -> list[str]:
    tags = set(defect_tags(row))
    actions: list[str] = []
    if "activity-retention risk" in tags:
        actions.append("compare free vs LLPS enzyme kinetics")
        actions.append("screen linker/fusion orientation")
    if "partition/selectivity risk" in tags:
        actions.append("measure enzyme/substrate/product partition")
        actions.append("tune condensate polarity/charge")
    if "mass-transfer/fluidity risk" in tags:
        actions.append("include FRAP/droplet-size constraint")
        actions.append("avoid over-dense condensates")
    if "host-burden risk" in tags:
        actions.append("constrain growth and expression burden")
    if "no catalytic readout" in tags:
        actions.append("use as mechanism prior only")
    if "host-compatible prior" in tags:
        actions.append("use as yeast starting condition prior")
    return actions or ["use as background distribution"]


def condition_scope(row: dict[str, str]) -> str:
    if is_yeast(row) and is_llps_related(row):
        return "yeast + LLPS specific starting window"
    if is_yeast(row):
        return "yeast host-compatible prior"
    if is_llps_related(row):
        return "LLPS mechanism prior; retest in yeast"
    return "background prior; do not directly transfer"


def enrich_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        score, cls = llps_transfer_score(row)
        new = dict(row)
        flags = project_flags(row)
        new.update(
            {
                "project_tier": project_tier(row),
                "project_subset_flags": ";".join(flags),
                "llps_transferability_score": str(score),
                "llps_transferability_class": cls,
                "defect_risk_tags": ";".join(defect_tags(row)),
                "design_action_tags": ";".join(design_actions(row)),
                "condition_prior_scope": condition_scope(row),
                "llps_project_trigger_class": project_trigger_class(row),
                "is_project_compatible_llps_trigger": str(is_project_compatible_trigger(row)),
                "is_project_yeast": str(is_yeast(row)),
                "is_project_flavonoid_related": str(is_flavonoid_related(row)),
                "is_project_isoflavonoid_or_glabridin": str(is_isoflavonoid(row)),
                "is_project_glabridin_direct": str(is_glabridin_direct(row)),
                "is_project_llps_related": str(is_llps_related(row)),
                "is_project_llps_enzyme": str(is_llps_related(row) and has_enzyme_context(row)),
                "is_project_high_transfer_llps": str(cls == "high_transferability"),
            }
        )
        out.append(new)
    return out


def write_enriched_csv(rows: list[dict[str, str]]) -> None:
    fields = list(rows[0].keys())
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def wrap(text: str, width: int = 92) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def page_title(fig, title: str, subtitle: str = "") -> None:
    title_wrapped = wrap(title, 72)
    lines = title_wrapped.count("\n") + 1
    fig.text(0.045, 0.952, title_wrapped, ha="left", va="top", fontsize=20.5, fontweight="bold", color=INK, linespacing=1.08)
    if subtitle:
        fig.text(0.045, 0.895 - 0.045 * (lines - 1), wrap(subtitle, 128), ha="left", va="top", fontsize=11.8, color=MUTED, linespacing=1.2)


def caption(fig, text: str) -> None:
    fig.text(0.045, 0.038, wrap(text, 155), ha="left", va="bottom", fontsize=9.8, color=INK, linespacing=1.2)


def clean_axes(ax, grid_axis: str = "x") -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(length=3, width=0.7, pad=5)
    if grid_axis:
        ax.grid(axis=grid_axis, color=LINE, lw=0.55, alpha=0.75)
    ax.set_axisbelow(True)


def barh(ax, counter: Counter[str], highlight: set[str], topn: int = 10) -> None:
    items = [(k, v) for k, v in counter.most_common(topn) if k][::-1]
    labels = [k for k, _ in items]
    values = [v for _, v in items]
    colors = [ACCENT if k in highlight else MAIN for k in labels]
    alphas = [0.95 if k in highlight else 0.58 for k in labels]
    bars = ax.barh(labels, values, color=colors, height=0.58)
    for b, a in zip(bars, alphas):
        b.set_alpha(a)
    if values:
        ax.set_xlim(0, max(values) * 1.28)
        for y, (label, value) in enumerate(items):
            ax.text(value + max(values) * 0.018, y, f"{value:,}", va="center", fontsize=10.0, color=ACCENT_DARK if label in highlight else INK, fontweight="bold" if label in highlight else "normal")
    ax.set_xlabel("Records")
    clean_axes(ax)


def subset(rows: list[dict[str, str]], predicate) -> list[dict[str, str]]:
    return [r for r in rows if predicate(r)]


def numeric_values(rows: list[dict[str, str]], fn) -> list[float]:
    out = []
    for row in rows:
        value = fn(row)
        if value is not None and math.isfinite(value):
            out.append(value)
    return out


def hist_line(ax, values: list[float], bins: np.ndarray, label: str, color: str, alpha: float, lw: float = 2.0) -> None:
    if not values:
        return
    counts, edges = np.histogram(values, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2
    if counts.max() > 0:
        counts = counts / counts.max()
    ax.plot(centers, counts, color=color, lw=lw, alpha=alpha, label=label)


def generate_pdf(rows: list[dict[str, str]]) -> None:
    setup_style()
    all_rows = rows
    yeast_rows = subset(rows, is_yeast)
    yeast_flav_rows = subset(rows, lambda r: is_yeast(r) and is_flavonoid_related(r))
    glab_rows = subset(rows, is_glabridin_direct)
    llps_rows = subset(rows, is_llps_related)
    llps_enzyme_rows = subset(rows, lambda r: is_llps_related(r) and has_enzyme_context(r))
    high_llps_rows = subset(rows, lambda r: llps_transfer_score(r)[1] == "high_transferability")

    with PdfPages(OUT_PDF) as pdf:
        fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
        page_title(fig, "The database is now stratified into project-conditioned evidence layers", "The full corpus remains useful as background, but project claims should come from yeast, glabridin/flavonoid and LLPS-enzyme subsets.")
        ax = fig.add_axes([0.15, 0.20, 0.74, 0.56])
        tier_counts = Counter(project_tier(r) for r in rows)
        tier_order = [
            "Background | broad literature prior",
            "Tier 4 | transferable LLPS mechanism prior",
            "Tier 3 | LLPS-enzyme catalytic prior",
            "Tier 2 | yeast natural-product pathway prior",
            "Tier 1 | direct yeast-flavonoid/glabridin evidence",
        ]
        vals = [tier_counts.get(t, 0) for t in tier_order]
        labels = [t.split("|", 1)[0].strip() for t in tier_order]
        colors = [LIGHT, MAIN, MAIN_DARK, MAIN, ACCENT]
        bars = ax.barh(labels, vals, color=colors, height=0.56)
        for i, (bar, v) in enumerate(zip(bars, vals)):
            ax.text(v + max(vals) * 0.015, bar.get_y() + bar.get_height() / 2, f"{v:,}", va="center", fontsize=10.5, color=ACCENT_DARK if i == 4 else INK, fontweight="bold" if i == 4 else "normal")
        ax.set_xlabel("Records")
        clean_axes(ax)
        caption(fig, "Fig. 1 | Project-tier labels convert the database from a generic evidence pool into a conditional evidence hierarchy. Tier 1-3 should drive project claims; background records provide priors only.")
        pdf.savefig(fig)
        plt.close(fig)

        fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
        page_title(fig, "pH and temperature are host-compatible starting priors, not final LLPS optima", "All-corpus distributions are shown only as context; yeast and LLPS-enzyme subsets define what should be re-tested in the project system.")
        gs = fig.add_gridspec(1, 2, left=0.09, right=0.94, bottom=0.20, top=0.70, wspace=0.30)
        ax1 = fig.add_subplot(gs[0, 0])
        bins_t = np.arange(10, 82, 2)
        hist_line(ax1, numeric_values(all_rows, base.temperature_c), bins_t, "All records", "#BFC8D0", 0.90, 1.8)
        hist_line(ax1, numeric_values(yeast_rows, base.temperature_c), bins_t, "Yeast", MAIN_DARK, 0.95, 2.5)
        hist_line(ax1, numeric_values(llps_enzyme_rows, base.temperature_c), bins_t, "LLPS-enzyme", ACCENT, 0.95, 2.5)
        ax1.axvspan(28, 30, color=ACCENT, alpha=0.16)
        ax1.text(30.5, 0.82, "yeast starting\nwindow", color=ACCENT_DARK, fontsize=10.8, fontweight="bold")
        ax1.set_xlabel("Temperature (deg C)")
        ax1.set_ylabel("Normalized density")
        ax1.set_title("Temperature prior", loc="left", fontweight="bold")
        ax1.legend(frameon=False, loc="upper right")
        clean_axes(ax1, "both")
        ax2 = fig.add_subplot(gs[0, 1])
        bins_p = np.arange(1, 14.5, 0.5)
        hist_line(ax2, numeric_values(all_rows, base.ph_value), bins_p, "All records", "#BFC8D0", 0.90, 1.8)
        hist_line(ax2, numeric_values(yeast_rows, base.ph_value), bins_p, "Yeast", MAIN_DARK, 0.95, 2.5)
        hist_line(ax2, numeric_values(llps_enzyme_rows, base.ph_value), bins_p, "LLPS-enzyme", ACCENT, 0.95, 2.5)
        ax2.axvspan(6, 7.5, color=ACCENT, alpha=0.16)
        ax2.text(7.65, 0.82, "neutral starting\nwindow", color=ACCENT_DARK, fontsize=10.8, fontweight="bold")
        ax2.set_xlabel("pH")
        ax2.set_ylabel("Normalized density")
        ax2.set_title("pH prior", loc="left", fontweight="bold")
        ax2.legend(frameon=False, loc="upper right")
        clean_axes(ax2, "both")
        caption(fig, "Fig. 2 | Conditional distributions prevent over-transfer. The project should use yeast-compatible ranges as starting priors, then re-optimize around LLPS stability and catalytic activity.")
        pdf.savefig(fig)
        plt.close(fig)

        fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
        page_title(fig, "The 5 mg/L target should be judged against yeast-flavonoid evidence, not the full corpus alone", "This reframes the titer benchmark from a broad literature comparison into a project-specific feasibility check.")
        ax = fig.add_axes([0.12, 0.22, 0.76, 0.50])
        groups = [
            ("All", numeric_values(all_rows, base.titer_mg_l)),
            ("Yeast", numeric_values(yeast_rows, base.titer_mg_l)),
            ("Yeast + flavonoid", numeric_values(yeast_flav_rows, base.titer_mg_l)),
            ("Glabridin direct", numeric_values(glab_rows, base.titer_mg_l)),
            ("LLPS-enzyme", numeric_values(llps_enzyme_rows, base.titer_mg_l)),
        ]
        data = [[math.log10(v) for v in vals if v > 0] for _, vals in groups]
        positions = np.arange(len(groups))
        box = ax.boxplot(data, positions=positions, patch_artist=True, widths=0.55, showfliers=False)
        for patch, (name, _) in zip(box["boxes"], groups):
            patch.set_facecolor(ACCENT if name in {"Yeast + flavonoid", "Glabridin direct"} else MAIN)
            patch.set_alpha(0.82 if name in {"Yeast + flavonoid", "Glabridin direct"} else 0.48)
            patch.set_edgecolor(INK)
        for key in ["whiskers", "caps", "medians"]:
            for item in box[key]:
                item.set_color(INK)
                item.set_linewidth(1.0)
        ax.axhline(math.log10(0.5), color=ACCENT, lw=1.6)
        ax.axhline(math.log10(5), color=ACCENT_DARK, lw=1.8)
        ax.text(len(groups) - 0.15, math.log10(0.5) + 0.05, "0.5 mg/L", color=ACCENT, fontsize=10.5, fontweight="bold")
        ax.text(len(groups) - 0.15, math.log10(5) + 0.05, "5 mg/L", color=ACCENT_DARK, fontsize=10.5, fontweight="bold")
        ax.set_xticks(positions, [name for name, _ in groups], rotation=12, ha="right")
        ax.set_ylabel("log10(titer, mg/L)")
        clean_axes(ax, "y")
        caption(fig, "Fig. 3 | Titer is conditionally benchmarked across project-relevant subsets. This makes the target rationale dependent on yeast/flavonoid evidence rather than on unrelated systems.")
        pdf.savefig(fig)
        plt.close(fig)

        fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
        page_title(fig, "LLPS-specific defects can be translated into measurable design rules", "The literature evidence is useful when it is mapped from risk mode to proxy measurement and then to an optimization knob.")
        ax = fig.add_axes([0.05, 0.16, 0.90, 0.63])
        ax.axis("off")
        rows_map = [
            ("Activity loss", "free vs LLPS kcat/Km, Km, Vmax", "fusion site, linker, scaffold density"),
            ("Partition mismatch", "enzyme/substrate/product partition coefficient", "condensate charge, polarity, client motif"),
            ("Mass-transfer limit", "FRAP, droplet size, time-course lag", "avoid over-dense condensates"),
            ("Host burden", "growth, expression, puncta count", "expression ratio, induction strength"),
            ("No catalytic readout", "missing titer/conversion/activity", "mechanism prior only"),
        ]
        colx = [0.04, 0.32, 0.66]
        headers = ["Exposed defect", "Data proxy", "Design response"]
        for x, h in zip(colx, headers):
            ax.text(x, 0.93, h, fontsize=13.5, fontweight="bold", color=INK, transform=ax.transAxes)
        for i, (a, b, c) in enumerate(rows_map):
            y = 0.82 - i * 0.15
            ax.add_patch(Rectangle((0.02, y - 0.055), 0.93, 0.105, transform=ax.transAxes, facecolor=LIGHTER if i % 2 == 0 else "white", edgecolor=LINE, lw=0.8))
            ax.text(colx[0], y, a, fontsize=12.0, color=ACCENT_DARK, fontweight="bold", va="center", transform=ax.transAxes)
            ax.text(colx[1], y, wrap(b, 34), fontsize=11.2, color=INK, va="center", transform=ax.transAxes)
            ax.text(colx[2], y, wrap(c, 34), fontsize=11.2, color=INK, va="center", transform=ax.transAxes)
            ax.add_patch(FancyArrowPatch((0.27, y), (0.30, y), transform=ax.transAxes, arrowstyle="-|>", mutation_scale=14, lw=1.2, color=ACCENT))
            ax.add_patch(FancyArrowPatch((0.61, y), (0.64, y), transform=ax.transAxes, arrowstyle="-|>", mutation_scale=14, lw=1.2, color=ACCENT))
        caption(fig, "Fig. 4 | Defect-to-design map. This table converts LLPS-specific failure modes into assay readouts and optimization rules for the yeast glabridin system.")
        pdf.savefig(fig)
        plt.close(fig)

        fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
        page_title(fig, "Direct Glabridin evidence is separated from broader flavonoid and isoflavonoid priors", "This prevents a glabridin-focused extraction schema from inflating generic product-family conclusions.")
        gs = fig.add_gridspec(1, 2, left=0.10, right=0.92, bottom=0.20, top=0.68, wspace=0.34)
        ax1 = fig.add_subplot(gs[0, 0])
        counts = Counter(
            {
                "Glabridin direct": len(glab_rows),
                "Isoflavonoid/glabridin": len(subset(rows, is_isoflavonoid)),
                "Yeast + flavonoid": len(yeast_flav_rows),
                "LLPS-enzyme": len(llps_enzyme_rows),
                "High-transfer LLPS": len(high_llps_rows),
            }
        )
        barh(ax1, counts, {"Glabridin direct", "High-transfer LLPS"}, 8)
        ax1.set_title("Project sublibrary sizes", loc="left", fontweight="bold")
        ax2 = fig.add_subplot(gs[0, 1])
        families = Counter(product_family(r) for r in yeast_rows if product_family(r) != "Unlabeled")
        barh(ax2, families, {"Flavonoid", "Isoflavonoid", "LLPS System"}, 8)
        ax2.set_title("Yeast product-family priors", loc="left", fontweight="bold")
        caption(fig, "Fig. 5 | Project sublibraries split direct molecule evidence, broader pathway priors and LLPS mechanism priors, making the database easier to use for experimental planning.")
        pdf.savefig(fig)
        plt.close(fig)

        fig = plt.figure(figsize=(14.4, 9.2), facecolor="white")
        page_title(fig, "Only high-transferability LLPS records with compatible triggers should guide design knobs", "Stress and DNA-damage condensates remain useful as mechanism priors, but project knobs should prioritize substrate/ligand response, induction, concentration threshold, pH/temperature and ionic/crowding control.")
        gs = fig.add_gridspec(1, 2, left=0.10, right=0.92, bottom=0.20, top=0.68, wspace=0.34)
        ax1 = fig.add_subplot(gs[0, 0])
        classes = Counter(llps_transfer_score(r)[1] for r in rows)
        order = ["not_llps", "low_transferability", "medium_transferability", "high_transferability"]
        vals = [classes.get(k, 0) for k in order]
        labels = ["Not LLPS", "Low", "Medium", "High"]
        ax1.bar(labels, vals, color=[LIGHT, MAIN, MAIN_DARK, ACCENT], alpha=0.85)
        for i, v in enumerate(vals):
            ax1.text(i, v + max(vals) * 0.02, f"{v:,}", ha="center", fontsize=10.3, color=ACCENT_DARK if labels[i] == "High" else INK, fontweight="bold" if labels[i] == "High" else "normal")
        ax1.set_ylabel("Records")
        ax1.set_title("LLPS transferability class", loc="left", fontweight="bold")
        clean_axes(ax1, "y")
        ax2 = fig.add_subplot(gs[0, 1])
        compatible_high = [r for r in high_llps_rows if is_project_compatible_trigger(r)]
        triggers = Counter(project_trigger_class(r) for r in compatible_high)
        barh(ax2, triggers, set(triggers.keys()), 8)
        ax2.set_title("Project-compatible triggers in high-transfer LLPS", loc="left", fontweight="bold")
        caption(fig, "Fig. 6 | Transferability scoring filters broad LLPS biology into records that are more likely to inform a yeast enzyme-catalysis system. The trigger panel further excludes stress/DNA-damage-only mechanisms from direct design knobs.")
        pdf.savefig(fig)
        plt.close(fig)


def summarize(rows: list[dict[str, str]]) -> dict[str, object]:
    tier_counts = Counter(r["project_tier"] for r in rows)
    transfer_counts = Counter(r["llps_transferability_class"] for r in rows)
    flags = defaultdict(int)
    for row in rows:
        for flag in row["project_subset_flags"].split(";"):
            if flag:
                flags[flag] += 1
    return {
        "input_csv": str(base.SRC),
        "conditioned_csv": str(OUT_CSV),
        "report_pdf": str(OUT_PDF),
        "records": len(rows),
        "project_tiers": dict(tier_counts),
        "project_subset_flags": dict(sorted(flags.items())),
        "llps_transferability": dict(transfer_counts),
        "note": "Full-corpus distributions are background priors; project claims should use condition-specific subsets.",
    }


def main() -> None:
    rows = base.read_rows()
    enriched = enrich_rows(rows)
    write_enriched_csv(enriched)
    generate_pdf(enriched)
    summary = summarize(enriched)
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Wrote: {OUT_CSV}")
    print(f"Wrote: {OUT_SUMMARY}")
    print(f"Wrote: {OUT_PDF}")


if __name__ == "__main__":
    main()

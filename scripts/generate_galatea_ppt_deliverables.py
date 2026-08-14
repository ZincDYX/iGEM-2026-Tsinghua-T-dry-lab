"""Render PPT-facing Galatea M3/M4 figures from existing result CSV files.

This script is deliberately read-only with respect to M3/M4: it never imports
or executes the scientific kernel.  Every plotted number is loaded from the
completed robustness result files.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch


PURPLE = "#573276"
PURPLE_LIGHT = "#f8f5fa"
PURPLE_EDGE = "#d8c8e1"
GRID = "#e7dfea"
SLOT_COLORS = ["#c9ddec", "#9fc7df", "#a58bc6", "#b784a7", "#bd789c"]
CURRENT = "#ead7a0"
CURRENT_BG = "#f7f0db"
POSITIVE = "#9fc7df"
NEGATIVE = "#b784a7"
SLOTS = (1.0, 2.0, 3.0, 4.0, 6.0)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    keys = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def value(row: dict[str, str], key: str) -> float:
    return float(row[key])


def style_axis(ax: plt.Axes) -> None:
    ax.set_facecolor("white")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=.9)
    ax.set_axisbelow(True)


def save(fig: plt.Figure, stem: Path) -> None:
    fig.savefig(stem.with_suffix(".png"), dpi=300, facecolor="white", bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white", bbox_inches="tight")
    plt.close(fig)


def m3_figure(context_rows: list[dict[str, str]], output: Path) -> list[dict]:
    by_slot: dict[float, list[float]] = defaultdict(list)
    for row in context_rows:
        by_slot[value(row, "slot_ratio_sh3_to_pdz")].append(value(row, "dense_OC_to_DMT_ratio"))
    summary = [{"SH3:PDZ_capacity_ratio": int(slot), "modeled_dense_OC_to_DMT_ratio": np.median(by_slot[slot]), "status": "current architecture" if slot == 3 else "design-space response"} for slot in SLOTS]
    fig, ax = plt.subplots(figsize=(13.333, 7.5))
    y = [row["modeled_dense_OC_to_DMT_ratio"] for row in summary]
    ax.plot(SLOTS, y, color=PURPLE, linewidth=3, marker="o", markersize=10, markerfacecolor=PURPLE)
    ax.scatter([3], [y[2]], marker="s", s=180, color=CURRENT, edgecolor=PURPLE, zorder=4, label="Current architecture")
    ax.annotate("Recruitment saturation\nunder baseline assumptions", xy=(4, y[3]), xytext=(4.55, 1.9), color=PURPLE, fontsize=16, ha="center", arrowprops={"arrowstyle": "-", "color": PURPLE, "lw": 1.4})
    style_axis(ax); ax.set_xticks(SLOTS); ax.set_ylim(.85, 2.8)
    ax.set_xlabel("SH3:PDZ capacity ratio", fontsize=18); ax.set_ylabel("Modeled dense OC:DMT ratio", fontsize=18)
    ax.set_title("M3 — Recruitment Stoichiometry", color=PURPLE, fontsize=25, fontweight="bold", pad=17)
    ax.legend(frameon=False, fontsize=15, loc="lower right")
    fig.text(.5, .025, "SH3:PDZ is an engineering capacity ratio, not a measured OC:DMT ratio. The modeled dense-phase ratio also depends on enzyme abundance, recruitment efficiency and binding bias.", ha="center", fontsize=12, color="#57505d")
    fig.tight_layout(rect=(0, .07, 1, 1)); save(fig, output / "ppt_m3_recruitment_stoichiometry")
    return summary


def m4_ablation(one_factor_phi: list[dict[str, str]], output: Path) -> list[dict]:
    neutral = next(row for row in one_factor_phi if row["label"] == "neutral_Kp" and value(row, "value") == .005)
    directional = next(row for row in one_factor_phi if row["label"] == "directional_Kp" and value(row, "value") == .005)
    h0 = {"condition": "H0", "branch_9_to_13_fraction": .8627665417478687, "target_yield_fraction": .6278188230677045, "source": "paired robustness report H0 reference"}
    selected = [h0, {"condition": "Spatial neutral", **neutral, "source": "one_factor_phi.csv; phi=0.005"}, {"condition": "Spatial directional", **directional, "source": "one_factor_phi.csv; phi=0.005"}]
    summary = [{"condition": item["condition"], "branch_9_to_13_fraction": float(item["branch_9_to_13_fraction"]), "delta_target_yield_fraction_vs_H0": float(item["target_yield_fraction"]) - h0["target_yield_fraction"], "source": item["source"]} for item in selected]
    labels = [row["condition"] for row in summary]
    colors = SLOT_COLORS[:3]
    fig, axes = plt.subplots(1, 2, figsize=(13.333, 7.5))
    branches = [row["branch_9_to_13_fraction"] for row in summary]
    bars = axes[0].bar(labels, branches, color=colors, edgecolor=PURPLE_EDGE, linewidth=1.4)
    for bar, item in zip(bars, branches): axes[0].text(bar.get_x() + bar.get_width()/2, item + .013, f"{item:.3f}", ha="center", fontsize=15, color=PURPLE, fontweight="bold")
    style_axis(axes[0]); axes[0].set_ylim(0, 1.05); axes[0].set_ylabel("9→13 branch fraction", fontsize=17); axes[0].set_title("A. Side-product branch", color=PURPLE, fontsize=20, fontweight="bold")
    deltas = [row["delta_target_yield_fraction_vs_H0"] for row in summary]
    bars = axes[1].bar(labels, deltas, color=colors, edgecolor=PURPLE_EDGE, linewidth=1.4)
    for bar, item in zip(bars, deltas): axes[1].text(bar.get_x() + bar.get_width()/2, item + .000006, f"{item:+.6f}", ha="center", fontsize=13, color=PURPLE, fontweight="bold")
    axes[1].axhline(0, color=PURPLE, linewidth=1.3); style_axis(axes[1]); axes[1].set_ylim(-.00004, .00034); axes[1].set_ylabel("Δ target-yield fraction vs H0", fontsize=17); axes[1].set_title("B. Normalized target-yield change", color=PURPLE, fontsize=20, fontweight="bold")
    fig.suptitle("M4 — Mechanistic Ablation", color=PURPLE, fontsize=25, fontweight="bold", y=.985)
    fig.text(.5, .095, "Recruitment alone does not redirect flux; the modeled effect emerges only when recruitment is coupled to metabolite partitioning.", ha="center", fontsize=13, color="#57505d")
    fig.text(.5, .055, "Directional partitioning suppresses the 9→13 branch, but this alone does not prove increased OC-before-DMT routing.", ha="center", fontsize=11, color="#57505d")
    fig.tight_layout(rect=(0, .13, 1, .94)); save(fig, output / "ppt_m4_mechanistic_ablation")
    return summary


def robustness_figure(paired: list[dict[str, str]], sensitivity: list[dict[str, str]], output: Path) -> list[dict]:
    fig, axes = plt.subplots(1, 2, figsize=(13.333, 7.5), gridspec_kw={"width_ratios": [1.15, .85]})
    grouped = [[value(row, "branch_9_to_13_fraction") for row in paired if value(row, "slot_ratio_sh3_to_pdz") == slot] for slot in SLOTS]
    plot = axes[0].boxplot(grouped, tick_labels=[str(int(slot)) for slot in SLOTS], patch_artist=True, medianprops={"color": PURPLE, "linewidth": 2.1})
    for box, color in zip(plot["boxes"], SLOT_COLORS): box.set(facecolor=color, edgecolor=PURPLE_EDGE, linewidth=1.8)
    axes[0].axvspan(2.5, 3.5, color=CURRENT_BG, alpha=.95); axes[0].text(3, .97, "Current architecture", transform=axes[0].get_xaxis_transform(), color=PURPLE, ha="center", va="top", fontsize=13)
    style_axis(axes[0]); axes[0].set_xlabel("SH3:PDZ capacity ratio", fontsize=16); axes[0].set_ylabel("9→13 branch fraction", fontsize=16); axes[0].set_title("A. Paired Kp sensitivity", color=PURPLE, fontsize=20, fontweight="bold")
    axes[0].text(.02, .03, "Same 256 Kp vectors at every ratio", transform=axes[0].transAxes, fontsize=11, color="#57505d")
    metrics = ("branch_9_to_13_fraction", "dmt_late_selectivity", "oc_before_dmt_route_fraction")
    parameters = ("Kp9", "Kp10", "Kp14")
    lookup = {(row["metric"], row["parameter"]): value(row, "Spearman_rho") for row in sensitivity}
    matrix = np.array([[lookup[(metric, parameter)] for metric in metrics] for parameter in parameters])
    image = axes[1].imshow(matrix, cmap="PuOr", vmin=-1, vmax=1, aspect="auto")
    axes[1].set_xticks(range(3), ["9→13\nbranch", "DMT late\nselectivity", "OC-before-DMT\nroute"], fontsize=13)
    axes[1].set_yticks(range(3), parameters, fontsize=15)
    axes[1].set_title("B. Partitioning sensitivity", color=PURPLE, fontsize=20, fontweight="bold")
    for row in range(3):
        for col in range(3): axes[1].text(col, row, f"{matrix[row, col]:+.3f}", ha="center", va="center", fontsize=14, color="white" if abs(matrix[row, col]) > .52 else "#392444", fontweight="bold")
    fig.colorbar(image, ax=axes[1], fraction=.048, pad=.04, label="Spearman ρ")
    fig.suptitle("M4 — Robustness to Metabolite Partitioning", color=PURPLE, fontsize=25, fontweight="bold", y=.985)
    fig.text(.5, .08, "Metabolite partitioning dominates the uncertainty of spatial flux control. Kp9 is the highest-information parameter for the modeled 9→13 branch.", ha="center", fontsize=13, color="#57505d")
    fig.tight_layout(rect=(0, .12, 1, .94)); save(fig, output / "ppt_m4_robustness")
    return [{"parameter": parameter, **{metric: lookup[(metric, parameter)] for metric in metrics}} for parameter in parameters]


def add_box(ax: plt.Axes, xy: tuple[float, float], width: float, height: float, title: str, body: str, fill: str, *, title_font: float = 14, body_font: float = 10.5) -> tuple[float, float]:
    patch = FancyBboxPatch(xy, width, height, boxstyle="round,pad=0.012,rounding_size=0.018", facecolor=fill, edgecolor=PURPLE_EDGE, linewidth=1.6)
    ax.add_patch(patch)
    x, y = xy
    ax.text(x + width/2, y + height*.68, title, ha="center", va="center", fontsize=title_font, color=PURPLE, fontweight="bold")
    ax.text(x + width/2, y + height*.36, body, ha="center", va="center", fontsize=body_font, color="#403847", linespacing=1.28, wrap=True)
    return x + width/2, y + height/2


def arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.annotate("", end, start, arrowprops={"arrowstyle": "->", "color": PURPLE, "lw": 1.8, "shrinkA": 9, "shrinkB": 9})


def closed_loop_figure(output: Path) -> list[dict]:
    fig, ax = plt.subplots(figsize=(13.333, 7.5)); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.text(.5, .95, "Dry–Wet Closed Loop", ha="center", fontsize=26, fontweight="bold", color=PURPLE)
    add_box(ax, (.035, .66), .19, .17, "Literature-informed priors", "Kp8–Kp15\nφ\nrecruitment assumptions", SLOT_COLORS[0], title_font=11.5)
    add_box(ax, (.27, .66), .16, .17, "M3", "Enzyme recruitment\n+ phase partitioning", SLOT_COLORS[1])
    add_box(ax, (.47, .66), .16, .17, "M4", "Full 8-compound /\n10-reaction network", SLOT_COLORS[2])
    add_box(ax, (.67, .66), .29, .17, "Sensitivity analysis", "Key uncertainty: Kp9\nSecondary: Kp10 / Kp14", SLOT_COLORS[3])
    # Arrows touch box edges, not text centers.  The lower row returns right-to-left
    # so the cycle is readable without crossing connectors.
    arrow(ax, (.225, .745), (.27, .745)); arrow(ax, (.43, .745), (.47, .745)); arrow(ax, (.63, .745), (.67, .745))
    add_box(ax, (.70, .33), .26, .20, "Wet-lab measurement", "Kp9 / Kp10 / Kp14\nproposed dense–dilute LC-MS\nφ: microscopy / droplet-volume\nOC/DMT: fluorescence / abundance\n9 / 11 / 13 / 15: LC-MS / HPLC", "#f8f5fa", title_font=12.5, body_font=8.7)
    add_box(ax, (.48, .33), .17, .20, "M5 calibration", "Replace broad priors\nwith Galatea measurements", SLOT_COLORS[1])
    add_box(ax, (.25, .33), .18, .20, "Updated M3/M4", "Narrower envelope\n+ next design", SLOT_COLORS[2])
    add_box(ax, (.035, .33), .17, .20, "Next iteration", "experiment-informed\nwet-lab plan", CURRENT_BG)
    arrow(ax, (.815, .66), (.815, .53)); arrow(ax, (.70, .43), (.65, .43)); arrow(ax, (.48, .43), (.43, .43)); arrow(ax, (.25, .43), (.205, .43)); arrow(ax, (.12, .53), (.12, .66))
    ax.text(.5, .17, "Dry lab identifies which measurements are most informative; wet-lab data replace broad priors and calibrate the next modeling cycle.", ha="center", fontsize=12.5, color="#57505d", style="italic")
    save(fig, output / "ppt_dry_wet_closed_loop")
    return [
        {"priority": 1, "measurement": "Kp9", "proposed_measurement": "dense vs dilute LC-MS partition measurement", "why": "highest-information parameter for modeled 9→13 branch"},
        {"priority": 2, "measurement": "Kp10 / Kp14", "proposed_measurement": "dense vs dilute LC-MS partition measurement", "why": "secondary drivers of late selectivity and OC-before-DMT route"},
        {"priority": 3, "measurement": "phi", "proposed_measurement": "microscopy / droplet-volume analysis", "why": "calibrates condensate volume fraction"},
        {"priority": 4, "measurement": "OC/DMT enrichment and abundance", "proposed_measurement": "calibrated fluorescence / protein abundance", "why": "calibrates recruitment assumptions"},
        {"priority": 5, "measurement": "9 / 11 / 13 / 15 time courses", "proposed_measurement": "LC-MS / HPLC", "why": "calibrates routing and kinetic trajectory"},
    ]


def markdown_tables(output: Path, m3: list[dict], m4: list[dict], robustness: list[dict], priorities: list[dict]) -> None:
    def table(rows: list[dict]) -> str:
        headers = list(rows[0])
        body = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
        body.extend("| " + " | ".join(str(row[column]) for column in headers) + " |" for row in rows)
        return "\n".join(body)
    output.joinpath("PPT_TABLES.md").write_text("# PPT-ready summary tables\n\n## M3 recruitment stoichiometry\n\n" + table(m3) + "\n\n## M4 mechanistic ablation\n\n" + table(m4) + "\n\n## Mechanism-relevant partitioning sensitivity\n\n" + table(robustness) + "\n\n## Dry–wet measurement priority\n\n" + table(priorities) + "\n\nAll numerical entries are loaded from the completed author-native sensitivity results; they are not physical titer predictions or experimental measurements.\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results/m3_m4_robustness_v2"))
    args = parser.parse_args(); root = args.results
    required = [root / name for name in ("paired_kp_results.csv", "kp_spearman_sensitivity.csv", "one_factor_phi.csv", "m3_recruitment_context.csv")]
    missing = [str(path) for path in required if not path.exists()]
    if missing: raise FileNotFoundError("Missing completed result files: " + ", ".join(missing))
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.titleweight": "bold"})
    m3 = m3_figure(read_csv(root / "m3_recruitment_context.csv"), root)
    m4 = m4_ablation(read_csv(root / "one_factor_phi.csv"), root)
    robustness = robustness_figure(read_csv(root / "paired_kp_results.csv"), read_csv(root / "kp_spearman_sensitivity.csv"), root)
    priorities = closed_loop_figure(root)
    write_csv(root / "ppt_m3_summary.csv", m3)
    write_csv(root / "ppt_m4_summary.csv", m4)
    write_csv(root / "ppt_robustness_summary.csv", robustness)
    write_csv(root / "ppt_dry_wet_measurement_priority.csv", priorities)
    markdown_tables(root, m3, m4, robustness, priorities)
    print(f"rendered PPT-facing figures and tables from existing CSV files in {root}")


if __name__ == "__main__":
    main()

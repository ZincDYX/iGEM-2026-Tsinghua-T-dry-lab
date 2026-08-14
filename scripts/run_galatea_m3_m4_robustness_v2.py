"""Run the paired Galatea M3/M4 Kp robustness experiment.

This is a sensitivity-design correction, not a new kinetic model.  One
log-uniform Latin-hypercube Kp8--Kp15 vector is evaluated at every SH3:PDZ
capacity ratio, while phi, recruitment fraction, and recruitment bias remain
fixed.  Outputs are author-native and relative only.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import yaml
from scipy.stats import spearmanr

from igem_drylab.full_network import COMPOUNDS, phase_partition
from igem_drylab.galatea_m3_m4 import (
    M3EffectiveRatioInputs,
    load_author_native_reactions,
    run_galatea_full_m4,
    run_m3_effective_ratio,
)


SEED = 20260815
SLOTS = (1.0, 2.0, 3.0, 4.0, 6.0)
METRICS = (
    "target_yield_fraction",
    "branch_9_to_13_fraction",
    "dmt_late_selectivity",
    "early_dmt_fraction",
    "oc_before_dmt_route_fraction",
    "side_product_fraction_13",
    "mass_balance_error",
)
PRIMARY_METRICS = (
    "branch_9_to_13_fraction",
    "target_yield_fraction",
    "dmt_late_selectivity",
    "oc_before_dmt_route_fraction",
)

# M1/M2 presentation palette: pastel blue → lilac → mauve, with plum accents.
PURPLE = "#573276"
PURPLE_LIGHT = "#f8f5fa"
PURPLE_EDGE = "#d8c8e1"
SLOT_COLORS = ["#c9ddec", "#9fc7df", "#a58bc6", "#b784a7", "#bd789c"]
CURRENT_HIGHLIGHT = "#eee6f1"
POSITIVE = "#9fc7df"
NEGATIVE = "#b784a7"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def lhs_log_uniform(rng: np.random.Generator, count: int, lower: float, upper: float) -> np.ndarray:
    """Generate one reproducible LHS column in a log-uniform prior."""
    bins = (np.arange(count) + rng.random(count)) / count
    rng.shuffle(bins)
    return lower * (upper / lower) ** bins


def run_condition(
    *, identifier: str, sample_id: str, phi: float, slot_ratio: float,
    recruited_fraction: float, bias: float, kp: dict[str, float], reactions: tuple,
    initial: dict[str, float], scales: dict[str, float], t_end: float, provenance: str,
) -> tuple[dict, dict, dict]:
    """Run unchanged M3 recruitment and the unchanged full M4 kernel once."""
    m3 = run_m3_effective_ratio(M3EffectiveRatioInputs(
        phi=phi,
        ptr_total=scales["PTR"], pt_total=scales["PT"],
        oc_total=scales["OC"], dmt_total=scales["DMT"],
        slot_ratio_sh3_to_pdz=slot_ratio,
        total_recruited_fraction=recruited_fraction,
        recruitment_bias_oc_vs_dmt=bias,
        metabolite_kp=kp,
    ))
    result = run_galatea_full_m4(
        enzyme_distributions=m3.enzyme_distributions,
        phi=phi,
        metabolite_kp=kp,
        reactions=reactions,
        initial_intracellular=initial,
        t_end=t_end,
        scenario="galatea_spatial",
        unit_mode="author_native_sensitivity",
    )
    dmt_dense = m3.enzyme_distributions["DMT"].dense
    dense_ratio = m3.enzyme_distributions["OC"].dense / dmt_dense if dmt_dense else None
    summary = {
        "experiment": "paired_global_kp_sensitivity_v2",
        "condition_id": identifier,
        "sample_id": sample_id,
        "random_seed": SEED,
        "scenario": "galatea_spatial",
        "unit_mode": "author_native_sensitivity",
        "transport_enabled": False,
        "phi": phi,
        "total_recruited_fraction": recruited_fraction,
        "recruitment_bias_oc_vs_dmt": bias,
        "slot_ratio_sh3_to_pdz": slot_ratio,
        "dense_OC_to_DMT_ratio": dense_ratio if dense_ratio is not None else "unresolved",
        "provenance_status": provenance,
        **{f"Kp{compound}": kp[compound] for compound in COMPOUNDS},
        **{metric: result.diagnostics[metric] for metric in METRICS},
        **{f"integrated_{reaction_id}": value for reaction_id, value in result.flux_integrals.items()},
    }
    m3_row = {
        "condition_id": identifier,
        "sample_id": sample_id,
        "slot_ratio_sh3_to_pdz": slot_ratio,
        "dense_OC_to_DMT_ratio": dense_ratio,
        "OC_dense": m3.enzyme_distributions["OC"].dense,
        "OC_dilute": m3.enzyme_distributions["OC"].dilute,
        "DMT_dense": m3.enzyme_distributions["DMT"].dense,
        "DMT_dilute": m3.enzyme_distributions["DMT"].dilute,
        "OC_recruited_fraction": m3.recruitment.oc_bound / scales["OC"],
        "DMT_recruited_fraction": m3.recruitment.dmt_bound / scales["DMT"],
    }
    return summary, m3_row, result.flux_integrals


def quantile_summary(rows: list[dict], h0: dict) -> list[dict]:
    """Summarise matched samples without presenting prior fractions as confidence."""
    output: list[dict] = []
    for slot in SLOTS:
        group = [row for row in rows if row["slot_ratio_sh3_to_pdz"] == slot]
        for metric in PRIMARY_METRICS:
            values = np.array([row[metric] for row in group], dtype=float)
            output.append({
                "slot_ratio_sh3_to_pdz": slot, "metric": metric, "n_paired_samples": len(values),
                "median": np.median(values), "q25": np.quantile(values, .25),
                "q75": np.quantile(values, .75), "p05": np.quantile(values, .05),
                "p95": np.quantile(values, .95),
                "reference_H0": h0[metric],
                "fraction_sensitivity_samples_showing_improvement": (
                    float(np.mean(values < h0[metric])) if metric == "branch_9_to_13_fraction"
                    else float(np.mean(values > h0[metric]))
                ),
            })
        output.extend([
            {
                "slot_ratio_sh3_to_pdz": slot,
                "metric": "joint_branch_lower_and_yield_not_lower_than_H0",
                "n_paired_samples": len(group),
                "fraction_sensitivity_samples_showing_improvement": float(np.mean([
                    row["branch_9_to_13_fraction"] < h0["branch_9_to_13_fraction"]
                    and row["target_yield_fraction"] >= h0["target_yield_fraction"] for row in group
                ])),
            },
        ])
    return output


def paired_deltas(rows: list[dict], h0: dict) -> list[dict]:
    by_sample = {sample: {row["slot_ratio_sh3_to_pdz"]: row for row in rows if row["sample_id"] == sample}
                 for sample in {row["sample_id"] for row in rows}}
    output: list[dict] = []
    for sample_id, group in by_sample.items():
        current = group[3.0]
        for slot, row in group.items():
            output.append({
                "sample_id": sample_id, "slot_ratio_sh3_to_pdz": slot,
                **{f"delta_{metric}_vs_current_3": row[metric] - current[metric] for metric in PRIMARY_METRICS},
                **{f"delta_{metric}_vs_H0": row[metric] - h0[metric] for metric in PRIMARY_METRICS},
            })
    return output


def spearman_table(rows: list[dict]) -> list[dict]:
    output: list[dict] = []
    # Use the current 3:1 architecture only.  This avoids allowing slot-ratio
    # variation to confound a stated metabolite-partitioning sensitivity ranking.
    rows = [row for row in rows if row["slot_ratio_sh3_to_pdz"] == 3.0]
    for metric in PRIMARY_METRICS:
        for compound in COMPOUNDS:
            rho, p_value = spearmanr(
                [row[f"Kp{compound}"] for row in rows],
                [row[metric] for row in rows],
            )
            output.append({"metric": metric, "parameter": f"Kp{compound}", "Spearman_rho": rho, "p_value": p_value})
    for metric in PRIMARY_METRICS:
        ranked = sorted((row for row in output if row["metric"] == metric), key=lambda row: abs(row["Spearman_rho"]), reverse=True)
        for index, row in enumerate(ranked, start=1):
            row["absolute_rho_rank"] = index
    return output


def configure_axes(ax: plt.Axes) -> None:
    ax.set_facecolor("#ffffff")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e9e1ed", linewidth=.8)
    ax.set_axisbelow(True)


def figures(*, paired: list[dict], m3_stoichiometry: list[dict], one_factor: dict[str, list[dict]], h0: dict, output: Path) -> None:
    figure_dir = output / "figures"; figure_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.titleweight": "bold", "axes.titlecolor": PURPLE})

    # Figure 1: M3 response, independent of biological-performance interpretation.
    reference_rows = m3_stoichiometry
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    values = [next(row["dense_OC_to_DMT_ratio"] for row in reference_rows if row["slot_ratio_sh3_to_pdz"] == slot) for slot in SLOTS]
    ax.plot(SLOTS, values, marker="o", markersize=7, linewidth=2.4, color=PURPLE)
    ax.scatter([3.0], [values[2]], s=95, marker="s", color=SLOT_COLORS[2], zorder=3, label="current architecture")
    configure_axes(ax); ax.set_xticks(SLOTS); ax.set_xlabel("SH3:PDZ capacity ratio"); ax.set_ylabel("Dense OC:DMT ratio")
    ax.set_title("M3 Recruitment Stoichiometry Sensitivity"); ax.legend(frameon=False, loc="upper left")
    fig.tight_layout(); fig.savefig(figure_dir / "m3_recruitment_stoichiometry.png", dpi=240); plt.close(fig)

    # Figure 2: same samples for each slot.
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    grouped = [[row["branch_9_to_13_fraction"] for row in paired if row["slot_ratio_sh3_to_pdz"] == slot] for slot in SLOTS]
    plot = ax.boxplot(grouped, tick_labels=[str(int(slot)) for slot in SLOTS], patch_artist=True, medianprops={"color": PURPLE, "linewidth": 1.8})
    for box, color in zip(plot["boxes"], SLOT_COLORS): box.set(facecolor=color, edgecolor=PURPLE_EDGE)
    ax.axvspan(2.5, 3.5, color=CURRENT_HIGHLIGHT, alpha=.8)
    ax.text(3, .97, "current design", transform=ax.get_xaxis_transform(), ha="center", va="top", color=PURPLE, fontsize=9)
    configure_axes(ax); ax.set_xlabel("SH3:PDZ capacity ratio"); ax.set_ylabel("Branch 9→13 fraction")
    ax.set_title("Paired Kp Sensitivity Across SH3:PDZ Ratios")
    fig.tight_layout(); fig.savefig(figure_dir / "paired_kp_branch_envelope.png", dpi=240); plt.close(fig)

    # Figure 3: pairwise delta from the current 3:1 construct.
    deltas = paired_deltas(paired, h0)
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    grouped = [[row["delta_branch_9_to_13_fraction_vs_current_3"] for row in deltas if row["slot_ratio_sh3_to_pdz"] == slot] for slot in SLOTS]
    plot = ax.boxplot(grouped, tick_labels=[str(int(slot)) for slot in SLOTS], patch_artist=True, medianprops={"color": PURPLE, "linewidth": 1.8})
    for box, color in zip(plot["boxes"], SLOT_COLORS): box.set(facecolor=color, edgecolor=PURPLE_EDGE)
    ax.axhline(0, color=PURPLE, linewidth=1, linestyle="--")
    configure_axes(ax); ax.set_xlabel("SH3:PDZ capacity ratio"); ax.set_ylabel("Δ branch 9→13 fraction vs current 3:1")
    ax.set_title("Paired Change Relative to Current Architecture")
    fig.tight_layout(); fig.savefig(figure_dir / "paired_slot_delta_branch.png", dpi=240); plt.close(fig)

    # Figure 4: retain scale honesty by separating branch fraction from tiny yield change.
    selected = [
        h0,
        next(row for row in one_factor["recruitment_fraction"] if row["label"] == "neutral_Kp" and row["value"] == .7 and row["slot_ratio_sh3_to_pdz"] == 3.0),
        next(row for row in one_factor["recruitment_fraction"] if row["label"] == "directional_Kp" and row["value"] == .7 and row["slot_ratio_sh3_to_pdz"] == 3.0),
    ]
    labels = ["H0", "Spatial neutral", "Spatial directional"]
    fig, (branch_ax, yield_ax) = plt.subplots(1, 2, figsize=(9.6, 4.2))
    branch_ax.bar(labels, [row["branch_9_to_13_fraction"] for row in selected], color=[SLOT_COLORS[0], SLOT_COLORS[1], SLOT_COLORS[2]], edgecolor=PURPLE_EDGE)
    configure_axes(branch_ax); branch_ax.set_ylabel("Branch 9→13 fraction"); branch_ax.set_title("A. Side-product branch")
    yield_delta = [row["target_yield_fraction"] - h0["target_yield_fraction"] for row in selected]
    yield_ax.bar(labels, yield_delta, color=[SLOT_COLORS[0], SLOT_COLORS[1], SLOT_COLORS[2]], edgecolor=PURPLE_EDGE)
    yield_ax.axhline(0, color=PURPLE, linewidth=1); configure_axes(yield_ax); yield_ax.set_ylabel("Δ normalized 15 yield vs H0"); yield_ax.set_title("B. Yield change")
    fig.suptitle("M4 Representative Comparison", color=PURPLE, fontweight="bold", y=1.02)
    fig.tight_layout(); fig.savefig(figure_dir / "m4_representative_comparison.png", dpi=240, bbox_inches="tight"); plt.close(fig)

    # Figure 5: Kp drivers for the two mechanism-relevant outcomes.
    sensitivity = spearman_table(paired)
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.4), sharey=True)
    for ax, metric, title in zip(axes, ("branch_9_to_13_fraction", "oc_before_dmt_route_fraction"), ("Branch 9→13", "OC-before-DMT route")):
        metric_rows = sorted((row for row in sensitivity if row["metric"] == metric), key=lambda row: row["Spearman_rho"])
        ax.barh([row["parameter"] for row in metric_rows], [row["Spearman_rho"] for row in metric_rows], color=[POSITIVE if row["Spearman_rho"] >= 0 else NEGATIVE for row in metric_rows], edgecolor=PURPLE_EDGE)
        ax.axvline(0, color=PURPLE, linewidth=1); configure_axes(ax); ax.set_xlabel("Spearman ρ"); ax.set_title(title)
    fig.suptitle("Metabolite Partitioning Sensitivity", color=PURPLE, fontweight="bold", y=1.02)
    fig.tight_layout(); fig.savefig(figure_dir / "metabolite_kp_sensitivity.png", dpi=240, bbox_inches="tight"); plt.close(fig)
    write_csv(output / "kp_spearman_sensitivity.csv", sensitivity)
    write_csv(output / "paired_kp_deltas.csv", deltas)


def write_report(output: Path, h0: dict, summary: list[dict], sensitivity: list[dict]) -> None:
    best = {metric: max((row for row in sensitivity if row["metric"] == metric), key=lambda row: abs(row["Spearman_rho"])) for metric in PRIMARY_METRICS}
    report = f"""# Galatea M3/M4 paired Kp robustness sensitivity v2

## Scope and data status

This run preserves the unchanged full eight-compound, ten-reaction Galatea kernel, author-native Zhang kinetics, M3 effective-ratio recruitment equation, and Kp prior range. It is an author-native, prior-driven sensitivity analysis: concentrations, rates, and yields are normalized/model-native and are not experimental titers or physical-unit predictions. Transport and temporal DMT gating are disabled in the primary spatial analysis.

The earlier global Kp run remains preserved as `exploratory_global_sensitivity_v1`; its slot ratio, phi, recruitment fraction, and bias were not strictly paired, so it is not used for a causal slot-ratio inference here.

## Paired design

For each of 256 reproducible LHS Kp8--Kp15 vectors over the literature-informed 0.14--35 prior, the identical vector was run at SH3:PDZ 1, 2, 3, 4, and 6. The primary comparison fixes phi=0.005, total recruited fraction=0.7, and OC:DMT recruitment bias=1.0. SH3:PDZ=3 is the current Galatea nominal architecture, not an optimum assumption.

## What the model supports

- The paired dataset supports comparison of modeled slot-ratio response under the stated Kp prior; it does not establish a biological optimum.
- Neutral-Kp and directional-Kp one-factor controls are reported separately from the paired experiment, so their effect direction is not conflated with Kp uncertainty.
- At the current 3:1 architecture, the strongest absolute Spearman driver of the modeled 9→13 branch is {best['branch_9_to_13_fraction']['parameter']} (rho={best['branch_9_to_13_fraction']['Spearman_rho']:.3f}); this is a model sensitivity ranking, not a measured partition coefficient.

## What the model does not support

- It does not predict enzyme activity, absolute glabridin titer, extracellular compound-13 leakage, or a uniquely optimal SH3:PDZ ratio.
- Lower 9→13 is not interpreted alone as intended routing; the report retains late-DMT selectivity, OC-before-DMT route fraction, and integrated R7/R10 fluxes.

## Wet-lab measurements with highest information value

Prioritize phase-partition measurements for the metabolite Kp values ranked highest by absolute Spearman sensitivity, then measure intracellular time courses of compounds 9, 11, 13, and 15. Those measurements are required to calibrate rather than merely stress-test this model.

## H0 reference

H0 homogeneous constitutive: target yield fraction={h0['target_yield_fraction']:.6g}; branch 9→13 fraction={h0['branch_9_to_13_fraction']:.6g}. Fractions in `paired_kp_summary.csv` are *fractions of sensitivity samples showing improvement*, not statistical confidence.
"""
    (output / "M3_M4_ROBUSTNESS_REPORT.md").write_text(report, encoding="utf-8")


def write_figure_captions(output: Path) -> None:
    """Keep slide-facing interpretation separate from the numerical tables."""
    captions = """# Figure captions

**M3 Recruitment Stoichiometry Sensitivity.** Increasing scaffold SH3:PDZ capacity shifts the modeled dense-phase OC:DMT ratio under the effective-ratio recruitment assumption. This is an M3 model-response sanity check, not a biological-performance result.

**Paired Kp Sensitivity Across SH3:PDZ Ratios.** The same 256 Kp8--Kp15 vectors were evaluated at every SH3:PDZ ratio. The highlighted 3:1 condition is the current Galatea nominal architecture, not an optimum assumption.

**Paired Change Relative to Current Architecture.** Each point-wise delta compares the same Kp vector with the current 3:1 architecture; the zero line denotes no modeled change in the 9→13 branch.

**M4 Representative Comparison.** Branch fraction and normalized-yield change are separated to avoid visual exaggeration from their different scales. These are author-native model outputs, not titer or activity measurements.

**Metabolite Partitioning Sensitivity.** Horizontal bars show Spearman correlations at the current 3:1 architecture across the prior-driven Kp samples. Correlations identify model-sensitive partition coefficients, not experimental causality.
"""
    (output / "figure_captions.md").write_text(captions, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=Path("data/galatea_m3_m4_inputs"))
    parser.add_argument("--output", type=Path, default=Path("results/m3_m4_robustness_v2"))
    parser.add_argument("--kp-samples", type=int, default=256)
    args = parser.parse_args()
    if args.kp_samples < 2:
        raise ValueError("--kp-samples must be at least 2")

    priors = load_yaml(args.inputs / "m3_literature_priors.yaml")
    design = load_yaml(args.inputs / "galatea_design_space.yaml")
    author = json.loads((args.inputs / "published_author_native.json").read_text(encoding="utf-8"))
    reactions = load_author_native_reactions(args.inputs / "reaction_network.csv")
    scales = design["enzyme_totals"]
    initial = {key: float(value) for key, value in author["initial_state"]["intracellular"].items()}
    t_end = float(author["total_time"]["value"])
    neutral = {str(key).removeprefix("Kp_"): float(value) for key, value in priors["metabolite_partition"]["neutral_control"].items() if str(key).startswith("Kp_")}
    directional = {str(key).removeprefix("Kp_"): float(value) for key, value in priors["metabolite_partition"]["directional_hypothesis"].items() if str(key).startswith("Kp_")}
    output = args.output; output.mkdir(parents=True, exist_ok=True)

    h0, _, _ = run_condition(identifier="H0_homogeneous_constitutive", sample_id="H0", phi=0.0, slot_ratio=1.0, recruited_fraction=0.0, bias=1.0, kp=neutral, reactions=reactions, initial=initial, scales=scales, t_end=t_end, provenance="published_author_model_plus_assumption_sensitivity")
    paired: list[dict] = []
    m3_rows: list[dict] = []
    rng = np.random.default_rng(SEED)
    prior = priors["metabolite_partition"]["global_prior"]
    kp_matrix = {compound: lhs_log_uniform(rng, args.kp_samples, prior["lower"], prior["upper"]) for compound in COMPOUNDS}
    for index in range(args.kp_samples):
        sample_id = f"kp_{index:03d}"
        kp = {compound: float(kp_matrix[compound][index]) for compound in COMPOUNDS}
        for slot in SLOTS:
            summary, m3_row, _ = run_condition(identifier=f"paired_{sample_id}_slot{int(slot)}", sample_id=sample_id, phi=.005, slot_ratio=slot, recruited_fraction=.7, bias=1.0, kp=kp, reactions=reactions, initial=initial, scales=scales, t_end=t_end, provenance="literature_prior_Kp_LHS_paired_across_slot_ratios")
            paired.append(summary); m3_rows.append(m3_row)

    m3_stoichiometry: list[dict] = []
    for slot in SLOTS:
        m3 = run_m3_effective_ratio(M3EffectiveRatioInputs(
            phi=.005, ptr_total=scales["PTR"], pt_total=scales["PT"], oc_total=scales["OC"], dmt_total=scales["DMT"],
            slot_ratio_sh3_to_pdz=slot, total_recruited_fraction=.7, recruitment_bias_oc_vs_dmt=1.0, metabolite_kp=neutral,
        ))
        m3_stoichiometry.append({
            "slot_ratio_sh3_to_pdz": slot,
            "dense_OC_to_DMT_ratio": m3.enzyme_distributions["OC"].dense / m3.enzyme_distributions["DMT"].dense,
            "phi": .005, "total_recruited_fraction": .7, "recruitment_bias_oc_vs_dmt": 1.0,
            "note": "M3 model-response sanity check; not a biological-performance result",
        })
    one_factor: dict[str, list[dict]] = {"phi": [], "recruitment_fraction": [], "recruitment_bias": []}
    for label, kp in (("neutral_Kp", neutral), ("directional_Kp", directional)):
        for phi in priors["phi"]["grid"]:
            row, _, _ = run_condition(identifier=f"phi_{label}_{phi}", sample_id=f"phi_{label}_{phi}", phi=float(phi), slot_ratio=3.0, recruited_fraction=.7, bias=1.0, kp=kp, reactions=reactions, initial=initial, scales=scales, t_end=t_end, provenance="one_factor_assumption_sensitivity")
            row.update({"label": label, "value": float(phi)}); one_factor["phi"].append(row)
        for fraction in priors["recruitment"]["total_recruited_fraction_grid"]:
            row, _, _ = run_condition(identifier=f"recruitment_fraction_{label}_{fraction}", sample_id=f"recruitment_fraction_{label}_{fraction}", phi=.005, slot_ratio=3.0, recruited_fraction=float(fraction), bias=1.0, kp=kp, reactions=reactions, initial=initial, scales=scales, t_end=t_end, provenance="one_factor_assumption_sensitivity")
            row.update({"label": label, "value": float(fraction)}); one_factor["recruitment_fraction"].append(row)
        for bias in priors["recruitment"]["recruitment_bias_oc_vs_dmt_grid"]:
            row, _, _ = run_condition(identifier=f"recruitment_bias_{label}_{bias}", sample_id=f"recruitment_bias_{label}_{bias}", phi=.005, slot_ratio=3.0, recruited_fraction=.7, bias=float(bias), kp=kp, reactions=reactions, initial=initial, scales=scales, t_end=t_end, provenance="one_factor_assumption_sensitivity")
            row.update({"label": label, "value": float(bias)}); one_factor["recruitment_bias"].append(row)

    summary = quantile_summary(paired, h0)
    sensitivity = spearman_table(paired)
    write_csv(output / "paired_kp_results.csv", paired)
    write_csv(output / "paired_kp_summary.csv", summary)
    write_csv(output / "kp_spearman_sensitivity.csv", sensitivity)
    write_csv(output / "one_factor_phi.csv", one_factor["phi"])
    write_csv(output / "one_factor_recruitment_fraction.csv", one_factor["recruitment_fraction"])
    write_csv(output / "one_factor_recruitment_bias.csv", one_factor["recruitment_bias"])
    write_csv(output / "m3_recruitment_context.csv", m3_rows + m3_stoichiometry)
    figures(paired=paired, m3_stoichiometry=m3_stoichiometry, one_factor=one_factor, h0=h0, output=output)
    write_report(output, h0, summary, sensitivity)
    write_figure_captions(output)
    print(f"completed {len(paired)} paired spatial simulations and {sum(map(len, one_factor.values()))} one-factor simulations in {output}")


if __name__ == "__main__":
    main()

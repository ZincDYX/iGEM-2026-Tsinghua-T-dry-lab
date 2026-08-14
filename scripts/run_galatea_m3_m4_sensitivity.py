"""Run the audited CPU-only Galatea M3/M4 author-native sensitivity package.

This script intentionally writes only ignored local results.  It never maps
author-native inputs to physical units or to experimental titer claims.
"""
from __future__ import annotations

import argparse
import csv
import json
from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import yaml

from igem_drylab.full_network import COMPOUNDS, TemporalGate, phase_partition
from igem_drylab.galatea_m3_m4 import M3EffectiveRatioInputs, load_author_native_reactions, run_galatea_full_m4, run_m3_effective_ratio
from igem_drylab.published_reference import run_published_reference


METRICS = (
    "target_yield_fraction", "branch_9_to_13_fraction", "dmt_late_selectivity",
    "early_dmt_fraction", "oc_before_dmt_route_fraction", "side_product_fraction_13",
    "mass_balance_error",
)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader(); writer.writerows(rows)


def lhs_log_uniform(rng: np.random.Generator, count: int, lower: float, upper: float) -> np.ndarray:
    """One independent Latin-hypercube column in log space."""
    bins = (np.arange(count) + rng.random(count)) / count
    rng.shuffle(bins)
    return lower * (upper / lower) ** bins


def run_condition(*, identifier: str, scenario: str, phi: float, slot_ratio: float,
                  recruited_fraction: float, bias: float, kp: dict[str, float],
                  reactions: tuple, initial: dict[str, float], scales: dict[str, float],
                  t_end: float, temporal: bool = False, provenance: str) -> tuple[dict, list[dict], list[dict], object]:
    m3 = run_m3_effective_ratio(M3EffectiveRatioInputs(
        phi=phi, ptr_total=scales["PTR"], pt_total=scales["PT"], oc_total=scales["OC"], dmt_total=scales["DMT"],
        slot_ratio_sh3_to_pdz=slot_ratio, total_recruited_fraction=recruited_fraction,
        recruitment_bias_oc_vs_dmt=bias, metabolite_kp=kp,
    ))
    gate = TemporalGate(mode="published_delayed_ramp", disable_time=4.0) if temporal else TemporalGate()
    result = run_galatea_full_m4(
        enzyme_distributions=m3.enzyme_distributions, phi=phi, metabolite_kp=kp, reactions=reactions,
        initial_intracellular=initial, t_end=t_end, scenario=scenario, dmt_gate=gate,
        unit_mode="author_native_sensitivity",
    )
    summary = {
        "condition_id": identifier, "scenario": scenario, "phi": phi, "slot_ratio": slot_ratio,
        "total_recruited_fraction": recruited_fraction, "recruitment_bias_oc_vs_dmt": bias,
        "provenance_status": provenance, "unit_mode": "author_native_sensitivity",
        "time_axis": "author_native_day_axis", "transport_enabled": False,
        "dense_OC_to_DMT_ratio": (m3.enzyme_distributions["OC"].dense / m3.enzyme_distributions["DMT"].dense if m3.enzyme_distributions["DMT"].dense else "unresolved"),
        "recruited_OC_fraction": m3.recruitment.oc_bound / scales["OC"],
        "recruited_DMT_fraction": m3.recruitment.dmt_bound / scales["DMT"],
        **{f"Kp_{compound}": kp[compound] for compound in COMPOUNDS},
        **{metric: result.diagnostics[metric] for metric in METRICS},
    }
    enzyme_rows = [
        {"condition_id": identifier, "kind": "enzyme", "species": enzyme, "dense": dist.dense, "dilute": dist.dilute,
         "fraction_in_dense": (phi * dist.dense / scales[enzyme] if scales[enzyme] else 0.0), "provenance_status": provenance}
        for enzyme, dist in m3.enzyme_distributions.items()
    ]
    metabolite_rows = [
        {"condition_id": identifier, "kind": "metabolite_initial_state", "species": compound,
         "dense": phase_partition(initial[compound], kp[compound], phi).dense,
         "dilute": phase_partition(initial[compound], kp[compound], phi).dilute,
         "fraction_in_dense": (phi * phase_partition(initial[compound], kp[compound], phi).dense / initial[compound] if initial[compound] else 0.0),
         "provenance_status": provenance}
        for compound in COMPOUNDS
    ]
    recruitment_rows = [{"condition_id": identifier, "enzyme": "OC", "bound": m3.recruitment.oc_bound, "fraction": m3.recruitment.oc_bound / scales["OC"], "target_ratio": m3.recruitment.target_ratio},
                        {"condition_id": identifier, "enzyme": "DMT", "bound": m3.recruitment.dmt_bound, "fraction": m3.recruitment.dmt_bound / scales["DMT"], "target_ratio": m3.recruitment.target_ratio}]
    return summary, enzyme_rows + metabolite_rows, recruitment_rows, result


def save_reference(repo: Path, output: Path) -> None:
    reference = run_published_reference(repo)
    rows = []
    for index, time in enumerate(reference.time):
        rows.append({"time_author_native_day_axis": time, **{f"intracellular_{compound}": reference.state[col, index] for col, compound in enumerate(COMPOUNDS)}, **{f"extracellular_{compound}": reference.state[col + 8, index] for col, compound in enumerate(COMPOUNDS)}})
    write_csv(output / "m4" / "published_reference_trajectory.csv", rows)
    write_csv(output / "m4" / "published_reference_flux_or_rate_summary.csv", [{"status": "not_recomputed", "reason": "immutable_author_adapter provides exact state trajectory; fluxes are not inferred into Galatea metrics", "source_sha256": reference.source_sha256}])
    (output / "m4" / "published_reference_validation.md").write_text(
        "# Published reference reproduction\n\nExecuted only through the immutable Zhang author-code adapter on its author-native day axis. This is separate from the Galatea two-phase competitive kernel.\n",
        encoding="utf-8",
    )


def figures(rows: list[dict], output: Path) -> None:
    figure_dir = output / "figures"; figure_dir.mkdir(parents=True, exist_ok=True)
    deterministic = [row for row in rows if row["condition_id"].startswith("galatea_spatial_") and "global_Kp_uncertainty" not in row["condition_id"]]
    slots = sorted({row["slot_ratio"] for row in deterministic})
    means = [np.mean([row["dense_OC_to_DMT_ratio"] for row in deterministic if row["slot_ratio"] == slot]) for slot in slots]
    plt.figure(figsize=(6, 4)); plt.plot(slots, means, marker="o", color="#7663a6"); plt.xlabel("SH3:PDZ capacity ratio"); plt.ylabel("Dense OC:DMT ratio"); plt.title("M3 literature-informed sensitivity"); plt.tight_layout(); plt.savefig(figure_dir / "m3_dense_oc_dmt_vs_slot_ratio.png", dpi=200); plt.close()
    nominal = [row for row in deterministic if row["slot_ratio"] == 3 and row["phi"] == .012 and row["total_recruited_fraction"] == .7 and row["recruitment_bias_oc_vs_dmt"] == 1]
    if nominal:
        labels = ["H0", "Spatial neutral", "Spatial directional"]
        selected = [next(row for row in rows if row["scenario"] == "homogeneous_constitutive"), next(row for row in nominal if "neutral_Kp" in row["condition_id"]), next(row for row in nominal if "directional_Kp" in row["condition_id"])]
        plt.figure(figsize=(7, 4)); x = np.arange(3); plt.bar(x - .18, [row["branch_9_to_13_fraction"] for row in selected], .36, label="Branch 9→13", color="#8bb7a1"); plt.bar(x + .18, [row["target_yield_fraction"] for row in selected], .36, label="Normalized 15 yield", color="#b49bd1"); plt.xticks(x, labels); plt.legend(); plt.title("M4 representative branch comparison"); plt.tight_layout(); plt.savefig(figure_dir / "m4_representative_branch_comparison.png", dpi=200); plt.close()
    global_rows = [row for row in rows if row["condition_id"].startswith("galatea_spatial_global_Kp_uncertainty")]
    if global_rows:
        plt.figure(figsize=(7, 4)); grouped = [[row["branch_9_to_13_fraction"] for row in global_rows if row["slot_ratio"] == slot] for slot in slots]; plt.boxplot(grouped, labels=[str(slot) for slot in slots]); plt.xlabel("SH3:PDZ capacity ratio"); plt.ylabel("Branch 9→13 fraction"); plt.title("Prior-driven Kp sensitivity envelope"); plt.tight_layout(); plt.savefig(figure_dir / "m4_kp_sensitivity_envelope.png", dpi=200); plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, default=Path("data/galatea_m3_m4_inputs"))
    parser.add_argument("--output", type=Path, default=Path("results/galatea_m3_m4_author_native_sensitivity"))
    parser.add_argument("--kp-samples", type=int, default=256)
    args = parser.parse_args(); root = Path(__file__).resolve().parents[1]; output = args.output; output.mkdir(parents=True, exist_ok=True)
    priors, design, author = (load_yaml(args.inputs / "m3_literature_priors.yaml"), load_yaml(args.inputs / "galatea_design_space.yaml"), json.loads((args.inputs / "published_author_native.json").read_text(encoding="utf-8")))
    reactions = load_author_native_reactions(args.inputs / "reaction_network.csv")
    scales = design["enzyme_totals"]; initial = {key: float(value) for key, value in author["initial_state"]["intracellular"].items()}; t_end = float(author["total_time"]["value"])
    save_reference(root, output)
    neutral = {str(key).removeprefix("Kp_"): float(value) for key, value in priors["metabolite_partition"]["neutral_control"].items() if str(key).startswith("Kp_")}
    directional = {str(key).removeprefix("Kp_"): float(value) for key, value in priors["metabolite_partition"]["directional_hypothesis"].items() if str(key).startswith("Kp_")}
    rows: list[dict] = []; phase_rows: list[dict] = []; recruitment_rows: list[dict] = []; trajectory_rows: list[dict] = []
    controls = [("homogeneous_constitutive", "homogeneous_constitutive", 0., False), ("homogeneous_published_like_temporal", "homogeneous_published_like_temporal", 0., True)]
    for identifier, scenario, phi, temporal in controls:
        summary, phases, recruitment, result = run_condition(identifier=identifier, scenario=scenario, phi=phi, slot_ratio=1., recruited_fraction=0., bias=1., kp=neutral, reactions=reactions, initial=initial, scales=scales, t_end=t_end, temporal=temporal, provenance="published_author_model_plus_assumption_sensitivity")
        rows.append(summary); phase_rows.extend(phases); recruitment_rows.extend(recruitment)
    grid = list(product(priors["phi"]["grid"], design["slot_ratio_sweep"]["values"], priors["recruitment"]["total_recruited_fraction_grid"], priors["recruitment"]["recruitment_bias_oc_vs_dmt_grid"]))
    for label, kp in (("neutral_Kp", neutral), ("directional_Kp", directional)):
        for phi, slot, fraction, bias in grid:
            identifier = f"galatea_spatial_{label}_phi{phi}_slot{slot}_rec{fraction}_bias{bias}"
            summary, phases, recruitment, _ = run_condition(identifier=identifier, scenario="galatea_spatial", phi=float(phi), slot_ratio=float(slot), recruited_fraction=float(fraction), bias=float(bias), kp=kp, reactions=reactions, initial=initial, scales=scales, t_end=t_end, provenance="literature_prior_plus_assumption_sensitivity")
            rows.append(summary); phase_rows.extend(phases); recruitment_rows.extend(recruitment)
    rng = np.random.default_rng(20260815); lower, upper = priors["metabolite_partition"]["global_prior"]["lower"], priors["metabolite_partition"]["global_prior"]["upper"]
    kp_matrix = {compound: lhs_log_uniform(rng, args.kp_samples, lower, upper) for compound in COMPOUNDS}; phis = priors["phi"]["grid"]; slots = design["slot_ratio_sweep"]["values"]; fractions = priors["recruitment"]["total_recruited_fraction_grid"]; biases = priors["recruitment"]["recruitment_bias_oc_vs_dmt_grid"]
    for index in range(args.kp_samples):
        kp = {compound: float(kp_matrix[compound][index]) for compound in COMPOUNDS}; summary, phases, recruitment, _ = run_condition(identifier=f"galatea_spatial_global_Kp_uncertainty_{index:03d}", scenario="galatea_spatial", phi=float(phis[index % len(phis)]), slot_ratio=float(slots[index % len(slots)]), recruited_fraction=float(fractions[index % len(fractions)]), bias=float(biases[index % len(biases)]), kp=kp, reactions=reactions, initial=initial, scales=scales, t_end=t_end, provenance="literature_prior_Kp_LHS_plus_assumption_sensitivity")
        rows.append(summary); phase_rows.extend(phases); recruitment_rows.extend(recruitment)
    write_csv(output / "m3" / "m3_conditions.csv", rows); write_csv(output / "m3" / "m3_phase_concentrations.csv", phase_rows); write_csv(output / "m3" / "m3_recruitment.csv", recruitment_rows)
    write_csv(output / "m3" / "m3_assumptions_and_provenance.csv", [{"status": "literature-informed sensitivity", "unit_mode": "author_native_sensitivity", "kinetics": "Zhang author model", "enzyme_scale": "author-native relative scale", "transport": "disabled", "warning": "No Galatea-specific phi/Kp/recruitment measurement is claimed."}])
    write_csv(output / "m4" / "m4_condition_summary.csv", rows); write_csv(output / "m4" / "m4_flux_integrals.csv", [{key: value for key, value in row.items() if key in {"condition_id", "scenario", "phi", "slot_ratio", *METRICS}} for row in rows])
    figures(rows, output)
    (output / "M3_M4_REPORT.md").write_text("# Galatea M3/M4 literature-informed sensitivity\n\nThis CPU-only run uses author-native kinetics and relative enzyme scales. It is a mechanistic sensitivity analysis, not a calibrated titer or activity prediction. Galatea primary comparisons use recruitment stoichiometry plus LLPS partitioning with constitutive DMT; the delayed-DMT condition is a control. Transport is disabled in Galatea author-native sensitivity, so compound-13 extracellular leakage is not interpreted. Required M5 inputs are Galatea phi, protein/metabolite Kp, enzyme abundance/recruitment, phase activity, and HPLC time courses.\n", encoding="utf-8")
    print(f"completed {len(rows)} Galatea conditions in {output}")


if __name__ == "__main__":
    main()

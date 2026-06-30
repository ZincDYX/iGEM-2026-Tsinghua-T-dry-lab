#!/usr/bin/env python
"""Generate expression-ratio and condensate-volume scans for the example model."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from igem_drylab.kinetics import CascadeParameters, simulate_cascade


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/example_sweep"))
    parser.add_argument("--total-enzyme", type=float, default=2.0)
    parser.add_argument("--time", type=float, default=24.0)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    base = CascadeParameters(
        phi=0.05,
        kcat_oc=0.6,
        km_oc=1.5,
        kcat_dmt=1.2,
        km_dmt=0.8,
        partition_oc=50,
        partition_dmt=50,
        partition_a=4,
        partition_b=8,
        kdeg_b=0.02,
    )

    fractions = np.linspace(1 / 11, 10 / 11, 61)
    rows = []
    for oc_fraction in fractions:
        params = replace(
            base,
            oc_total=args.total_enzyme * oc_fraction,
            dmt_total=args.total_enzyme * (1 - oc_fraction),
        )
        result = simulate_cascade(params, t_end=args.time)
        rows.append(
            {
                "oc": params.oc_total,
                "dmt": params.dmt_total,
                "oc_to_dmt": params.oc_total / params.dmt_total,
                "product": result.product[-1],
                "peak_intermediate": result.intermediate.max(),
            }
        )
    ratio_frame = pd.DataFrame(rows)
    ratio_frame.to_csv(args.output / "ratio_scan.csv", index=False)

    enzyme_grid = np.linspace(0.1, args.total_enzyme, 31)
    surface = np.empty((len(enzyme_grid), len(enzyme_grid)))
    for i, oc in enumerate(enzyme_grid):
        for j, dmt in enumerate(enzyme_grid):
            result = simulate_cascade(replace(base, oc_total=oc, dmt_total=dmt), t_end=args.time)
            surface[j, i] = result.product[-1]
    xx, yy = np.meshgrid(enzyme_grid, enzyme_grid)
    figure = plt.figure(figsize=(8, 6))
    axis = figure.add_subplot(111, projection="3d")
    axis.plot_surface(xx, yy, surface, cmap="viridis")
    axis.set(xlabel="OC total", ylabel="DMT total", zlabel="Product")
    figure.tight_layout()
    figure.savefig(args.output / "expression_surface.png", dpi=200)
    plt.close(figure)

    volume_rows = []
    for phi in np.linspace(0, 0.5, 101):
        result = simulate_cascade(replace(base, phi=float(phi)), t_end=args.time)
        volume_rows.append({"phi": phi, "product": result.product[-1]})
    pd.DataFrame(volume_rows).to_csv(args.output / "volume_fraction_scan.csv", index=False)


if __name__ == "__main__":
    main()

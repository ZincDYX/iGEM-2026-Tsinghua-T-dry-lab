# Real metric scoring notes

The pipeline is now designed to stay lightweight. Heavy tools should generate artifacts only when needed; the M1-M4 pipeline should mostly read metric files and score quickly.

## M2 structure score

Input file example:

```text
examples/real_metrics/m2_structure_metrics.json
```

Fields:

- `sasa_retention`: fusion pocket SASA divided by wild-type pocket SASA.
- `pocket_rmsd_angstrom`: active-pocket RMSD after alignment.
- `mean_interdomain_pae`: PAE between linked domains.
- `iptm`: inter-chain or complex confidence.
- `mean_plddt`: local structure confidence.
- `interface_contact_count`: chain-chain contacts.
- `clash_count`: steric clashes.

Current rule-based policy:

- pocket SASA loss above 15% increases activity risk;
- pocket RMSD above 1.5 Å increases activity risk;
- clashes increase clash risk;
- ipTM/pLDDT contribute confidence;
- very low domain-domain PAE can indicate unwanted rigid sticking;
- very high domain-domain PAE can indicate uncertain global placement.

TODO: calibrate thresholds with wet-lab activity and expression data.

## M4 docking and ODE score

Vina output is parsed into best affinity. The docking penalty compares fusion and reference:

```text
ΔΔG = ΔG_fusion - ΔG_reference
```

If fusion docking is worse, the activity multiplier decreases. This is only a screening proxy, not a real enzyme rate.

The lightweight ODE uses `scipy.solve_ivp` and the existing two-phase mass-conserving cascade model. This is intentionally cheap enough to scan many OC:DMT ratios and induction delays later.

TODO: add explicit OC-first/DMT-later piecewise induction schedules.

## Why CALVADOS is not in the default score yet

CALVADOS is useful but expensive and sensitive to simulation setup. It should be used for top candidates or as a validation layer, not every routine pipeline run.

TODO: add a CALVADOS parser after the exact server output layout is fixed.

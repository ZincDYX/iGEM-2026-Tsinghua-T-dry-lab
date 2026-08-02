# Real metric scoring notes

The pipeline is intentionally lightweight: heavy tools generate artifacts only when needed, and the routine M1-M4 workflow should mostly parse existing outputs and score them quickly.

## Structure prediction outputs

`igem_drylab.parsers.structure_prediction` parses common confidence artifacts from AF3, Boltz, Chai, or ABCFold-organized output folders.

Supported examples:

- AF3-style `*_summary_confidences.json`: pTM, ipTM, ranking score, clash flag, chain-pair PAE/ipTM, atom pLDDT.
- Boltz-style `confidence_*_model_*.json`: confidence score, pTM, ipTM, complex pLDDT, chain-pair ipTM.
- Chai-style `scores*.npz` or compatible JSON: aggregate score, pTM, ipTM, pLDDT, inter-chain clash flag.

ABCFold is treated as an orchestrator rather than a single output format, so the parser scans its result directory and uses whichever supported child-tool confidence artifact it finds.

Uncertainty: Chai and ABCFold output layouts may vary across versions. The parser is deliberately tolerant, but if the lab fixes one exact version, add a fixture from that real run and lock the parser against it.

## CALVADOS outputs

`igem_drylab.parsers.calvados` parses:

- explicit summary JSON fields such as dense/dilute concentration, enrichment factor, cSat, and mean Rg;
- density/concentration profile CSV as a fallback, estimating dense and dilute phase concentrations from high/low quantiles.

The current LLPS score is transparent and rule-based: enrichment factor is mapped by `log10(EF) / 3`, clipped to `[0, 1]`. This is not a proof of LLPS; it is a sortable engineering proxy.

## M2 structure score

Input file example:

```text
examples/real_metrics/m2_structure_metrics.json
```

Main metrics:

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
- very low domain-domain PAE may indicate unwanted rigid sticking;
- very high domain-domain PAE may indicate uncertain global placement.

TODO: calibrate thresholds with wet-lab expression and activity data.

## M4 docking and ODE score

Vina output is parsed into best affinity. The docking penalty compares fusion and reference:

```text
ΔΔG = ΔG_fusion - ΔG_reference
```

If fusion docking is worse, the activity multiplier decreases. This is only a screening proxy, not a real enzyme rate.

The complete M4 piecewise model is now implemented as `simulate_piecewise_induction` and `score_m4_piecewise_ode`.

State variables:

- A: substrate that OC should consume, and DMT can leak into byproduct 13;
- B: OC-generated intermediate that DMT should convert into product 15;
- P: desired product;
- Q: leakage byproduct.

DMT uses one shared enzyme pool and two competing substrates:

```text
v_product = kcat_product * E_DMT * (B / Km_product) / (1 + A / Km_leak + B / Km_product)
v_leak    = kcat_leak    * E_DMT * (A / Km_leak)    / (1 + A / Km_leak + B / Km_product)
```

OC and DMT gates can turn on at different times. For step gates, the solver restarts at each on/off boundary instead of integrating across a discontinuity.

Useful MCP call:

```bash
igem-drylab tools call igem.scoring.m4_piecewise_ode --arguments-file examples/mcp/score_m4_piecewise_ode.json
```

TODO: replace placeholder kinetic parameters with values from literature or wet-lab fitting.

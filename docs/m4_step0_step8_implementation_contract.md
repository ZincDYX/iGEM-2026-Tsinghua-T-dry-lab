# M4 Step 0–8 implementation contract

This implementation follows `M1-M4_干湿实验闭环与代码实施规范.md` version 2026-09-27. Production `markdown_steady_state` mode implements the original ten-reaction, two-phase competitive steady-state equations. The existing dynamic full-network kernel remains an explicitly selected extension and is not relabeled as the original Step 5 derivation.

## Canonical network and competition

The solver requires the exact R1–R10 identity table. In particular, R10 is `14 -> 15` by OC; this records the correction of the source prose that mistakenly mentioned M11. One competing denominator is calculated for every enzyme in every phase: PTR competes over 8/12, PT over 9/13, OC over 10/14, and DMT over 8/9/10/11. Reaction flux is the volume-weighted dense plus dilute rate.

M4 consumes M3’s explicit phase enzyme concentrations. It does not reinterpret M3 E5 bound fractions as the entire dense-phase enzyme fraction, and it has no M1/M2 score, docking score, or channeling multiplier input.

## Metabolite partition and secretion

Cell-average metabolite pools are converted with the original lever expression:

```text
C_dilute = C_total / (phi*Kp + 1 - phi)
C_dense = Kp*C_dilute
```

`phi=0` follows an explicit single-phase path and never divides by `phi`. All Kp8–Kp15 must be positive reviewed inputs; the code never substitutes Kp=1 for missing data.

The production steady solver preserves the original `V_sec,i = k_sec,i*C_i_dilute` definition through the required enum `original_unweighted_dilute_concentration`. It does not silently add `(1-phi)`, because the source has not established the normalization basis of `k_sec`.

## Step 5 existence gate

The eight original balances are solved with nonnegative bounded least squares from an explicit caller-supplied initial guess. A result is released only if every residual is below the declared numerical tolerance. `V_in`, kcat/Km for all ten reactions, all Kp, and ksec8–ksec15 are required.

If `k_sec,15=0`, the solver returns `blocked`: the M15 equation cannot support a nonzero steady production flux without an M15 outlet. This is an algebraic consequence of the source equation, not an empirical threshold.

## Step 6–8 outputs and non-claims

For a valid steady state, the solver reports reaction fluxes, secretion fluxes, all eight residuals, `yield_abs=(V_R7+V_R10)/V_in`, secretion loss over 8–14, and the conditional mass invariant residual `yield_abs+secretion_loss-1`.

`yield_rel` requires a separately run, condition-matched H0 baseline and is not fabricated. Robustness/LHS, Spearman sensitivity, descriptor chain sensitivity, Kp feasibility, and scaffold scans remain `null` unless actual uncertainty distributions, calibrated mappings, or built constructs are supplied. M4 returns raw values and no GO/NO-GO or candidate ranking.

## MCP and alternate modes

The official stdio MCP server exposes `igem.m4.solve_steady_state`. `galatea_full_competitive` remains the explicit dynamic extension for real time-course inputs. `legacy_reduced` and `published_reference` remain isolated compatibility/ablation paths; example configurations name them explicitly.

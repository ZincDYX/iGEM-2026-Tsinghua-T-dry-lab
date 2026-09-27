# M3 S1–S5 / E1–E10 implementation contract

This implementation follows `M1-M4_干湿实验闭环与代码实施规范.md` version 2026-09-27. The production `finite_site` mode is the documented cytosolic two-phase equilibrium, not the previous “independent partition plus separately reported recruitment” approximation.

## Inputs and unit contract

All concentrations are canonical µM. `K_OC` and `K_DMT` are partition coefficients of **free** enzyme. `x` and `y` are dense-phase free OC and DMT. `c_dense` is the scaffold coexistence concentration and must use the same entity basis as `s_SH3/s_PDZ`: scaffold monomer or complete assembly. A mismatched basis is rejected; no implicit factor of 24 is inserted.

Formal inputs require measured/reviewed `phi`, OC/DMT totals, free-enzyme partition coefficients, matching SH3/PDZ `Kd`, and `c_dense`, plus the M2 site counts, accessibility factors, geometry factors, and a declaration that the joint co-occupancy result permits independent E1 treatment. Docking scores are never accepted as `Kd`. ER-localized constructs are outside this solver.

## Equations

The solver evaluates S1 and S5 directly:

```text
n_SH3_eff = s_SH3 * eta_acc_SH3 * eta_bind_SH3
n_PDZ_eff = s_PDZ * eta_acc_PDZ * eta_bind_PDZ
B = Kd_SH3 / Kd_PDZ
```

If measured `phi` is absent and all S4 inputs are supplied, it evaluates:

```text
phi = (c_scaffold_total - c_sat) / (c_dense - c_sat)
```

For each enzyme, SciPy `brentq` solves the monotonic E2/E3 residual with E1 occupancy. The output then applies E4–E6 exactly. `bound_fraction_of_whole_cell_total` is the original E5 numerator divided by total enzyme and therefore excludes dense free enzyme. `dense_phase_fraction_of_whole_cell_total` is the additional derived interface `phi*c_dense_total/c_total`; the two fields are never aliased.

Every result records the E2/E3 mass-balance residual. Zero total enzyme is handled explicitly without division by zero.

## Capacity and volume conversion

When reviewed scaffold and effective enzyme volumes are supplied in nm³, S2/S3 use

```text
N_A * c[uM] * V[nm3] * 1e-30
```

to keep amount and volume units consistent. If `c_OC_dense + c_DMT_dense` exceeds S3, the result is `capacity_conflict` and is not M4-ready. The code deliberately does not proportionally rescale the already conserved E2/E3 result, because that would break the same mass balances.

The single `V_enzyme` in S3 is retained as the source formula’s declared effective-volume approximation; the code does not silently substitute a two-species packing model.

## E7–E10 boundaries

E7’s low-occupancy dense-ratio expression and its stated free `x/y` expression are returned as `e7_*_candidate` fields alongside the full E1–E6 solution. They are explicitly marked low-occupancy/binding-dominated candidates rather than full-range equalities. When `r_target` is explicitly supplied, E8 low-occupancy and E9 saturation values are returned as `rho_star_*_candidate` and marked regime-conditional, never as a global optimum. No target is invented before M4 supplies one.

E10 normalized sensitivities are evaluated analytically from the implicit conservative equations for `Kd`, effective site counts, accessibility/geometry multipliers, `phi`, free-enzyme partition coefficients, scaffold coexistence concentration, and total OC/DMT. The exact model reports OC and DMT total sensitivities separately; it does not replace them with an unverified mRNA-derived `E_ratio`.

## MCP and compatibility

The official stdio MCP server exposes `igem.m3.solve_equilibrium`. The tool accepts the versioned input contract and returns the full conservative result with residuals and readiness status.

`legacy_independent_partition` remains available only as an explicitly selected historical regression mode. `effective_ratio` remains an explicitly labeled Galatea sensitivity mode. Neither is presented as the S1–E10 production implementation.

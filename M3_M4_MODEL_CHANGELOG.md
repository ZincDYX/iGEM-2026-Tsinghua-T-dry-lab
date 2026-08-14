# Galatea M3/M4 model change log

## Corrective patch: unit, context, and routing contracts

- Added explicit `author_native_sensitivity` mode. It is relative/normalized only and cannot produce physical-unit or absolute-titer claims.
- M3 now owns validated metabolite Kp8--Kp15 together with `phi` and enzyme dense/dilute distributions; M4 consumes this context and does not re-resolve Kp.
- Split route contracts: `published_reference` uses only the isolated immutable adapter; full-network controls are homogeneous constitutive, homogeneous published-like temporal, Galatea spatial, and Galatea spatiotemporal ablation.
- Primary full-network sensitivity uses declared unity phase-activity multipliers. Registry activity parameters are read only in explicit activity-sensitivity mode.
- Strengthened full-network validation and numerical negative-state handling. The full Galatea route is 8 compounds / 10 reactions; the reduced five-state route remains compatibility-only.

## Corrective patch: author-native input separation

- Split physical and author-native sensitivity parameter acquisition at M3 and M4. Author-native runs use explicit relative enzyme scales and author CSV kcat/Km; they never query physical abundance, kcat, or Km Registry records.
- Author-native output is labelled as a source-day normalized sensitivity axis with no absolute-titer or physical-rate claim. Transport is fail-fast until a separate author-native transport contract exists.

## Added before project-wide execution

- Preserved the supplied author model in `published_reference/author_uploaded/` as an immutable reference, with a separate LSODA adapter.
- Added an explicit full network for intracellular compounds 8--15 and optional extracellular compounds 8--15. The network implements R1--R10 exactly as specified in the input package.
- Added phase-specific, single-enzyme-pool competition for PTR `{8,12}`, PT `{9,13}`, OC `{10,14}`, and DMT `{8,9,10,11}`.
- Added mass-conserving effective-ratio recruitment. SH3:PDZ capacity ratio and OC:DMT recruitment bias are explicit sensitivity inputs; neither is treated as a measured affinity.
- Added explicit metabolite partitioning and dilute-phase transport access. No Vmax enrichment multiplier or ad-hoc DMT penalty is used.
- Made constitutive DMT mandatory for the `galatea_spatial` production scenario. The published delayed ramp remains available only as `published_reference` / spatiotemporal ablation behavior.
- Added reaction-flux integrals and mechanistic diagnostics.

## Retained deliberately

- The existing reduced five-state M4 kernel remains a compatibility path for existing configurations. It is not the full Galatea network.
- Finite-site recruitment remains available as a future measured-Kd mode.

## Not implemented or not calibrated

- No project-wide sweep has been run.
- No author-native parameter has been silently converted to a physical concentration or rate unit.
- No Galatea-specific protein abundance, Kp, phase activity, binding Kd, or transport access has been measured.
- M1/M2 structural or docking outputs never enter M3/M4 kinetic inputs.

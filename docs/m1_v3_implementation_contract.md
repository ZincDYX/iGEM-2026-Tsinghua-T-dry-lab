# M1 V3 implementation contract

This implementation follows `M1-M4_干湿实验闭环与代码实施规范.md` version 2026-09-27. M1 is a negative screen. It does not infer LLPS, expression success, catalytic activity, or a functional probability.

## Formula version

`configs/m1_feature_definitions.yaml` freezes the residue sets and Kyte–Doolittle scale. Every result records the file SHA-256 and formula version. For a sequence of length `L`, the code calculates residue-set fractions, `(K+R-D-E)/L`, base-2 Shannon entropy, top-two residue fraction, longest hydrophobic run, and mean hydropathy exactly as specified. Histidine is not added to the net-charge numerator.

`charge_blockiness` and `multivalency_density` remain unavailable because the project specification does not yet define a reviewed algorithm and parameterization. `rank_score` also remains unavailable without reviewed normalization and weights.

## V3 hard-screen policy

`configs/m1_rules_v3.yaml` contains only the unambiguous V3 hard boundaries: linker length, major-module linker minimum length, hydrophobic fraction/run, IUPred2A disorder requirements, and secondary-structure fraction. A rigid linker with predicted secondary structure is sent to review rather than rejected as though it were intended to be flexible.

Formal mode requires provenance-bearing predictor results for the exact sequence hash. Missing IUPred2A, PSIPRED/JPred, SignalP, DeepTMHMM, or TANGO/PASTA evidence produces `blocked`; a hash mismatch produces `reject`. An explicitly marked experimental baseline may continue to retrospective M2 assessment, but its missing M1 evidence remains visible and its M1 status is not changed to `valid`.

## External programs and MCP

The repository does not claim an external program is available merely because a command template exists. Configure each installed program with `mode: external`, verify it through `igem.compute.check_tool`, and execute it through `igem.compute.run_tool`. Both are available over the real stdio MCP server (`igem-drylab-mcp`). Execution uses an argument vector without a shell and writes a run manifest.

SignalP, DeepTMHMM, and some other predictors have access or licensing conditions. They must be installed or invoked under their actual terms; the pipeline does not replace them with a numerical imitation. Until their real, versioned outputs are supplied, formal M1 remains blocked.

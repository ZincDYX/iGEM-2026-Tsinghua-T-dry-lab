# M1 V3 implementation contract

This implementation follows `M1-M4_干湿实验闭环与代码实施规范.md` version 2026-09-27. M1 is a negative screen. It does not infer LLPS, expression success, catalytic activity, or a functional probability.

## Formula version

`configs/m1_feature_definitions.yaml` freezes the residue sets and Kyte–Doolittle scale. Every result records the file SHA-256 and formula version. For a sequence of length `L`, the code calculates residue-set fractions, `(K+R-D-E)/L`, base-2 Shannon entropy, top-two residue fraction, longest hydrophobic run, and mean hydropathy exactly as specified. Histidine is not added to the net-charge numerator.

No generic `charge_blockiness` or `multivalency_density` is invented. The nominal-descriptor tool reports explicitly defined localCIDER kappa, SCD and FUS sticker fractions separately, with their applicability limits. An initial equal-weight midrank comparison is available through `configs/m1_initial_equal_weight_20261015.yaml`; it requires a frozen, same-context cohort and all three eligible, versioned predictor outputs. Descriptive output is not a substitute for missing formal ranking evidence.

## V3 hard-screen policy

`configs/m1_rules_v3.yaml` contains only the unambiguous V3 hard boundaries: linker length, major-module linker minimum length, hydrophobic fraction/run, IUPred2A disorder requirements, and secondary-structure fraction. A rigid linker with predicted secondary structure is sent to review rather than rejected as though it were intended to be flexible.

Formal mode requires provenance-bearing predictor results for the exact sequence hash. Missing IUPred2A, PSIPRED/JPred, SignalP, DeepTMHMM, or TANGO/PASTA evidence produces `blocked`; a hash mismatch produces `reject`. An explicitly marked experimental baseline may continue to retrospective M2 assessment, but its missing M1 evidence remains visible and its M1 status is not changed to `valid`.

## External programs and MCP

The repository does not claim an external program is available merely because a command template exists. Configure each installed program with `mode: external`, verify it through `igem.compute.check_tool`, and execute it through `igem.compute.run_tool`. Both are available over the real stdio MCP server (`igem-drylab-mcp`). Execution uses an argument vector without a shell and writes a run manifest.

SignalP, DeepTMHMM, and some other predictors have access or licensing conditions. They must be installed or invoked under their actual terms; the pipeline does not replace them with a numerical imitation. Until their real, versioned outputs are supplied, formal M1 remains blocked.

## Exact full-fusion context

`igem.m1.bind_construct_contexts` and the durable `method.m1.construct_contexts` node share the same implementation. They assemble only source-declared, ordered parts, check the complete protein identity and retain every part occurrence. An arbitrary substring, matching name or similar length is not a construct association. Native full-fusion observations must bind the exact assembled sequence and are reparsed by the original screening implementation.

The recommended M1 workflow consumes the saved scientific project's construct definitions. Fragment decisions report every applicable construct separately as `construct_context_screens`; an unrelated construct, different localization or missing full-fusion evidence cannot approve a fragment. The unbound fragment result is retained rather than replaced with its most favorable context. Protein negative screens, DNA/cloning QC, soft flags and ranking have separate scopes. Missing CDS or cloning constraints remain visible even when SignalP and DeepTMHMM evidence is complete. A completed check does not itself imply an acceptable candidate.

An explicit project-owner cancellation of TANGO/PASTA is recorded through `m1_aggregation_exclusion_reference`. It removes only that predictor requirement, never creates a zero-hotspot result. DSSP from exact complete-fusion models is auxiliary context evidence and cannot fill an isolated-fragment PSIPRED/JPred requirement or silently relax its hard rule.

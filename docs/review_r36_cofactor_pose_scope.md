# Observed cofactor pose transfer

`igem.m2.transfer_cofactor` uses the existing C-alpha mapping and rigid-transform
implementation to transfer all selected heavy atoms from an experimental
structure into an exact target model. Predicted targets must retain their own
paired confidence file and complete sequence. Author residue numbering,
insertion codes and alternate conformers use the existing structure reader.

Inputs include explicit target/template residue pairs and optional target-to-
cofactor atom pairs. Outputs contain the full-precision transformed coordinates,
fit residual, mapping, source references and observed atom-pair distances. No
distance threshold approves a new covalent bond or metal coordination center.
The same typed tool is available through the actual stdio MCP server and the
durable workflow bridge, not a separate approximate implementation.

Project execution used [3FW9](https://www.rcsb.org/structure/3FW9), retained both
alternate conformers and all five paired models of each of three OC targets,
and retained three global-alignment sensitivity settings. The pre-existing
apo-only frozen core was not selected by favorable cofactor distances. Ninety
candidate poses, each containing 53 FAD heavy atoms, were calculated. One actual
request was replayed through real stdio MCP with identical results. These are
coordinate candidates, **not** a validated double-covalent FAD topology.

The force-field boundary is intentional: ordinary FAD, covalent protein–FAD
adducts, organic 2OG and an Fe/2OG coordination center have distinct chemical
requirements. No guessed charges, copied cross-force-field constants or generic
iron ion are substituted for missing target-specific parameters.

Verification ran only on the server: 1,060 tests passed and 16 skipped, including
three new synthetic transform/contract tests. Synthetic tests and the actual
coordinate replay do not establish chemical validity or biological activity.

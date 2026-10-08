# Scientific method differences and execution boundaries

## Method authority

M1 V3 and M2 V2 original proposals are interpreted with the user's
`M1-M4_干湿实验闭环与代码实施规范.md` and the implementation contracts.
Actual ordered project sequences, not illustrative double-FTH1 diagrams,
determine construct topology. Basic sequence features are not a complete M1 pass.

## M2 scientific parser correction (2026-10-08)

The previous scientific PDB reader joined NMR models and overwrote some C-alpha
identities. This was an implementation defect, not an intended method.
Multi-model inputs now require explicit model selection; alternate conformers
also require an explicit choice. Author chain, signed residue number, insertion
code, atom and model identities are retained. mmCIF additionally retains label
chain/sequence identity. PDB has no label numbering and does not invent one.
Declared selections are not shortened when coordinates are missing.

Kabsch alignment and core/pocket C-alpha RMSD equations are unchanged.
Heavy-atom distances and the strict `distance < cutoff` clash equation are
unchanged. Bounded exact matrix blocks replace the all-pairs temporary allocation;
no approximate neighbor search or physical model is introduced. Hydrogen and
its deuterium isotope are excluded from heavy atoms.

SASA uses a complete, one-to-one reference-to-model pocket mapping, including
model, chain and insertion code. Missing area records are not zero and do not
produce a retention ratio. Recorded zero area remains zero. A zero reference
denominator is undefined. On complete selections the original
`SASA(fusion pocket) / SASA(reference pocket)` and 0.70 boundary are unchanged.
Both real PDB calculations share the same FreeSASA parameter object and default
classifier; only the explicitly chosen model/conformer is passed to the library.
The mmCIF geometry reader does not silently convert multi-character chains to PDB
for FreeSASA: that route requires an explicitly mapped PDB input.

## Existing reviewed differences from the original proposal

The original Q4 single `scaffold_clash_count > 0` veto is not used as a universal
veto. The user specification requires high confidence, reviewed relative-domain
geometry, persistence across independent conformations, and direct folded-pocket
occlusion before rejection. Other clashes remain review evidence. High PAE
means uncertain relative position, not enzyme failure. Thresholds are design
rules, not measured enzymatic parameters.

Species-specific site conflict graphs, jointly feasible capacities and Pareto
combinations supersede using one maximum-independent-set fraction for both
enzymes. Static coordinates, template reuse, docking scores and sequence disorder
do not supply Kd, kcat, Km, Kp, c_sat or measured exclusion volume. No new defaults
or score weights are introduced by this correction.

M1 charge_blockiness, multivalency_density and composite rank_score remain
unavailable without reviewed algorithms/normalization. Missing licenses,
predictor outputs, full pocket definitions and dynamics conditions remain named
blockers; diagnostic/template calculations do not constitute formal M1/M2 passes.

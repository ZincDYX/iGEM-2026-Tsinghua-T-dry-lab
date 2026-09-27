# M2 V2 implementation contract

This implementation follows `M1-M4_干湿实验闭环与代码实施规范.md` version 2026-09-27. M2 is a confidence-gated structural and geometry negative screen. Its outputs are predictions, not measurements of activity, affinity, oligomer assembly, or phase separation.

## Implemented equations

`igem.m2.calculate_geometry` accepts an explicit reference-to-model residue mapping. It Kabsch-aligns model Cα coordinates to reference Cα coordinates on the declared folded core `C`, then calculates exactly:

```text
core_CA_RMSD   = sqrt(sum(j in C) ||R x_j + t - y_j||^2 / |C|)
pocket_CA_RMSD = sqrt(sum(j in P) ||R x_j + t - y_j||^2 / |P|)
```

Every declared mapping pair must have both Cα coordinates; the calculator does not silently drop unmatched residues. It can also calculate the minimum introduced-tail-to-pocket heavy-atom distance and

```text
clash_count(d_cut) = sum(a in module 1, b in module 2) 1{||a-b|| < d_cut}.
```

Selections must be disjoint. When clash selections are requested, the caller must explicitly supply the reviewed cutoff; the document's current draft proposes `2.5 Å`, but the tool does not silently insert it. Geometry output records SHA-256 hashes of both PDB inputs.

Pocket and recruitment-domain SASA retention use the same-residue ratio `SASA(fusion)/SASA(reference)`. Parsed FreeSASA JSON is eligible for a pass/fail comparison only when both configuration hashes are present and identical. A direct two-PDB call uses the same FreeSASA API invocation for both structures. The explicit pocket boundary is retention `< 0.70`.

Vina output is compared only as `score(fusion) - score(reference)`. Both configuration hashes and both ligand hashes must match. No undocumented kcal/mol cutoff is applied, and the result is never converted to `Kd`, `kcat`, activity, or a kinetic multiplier.

## Confidence and decisions

- Folded-region pLDDT `>70`: explicit pocket RMSD/SASA rules may reject.
- pLDDT `50–70`: geometry is reference-only and can only produce review.
- pLDDT `<50`: geometry is not interpretable and M2 is blocked.
- Core Cα RMSD `>4 Å` and pocket SASA retention `<0.70` are the only implemented numeric geometry rejection boundaries. Pocket Cα RMSD is still reported, but the source document does not assign it a separate numeric rejection boundary.
- A single rigid-model clash always produces review. A clash can reject only when high-confidence, severe in every declared independent conformation, and directly occluding a functional pocket.
- High inter-domain PAE in flexible linkers/IDRs is an uncertainty flag, not a failure.

No weighted or composite structure score is calculated. Retired compatibility fields remain `null`.

## Site co-occupancy contract

`igem.m2.site_cooccupancy` solves the declared binary conflict graph by mixed-integer optimization. It returns separate OC and DMT occupancy ranges plus the Pareto co-occupancy combinations and representative concrete site IDs. It deliberately does not return a shared `eta_binding_geometry` or `binding_site_efficiency`.

For a confirmed assembly, nominal counts are `subunit_count * sites_per_subunit`. FTH1 must declare 24 subunits and provide all concrete sites before the result is M3-ready. If applicability of the 24-mer topology to the actual fusion is unconfirmed, nominal multiplied counts are withheld.

## MCP and external programs

The official stdio MCP server exposes callable M2 tools:

- `igem.m2.calculate_geometry`
- `igem.m2.screen_structure`
- `igem.m2.pocket_sasa`
- `igem.m2.compare_docking`
- `igem.m2.site_cooccupancy`
- `igem.m2.parse_structure_prediction`

The server also exposes `igem.compute.check_tool` and `igem.compute.run_tool` for explicitly configured external programs. ColabFold, FreeSASA CLI, and AutoDock Vina are not treated as installed merely because command templates exist. Formal runs require the actual executable, versioned artifacts, hashes, residue definitions, and parameters; otherwise the corresponding step remains blocked.

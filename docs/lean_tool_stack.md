# Lean dry-lab tool stack

## Default computational path

```text
M0: construct and evidence database
  -> M1: FTH1 24-mer template expansion and geometric clash screen
  -> M2: ColabFold AlphaFold2-Multimer, then FreeSASA and AutoDock Vina
  -> M3: finite-site binding / mass-conserving local-concentration model
  -> M4: OC-first/DMT-later competitive piecewise ODE
  -> M5: wet-lab HPLC, protein-abundance, and imaging feedback
```

| Component | Default status | Why it is retained |
|---|---|---|
| ColabFold AlphaFold2-Multimer | external GPU command | Free, scriptable complex prediction; its public MMseqs2 MSA service avoids a local sequence database for small serial batches. |
| FTH1 template expansion | repository-native | Tests 24-arm geometry without attempting an infeasible all-atom condensate prediction. |
| FreeSASA | external CPU command | Directly measures pocket accessibility from a selected structural model. |
| AutoDock Vina | external CPU command | Compares substrate docking in reference and fusion enzymes. |
| M3/M4 models | repository-native | Fast, transparent interpretation of site saturation, expression allocation, induction delay, and 13/15 trends. |
| Literature / construct database | repository-native with public metadata APIs | Provides versioned provenance for sequences, parameters, plasmids, and wet-lab measurements. |

## Deliberately not default dependencies

- AlphaFold 3, ABCFold, Boltz, and Chai: optional cross-validation tools only. They require paid cloud compute, large local data/model deployments, or version-specific deployment work.
- CALVADOS: optional final-candidate analysis. It is useful for a focused IDR question, but is not justified as a mandatory screen for every linker/scaffold candidate.
- SignalP / DeepTMHMM: optional M0 checks when selecting the OC N-terminal truncation. The result must be checked against the enzyme literature and wet-lab activity; the default pipeline does not depend on an online service.
- DiffDock-PP: not in the default route. It is protein-protein docking and cannot substitute for Vina in enzyme-small-molecule docking.

## Important operational limits

The ColabFold public service supplies MSAs; it is not a service-level-guaranteed high-throughput API. Submit serial, rate-limited requests, cache the returned MSAs, and run the actual model inference on the laboratory GPU. The pipeline must not bypass public-service limits.

The default stack is designed to prioritize constructs and experiments. It cannot prove LLPS formation, enzyme activity, product titer, or the final OC:DMT ratio without microscopy, protein quantification, enzyme assays, and HPLC data.

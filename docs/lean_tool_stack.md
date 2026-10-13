# Lean dry-lab tool stack

## Default computational path

```text
M0: construct and evidence database
  -> M1: original sequence/IDR/linker checks and cytosolic-fusion predictor gates
  -> M2: ColabFold, FTH1 24-mer geometry, FreeSASA and AutoDock Vina
  -> M3: finite-site binding / mass-conserving local-concentration model
  -> M4: full competitive two-phase glabridin network
  -> M5: wet-lab HPLC, protein-abundance, and imaging feedback
```

| Component | Default status | Why it is retained |
|---|---|---|
| ColabFold AlphaFold2-Multimer | external GPU command | Free, scriptable complex prediction; its public MMseqs2 MSA service avoids a local sequence database for small serial batches. |
| FTH1 template expansion | repository-native | Tests 24-arm geometry without attempting an infeasible all-atom condensate prediction. |
| FreeSASA | external CPU command | Directly measures pocket accessibility from a selected structural model. |
| AutoDock Vina | external CPU command | Compares substrate docking in reference and fusion enzymes. |
| M3/M4 models | repository-native | Fast, transparent interpretation of recruitment stoichiometry, LLPS partitioning, optional published-like temporal ablation, and 13/15 trends. |
| Literature / construct database | repository-native with public metadata APIs | Provides versioned provenance for sequences, parameters, plasmids, and wet-lab measurements. |

## Deliberately not default dependencies

- AlphaFold 3, ABCFold, Boltz, and Chai: optional cross-validation tools only. They require paid cloud compute, large local data/model deployments, or version-specific deployment work.
- Mpipi / CALVADOS and LLPS propensity tools: execute the steps retained by the selected original plan; an installation label does not make a required step optional. These methods do not replace measured M3 concentration/partitioning inputs.
- SignalP / DeepTMHMM / TANGO: required predictor evidence for the selected original cytosolic-fusion M1 checks. Academic local installation is preferred where legally available; missing native output keeps the check incomplete. No silent substitution or fabricated passing gate is permitted.
- DiffDock-PP: not in the default route. It is protein-protein docking and cannot substitute for Vina in enzyme-small-molecule docking.

## Important operational limits

The local deployment still defaults to 15 GB; the authorized scientific server
has no user-imposed size limit. Original licensed tools and weights are private
external installations, not repository, bundle or executable content.

The ColabFold public service supplies MSAs; it is not a service-level-guaranteed high-throughput API. Submit serial, rate-limited requests, cache the returned MSAs, and run the actual model inference on the laboratory GPU. The pipeline must not bypass public-service limits.

The default stack is designed to prioritize constructs and experiments. It cannot prove LLPS formation, enzyme activity, product titer, or the final OC:DMT ratio without microscopy, protein quantification, enzyme assays, and HPLC data.

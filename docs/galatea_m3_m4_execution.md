# Galatea M3/M4 execution boundary

This repository is prepared for a later audited run but this modification step
does **not** run the project-wide M3/M4 sweep.

## Inputs kept local

Copy the supplied bundle's `inputs/` directory to `data/galatea_m3_m4_inputs/`
and the three author files to `published_reference/author_uploaded/`. Both
directories are ignored by Git. Do not add `.env`, input, reference, or output
files to a commit.

## Allowed now: publication reference only

```powershell
python scripts/run_published_reference.py
```

This writes an author-native trajectory and reproducibility note under the
ignored `published_reference/` directory.

## Commands reserved for the reviewed run

After human review of reviewed parameter records and a full-network project
configuration, validate before running a single configured condition:

```powershell
igem-drylab pipeline validate configs/galatea_m3_m4_reviewed.yaml
igem-drylab project missing-inputs configs/galatea_m3_m4_reviewed.yaml --stage m3
igem-drylab project missing-inputs configs/galatea_m3_m4_reviewed.yaml --stage m4
igem-drylab pipeline run configs/galatea_m3_m4_reviewed.yaml --output-dir outputs/galatea_m3_m4
```

The final command is intentionally not run in this change set. With
`network_mode: galatea_full_competitive`, physical mode must provide the full
8--15 initial state, a local reaction network file, complete reviewed kinetics,
and all metabolite Kp values. Primary sensitivity uses unity phase activity by
default; phase-specific activity records are required only when
`activity_mode: sensitivity_parameters`.

`author_native_sensitivity` is a separate, nonphysical route: it reads
author-native kcat/Km from the local reaction CSV and explicit relative enzyme
scales from `m3_concentration.author_native_inputs`. It never converts them to
physical units and currently rejects transport. Missing dimensionless phi/Kp
provenance still produces `insufficient_data`.

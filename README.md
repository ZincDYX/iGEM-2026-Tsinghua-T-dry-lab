# iGEM 2026 Tsinghua-T Dry Lab Pipeline

This repository contains a first-pass software skeleton for the M1-M4 dry-lab workflow:

- M1: LLPS/scaffold/linker candidate generation.
- M2: OC/DMT fusion and activity-risk assessment.
- M3: local concentration, binding, saturation, and leakage assessment.
- M4: OC-first / DMT-later reaction feasibility and yield prediction.

The current implementation is intentionally interface-first. Scientific tools are represented through adapters and deterministic mock outputs so the CLI, config schema, intermediate files, and tests can stabilize before heavy models are wired in.

## Quick Start

```bash
python -m pip install -e ".[dev]"
igem-pipeline run configs/example.yaml
```

The command writes a run directory like:

```text
outputs/demo-run/
  manifest.json
  m1_llps/candidates.json
  m1_llps/candidates.csv
  m2_fusion/fusion_assessments.json
  m2_fusion/fusion_assessments.csv
  m3_concentration/concentration_assessments.json
  m3_concentration/concentration_assessments.csv
  m4_reaction/reaction_predictions.json
  m4_reaction/reaction_predictions.csv
```

## External Tool Submodules

Open-source literature tools are tracked as git submodules under `vendor/` when available. The adapters currently point at these tool names and expected input/output contracts:

- `vendor/calvados`: coarse-grained LLPS simulation.
- `vendor/ABCFold`: wrapper for AlphaFold3/Boltz/Chai-style structure prediction workflows.
- `vendor/alphafold3`: AlphaFold3 adapter target.
- `vendor/boltz`: Boltz structure/co-folding adapter target.
- `vendor/chai-lab`: Chai-1 adapter target.
- `vendor/freesasa`: SASA/pocket accessibility adapter target.
- `vendor/AutoDock-Vina`: docking adapter target.
- `vendor/mdanalysis`: trajectory and structural analysis adapter target.

After cloning the real repository, initialize these with:

```bash
git submodule update --init --recursive
```

## Development Notes

The pipeline treats every stage as a data contract:

1. Config is validated with Pydantic.
2. M1 writes candidate condensate/scaffold/linker records.
3. M2 consumes M1 records and writes fusion-risk records.
4. M3 consumes M2 records and writes local concentration/binding records.
5. M4 consumes M3 records and writes reaction/yield records.

Replacing a mock model should happen inside `src/igem_pipeline/adapters/` or the corresponding stage module while preserving the Pydantic output models in `src/igem_pipeline/models.py`.

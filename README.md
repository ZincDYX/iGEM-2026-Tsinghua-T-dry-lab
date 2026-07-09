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

To update all external tools to their latest remote commits:

```bash
git submodule update --remote --merge
git status
```

Then review the changed gitlinks, run the pipeline smoke test, and commit the update:

```bash
python -m pytest
git add .gitmodules vendor/
git commit -m "Update external tool submodules"
```

Submodules are intentionally kept outside the main package code. Pipeline code should call them through adapters in `src/igem_pipeline/adapters/`, so each external tool can later be replaced, pinned, or disabled without rewriting the M1-M4 data contracts.

## GitHub SSH Access

The repository URL may use SSH form:

```text
git@github.com:ZincDYX/iGEM-2026-Tsinghua-T-dry-lab.git
```

That requires an SSH key. An SSH key is a public/private key pair on your computer:

- the private key stays on your machine, usually under `~/.ssh/`;
- the public key is copied to GitHub, either under your GitHub account or as a deploy key on the repository;
- GitHub uses the public key to verify that this machine is allowed to clone, push, and fetch private repository content.

Check whether this machine already has a key:

```bash
ls ~/.ssh
ssh -T git@github.com
```

If no usable key exists, generate one and add the printed public key to GitHub:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub
```

For a private repository, the GitHub account that owns this SSH key must also have access to `ZincDYX/iGEM-2026-Tsinghua-T-dry-lab`. Without that, `git push` will fail with `Permission denied (publickey)`.

## Development Notes

The pipeline treats every stage as a data contract:

1. Config is validated with Pydantic.
2. M1 writes candidate condensate/scaffold/linker records.
3. M2 consumes M1 records and writes fusion-risk records.
4. M3 consumes M2 records and writes local concentration/binding records.
5. M4 consumes M3 records and writes reaction/yield records.

Replacing a mock model should happen inside `src/igem_pipeline/adapters/` or the corresponding stage module while preserving the Pydantic output models in `src/igem_pipeline/models.py`.

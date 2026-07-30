# iGEM 2026 Tsinghua-T dry lab

This repository contains a reproducible dry-lab code base for the LUMOS/iGEM project.

Current maintained modules:

- `igem_drylab.kinetics`: two-phase mass-conserving enzyme-cascade model.
- `igem_drylab.structure_metrics`: structure metrics such as pocket RMSD, PAE, distances, and optional SASA.
- `igem_drylab.pipeline`: lightweight M1-M4 interface skeleton for LLPS candidate ranking, fusion-risk scoring, local concentration scoring, and reaction recommendation.
- `igem_drylab.literature`: minimal schema-first literature extraction utilities using an OpenAI-compatible chat API such as DeepSeek.

The M1-M4 pipeline is still a deterministic skeleton. It verifies config, data flow, intermediate outputs, and visualization-ready files; it does not yet call real AF3/Boltz/Chai/CALVADOS/FreeSASA/Vina engines.

## Install and test

```bash
python -m pip install -e ".[test,plot,sasa]"
pytest
```

## Run the original kinetics example

```bash
python scripts/sweep_kinetics.py --output results/example_sweep
```

## Run the M1-M4 skeleton

```bash
igem-drylab pipeline validate configs/m1_m4_example.yaml
igem-drylab pipeline run configs/m1_m4_example.yaml
```

Output is written under:

```text
outputs/m1-m4-demo/
```

## Build a literature extraction prompt

This command does not call an LLM. It only builds the schema-first prompt.

```bash
igem-drylab literature build-prompt \
  examples/literature/glabridin_excerpt.txt \
  data/schemas/glabridin_enzyme_catalysis.schema.json \
  --icl-bank data/icl/glabridin_examples.minimal.jsonl \
  --out outputs/literature_prompt.txt
```

Actual LLM extraction is implemented in `igem_drylab.literature.ChatClient`, which expects an OpenAI-compatible chat completions endpoint. DeepSeek is compatible with this format.

## Integration notes

See [docs/integration_refactor_notes.md](docs/integration_refactor_notes.md) for what was retained, removed, and intentionally not merged from the previous feature branches.

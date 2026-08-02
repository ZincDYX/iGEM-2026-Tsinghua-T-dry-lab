# iGEM 2026 Tsinghua-T dry lab

This repository contains a reproducible dry-lab code base for the LUMOS/iGEM project.

Current maintained modules:

- `igem_drylab.kinetics`: two-phase mass-conserving enzyme-cascade model and OC-first/DMT-later competitive piecewise ODE.
- `igem_drylab.structure_metrics`: structure metrics such as pocket RMSD, PAE, distances, and optional SASA.
- `igem_drylab.pipeline`: lightweight M1-M4 interface skeleton for LLPS candidate ranking, fusion-risk scoring, local concentration scoring, and reaction recommendation.
- `igem_drylab.literature`: schema-first literature extraction and offline database construction utilities.
- `igem_drylab.mcp`: MCP-style local tool definitions and structured tool-call results for future agent integration.
- `igem_drylab.multichain`: multichain input generation, chain-chain interface checks, and finite-site module binding models.
- `igem_drylab.parsers`: parsers for FreeSASA, AutoDock Vina, AF3/Boltz/Chai/ABCFold-style confidence outputs, and CALVADOS summaries.
- `igem_drylab.scoring`: transparent rule-based M2/M4 scoring with real-metric fallback support.
- `igem_drylab.agent`: planner/memory/policy/executor/recovery runtime skeleton for an agent learning project.
- `igem_drylab.pipeline.adapters`: command adapters for external compute tools such as ABCFold, CALVADOS, FreeSASA, AutoDock Vina, SignalP, and DeepTMHMM.

The M1-M4 pipeline is lightweight by default. It does not rerun heavy tools unless configured. If real M2 structure metrics, structure-prediction confidence artifacts, CALVADOS summaries, or M4 docking penalties are supplied, the pipeline can parse them and use rule-based real scoring; otherwise it falls back to deterministic mock scores.

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

## Run M1-M4 with real metric files

This example does not run ABCFold, FreeSASA, or Vina. It reads already-produced metrics and applies lightweight rule-based scoring.

```bash
igem-drylab pipeline validate configs/m1_m4_real_scoring_example.yaml
igem-drylab pipeline run configs/m1_m4_real_scoring_example.yaml
```

The intended usage is:

```text
heavy tools run only when needed
        ↓
parser extracts metrics
        ↓
M1-M4 reads metric JSON files
        ↓
fast rule-based scoring and ODE scan
```

## Parse real scientific-tool outputs

```bash
igem-drylab tools call igem.parsers.structure_prediction --arguments-file examples/mcp/parse_structure_prediction.json
igem-drylab tools call igem.parsers.calvados --arguments-file examples/mcp/parse_calvados.json
igem-drylab tools call igem.scoring.m4_piecewise_ode --arguments-file examples/mcp/score_m4_piecewise_ode.json
```

The structure parser is version-tolerant rather than version-perfect: AF3 and Boltz have clearer output schemas, while Chai/ABCFold/CALVADOS layouts should be locked with real lab fixtures once your server versions are fixed.

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

## Build a literature database from cached text

First, candidate literature can be searched and exported as a manifest:

```bash
igem-drylab literature search \
  "glabridin biosynthesis DMT OC" \
  --provider openalex \
  --provider crossref \
  --output-manifest outputs/literature_search_manifest.csv \
  --max-results 25
```

This command builds a small offline database from a CSV manifest whose rows point to cached article text files. It mines numeric evidence, maps evidence to the schema, aggregates records, and writes clean/excluded outputs.

```bash
igem-drylab literature build-database \
  examples/literature_database/manifest.csv \
  data/schemas/glabridin_enzyme_catalysis.schema.json \
  --output-dir outputs/literature_database_demo
```

Expected outputs:

```text
numeric_evidence.csv
structured_records.csv
clean_database.csv
excluded_records.csv
summary.json
```

## Inspect and call MCP-style tools

The repository does not run a network MCP server yet. It exposes a small local registry whose tool definitions follow the core MCP tool shape: `name`, `title`, `description`, `inputSchema`, optional `outputSchema`, and tool-call results with `content`, `structuredContent`, and optional `isError`.

```bash
igem-drylab tools list
igem-drylab tools call igem.pipeline.validate --arguments-json '{"config_path":"configs/m1_m4_example.yaml"}'
igem-drylab tools call igem.pipeline.run --arguments-json '{"config_path":"configs/m1_m4_example.yaml","output_dir":"outputs"}'
```

On PowerShell, `--arguments-file` is usually less error-prone than inline JSON quoting.

```bash
igem-drylab tools call igem.pipeline.validate --arguments-file examples/tool_args/pipeline_validate.json
igem-drylab tools call igem.pipeline.run --arguments-file examples/tool_args/pipeline_run.json
igem-drylab tools call igem.literature.build_prompt --arguments-file examples/tool_args/literature_build_prompt.json
igem-drylab tools call igem.literature.search --arguments-file examples/tool_args/literature_search_openalex_crossref.json
igem-drylab tools call igem.literature.build_database --arguments-file examples/tool_args/literature_build_database.json
```

Compute-tool commands can also be inspected or dry-run through the same tool interface:

```bash
igem-drylab tools call igem.compute.check_tool --arguments-file examples/tool_args/compute_check_abcfold.json
igem-drylab tools call igem.compute.run_tool --arguments-file examples/tool_args/compute_dry_run_abcfold.json
```

The example config keeps heavy scientific tools in `mode: mock`. To run them on a workstation or server, edit `configs/m1_m4_example.yaml`, set the intended tool to `mode: external`, and point `command` to the installed executable or wrapper script. Command templates are rendered without a shell; values such as `{input_file}`, `{config_file}`, `{pdb_file}`, `{fasta_file}`, and `{output_dir}` come from the tool-call context.

## Multichain module design tools

For designs where the yeast expresses separate modules, such as `FTH1-iLID` and `SspB-IDR-SH3/PDZ`, the repository exposes explicit multichain tools:

```bash
igem-drylab tools call igem.multichain.build_input --arguments-file examples/tool_args/multichain_build_input.json
igem-drylab tools call igem.multichain.binding_equilibrium --arguments-file examples/tool_args/multichain_binding_equilibrium.json
igem-drylab tools call igem.multichain.assess_interface --arguments-file examples/tool_args/multichain_assess_interface.json
igem-drylab tools call igem.multichain.expand_fth1_arms --arguments-file examples/tool_args/multichain_expand_fth1_arms.json
```

These tools do not replace ABCFold/Boltz/Chai. They prepare multichain inputs, quantify finite-site binding stoichiometry, and assess chain-chain contacts/clashes after a structure is available.

`igem.multichain.expand_fth1_arms` is the lightweight FTH1-cage step: it reads a complete FTH1 24-mer PDB template, maps a separately predicted local fusion arm to each subunit, writes an optional assembled PDB, and reports core-arm/arm-arm clashes plus a geometric exposure proxy. It deliberately does **not** claim to predict LLPS, linker ensembles, or enzyme activity. Use a biologically appropriate FTH1 24-mer template and a local-arm PDB that does not include a duplicate FTH1 chain.

## Real-metric parser and scoring tools

```bash
igem-drylab tools call igem.scoring.pocket_sasa --arguments-file examples/tool_args/scoring_pocket_sasa.json
igem-drylab tools call igem.scoring.m2_structure --arguments-file examples/tool_args/scoring_m2_structure.json
igem-drylab tools call igem.scoring.docking_penalty --arguments-file examples/tool_args/scoring_docking_penalty.json
igem-drylab tools call igem.scoring.m4_ode --arguments-file examples/tool_args/scoring_m4_ode.json
```

The current scoring rules are intentionally transparent, not a trained black-box model. Update the TODO calibration points after wet-lab HPLC data becomes available.

## Agent framework skeleton

The `igem_drylab.agent` package contains the main agent architecture slots:

- planner;
- memory;
- decision policy;
- tool executor;
- error recovery policy;
- runtime trace.

Important policy decisions are marked with `TODO`. See [docs/agent_framework_notes.md](docs/agent_framework_notes.md) before filling them in.

Tools that call external APIs read secrets from environment variables instead of JSON arguments:

```bash
set DEEPSEEK_API_KEY=...
set ELSEVIER_API_KEY=...
```

## Integration notes

See [docs/integration_refactor_notes.md](docs/integration_refactor_notes.md) for what was retained, removed, and intentionally not merged from the previous feature branches.

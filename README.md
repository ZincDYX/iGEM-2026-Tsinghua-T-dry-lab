# iGEM 2026 Tsinghua-T dry lab

This repository contains a reproducible dry-lab code base for the LUMOS/iGEM project. It separates deterministic scientific calculations from orchestration and from wet-lab feedback. A result is never promoted from a fixture, heuristic, docking score, or extracted sentence to a validated biological fact.

Current maintained modules:

- `igem_drylab.kinetics`: generic demonstration kinetics plus an explicit, mass-conserving glabridin network: PT `9→10`, OC `10→11`, DMT `9→13` / `11→15` with a shared competitive DMT pool.
- `igem_drylab.structure_metrics`: structure metrics such as pocket RMSD, PAE, distances, and optional SASA.
- `igem_drylab.pipeline`: M0 evidence/configuration, M1 construct screen, M2 structural negative screen, M3 partitioning, M4 kinetics, and M5 wet-lab feedback. Real mode returns `insufficient_data` instead of mock scientific scores.
- `igem_drylab.parameters`: reviewed parameter registry with value, unit, DOI/source, condition, uncertainty, and review state.
- `igem_drylab.wetlab`: structured wet-lab data, non-destructive QC, bounded least-squares fitting, deterministic diagnosis, and transparent measurement ranking.
- `igem_drylab.literature`: schema-first literature extraction and offline database construction utilities.
- `igem_drylab.mcp`: MCP-style local tool definitions and structured tool-call results for future agent integration.
- `igem_drylab.multichain`: multichain input generation, chain-chain interface checks, and finite-site module binding models.
- `igem_drylab.parsers`: parsers for FreeSASA, AutoDock Vina, ColabFold/AF3/Boltz/Chai/ABCFold-style confidence outputs, and optional CALVADOS summaries.
- `igem_drylab.scoring`: transparent structural and docking negative screens. Vina affinity is not converted into enzyme activity.
- `igem_drylab.agent`: planner/memory/policy/executor/recovery runtime skeleton for an agent learning project.
- `igem_drylab.pipeline.adapters`: command adapters for the lean default stack: ColabFold, FreeSASA, and AutoDock Vina. Optional legacy/advanced adapters are retained but not default dependencies.

The pipeline has two execution modes. `demo` may use explicit fixtures to test software plumbing. `real` requires reviewed, provenance-bearing inputs and never falls back to mock scores. Sequence-level M1 flags are engineering screens, not LLPS probabilities; M2 and Vina are negative screens, not enzyme-activity measurements.

## Install and test

```bash
python -m pip install -e ".[test,plot,sasa]"
pytest
```

## Run the original kinetics example

```bash
python scripts/sweep_kinetics.py --output results/example_sweep
```

## Run the M0-M5 workflow

```bash
igem-drylab pipeline validate configs/m1_m4_example.yaml
igem-drylab pipeline run configs/m1_m4_example.yaml
```

Output is written under:

```text
outputs/m1-m4-demo/
```

## Run with existing structural metrics

This example does not run ColabFold, FreeSASA, or Vina. It reads already-produced metrics. It remains `insufficient_data` for M3/M4 until reviewed partition and kinetic parameter records are supplied.

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
igem-drylab tools call igem.parsers.structure_prediction --arguments-file examples/mcp/parse_colabfold.json
# Legacy generic A/B/P/Q demonstration only; production M4 is igem.pipeline.run_stage with stage=m4.
igem-drylab tools call igem.scoring.m4_piecewise_ode --arguments-file examples/mcp/score_m4_piecewise_ode.json
```

The default structure backend is ColabFold AlphaFold2-Multimer. Its `ranking_debug.json` parser extracts pLDDT, pTM and ipTM. It deliberately does not claim an inter-chain PAE value without chain boundaries. AF3/Boltz/Chai/ABCFold/CALVADOS parsers are retained as optional compatibility tools, not required dependencies.

Production M3 passes a candidate-specific, mass-conserving enzyme distribution to M4. Construct/condition-scoped reviewed parameters override global records; recruitment, docking, and structure scores are not kinetic multipliers. The optional M5 FitPlan fits exactly one declared mechanistic parameter and emits a validated candidate requiring human approval.

Before pilot ingestion, use the typed evidence contracts for enzyme kinetics, LLPS partitioning, abundance, and recruitment. Evidence extraction remains review-only; it cannot write an approved production parameter.

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
igem-drylab tools call igem.compute.check_tool --arguments-file examples/tool_args/compute_check_colabfold.json
igem-drylab tools call igem.compute.run_tool --arguments-file examples/tool_args/compute_dry_run_colabfold.json
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

These tools complement ColabFold; they prepare multichain inputs, quantify finite-site binding stoichiometry, and assess chain-chain contacts/clashes after a structure is available.

`igem.multichain.expand_fth1_arms` is the lightweight FTH1-cage step: it reads a complete FTH1 24-mer PDB template, maps a separately predicted local fusion arm to each subunit, writes an optional assembled PDB, and reports core-arm/arm-arm clashes plus a geometric exposure proxy. It deliberately does **not** claim to predict LLPS, linker ensembles, or enzyme activity. Use a biologically appropriate FTH1 24-mer template and a local-arm PDB that does not include a duplicate FTH1 chain.

## Real-metric parser and scoring tools

```bash
igem-drylab tools call igem.scoring.pocket_sasa --arguments-file examples/tool_args/scoring_pocket_sasa.json
igem-drylab tools call igem.scoring.m2_structure --arguments-file examples/tool_args/scoring_m2_structure.json
igem-drylab tools call igem.scoring.docking_penalty --arguments-file examples/tool_args/scoring_docking_penalty.json
igem-drylab tools call igem.scoring.m4_ode --arguments-file examples/tool_args/scoring_m4_ode.json
```

The current scoring rules are intentionally transparent, not a trained black-box model. Update the TODO calibration points after wet-lab HPLC data becomes available.

## Agent framework

The `igem_drylab.agent` package provides a conservative runnable agent loop:

- planner;
- memory;
- decision policy;
- tool executor;
- error recovery policy;
- runtime trace, JSONL events, artifact checksums, typed memory, recovery, and reflection.

Run a safe example with `igem-drylab agent dry-run examples/agent/validate_config_task.json` or `igem-drylab agent run examples/agent/validate_config_task.json`.

The default planner is local and deterministic. To explicitly use the optional OpenAI-compatible planner, copy `.env.example` to `.env`, add the key locally, then pass `--planner llm`. `.env` is ignored by Git; never commit API keys.

## Lean default tool stack

The maintained default route is **ColabFold Multimer -> FTH1 24-mer geometric expansion -> FreeSASA -> AutoDock Vina -> M3/M4 ODE**. It uses no local sequence database for small serial jobs because ColabFold can request MSAs from its public service; model inference itself remains local to the GPU server. Optional AF3/ABCFold/Boltz/Chai/CALVADOS integrations are retained for compatibility but are not mandatory. See [docs/lean_tool_stack.md](docs/lean_tool_stack.md) for scope and limits.

Tools that call external APIs read secrets from environment variables instead of JSON arguments:

```bash
set DEEPSEEK_API_KEY=...
set ELSEVIER_API_KEY=...
```

## Literature evidence QA

The evidence QA route is deliberately local and conservative: it uses transparent TF-IDF retrieval over a supplied `.jsonl`, `.json`, or `.csv` evidence file and returns evidence text, DOI, and score. It does not call an LLM or turn a retrieved sentence into a validated parameter.

```bash
igem-drylab literature qa "What evidence reports OC activity?" --evidence path/to/evidence.jsonl
igem-drylab literature serve-qa --evidence path/to/evidence.jsonl
```

The browser page binds to `127.0.0.1` by default, accepts only a question, and has no file-upload, command-execution, or API-key endpoint. For long articles, `igem.literature.extract_chunked_records` adds chunk provenance and schema validation to the existing OpenAI-compatible extractor. Its optional `repair_invalid` flag makes at most one extra formatting-only call per invalid record; both the original extraction and repair remain unverified until human review.

## Integration notes

See [docs/integration_refactor_notes.md](docs/integration_refactor_notes.md) for what was retained, removed, and intentionally not merged from the previous feature branches.

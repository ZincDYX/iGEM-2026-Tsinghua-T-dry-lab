# iGEM 2026 Tsinghua-T Dry Lab

Reproducible dry-lab software for the Tsinghua-T iGEM 2026 glabridin project. The repository connects literature evidence, construct-level screening, two-phase condensate modelling, kinetic simulation, and wet-lab feedback without promoting predictions into biological facts.

> **Project status:** ready for a small, human-reviewed `evidence.jsonl` pilot. The default workflow is deterministic and local. Optional external tools and LLM APIs are explicit opt-ins.

## What this repository does

The maintained workflow is intentionally conservative:

```text
Evidence database
  -> typed, reviewable parameter candidates
  -> human approval and scoped parameter registry
  -> M0–M5 dry-lab workflow
  -> wet-lab measurements
  -> QC, bounded fitting, and a new review cycle
```

It provides:

- M0–M5 pipeline stages for input validation, construct screening, structural negative screening, phase partitioning, kinetic simulation, and wet-lab feedback;
- a mass-conserving glabridin reaction model with PT `9 -> 10`, OC `10 -> 11`, and competing DMT reactions `9 -> 13` / `11 -> 15`;
- provenance-bearing literature evidence retrieval with BM25, optional embeddings, DOI de-duplication, MMR diversity, and optional one-call grounded synthesis;
- deterministic evidence knowledge graphs and optional GraphRAG fusion with auditable entity paths;
- a reviewed Parameter Registry with unit, identity, construct, condition, and provenance checks;
- parsers and tool contracts for structure predictors, FreeSASA, AutoDock Vina, and CALVADOS-style outputs;
- lightweight FTH1 24-mer geometric expansion and finite-site multichain binding utilities;
- an MCP-style local tool registry and a conservative agent runtime for orchestration experiments.

## Scientific boundaries

This project is designed to be useful before complete project-specific measurements exist, but it does not invent them.

- `demo` inputs test software plumbing only. They never support a real scientific conclusion.
- `real` mode returns `insufficient_data` when reviewed parameters, identities, units, or conditions are missing.
- Structure confidence, docking affinity, LLPS scores, and retrieval rank are bounded evidence or negative screens. They are not enzyme activities or validated kinetic constants.
- Literature extraction and AI synthesis produce evidence for review; only a human-approved `ParameterRecord` can enter production M3/M4 calculations.
- Physical-unit M4 production mode uses `uM`, `h`, and `1/h`; incompatible or missing units are rejected rather than guessed. The isolated `author_native_sensitivity` mode preserves Zhang author-native numbers only for relative/normalized sensitivity analysis and never labels its values as physical concentration, rate, time, or titer.

See [scientific_model_contract.md](docs/scientific_model_contract.md) for the complete model and data contract.

## Quick start

Requirements: Python 3.10 or newer.

```bash
git clone https://github.com/ZincDYX/iGEM-2026-Tsinghua-T-dry-lab.git
cd iGEM-2026-Tsinghua-T-dry-lab
python -m pip install -e ".[test,plot,sasa]"
pytest -q
```

The repository includes the canonical 20,567-record evidence database through
Git LFS. After cloning, run `git lfs pull`. For a clean-machine walkthrough,
including database verification and GraphRAG startup, see
[new_environment_setup.md](docs/new_environment_setup.md).

Run the demonstration pipeline:

```bash
igem-drylab pipeline validate configs/m1_m4_example.yaml
igem-drylab pipeline run configs/m1_m4_example.yaml
```

The example writes artifacts under `outputs/m1-m4-demo/`. It is a software demonstration, not a project-specific prediction.

To inspect available local tools:

```bash
igem-drylab tools list
igem-drylab tools call igem.pipeline.validate --arguments-file examples/tool_args/pipeline_validate.json
```

## Recommended workflow

### 1. Build and review literature evidence

Search literature metadata, then build a local database from cached article text:

```bash
igem-drylab literature search "glabridin biosynthesis DMT OC" \
  --provider openalex --provider crossref \
  --output-manifest outputs/literature_search_manifest.csv --max-results 25

igem-drylab literature build-database \
  examples/literature_database/manifest.csv \
  data/schemas/glabridin_enzyme_catalysis.schema.json \
  --output-dir outputs/literature_database_demo
```

Extracted evidence is not automatically a model parameter. Map it to a declared requirement, review it, and approve it before a real run.

```text
raw article text -> typed EvidenceRecord -> ParameterCandidate -> human approval -> ParameterRegistry
```

### 2. Search the local evidence database

The default QA route is offline, deterministic BM25 retrieval. It accepts `.jsonl`, `.json`, and `.csv` evidence databases. Legacy project-conditioned CSV exports are read through a thin field-alias layer: original provenance and project metadata are retained, while `primary_result_evidence`, `best_enzyme_name_value`, `best_substrate_name_value`, and `primary_result_metric` also populate canonical QA fields. Legacy rules and decision engines are not reintroduced.

```bash
igem-drylab literature qa "What evidence reports OC activity?" \
  --evidence path/to/evidence.jsonl

igem-drylab literature serve-qa --evidence path/to/evidence.jsonl
```

Optional semantic retrieval and synthesis are configured through environment variables. Copy `.env.example` to a local `.env`; never commit credentials.

```bash
igem-drylab literature qa "Find DMT kinetics" \
  --evidence path/to/evidence.jsonl --semantic

igem-drylab literature qa "Summarize OC activity" \
  --evidence path/to/evidence.jsonl --mode synthesize
```

Semantic retrieval builds a local cache only after all embedding batches complete successfully. If an optional embedding or synthesis API is unavailable, lexical retrieval remains available.

Build a provenance-bearing graph and add it as a third retrieval route:

```bash
igem-drylab literature build-graph --evidence path/to/evidence.jsonl --output outputs/evidence_graph.json
igem-drylab literature qa "DMT activity in yeast LLPS condensates" --evidence path/to/evidence.jsonl --semantic --graph --graph-path outputs/evidence_graph.json
```

Graph edges are derived only from stored evidence fields and retain record/DOI provenance. See [graph_rag_and_agent_baselines.md](docs/graph_rag_and_agent_baselines.md).

### 3. Run structure and partitioning screens

The lean default stack is:

```text
ColabFold Multimer -> FTH1 24-mer expansion -> FreeSASA -> AutoDock Vina -> M3/M4 ODE
```

Heavy tools run externally only when requested. Their outputs are parsed into explicit artifacts that the pipeline reads; the repository does not silently download model weights or invoke web services.

```bash
igem-drylab tools call igem.parsers.structure_prediction \
  --arguments-file examples/mcp/parse_colabfold.json
igem-drylab tools call igem.scoring.pocket_sasa \
  --arguments-file examples/tool_args/scoring_pocket_sasa.json
```

AF3, ABCFold, Boltz, Chai, and CALVADOS compatibility parsers are available, but they are not default runtime dependencies. See [lean_tool_stack.md](docs/lean_tool_stack.md) for scope and limitations.

### 4. Run a real-data workflow only after review

Use the real-scoring example to validate existing artifacts and contracts:

```bash
igem-drylab pipeline validate configs/m1_m4_real_scoring_example.yaml
igem-drylab pipeline run configs/m1_m4_real_scoring_example.yaml
```

Production Galatea M3 supplies candidate-specific, mass-conserving enzyme dense/dilute distributions together with `phi` and metabolite Kp8--Kp15 to the full 8-compound/10-reaction M4 route. The legacy reduced kernel remains only as a compatibility path. Registry resolution follows exact `construct + condition`, construct-only, condition-only, then global scope. Recruitment, docking, and structural scores are never multiplied into `kcat`.

The primary Galatea mechanism is recruitment stoichiometry plus LLPS partitioning; delayed DMT is only a published-like temporal control or ablation. `author_native_sensitivity` is a separate nonphysical path: author-native kinetics come only from the cited reaction CSV and enzyme scales come only from an explicit sensitivity block, never from physical Registry records.

## Repository layout

```text
configs/       Example demo and real-data configurations
data/          Evidence schemas and ICL examples
docs/          Scientific contract, tool-stack and integration notes
examples/      Small command arguments and fixture inputs
src/           Python package source
tests/         Unit and contract tests
```

Key packages:

- `igem_drylab.pipeline` — M0–M5 execution and artifacts
- `igem_drylab.parameters` — reviewed/scoped parameter resolution
- `igem_drylab.wetlab` — measurement QC, bounded fitting, diagnosis
- `igem_drylab.literature` — evidence extraction, database construction, QA
- `igem_drylab.multichain` — multichain inputs, binding, FTH1 arm geometry
- `igem_drylab.parsers` and `igem_drylab.scoring` — external-tool result parsing and transparent screens
- `igem_drylab.mcp` — local MCP-style tool contracts
- `igem_drylab.agent` — optional planner, memory, policy, execution, and recovery framework

## Agent orchestration benchmark

The optional Agent is an orchestration layer. It selects deterministic M1–M5 stage dispatches, validates artifact reuse, requests missing inputs or human review, and records traces. It does not replace the scientific modules or generate biological results itself.

`benchmarks/agent_orchestration_v1/` is a frozen 24-case project-specific regression set. Version 2 retains the same cases and gold decisions, and adds typed change routing, checksum-aware reuse blocking, stage-aware dispatch, and strict OpenAI-compatible JSON Output validation. Run it only with configured local credentials; outputs remain ignored by Git:

```bash
python scripts/evaluate_agent_benchmark.py --benchmark benchmarks/agent_orchestration_v1 --output results/agent_benchmark_v2/rule_based --planner rule-based --mode dry-run
python scripts/evaluate_agent_benchmark.py --benchmark benchmarks/agent_orchestration_v1 --output results/agent_benchmark_v2/llm --planner llm --mode dry-run --jobs 4
python scripts/render_agent_benchmark_v2_report.py
```

An accepted LLM plan is still subject to the normal policy, budget, artifact, and human-approval gates. Passing this frozen benchmark indicates project-specific orchestration behavior only—not general scientific intelligence or biological prediction accuracy.

The recommended v3 hybrid route further separates responsibilities: `LLM → PlanningDecision → DeterministicPlanCompiler → Policy/approval → deterministic M1–M5 tools`. Direct LLM DAG generation remains available as an ablation through `--planner llm`; the hybrid route is `--planner hybrid`. Qwen is optional and configured only through local `QWEN_API_KEY`, `QWEN_API_BASE`, and `QWEN_MODEL` variables.

For a provider-by-architecture comparison of rule-based, Qwen, DeepSeek,
Hybrid Qwen, and Hybrid DeepSeek on identical frozen cases, run:

```bash
python scripts/run_agent_baseline_matrix.py --benchmark benchmarks/agent_orchestration_heldout_v2 --output-root results/agent_baseline_matrix --jobs 5
```

## Configuration and secrets

All project inputs should be versioned configuration, reviewed evidence, or explicit command arguments. API credentials must only be environment variables.

```bash
copy .env.example .env  # Windows PowerShell/cmd users may also create this manually
```

`.env`, embedding caches, generated outputs, and local learning notes are ignored by Git. Do not pass an API key in JSON tool arguments or commit generated private data.

## External tools and APIs

The Python package itself depends only on NumPy, SciPy, Pydantic, PyYAML, Typer, and Requests. Optional integrations include:

| Integration | Role | Required? |
| --- | --- | --- |
| ColabFold Multimer | structure prediction | No |
| FreeSASA | pocket accessibility | No |
| AutoDock Vina | small-molecule docking screen | No |
| CALVADOS | coarse-grained condensate simulation parsing | No |
| OpenAI-compatible API | optional literature extraction, planning, embeddings, synthesis | No |

For external compute commands, switch the intended adapter from `mode: mock` to `mode: external` in a configuration and point it to an installed executable or wrapper. Commands are rendered without a shell.

## Agent and MCP interface

The agent runtime is intentionally conservative: its default planner is local and deterministic, tools expose typed inputs/outputs, and human approval remains a separate mutation step. It does not autonomously approve literature-derived scientific parameters.

```bash
igem-drylab agent dry-run examples/agent/validate_config_task.json
igem-drylab agent run examples/agent/validate_config_task.json
```

The local MCP-style registry can be inspected with `igem-drylab tools list`. It is a tool-contract layer, not a network MCP server.

## Contributing

Use short-lived branches based on `develop`, add or update tests for behavioral changes, and open a pull request back to `develop`. Keep `main` for reviewed releases. Do not commit `.env`, generated outputs, raw private experimental data, model weights, or local review bundles.

Before opening a pull request:

```bash
pytest -q
git diff --check
```

For the scientific assumptions and known model limitations, start with [scientific_model_contract.md](docs/scientific_model_contract.md) and [integration_refactor_notes.md](docs/integration_refactor_notes.md).

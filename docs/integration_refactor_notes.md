# Clean integration notes

This branch was created from `develop` and manually integrates the useful core ideas from:

- `feature/m1-m4-pipeline-skeleton`
- `Literature-LKD-AI-Agent`

It intentionally avoids direct whole-branch merges because `feature/m1-m4-pipeline-skeleton` has unrelated history and conflicts in root files, while `Literature-LKD-AI-Agent` contains many redundant scripts and legacy modules.

## Retained from M1-M4 skeleton

Retained as `src/igem_drylab/pipeline/`:

- YAML config validation with Pydantic.
- M1 candidate generation.
- M2 fusion-risk assessment.
- M3 concentration/risk assessment.
- M4 reaction recommendation.
- JSON and CSV stage outputs.
- Manifest output.
- CLI entry points.

The formulas and mock behavior are kept equivalent to the feature branch. They are now namespaced under `igem_drylab.pipeline` instead of a separate `igem_pipeline` package.

## Retained from Literature-LKD-AI-Agent

Retained as `src/igem_drylab/literature/`:

- OpenAI-compatible chat client suitable for DeepSeek-style endpoints.
- JSON block parsing.
- Rule-based dynamic ICL example selection.
- Schema loading.
- Schema-first prompt construction.
- Minimal Elsevier API helpers.

The large script collection was not copied. The integrated module is designed as a reusable library rather than a standalone pile of batch scripts.

## Removed or not merged

Not merged:

- `literature_extraction_agent/EntireProgram.py`
- `literature_extraction_agent/datacleaning.py`
- CO2/methanol legacy optimization defaults.
- Large `literature_extraction_agent/scripts/` batch pipeline.
- UI/API server scaffolding.
- softcopy export templates.
- `vendor/` scientific submodules from M1-M4 skeleton.
- duplicated root `README.md`, `.gitignore`, `.gitmodules`, and `pyproject.toml`.

These can be reintroduced later only if they have a clear owner, tests, and a stable interface.

## Feature retention matrix

| Source capability | Current status | Notes |
| --- | --- | --- |
| Existing `develop` kinetics model | Retained | Original imports and tests are unchanged. |
| Existing `develop` structure metrics | Retained | Original imports and tests are unchanged. |
| M1-M4 config validation | Retained and renamed | Implemented under `igem_drylab.pipeline`; old `igem_pipeline` package name is not kept. |
| M1-M4 staged JSON/CSV outputs | Retained | Deterministic skeleton behavior is preserved. |
| M1 LLPS candidate ranking skeleton | Retained | Still a placeholder score, not a real CALVADOS/PICNIC calculation. |
| M2 fusion-risk scoring skeleton | Retained and upgraded | Uses rule-based real scoring when structure metrics are provided; otherwise falls back to mock scoring. |
| M3 local concentration scoring skeleton | Retained | Still a placeholder score, not a fitted two-phase binding model. |
| M4 reaction recommendation skeleton | Retained and upgraded | Uses lightweight ODE scoring with optional docking penalty when metric files are provided. |
| Literature OpenAI-compatible chat client | Retained and simplified | Suitable for DeepSeek-style chat-completions endpoints. |
| Literature ICL example selection | Retained and simplified | Deterministic rule-based selector. |
| Literature schema-first prompt construction | Retained | Output contract remains JSON records. |
| Literature source search | Reintroduced and refactored | OpenAlex, Crossref, and Elsevier Scopus search providers normalize results to a shared manifest format. |
| Offline literature database construction | Reintroduced and refactored | Manifest-to-text, numeric evidence mining, schema mapping, aggregation, cleaning, and export are now in `igem_drylab.literature.database`. |
| Elsevier Scopus/article helper functions | Retained minimally | Requires API entitlement; not tested against paid endpoints in unit tests. |
| Legacy all-in-one agent script | Not retained | Dropped because it mixed orchestration, defaults, cleaning, prompting, and execution in one large script. |
| Literature batch script collection | Partially retained by behavior | The stable offline database-building behavior was refactored into library code; large network/download/re-extraction scripts are not copied verbatim. |
| CO2/methanol legacy defaults | Not retained | Out of scope for glabridin/LLPS pipeline. |
| UI/API server scaffolding | Not retained | Out of scope for a minimal maintainable core. |
| Softcopy export templates | Not retained | Can be reintroduced as a separate reporting module if needed. |
| Vendor submodule directory from skeleton branch | Not retained | The integrated code uses explicit adapters and `third_party/` placeholders instead. |

So this branch should not be described as "no feature loss" relative to every old branch file. It is a cleaned integration that preserves the maintained core behavior and intentionally removes untested or out-of-scope code.

## MCP-style tool interface

Added as `src/igem_drylab/mcp/`:

- `McpTool`: local representation of a tool definition with `name`, `title`, `description`, `inputSchema`, and optional `outputSchema`.
- `McpToolResult`: local representation of a tool result with `content`, `structuredContent`, and optional `isError`.
- `ToolRegistry`: deterministic local registry for listing and calling tools.

Currently exposed tools:

- `igem.pipeline.validate`
- `igem.pipeline.run`
- `igem.literature.build_prompt`
- `igem.literature.extract_records`
- `igem.elsevier.search_scopus`
- `igem.elsevier.fetch_article_text`
- `igem.compute.check_tool`
- `igem.compute.run_tool`
- `igem.literature.build_database`
- `igem.literature.search`
- `igem.multichain.build_input`
- `igem.multichain.binding_equilibrium`
- `igem.multichain.assess_interface`
- `igem.scoring.pocket_sasa`
- `igem.scoring.m2_structure`
- `igem.scoring.docking_penalty`
- `igem.scoring.m4_ode`

This is not yet a transport-level MCP server. It is the stable tool layer that a future MCP server can wrap without rewriting the pipeline or literature modules.

## External compute tool adapters

Added command adapters in `src/igem_drylab/pipeline/adapters.py` for the scientific tools used in the dry-lab flowchart:

- structure prediction: ABCFold, Boltz, Chai
- LLPS simulation: CALVADOS
- structure metric calculation: FreeSASA
- docking: AutoDock Vina
- sequence screening: SignalP and DeepTMHMM

The adapters provide a shared contract:

- render a command from the YAML `command` template;
- avoid shell execution;
- support `dry_run`;
- check executable availability;
- run external commands when `mode: external`;
- record `argv`, `cwd`, stdout, stderr, return code, duration, output directory, and a JSON manifest.

They do not yet run and parse every scientific tool end-to-end. FreeSASA-style pocket SASA JSON, Vina outputs, rule-based M2 scoring, and lightweight M4 ODE scoring have been added. ABCFold/Boltz/Chai and CALVADOS parser integration still depends on the exact tool version and server output layout.

## Real-metric parser and scoring layer

Added:

- `src/igem_drylab/parsers/freesasa.py`
- `src/igem_drylab/parsers/vina.py`
- `src/igem_drylab/scoring/m2_structure.py`
- `src/igem_drylab/scoring/m4_reaction.py`

The pipeline now supports optional real metric files:

- `stages.m2_fusion.structure_metrics_file`
- `stages.m4_reaction.docking_penalties_file`

If files are present, M2/M4 use transparent rule-based scoring. If files are absent, the pipeline uses the previous lightweight fallback. This avoids re-running heavy tools every time.

## Agent framework skeleton

Added `src/igem_drylab/agent/`:

- planner;
- memory;
- decision policy;
- tool executor;
- error recovery policy;
- runtime trace.

Important scientific and engineering decisions are intentionally marked with TODO. See `docs/agent_framework_notes.md`.

## Multichain and multicomponent module support

Added `src/igem_drylab/multichain/` for designs where the wet lab expresses multiple protein modules instead of a single fused construct.

Current tools:

- `build_multichain_input`: writes a multichain FASTA and JSON manifest for complex prediction tools such as ABCFold.
- `solve_binding_equilibrium`: solves finite-site A+B binding with configurable Kd and valency, suitable for iLID/SspB, SH3/ligand, PDZ/ligand, and similar recruitment pairs.
- `assess_interface`: reads a PDB file and reports inter-chain contact count, clash count, minimum distance, and contact residues.

This keeps the code aligned with an agent-style tool architecture: tools have explicit JSON inputs, structured outputs, deterministic side effects, and artifact manifests. It still does not implement autonomous planning, tool-choice reasoning, long-term memory, or advanced retry/error-recovery policies.

## Literature database construction

Added `src/igem_drylab/literature/database.py` to preserve the useful parts of the previous literature batch pipeline without keeping the fragile script pile.

The current offline database flow is:

1. read a CSV manifest with article metadata and cached `text_file` paths;
2. scan cached text for numeric experimental evidence with units;
3. assign metric hints such as titer, conversion, kinetics, LLPS, or condition;
4. map hints into the selected extraction schema;
5. write intermediate `numeric_evidence.csv` and `structured_records.csv`;
6. aggregate duplicate evidence groups into `clean_database.csv`;
7. write rejected/low-quality rows to `excluded_records.csv`;
8. write `summary.json`.

This preserves the practical intent of the old database scripts: turn cached literature text into a structured experimental database. It does not yet reintroduce automatic large-scale article discovery, PDF download, supplementary-material download, or LLM-based repair passes, because those need separate entitlement, copyright, and reliability handling.

## Literature search interfaces

Added `src/igem_drylab/literature/sources.py` for source search and manifest export.

Current providers:

- `openalex`: free metadata search through OpenAlex Works.
- `crossref`: free DOI/metadata search through Crossref Works.
- `elsevier_scopus`: Scopus search through Elsevier API, requiring `ELSEVIER_API_KEY`.

All providers normalize into `LiteratureSearchResult` and can be exported as the manifest format consumed by the offline database builder. The manifest intentionally leaves `text_file` empty because source search returns metadata, not guaranteed full text. A separate caching/downloader layer should fill `text_file` after entitlement and copyright handling are decided.

## Compatibility impact

- Existing `igem_drylab.kinetics` and `igem_drylab.structure_metrics` imports are unchanged.
- The old `igem_pipeline` package name from the M1-M4 branch is not preserved.
- The old `literature_extraction_agent` directory is not preserved.
- The new public CLI is `igem-drylab`.
- New MCP-style CLI commands are `igem-drylab tools list` and `igem-drylab tools call`.

## Known limitations

- M1-M4 is still lightweight by default. It can consume real SASA/docking/structure metric files, but it does not automatically run all heavy tools end-to-end.
- Literature extraction can build prompts and call OpenAI-compatible APIs through `ChatClient`, but no end-to-end paid API test is run in CI.
- Elsevier helpers require valid API entitlement; ScienceDirect full-text access may fail even if Scopus search works.
- API keys are read from environment variables such as `DEEPSEEK_API_KEY` and `ELSEVIER_API_KEY`, not passed directly in tool arguments.
- Compute adapters are real command wrappers, but the repository does not bundle ABCFold, CALVADOS, FreeSASA, Vina, SignalP, or DeepTMHMM binaries/environments.

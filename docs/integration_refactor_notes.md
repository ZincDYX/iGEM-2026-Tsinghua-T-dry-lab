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
| M2 fusion-risk scoring skeleton | Retained | Still a placeholder score, not real Boltz/Chai/ABCFold structural prediction. |
| M3 local concentration scoring skeleton | Retained | Still a placeholder score, not a fitted two-phase binding model. |
| M4 reaction recommendation skeleton | Retained | Still a placeholder recommendation, not a mechanistic ODE over the full pathway. |
| Literature OpenAI-compatible chat client | Retained and simplified | Suitable for DeepSeek-style chat-completions endpoints. |
| Literature ICL example selection | Retained and simplified | Deterministic rule-based selector. |
| Literature schema-first prompt construction | Retained | Output contract remains JSON records. |
| Elsevier Scopus/article helper functions | Retained minimally | Requires API entitlement; not tested against paid endpoints in unit tests. |
| Legacy all-in-one agent script | Not retained | Dropped because it mixed orchestration, defaults, cleaning, prompting, and execution in one large script. |
| Literature batch script collection | Not retained | Dropped until each script has a stable interface and test. |
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

They do not yet parse scientific output files into M1-M4 scores. The current M1-M4 scoring remains deterministic mock scoring. Parser integration should be added only after the exact output files from the lab/server installation are fixed.

## Compatibility impact

- Existing `igem_drylab.kinetics` and `igem_drylab.structure_metrics` imports are unchanged.
- The old `igem_pipeline` package name from the M1-M4 branch is not preserved.
- The old `literature_extraction_agent` directory is not preserved.
- The new public CLI is `igem-drylab`.
- New MCP-style CLI commands are `igem-drylab tools list` and `igem-drylab tools call`.

## Known limitations

- M1-M4 is still a mock/interface skeleton and does not perform real structure prediction, LLPS simulation, SASA, docking, or ODE pathway prediction.
- Literature extraction can build prompts and call OpenAI-compatible APIs through `ChatClient`, but no end-to-end paid API test is run in CI.
- Elsevier helpers require valid API entitlement; ScienceDirect full-text access may fail even if Scopus search works.
- API keys are read from environment variables such as `DEEPSEEK_API_KEY` and `ELSEVIER_API_KEY`, not passed directly in tool arguments.
- Compute adapters are real command wrappers, but the repository does not bundle ABCFold, CALVADOS, FreeSASA, Vina, SignalP, or DeepTMHMM binaries/environments.

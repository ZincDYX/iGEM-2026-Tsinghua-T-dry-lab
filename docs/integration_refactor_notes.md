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

## Compatibility impact

- Existing `igem_drylab.kinetics` and `igem_drylab.structure_metrics` imports are unchanged.
- The old `igem_pipeline` package name from the M1-M4 branch is not preserved.
- The old `literature_extraction_agent` directory is not preserved.
- The new public CLI is `igem-drylab`.

## Known limitations

- M1-M4 is still a mock/interface skeleton and does not perform real structure prediction, LLPS simulation, SASA, docking, or ODE pathway prediction.
- Literature extraction can build prompts and call OpenAI-compatible APIs through `ChatClient`, but no end-to-end paid API test is run in CI.
- Elsevier helpers require valid API entitlement; ScienceDirect full-text access may fail even if Scopus search works.

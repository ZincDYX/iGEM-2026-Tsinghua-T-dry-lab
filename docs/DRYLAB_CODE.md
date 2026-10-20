# Dry-lab scientific source — 20 October 2026

This update belongs to the research repository's **develop** branch, not the
public GALATEA-Caelum software repository. It adds current scientific code
without uploading experimental input files, simulation trajectories, result
bundles, credentials, private host settings or third-party predictor weights.
Existing repository history and legacy files are retained.

The scientific modules come from the local research revision `10162e0`.
[drylab_source_manifest.json](drylab_source_manifest.json) lists source and
published hashes. The DBTL supplement also contains the exact independent
kernel snapshot used for that study; it is deliberately separate from newer
research modules. Path adaptations affect I/O configuration only, not equations,
thresholds, candidate identities or numerical algorithms. The original local
files and completed results were not edited. Published text uses normalized line
endings and trailing whitespace; both original and published hashes are recorded.

## Scientific code map

| Layer | Source | Purpose |
| --- | --- | --- |
| M1 | `constructs/`, `m1_prioritization.py`, `prediction.py`, predictor adapters | Sequence features, construct identities, source-aware screening and localization/transport evidence |
| Adopted M1 run | `analyses/m1_29_constructs/` | Actual 29-construct input ordering, Q29 override handling, sequence/product extraction and predictor-output consolidation; Q08 remains excluded |
| M2 | `structural_workflow.py`, `template_geometry.py`, `region_assessment.py`, `membrane_geometry.py`, `structure_metrics.py` | Structure/reference selection, geometry, pocket/solvent access and static membrane compatibility |
| M2 preparation | `scripts/prepare_m2_models.py`, `prepare_m2_gpu.py`, `prepare_m2_pocket.py` | Inventory reusable exact sequence models, explicitly run missing predictions and prepare sourced pockets |
| ER static audit | `analyses/er_static/audit_geometry.py` | Saved 24-mer geometry and linker reachability checks; not complete membrane-MD validation |
| M3 | `m3_equilibrium.py`, `m3_er.py`, `m3_workflow.py`, `avidity_binding.py` | Mass-conserving enzyme recruitment, partitioning and declared uncertainty propagation |
| M4 | `full_network.py`, `kinetics.py`, `compartments.py`, `m4_compartments.py`, `m4_steady_state.py`, `m4_workflow.py` | Kinetic ODEs, conserved compartment amounts, exchange and explicitly defined outcomes |
| Matched DBTL supplement | `analyses/dbtl_20261020/` | Frozen matched-control model, parameter scans, LC feedback, identity audit and identifiability diagnostics |
| Wet-data processing | `wetlab/` | Source-preserving QC, comparisons, parameter-update proposals and evidence limits |

Paths in the first column's module descriptions are relative to
`src/igem_drylab/`, except where `analyses/` or `scripts/` is explicit.
The upload is not a claim that every optional external predictor, quantum
calculation, docking method or CG/atomistic simulation has been rerun or completed.
Legacy Agent benchmarks are not evidence for the maintained software's quality.

## Installation and pure-model checks

Use a separate environment from GALATEA-Caelum because both historical projects
use the `igem_drylab` Python namespace:

```bash
python -m venv .venv
# Activate .venv for your shell.
python -m pip install -e .
python -c "from igem_drylab.m3_equilibrium import M3EquilibriumInput, solve_m3_equilibrium; from igem_drylab.m4_compartments import CompartmentNetworkInput, solve_compartment_network; print('M3/M4 imports OK')"
python scripts/prepare_m2_models.py --help
python scripts/prepare_m2_gpu.py --help
python scripts/prepare_m2_pocket.py --help
```

Core dependencies include NumPy, SciPy, Pydantic, PyYAML, requests, Biopython and
jsonschema. Plotting additionally needs pandas/matplotlib. Optional methods need
their separately installed upstream software and applicable licenses: installing
this repository does not install predictor executables, weights or a GPU stack.
External execution remains an explicit action, not an import-time calculation.

## M1 adopted-construct pipeline

Provide original construct files, the corrected Q29 input, and an authorized
IUPred installation yourself. Example PowerShell configuration:

```powershell
$env:GALATEA_M1_INPUT_DIR = 'X:/project/constructs'
$env:GALATEA_CONSTRUCT_ARCHIVE = 'X:/project/constructs.zip'
$env:GALATEA_Q29_OVERRIDE = 'X:/project/Q29_override.dna'
$env:GALATEA_IUPRED_LIBRARY = 'X:/tools/iupred2a/iupred2a_lib.py'
$env:GALATEA_M1_OUTPUT_DIR = 'X:/project/new-m1-output'
python analyses/m1_29_constructs/run_m1_29_constructs.py
```

Consolidate separately obtained predictor outputs with
`analyses/m1_29_constructs/finalize_m1_results.py`, using the same output root.
Choose a new output directory; these historical analysis scripts are not a
replacement for immutable result archiving. Predictor licenses remain upstream.

## Frozen matched-control and LC analysis

Set `GALATEA_STUDY_ROOT` to a new external study directory. The scripts import
their frozen kernel from the adjacent `native/` directory, while reading and
writing study inputs/results in the configured external directory. Required
private inputs include:

- `inputs/PSv3_project.json` and `inputs/PS-v3/m3_phase_recruitment.csv`;
- `inputs/PS-v3/m4_kinetics.csv`;
- `inputs/LC.xlsx` for the independent chromatography reader;
- the construct/translation manifests and structural audit inputs when running
  the corresponding identity checks.

Those are owner-supplied study inputs, not files silently reconstructed from
final wet-lab outcomes. Consult each script's explicit file reads before running
a downstream diagnostic. Simulation preparation needs the PS-v3 inputs first:

```powershell
$env:GALATEA_STUDY_ROOT = 'X:/project/new-dbtl-study'
python analyses/dbtl_20261020/scripts/run_models.py prepare
python analyses/dbtl_20261020/scripts/run_models.py run
python analyses/dbtl_20261020/scripts/analyze_lc.py
python analyses/dbtl_20261020/scripts/audit_model_parameters.py
python analyses/dbtl_20261020/scripts/diagnose_identifiability.py
python analyses/dbtl_20261020/scripts/plot_results.py
```

Identity auditing additionally uses `GALATEA_CONSTRUCT_ARCHIVE` and
`GALATEA_Q29_OVERRIDE`. `verify_study.py` also requires the complete study's
archived manifests; merely downloading code is not sufficient for its historical
preservation checks. This upload therefore does not pretend to reproduce the
study's exact private-data outputs from an empty checkout.

The frozen matched-control results are conditional model predictions, not
measured yields. LC observations retain missing values and the original star
meaning; a star is not a statistical significance marker. The scripts do not
identify unique kinetic/partition parameters from endpoints or turn a static
ER geometry check into full membrane-system validation.

## Scope of this update

Upload verification passed 41 targeted scientific-model checks; four optional
checks were skipped and four CLI/MCP checks were deselected. The legacy
software-workflow localization test was outside this scientific-only migration
and was not included. M3/M4 imports, the existing CLI help and all three M2
preparation help commands were exercised. This is not a claim that the complete
historical Agent/software test suite or external predictors were revalidated.

Only research code, method-policy configuration and documentation are added.
No source `.dna`, LC workbook, result CSV, structure coordinates, trajectory,
third-party archive, `.env` or server credentials are included in the new commit.
The old repository already contains historical fixtures and examples; this
ordinary commit does not rewrite or remove them from history.

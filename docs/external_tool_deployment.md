# External-tool deployment contract

## Current scope (2026-10-13)

The user retains the **15 GB local deployment limit**, but explicitly removes
that limit for the authorized scientific validation server. For that deployment,
pass `budget_bytes: null` to `igem.compute.audit_deployment`. This still measures
and reports every configured root; it does not hide model/database sizes. Omitting
the argument still applies the 15,000,000,000-byte default. Old measurements below
are historical, not a current combined local/server size claim.

Original licensed distributions, model weights, databases, download links and
registration details stay in private installation directories, outside the source
repository, code bundle and desktop release. Downloading or compiling a tool is
not proof that an exact-project prediction or a complete M1/M2 result succeeded.

Installation-route labels such as `optional_local` do **not** waive steps retained
by a selected scientific protocol. Missing required predictions or simulations
must remain incomplete. Original catGRANULE, PScore and PSPredictor are distinct
methods; newer variants or distilled surrogates must not silently replace them.

## Historical deployment measurements

Measured on `validation host` on 2026-10-03 after the MCP runtime was installed. Byte counts are the conservative logical-file totals returned by `igem.compute.audit_deployment`. **User update (2026-10-04): the current limit is 15 GB = 15,000,000,000 bytes.** The recorded deployment is below that new limit. It was not below the original 10 GB requirement: treating that requirement as 10 GiB was an error. This is a historical measurement, not a fresh combined audit. No server files were removed during this correction.

## Lean deployed environment

| Deployment root | Bytes | Verified behavior |
|---|---:|---|
| `${PRODUCTION_ENV}` | 6,547,731,215 | ColabFold 1.6.2 GPU run; FreeSASA calculation; Vina 1.2.7 docking; Meeko import; JPred REST v1.5; BioLib CLI; MCP 2.3.0 server/client |
| `${MODEL_CACHE}` | 3,722,743,024 | Local AlphaFold/ColabFold parameter cache used by the GPU smoke run |
| `${DEPLOYMENT_ROOT}/drylab-tools` | 211,341 | Standalone NCBI SEG executable |
| **Total external deployment** | **10,270,685,580** | **4,729,314,420 bytes below the current 15 GB limit** |

Smoke-test inputs and outputs occupy another 758,346 bytes under `${DEPLOYMENT_ROOT}/drylab-tool-smoke`. The clean deployed source tree is separate from the external-tool budget and occupies 2,629,704 bytes. A fresh combined audit is needed before claiming the current deployment still meets 15 GB. The FusionLab plugin-directory budget alone is not a combined deployment-size guarantee.

Fresh read-only audit on 2026-10-04 used the same `audit_deployment` function with `budget_bytes=15000000000`, including all four roots above: **10,271,419,350 bytes, within budget**, leaving 4,728,580,650 bytes. The smoke directory contributes 733,770 logical file bytes. `du -sb` reports a different figure because its directory/hardlink accounting differs; the acceptance value here is the original per-file audit method. This budget is the declared validation host deployment, not unrelated environments or this workstation's developer/compiler caches.

The deployment audit must include these roots in the project YAML `deployment_paths` and call `igem.compute.audit_deployment` before a formal run. Nested paths are deduplicated by the audit. A real stdio MCP smoke call listed 18 tools, passed this audit, invoked `igem.compute.run_tool`, and wrote both FreeSASA output and its run manifest.

## Formal M1/M2 routes

| Capability | Selected route | Current verification |
|---|---|---|
| Disorder | local IUPred2A | real FASTA invocation succeeded |
| Secondary structure | official JPred REST API | service returned REST `v.1.5`; smoke job `jp_qO3dw1A` completed and its result archive was downloaded |
| Low complexity | local NCBI SEG | executable installed and help invocation succeeded |
| Protein properties | local Biopython ProtParam | package and project calculation tests succeeded |
| Signal peptide | SignalP 6 through official service/BioLib or academic/commercial portable route | BioLib client installed; an actual full prediction is not verified. Academic download and non-academic terms differ; do not assume every route needs a paid license/token. |
| Transmembrane topology | official DeepTMHMM/BioLib route | Official service is free for academic/commercial users; commercial own-server deployment requires a license. Academic users do not need a commercial license. Full prediction remains unverified. |
| Aggregation | TANGO academic/commercial distribution or PASTA 2 distribution | TANGO academic/non-profit research license is free. PASTA downloads require accepting the author's license; commercial/redistribution terms were not fully verified. No substitute score is generated. |
| Structure | local ColabFold GPU inference with public MSA for small serial jobs | real A100 inference produced PDB and confidence JSON artifacts |
| SASA | local FreeSASA Python API via `igem-freesasa` | real PDB calculation produced parser-compatible residue JSON |
| Docking negative screen | local Vina Python API via `igem-vina`; inputs prepared with Meeko | official `1iep` tutorial inputs produced a pose and recorded seed/box/energies |

Formal output still requires the project's exact full-length constructs, receptors, ligands, pocket residues, box definitions, and licensed predictor results. Smoke artifacts prove execution only and are not project evidence.

## Optional and metadata routes

`external_tools.py` catalogs installation routes for M0 metadata APIs, LLPS predictors, structure viewers, molecular dynamics, and alternative structure predictors. Scientific completeness follows the selected protocol, not an installation label. FuzDrop and PSPredictor are marked `manual_artifact`, not API, because no supported programmatic endpoint was verified; that does not complete or waive a required original step. A local ColabFold sequence database was excluded from the historical lean deployment, not prohibited on an explicitly unrestricted server.

## Commands

```bash
igem-freesasa --pdb model.pdb --output freesasa.json

igem-vina \
  --receptor receptor.pdbqt --ligand ligand.pdbqt \
  --center X Y Z --size SX SY SZ \
  --exhaustiveness 32 --num-modes 9 --seed 2026 \
  --output poses.pdbqt --summary vina_summary.json
```

For a real run, set the corresponding YAML tool to `enabled: true`, `mode: external`, and use these commands. The MCP tool `igem.compute.run_tool` executes that same command boundary and writes a run manifest; it does not emulate a successful predictor.

Deployment verification now takes explicit machine-local paths; no private deployment is preconfigured:

```bash
python scripts/verify_latest_review_tools.py \
  --results-root /absolute/new-results \
  --pdb /absolute/structure.pdb \
  --tool-config /absolute/tools.yaml \
  --deployment-root /absolute/tool-environment \
  --deployment-root /absolute/model-cache
```

Repeat `--deployment-root` for every tool/environment/cache included in the combined budget. Paper diagnostics require `--sources`; historical evidence packaging requires `--historical-python`. Historical report paths below/above are placeholders, not a claim that those directories exist on a new workstation.

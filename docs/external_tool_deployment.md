# External-tool deployment contract

Measured on `air-lab` on 2026-10-03 after the MCP runtime was installed. Byte counts are the conservative logical-file totals returned by `igem.compute.audit_deployment`; the hard budget is 10 GiB = 10,737,418,240 bytes.

## Lean deployed environment

| Deployment root | Bytes | Verified behavior |
|---|---:|---|
| `/mnt/data/dyx/miniconda3/envs/drylab-m1m2` | 6,547,731,215 | ColabFold 1.6.2 GPU run; FreeSASA calculation; Vina 1.2.7 docking; Meeko import; JPred REST v1.5; BioLib CLI; MCP 2.3.0 server/client |
| `/mnt/data/dyx/redirect/dongyuxin/cache/colabfold` | 3,722,743,024 | Local AlphaFold/ColabFold parameter cache used by the GPU smoke run |
| `/mnt/data/dyx/drylab-tools` | 211,341 | Standalone NCBI SEG executable |
| **Total external deployment** | **10,270,685,580** | **466,732,660 bytes below 10 GiB** |

Smoke-test inputs and outputs occupy another 758,346 bytes under `/mnt/data/dyx/drylab-tool-smoke`; even when counted, the total remains below 10 GiB. The clean deployed source tree is separate from the external-tool budget and occupies 2,629,704 bytes.

The deployment audit must include these roots in the project YAML `deployment_paths` and call `igem.compute.audit_deployment` before a formal run. Nested paths are deduplicated by the audit. A real stdio MCP smoke call listed 18 tools, passed this audit, invoked `igem.compute.run_tool`, and wrote both FreeSASA output and its run manifest.

## Formal M1/M2 routes

| Capability | Selected route | Current verification |
|---|---|---|
| Disorder | local IUPred2A | real FASTA invocation succeeded |
| Secondary structure | official JPred REST API | service returned REST `v.1.5`; smoke job `jp_qO3dw1A` completed and its result archive was downloaded |
| Low complexity | local NCBI SEG | executable installed and help invocation succeeded |
| Protein properties | local Biopython ProtParam | package and project calculation tests succeeded |
| Signal peptide | SignalP 6 through BioLib or licensed portable package | BioLib client installed; prediction is blocked until an authorized account/token or package is supplied |
| Transmembrane topology | DeepTMHMM through BioLib or licensed package | same authorization boundary as SignalP |
| Aggregation | licensed TANGO or PASTA 2 command-line distribution | blocked until the academic/commercial license artifact is supplied; no substitute score is generated |
| Structure | local ColabFold GPU inference with public MSA for small serial jobs | real A100 inference produced PDB and confidence JSON artifacts |
| SASA | local FreeSASA Python API via `igem-freesasa` | real PDB calculation produced parser-compatible residue JSON |
| Docking negative screen | local Vina Python API via `igem-vina`; inputs prepared with Meeko | official `1iep` tutorial inputs produced a pose and recorded seed/box/energies |

Formal output still requires the project's exact full-length constructs, receptors, ligands, pocket residues, box definitions, and licensed predictor results. Smoke artifacts prove execution only and are not project evidence.

## Optional and metadata routes

`external_tools.py` is the authoritative catalog for M0 metadata APIs, optional LLPS predictors, structure viewers, molecular dynamics, and alternative structure predictors. Optional tools are not installed merely because the Markdown mentions them. FuzDrop and PSPredictor are marked `manual_artifact`, not API, because no supported programmatic endpoint was verified. ColabFold's local sequence database is deliberately excluded because its documented database footprint alone is far beyond this budget.

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

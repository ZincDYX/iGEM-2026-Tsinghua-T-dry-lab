# FusionLab — fusion-protein and self-assembly workbench

FusionLab helps researchers import real protein/design inputs, calculate sequence
and structure risks, review evidence, and execute supported recruitment and
reaction models. The local-first Windows desktop includes Python and SQLite;
no team server, LLM or account is needed to open it.
It is intended for wet-lab researchers, dry-lab collaborators and other iGEM
teams; ordinary desktop tasks do not require editing Python or workflow JSON.

The generic workspace is separate from the Galatea glabridin reference model.
The original cytosolic model has eight metabolites and ten competing reactions.
ER anchoring is a separately versioned fixed-geometry extension, not silent
substitution of cytosolic equations. Missing tools or physical measurements
stay visible. Sequence descriptors and predicted structures do not prove enzyme
activity, LLPS, assembly, or improved yield.

Official source: [iGEM GitLab](https://gitlab.igem.org/2026/software/tsinghua-t/galatea).
Development mirror: [GitHub](https://github.com/ZincDYX/iGEM-2026-Tsinghua-T-dry-lab).
The requested FusionLab develop branch is not yet pushed: authenticated GitLab
access is pending. Main contains an independently changed version and will not
be overwritten. Check the exact branch/commit before installation.
The single [evidence index](docs/best_software_evidence.md) records submission,
build, real-case and validation status. Eligibility and independent non-expert
usability are not yet verified.

## Start the desktop

Obtain a verified Windows portable release from the team's distribution.
Extract the complete folder and double-click **FusionLab.exe**. Keep python
and resources beside it; Microsoft WebView2 Runtime is required. Read the
included English START_HERE.txt. This is a portable ZIP/folder, not a signed
single-file installer. Model weights and restricted predictors are not bundled.

Import your sequence/design, confirm its role, and choose an available task in
Tools or Workflow. M1/M2 do not require unrelated M3/M4 parameters. Follow the
specific tool/data gaps instead of entering sample physical values.

Default connection is Local. Optional Settings connect to your compatible
HTTPS API using an access token, **not SSH**. Addresses and credentials are
user-local, and Windows DPAPI protects stored tokens. The desktop neither
starts nor shuts down a remote service and does not default to a team server.

## Run a small real-input case

[Public GFP case](examples/public_gfp/README.md): import the supplied UniProt
P42212 canonical FASTA and calculate sequence properties. It needs no network,
restricted predictor or LLM after installation. From the source root:

```powershell
.venv/Scripts/python.exe -B scripts/reproduce_public_case.py --output outputs/public-gfp
```

The runner executes the real stdio MCP tool and checks mean hydropathy against
independent Biopython ProtParam. Read REPORT.md and result.json in the output.
This is one sequence-property task, **not complete formal M1–M4 or fusion/LLPS
validation**. Accession, source version, attribution and scope accompany it.

The separate [glabridin paper reproduction](docs/glabridin_reference_reproduction.md)
uses unchanged author code, raw parameters and Source Data. It reproduces
selected numerical figures and reanalyses published assays, not all omics, MD
or wet experiments. Source links, commands and discrepancies are recorded there.
Its historical environment must not be replaced by the product release lock.

## Locked source installation and build

Supported desktop target: Windows x64, Python **3.13.13**, Node **24.19.0**,
pnpm **10.30.3**, Rust **1.95.0**, and WebView2.
[Toolchain record](requirements/release-toolchain.json),
runtime/build locks, pnpm-lock.yaml and Cargo.lock are consumed by the common
release entry. Compatibility ranges are not release locks.

After the develop branch is synchronized and reviewed:

```powershell
git clone --branch develop https://gitlab.igem.org/2026/software/tsinghua-t/galatea.git
cd galatea
python -m venv .venv
.venv/Scripts/python.exe -B scripts/install_locked.py
.venv/Scripts/python.exe -m igem_drylab.cli software serve --port 8780
```

Until then, these new scripts are on the development mirror branch
feature/m1-m4-markdown-contract, not necessarily GitLab main.
For the browser frontend, in a second terminal:

```powershell
cd software/dashboard
pnpm install --frozen-lockfile
pnpm dev --host 127.0.0.1
```

Build a portable release from a clean committed checkout at the root:

```powershell
.venv/Scripts/python.exe -B scripts/build_release.py --output C:/FusionLab-release --download-cache C:/FusionLab-build-cache
```

Choose new user-owned output/cache directories. The script installs exact pins,
builds frontend/native embedded assets with frozen/locked flags, retrieves and
checks fixed official CPython, and invokes the existing single packager. It
does not replace old packages or include credentials, private data, test suites,
GPU weights or restricted tools. Dedicated locked CI uses the same entry.
Its actual acceptance status is in the evidence index; other OS native builds
and independent clean-machine acceptance are not claimed.

## Methods and extensions

- [M1 V3](docs/m1_v3_implementation_contract.md): exact descriptors and
  evidence-dependent negative screens.
- [M2 V2](docs/m2_v2_implementation_contract.md): mapped, confidence-gated
  geometry, SASA, docking differences and concrete site co-occupancy.
- [M3 S1–S5/E1–E10](docs/m3_s1_e10_implementation_contract.md): conserved
  recruitment with explicit units/applicability.
- [M4 Step 0–8](docs/m4_step0_step8_implementation_contract.md): complete
  ten-reaction competition, reviewed inputs and existence gates.
- [Implementation ledger](docs/r19_review_implementation.md): ER, recovery,
  Agent observations, real tools, tests and unfinished work.
- [Platform guide](docs/fusionlab_platform.md),
  [plugin development](docs/plugin_development.md),
  [tool deployment/terms](docs/external_tool_deployment.md), and
  [original Mpipi boundaries](docs/mpipi-original.md).

Start actual MCP with python -m igem_drylab.mcp.server. Tools and workflows call
the same scientific implementations, not parallel solvers. Trusted plugins
have versioned environments; a venv is not an OS sandbox. Optional LLM proposals
cannot approve scientific evidence themselves.

## Validation and licensing

Compatibility CI separately tests the Python 3.10 numerical floor and current
Python 3.13 range, not exact release reproducibility. Tests cover mathematical
oracles, data contracts, protocol, storage/recovery, UI and author regressions.
Project numerical/author acceptance runs on the designated compute environment,
not the desktop workstation. Green CI is not wet-lab validation.

Keep secrets in user settings/environment variables. Do not commit private
uploads, outputs, weights, trajectories or portable archives. Measure complete
clones with scripts/check_submission_size.py; ZIP or shallow checkout sizes
cannot establish official repository compliance. Never overwrite another
official tree or rewrite history to hide artifacts.

Project-authored code: [Apache-2.0](LICENSE), confirmed by the team.
[NOTICE](NOTICE) explains the scope. Third-party code, data, weights and services
retain their licenses/attribution. This does not grant restricted-tool access
or relicense paper data.

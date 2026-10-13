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
Complete FusionLab source is on **develop**. Main contains an independently
changed version and has been preserved. Check the exact branch/commit before
installation; the development mirror's oversized historical LFS archive is
not part of the official source history.
The single [evidence index](docs/best_software_evidence.md) records submission,
build, real-case and validation status. Eligibility and independent non-expert
usability are not yet verified.

## Local browser and CLI (no Rust required)

An already built Web wheel includes the production React page. End users need
the supported Python runtime, the platform lock and that wheel, not Node,
pnpm, Rust or a model account. A public download/hosted demo is not yet provided.
Install in a private virtual environment and run:

```text
fusionlab serve --open
```

The page and API share one origin. The browser receives a private HttpOnly
session automatically, so there is no token to copy. The service listens only
on 127.0.0.1. Stop with Ctrl+C; SQLite projects are retained in the user's
FusionLab workspace. If the port is occupied use `fusionlab serve --open --port 0`.
This is local single-user authentication, **not a public hosted login system**.

For builders, use exact Node/pnpm versions below, but no Rust:

```text
python -B scripts/build_web.py --output build/web-new
```

Use a new output directory. This produces a Web/CLI wheel with built assets;
it does not download scientific predictors. On Windows install the existing
root requirements. Linux x86_64 uses CPython 3.12.14 and the separate
`requirements/web-linux-py312.lock`, checked against an actual Linux runtime:

```sh
python3.12 -m venv .venv
.venv/bin/python -B scripts/install_locked.py --profile web-linux
.venv/bin/python -m pip install --no-deps build/web-new/igem_drylab_2026-0.1.0-py3-none-any.whl
.venv/bin/fusionlab serve --open
```

Source installation alone does not contain a prebuilt page. For Linux Docker,
`docker compose -f compose.web.yaml up --build` builds pinned base images and
dependencies; open `http://127.0.0.1:8780`. Stop with Ctrl+C; the named data
volume is retained. This route uses Linux host networking, **not Windows Docker
port publishing**. Container build/clean-machine acceptance remains pending;
no published/prebuilt image is claimed.

CLI and Web share the same SQLite project/revision, approvals and engine:

```text
fusionlab project create --name Study
fusionlab import examples/public_gfp/P42212.fasta --project <project-id>
fusionlab plan --project <project-id> --method sequence-properties
fusionlab workflow inspect <plan-id>
fusionlab workflow decide <plan-id> --accept
fusionlab workflow run <plan-id>
fusionlab jobs watch <run-id>
fusionlab results export <run-id> --format csv,json --output outputs/my-new-run
```

Use `fusionlab --json ...` for automation and `fusionlab --data-dir <workspace>
...` to choose another durable workspace. Return codes are 0 for completion,
2 for missing/invalid inputs or approval, and 3 for run failure/interruption.
`check-inputs --project <id> --through M2` and method `galatea-m1-m2` use the
existing scientific contracts; incomplete or unlicensed tools are not replaced
with example outputs. Public GFP descriptors are not formal M1–M4 validation.
See the [current parameter editing and review record](docs/review_r25_parameter_editing_20261012.md)
and [complete-input and IDR execution record](docs/review_r28_complete_inputs_and_IDRs_20261013.md)
for the latest native-tool jobs, actual-model browser checks and unresolved scientific evidence.
The [earlier review ledger](docs/web_cli_review_20261011.md) records historical validation
and external blockers; an entry point is not full biological validation.

File, folder and ZIP imports share one saved preview. Ambiguous FASTA asks for
DNA, RNA or protein; nucleic acids are not translated automatically. In the
browser, resume an unfinished import or add missing relative files to it. The
same operations are available without editing SHA values in the CLI:

```text
fusionlab import design.fa --project <project-id> --preview
fusionlab import-review <import-id> --project <project-id> --file design.fa --molecule-type DNA
fusionlab import missing-files-folder --project <project-id> --into <import-id>
fusionlab import-commit <import-id> --project <project-id>
```

CSV/TSV are fully shape/type-checked and need explicit measurement column roles
and units. JSON/YAML require a known schema or a chosen role. PDB/mmCIF/BCIF
retain model and author/label identities, but coordinates alone do not approve
confidence, enzyme identity or a functional pocket. Chemical identity parsing
requires an available RDKit chemistry profile; an unparsed SDF is an attachment,
not a verified substrate. SBOL/SBML semantic import remains pending. Uploaded
source files are never executed by normal Import.

Workflow has Graph/List views of the same saved definition. Select modules,
move them by pointer or arrow keys, add ordering dependencies, or remove an
unreferenced module. Data-reference edges are derived from actual input bindings,
not a second diagram. Cycles, missing required upstreams, unknown tools and known
incompatible IO types are rejected by the backend. Open saved workflows to resume
their view/selection/layout. Position changes do not alter computational approval;
dependency or execution-policy changes need a new reviewed and accepted proposal.
Run, checkpoint/scope, pause/cancel and retry controls live in Workflow, not the
global toolbar. Frozen run definitions and old scientific revisions are retained.

The CLI uses the same document and review service:

```text
fusionlab workflow draft <plan-id>
fusionlab workflow document <document-id> --project <project-id>
fusionlab workflow edit <document-id> --project <project-id> --upstream <module-id> --downstream <module-id>
fusionlab workflow edit <document-id> --project <project-id> --view list
fusionlab workflow review-draft <document-id> --project <project-id>
```

Select an original M1–M4 module in Workflow to inspect Tools and its calculation. Original
method versions, assumptions and discrepancies are retained; frozen runs show
their own recorded tool versions and parameters. In a historical run, click
**Edit as new run** to copy that run's actual model and sources, not a newer draft.
Click a bound value in the formula: Enter saves, Escape cancels; its unit is inherited.
Inputs not represented in a supported formula use a minimal Name / Value / Unit table.
The saved workflow stays selected. Review formal parameter
overrides before running; a pending replacement does not silently use its old value.
Scalar bindings use their admitted expression tree and create a new immutable executable version.
View → Assistant / Jobs panel are the only global panel controls.
Custom formula versions remain scientifically unvalidated and never replace an
original scientific kernel. LaTeX alone is not executable. Add an explicit scalar
expression, sourced values and units, then **Prepare exploratory workflow →
Review changes → Accept changes → Run**. Results retain the exact version and original
inputs after restart. Supported syntax, unit conversions and boundaries are in
[Custom formula execution](docs/custom_formula_execution.md).
General typed module/binding creation remains pending. Editing/reviewing is not
execution, scientific approval, or proof that an installed tool is validated.
Fixed baseline rules and unsupported model bindings remain read-only. Supported
typed ER quantities update both their versioned record and actual model reference;
plain reaction bindings still require a revised model and matched evidence.
Tools explicitly distinguishes reviewing a task from running an approved task.

Assistant retains project-scoped proposal history. Accept, Reject and Modify use
the same workflow engine; a revision shows its actual graph/policy changes and
requires new acceptance. Settings → Assistant defaults to None: manual
workflows do not require a model. Optional compatible/local model endpoints and
write-only keys are stored in the private workspace, outside scientific exports.
The connection test sends public test text only and can incur three small API
requests. Hosted deployments require an administrator endpoint allowlist; a hosted
server's localhost is not the user's computer. A streaming capability probe is not
a streaming chat interface, and software transport tests are not real LLM validation.

Tools → Tools & extensions shows actual registered capabilities, trusted plugin
source inspection/install/enable controls and editable instruction-only SKILL.md.
Registration is not readiness. Python plugin environments isolate dependencies,
not hostile code; install only trusted code. Importing Skills never executes their
scripts or approves evidence. Hosted raw shell access is unavailable; use your own
trusted local terminal for the documented CLI.

Inputs and Results open selected files directly in closeable named documents;
there is no independent Resources/Artifacts catalogue. PDB/mmCIF geometry supports rotation, chain selection,
reset and native PNG export. Original coordinates remain downloadable if WebGL is
unavailable. B-factors are not relabelled pLDDT; references need recorded mappings
and transforms, not an inferred alignment. Residue tables load only when requested.
Actual 1CRN display/lifecycle acceptance
and scoped loading measurements are recorded in
[the review implementation record](docs/web_cli_review_20261011.md).

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

## Build your own Windows desktop

The official repository contains the complete source. Its Releases/Package
Registry are currently disabled, so it does not yet provide a desktop download.
You can build a portable desktop yourself; you do not need to edit code or connect
to a team server. Use Windows x64 and allow internet access for dependencies.

Install these build prerequisites once, then reopen PowerShell:

These are the host tools, not individual Python packages. Python dependencies
are already pinned and installed automatically by the build command from the
root [requirements.txt](requirements.txt), which includes the existing runtime
and build locks without duplicating versions. Frontend dependencies are installed
from `pnpm-lock.yaml`; Rust libraries are installed from `Cargo.lock`.
`pip install -r requirements.txt` cannot install Python itself, Node, Rust,
Microsoft C++ Build Tools or WebView2.

1. [Git for Windows](https://git-scm.com/downloads/win).
2. [Python 3.13.13 x64](https://www.python.org/downloads/release/python-31313/).
3. [Node 24.19.0 x64](https://nodejs.org/dist/v24.19.0/).
4. [Rustup](https://rustup.rs/), with the Windows MSVC host. The command below
   prepares Rust 1.95.0 if missing without changing your global default.
5. [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/):
   select **Desktop development with C++**, including the Windows SDK.
6. [WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/)
   to run the desktop. It may already be installed. This is a runtime prerequisite,
   not a compiler. See the [official Tauri Windows prerequisites](https://v2.tauri.app/start/prerequisites/#windows).

From PowerShell:

```powershell
git clone --branch develop https://gitlab.igem.org/2026/software/tsinghua-t/galatea.git
cd galatea
powershell -NoProfile -ExecutionPolicy Bypass -File .\build-desktop.ps1
```

That single build command creates/reuses `.venv`, prepares pinned pnpm/Rust,
installs the locked Python/frontend dependencies, builds the production frontend
and native window, and calls the existing single release packager. It does not
install scientific predictors, run scientific models, change the global Rust
default, or silently install the large Microsoft compiler workload. Initial
compilation can take substantially longer than opening a prebuilt desktop;
you need free disk space for the compiler/dependencies/build cache. The final
package size is not the peak build workspace size. No build-time benchmark is
claimed.

After success, double-click **build/releases/FusionLab/FusionLab.exe**. To share
the software, use **build/releases/FusionLab.zip**; recipients extract the entire
folder and do not need Python, Node, Rust, Git or C++ Build Tools installed.
They still need WebView2. The exe is not a signed installer and must remain next
to its `python` and `resources` directories. Heavy/licensed predictors remain
optional and separately configured.

To check prerequisites without installing/building:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build-desktop.ps1 -Check
```

For multiple Python installations, add `-Python "C:/path/to/python.exe"`.
To keep an old package and build another, add `-Output "C:/FusionLab-new"`.
Use a clean committed Git checkout, not the automatically downloaded source ZIP:
the existing packager records and archives the actual Git commit. The script
does not delete dirty files or overwrite an old release. `ExecutionPolicy Bypass`
applies only to the new PowerShell process, not the machine/user policy.

## Locked backend installation and advanced build

Supported desktop target: Windows x64, Python **3.13.13**, Node **24.19.0**,
pnpm **10.30.3**, Rust **1.95.0**, and WebView2.
[Toolchain record](requirements/release-toolchain.json),
runtime/build locks, pnpm-lock.yaml and Cargo.lock are consumed by the common
release entry. Compatibility ranges are not release locks.

If you only want to install the pinned Python dependencies, use the supported
Python version and a virtual environment:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

This installs Python dependencies only, not FusionLab itself, external scientific
tools or a desktop executable. For the complete backend, use `install_locked.py`
below; for an exe, use `build-desktop.ps1` above. Both use the same requirements
entry automatically, so users do not need to run the dependency-only commands
before building the desktop.

Clone the official develop branch:

```powershell
git clone --branch develop https://gitlab.igem.org/2026/software/tsinghua-t/galatea.git
cd galatea
python -m venv .venv
.venv/Scripts/python.exe -B scripts/install_locked.py
.venv/Scripts/python.exe -B scripts/build_web.py --output build/web-new
.venv/Scripts/python.exe -m pip install --no-deps build/web-new/igem_drylab_2026-0.1.0-py3-none-any.whl
.venv/Scripts/fusionlab.exe serve --open
```

The built browser route needs no second Vite terminal. Advanced frontend
development uses the explicit local development API/proxy, not a public default
token; the normal browser entry above remains authenticated.

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

Annotated GenBank import retains the original nucleotide records, full source
annotations, strand, fuzzy/compound locations and CDS-to-protein references.
Only source-supplied CDS translations create proteins; DNA-only/contig-only
records remain designs, not guessed protein sequences. Inputs provides paged
DNA/features and exports the unchanged original GenBank. Editing a protein
does not edit its source DNA: disagreement is shown explicitly. This is source
preservation, not a redesigned-DNA writer, SBOL or SBML implementation.

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

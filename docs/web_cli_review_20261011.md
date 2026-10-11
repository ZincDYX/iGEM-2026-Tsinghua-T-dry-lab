# Web/CLI review implementation and acceptance ledger

Review baseline: official develop `34e0f3ec366555bb4917dba6e641c60d8c332d6e`.
Implementation starts from its byte-identical development mirror tree.
This ledger is not a claim that the whole review or award criteria are satisfied.

## Batch 0: scientific admission, before interface changes

The original M1 V3, M2 V2, M3 S/E and ten-reaction competitive-MM rate laws,
ER exchange equations and biological inputs are unchanged.

- SCI-01: M2 records site species, actual enzyme fusion identity, ligand, domain
  and binding-pair source. M3 must match those registered identities, not just a
  site's arbitrary name. Legacy unidentified sites remain blocked.
- SCI-02: steady-state search includes the initial compatibility class. The
  left nullspace of active stoichiometry includes only invariants not broken by
  actual feed/loss boundaries. Both RHS and amount constraints must pass their
  separately declared tolerances. Residuals are normalized by those tolerances;
  this changes numerical admission, not the rate law or biological parameters.
- SCI-03: each concrete membrane pose is eligible, conditional or excluded.
  Recorded static clash/side/tether rules determine the pose, not global rejection
  of the construct. Conditional/low-confidence poses are not deterministic capacity.
- SCI-04: matched controls also compare each initial metabolite's total amount,
  total reference volume, feeds and loss conditions. Pool distribution can differ;
  total bolus cannot. The same explicitly supplied comparison tolerance is used.
- SCI-05: total amount and invariant residuals now gate numerical admission.
  Failed admission retains trajectories and residuals; it does not clip data or
  adjust biological parameters. No downstream ER stage accepts the failed status.

Server-only tests: `test_web_cli_scientific_admission.py`,
`test_r19_er_equations.py`, `test_r19_er_stage_bindings.py`,
`test_r19_membrane_geometry.py`. Fixtures are explicitly synthetic mathematical
oracles, not project measurements, real predictor jobs or experimental validation.
Initial 24-test run passed after fixing residual scaling; the expanded four-file
server suite passed 25 tests (4.82 s). This is targeted admission regression,
not the entire scientific/author suite.

Implementation references: [SciPy null_space](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.null_space.html)
and [bounded least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html).
The source methods remain the four existing implementation contracts and
the independently versioned ER contracts; these numerical-library references do
not provide or replace biological parameters.

## Batch 1: shared application and installed local browser entry

Project saving, import preview, input checks, workflow validation, approved run
creation and CLI execution now use `software/application.py`, the existing
PlanningService/store and the same WorkflowEngine. The old import parser was
moved, not copied into a competing CLI implementation. Typed import transactions
and the remaining HTTP-only service operations are subsequent work.

`fusionlab` exposes project/import/check/plan/inspect/decide/run/watch/export/serve
commands with JSON output and distinct blocked/run-failed return codes. It binds
approval to the saved revision; repeating an approved run returns the same job.
The source Web builder uses exact Node/pnpm and Python packaging pins but no
Rust. Its wheel carries the built SPA. Same-origin relative API requests receive
an origin-checked private HttpOnly loopback cookie; unknown API/assets remain
404. Existing optional desktop transport is retained. This bootstrap is not
public hosted authentication or a host-shell grant.

Evidence collected for this batch:

- Windows software-only HTTP/session/CLI persistence/lock suite: 18 passed.
- Frontend unit suite: 61 passed in 23 files. The initial failure was an obsolete
  App navigation fixture that did not accept the schema query parameter; fixed
  the fixture, not the error assertion or API contract.
- Compute-server shared-service/admission suite: 34 passed, 10.62 s. The first
  snapshot omitted generated contracts and failed one schema-file test; after
  shipping the actual generated source, the complete suite passed.
- Real UniProt P42212 (238 aa) CLI run, explicit approval, idempotent repeat,
  original-precision CSV/JSON export, independent ProtParam molecular-weight
  oracle and Web read after restart passed on the server. Sequence descriptors
  are not formal M1 screening, transfer-case validation or LLPS evidence.
- Actual built-wheel browser test outside the checkout passed (17.4 s): Inputs
  is the only initial tab; no token entry/desktop bridge; HttpOnly cookie; real
  annotated GenBank preview/save/reload/original-byte export; no browser errors;
  missing asset remains 404. A 1280x800 screenshot and video were recorded.
  This is software acceptance by the developer, not five independent novices.
- Linux CPython 3.12.14 actual installed dependency closure: 49 runtime pins
  verified. It is a pre-existing configured server environment, not a fresh
  machine installation. Linux GitLab CI now consumes this independent lock.
- Docker/compose source pins verified registry manifest identities and restricts
  the service to Linux host-loopback networking. Image build, new clean-machine
  install, published download/image and hosted deployment are **not yet verified**.

Implementation sources: [Starlette cookie responses](https://starlette.dev/responses/)
and [Docker image pinning/build guidance](https://docs.docker.com/build/building/best-practices/).
No screenshot/test result substitutes for the remaining review criteria.

## Batch 4 (partial) and independent PS-v3 integration

Amount-model output now records each actual pool volume and its original typed
source. A single typed projection checks amount/concentration against those
volumes and the declared numerical tolerance; tables, plots and CSV use this
same recorded projection. Missing data remain missing. Outer synthetic flags
survive nested valid results. Conditional real data are not relabelled synthetic.
No biological equation or parameter was changed for display.

Run summaries distinguish job state, recorded numerical checks, evidence state
and experimental validation. PS-v3 explicitly includes blocked E3 alongside
the four solved demonstration scenarios. No experiment is claimed validated.

The corrected external package is not redistributed in Git. Only canonical
parameters and solver-input templates are read: uploaded scripts, archived
material and reference outputs are not executed or treated as new results.
The existing approved WorkflowEngine runs the original M3 and competitive
amount-model M4 kernels. The formal evidence path rejects synthetic input,
including synthetic outer wrappers containing an inner valid result.

Actual compute-server evidence:

- Corrected C1/C2/E1/E2 endpoints (µmol, 240 h): 2380.9388642547897,
  2937.4999999999973, 2838.2776234100697, 2937.4999999999995.
- Independent rounded endpoint oracles and canonical-only perturbation: two
  real-kernel tests passed. Conservation and M3 mass recovery, idempotent run,
  pool-aware display and original-precision CSV were checked by the runner.
- Scientific admission/ER and format suite: 34 passed. This is not the full
  author/scientific regression suite.
- The first engine run rejected absolute artifact paths at the disclosure
  boundary. Native synthetic outputs now use the existing registered-asset
  projection, not a weakened disclosure check; the rerun succeeded.
- Actual browser import → proposal → explicit accept → server computation →
  E1 M3 table/Plotly time course → CSV passed in 9.7 s. The first browser attempt
  computed successfully but used a nonexistent Results button; corrected the
  test to the actual result navigation. Screenshot/video were recorded.
- Local software boundary/execution suite: 56 passed; subsequent projection,
  archive and display checks: 29 passed. Frontend: 61 tests and production build
  passed. These do not establish real WebGL/20-cycle or novice-user acceptance.

`scripts/reproduce_ps_v3.py` refuses an existing output directory and retains
the synthetic scope in JSON/CSV. Use the compute deployment, not a workstation
where scientific regression is prohibited. E3 and all formal experimental
claims remain blocked. General typed import transactions and the remaining
Results/structure acceptance requirements are still pending.

## Batch 2: unified saved input transactions (partial review completion)

Web, File-menu file/folder import, ZIP and CLI now use one ParserRegistry and
project-scoped ImportService. Inputs shows Biological data and Analysis plan
and configuration. The redundant standalone ScientificBundleImporter UI was
removed; original versions remain recoverable from Git history.

Preview IDs and immutable source assets survive restart. Molecule choices,
table roles/units, source identities and duplicate decisions are explicit.
Commit is project-revision checked and atomic. Missing dependencies can be
appended without retransmitting/reparsing unchanged originals; relative paths
cannot escape the transaction. Multiple project configs cannot silently use
the last file. Unknown configuration trees or non-measurement tables can be
explicitly retained as evidence rather than treated as model inputs.

Native GenBank metadata and missing translations are retained. PDB uses the
existing native model-scope parser; mmCIF/BCIF retain auth/label identities and
insertion codes. Water/ligand residues are not invented amino acids in sequence
binding proposals. No B-factor is labelled pLDDT. Typed path/hash credentials
are supplied from project-owned registered assets in the backend; supplied
conflicting identities are rejected. Source/condition/unit gates remain intact.

Actual acceptance evidence:

- Compute-server full suite with immutable author inputs and actual original
  LAMMPS/2PDZ references: 890 passed, 12 skipped (103.37 s). Nine skips require
  the separate FreeSASA profile; the other three are Windows-only entry tests.
- The existing chemistry/structure tool profile separately ran 56 tests,
  including real FreeSASA/2PDZ and original LAMMPS potential oracles: all passed.
  No second scientific installation was downloaded.
- Updated shared-import PS-v3 browser → explicit approval → actual compute
  server → E1 table/Plotly → scoped CSV chain passed (8.7 s).
- Original supplied M1/M2 server data: eight files / 6,141,204 bytes imported
  without user SHA fields; six confirmed actual design/baseline proteins,
  15-model/30-protein-chain 2PDZ, and 24 distinct label-chain FTH1 assembly were
  checked. The initial acceptance script incorrectly expected 15 chains rather
  than 15 models; corrected against independent Biopython model/chain identities.
  All original structure/pocket applicability warnings remain. This is actual
  format/data integration, not formal M1/M2 completion.
- RDKit is absent from the selected light runtime. The actual SDF is explicitly
  retained with chemistry_runtime_unavailable; no chemical identity was fabricated.
- Three actual installed-wheel browser tasks passed (16.4 s): same-origin
  session/GenBank preservation, restart/review of ambiguous DNA without protein
  conversion, and adding a missing configuration dependency. No solver ran on
  the workstation. Screenshot/video and original-file export were recorded.
- Frontend suite: 61 passed with one bounded worker. Earlier concurrent Node
  workers failed allocation on the workstation; those runs were failures, not
  passes. A separate browser test initially read state before commit finished;
  it now waits for committed preview closure. Existing GenBank protein records
  are preserved, not incorrectly expected to disappear during DNA import.
- Build cache contained obsolete Python/frontend files. The release builder
  now cleans only its verified generated package directory. Actual same-source
  Web wheel decreased from 5,510,428 to 3,218,009 bytes, with source/history kept.
  The real setuptools isolation test and clean installed-wheel/browser passed.

Still pending in this input batch: contextual Add/Use/Defer inspector actions,
full typed parameter/measurement binding and AnalysisPlan opening into editable
Workflow, standard-library SBOL/SBML semantic import and actual chemical-profile
execution. No scientific equation, biological default, solver tolerance or
scientific approval was changed by these interface/import/build changes.

## Batch 3a: persisted Graph/List and Workflow-only execution controls

Web and CLI now use WorkflowDocuments through ApplicationService. There is no
second graph, scheduler or scientific implementation. A single Workflow model
supplies data/reference and ordering edges, including fan-out. Scientific
definitions are stored once per semantic revision; the latest layout, selection
and view are stored separately, not repeated full scientific snapshots on every
click. Layout-only requests do not retransmit the workflow or revalidate unchanged
tool inputs. Identical state saves are no-ops. Semantic history remains immutable.

Backend checks cycles, required upstreams, policy scope, registered tools, static
typed values/project bindings and declared output/input primitive types. MCP uses
its actual input schema rather than its empty transport wrapper. Open/unspecified
output schemas are not falsely called type-proven; native dispatch validation and
all existing scientific binding/gate checks still apply. Revision/project conflicts
cannot overwrite another operation. Typed graph errors survive Pydantic/HTTP/CLI
wrapping and yield readable safe messages, not raw source strings or private traces.

Graph/List share selection; pointer/keyboard movement and re-opened view/layout are
saved. Removing a required upstream displays affected modules and is rejected,
without injecting placeholders. The existing list remains the detailed job/science
status view. Changed graphs cannot start the old accepted proposal. Review changes
uses the existing PlanningService and preserves document identity/history/layout.
Policy edits save a semantic revision of that exact graph; they do not silently
replace a custom graph with a template. Frozen run policy cannot be edited in place.

Duplicate top-level Import/Save/Inspect proposal and Tools-menu run controls were
removed. Run/review/scope/pause/cancel/retry controls are in Workflow. Primary
navigation is Inputs / Workflow / Results; the tree shows the active context's
categories, modules or run results rather than all three simultaneously. Contextual
object selection, full Assistant and general result presentation still need work.

Actual acceptance records:

- Compute-server full regression: 903 passed, 12 skipped (108.02 s), including
  immutable author regression and original LAMMPS cases. The separate existing
  native structure/chemistry profile: 56 passed (6.98 s), real FreeSASA/2PDZ and
  original LAMMPS checks. No scientific computation was run on the workstation.
- Native API/CLI/editor software tests verify history, no created jobs, cycles,
  deleted upstreams, declared IO mismatch, source ownership, concurrency, stale
  approval, and the actual MCP-schema boundary. These are not biological oracles.
- Final frontend software suite: 67 passed in 24 files (44.33 s), one bounded
  worker. Final installed-wheel browser suite: four passed (27.3 s), including
  shared Graph/List, real fan-out edges, keyboard/pointer movement, restart,
  invalid-edit recovery and absence of jobs. The delivered Web wheel is
  3,228,236 bytes; production use does not require Node or Rust. These are software
  tasks, not scientific execution on the workstation.
- Final installed Web package/server synthetic PS-v3 chain passed (10.5 s):
  corrected package → approval → original M3/M4 kernels → result table/Plotly →
  exact scoped CSV. E3 remains blocked and experimental validation unestablished.
- A browser fixture initially received 403 because its direct REST helper lacked
  the browser-origin checks. It now seeds metadata through a real same-origin
  browser fetch; authentication/CSRF rules were not weakened.
- Real pointer acceptance found a stale click-suppression flag after dragging;
  removed the unnecessary flag and re-ran the real browser. No test-only bypass.
- Generated TypeScript incorrectly described annotation-only Any schemas as
  objects, excluding valid JSON arrays/primitives. Generation now maps that
  unconstrained schema to equivalent boolean true for TypeScript only; runtime
  Pydantic/Ajv validation semantics and scientific values are unchanged.

Still incomplete: full MethodRegistry/formulas and scientific parameter UI;
general typed node/tool creation and data-binding edits; deep compatibility for
all structured IO schemas; comprehensive module status badges in Graph; Inputs
Add/Use/Defer; the remaining Results/Assistant/Tools/Skills/model/terminal tasks;
schema-family lazy loading, real WebGL/lifecycle/performance acceptance and external
experimental/user/publication evidence. No new biological parameter, approximation,
method equation or relaxed gate was introduced.

## Remaining review acceptance tasks

| ID | Required outcome | Current status |
|---|---|---|
| WEB-01 | Authenticated same-origin local Web package, Linux lock, container and clean startup | Local installed-wheel/browser and existing Linux closure verified; container/clean deployment pending |
| CLI-01 / ARCH-01 | Shared application services and durable CLI workflow | Core project/approval/run and persisted typed-import parity verified; remaining route/service extraction pending |
| IN-01 | Inputs first, two regions, default project and single import controller | Verified file/folder/ZIP shared transactions and installed Web first-start/browser import |
| IN-02 | Typed format registry, transactions and ambiguity handling | Required core format/recovery/relative-binding paths verified; chemical profile, SBOL/SBML and full measurement/parameter binding pending |
| IN-03 | Contextual gaps with Add/Use/Defer actions | Pending |
| IN-04 | Server-calculated asset identity, no user SHA entry | Registered typed file references obtain hashes server-side; ownership/conflicting identities still rejected |
| WF-01 | Graph/List editing of one workflow revision | Shared persisted graph/list, movement, selection/recovery, revision and dependency rejection verified; general typed module/binding creation and full IO compatibility pending |
| WF-02 | Versioned full method formulas, tools and parameter records | Pending |
| WF-03 | Save/review/run and controls only in Workflow | Existing-engine review, graph/policy stale-approval protection and Workflow-only controls implemented; full final UI acceptance recorded per batch |
| RES-01 / SCI-06 | Grouped results, independent job/numeric/evidence/validation status | Four-state summary and synthetic tables verified; general module grouping pending |
| RES-02 / SCI-07 | Pool-aware ER tables/curves and actual viewer acceptance | Typed actual-volume projection and CSV verified; real structure/WebGL/lifecycle acceptance pending |
| AG-01 / AG-02 | Persistent conversational proposals/diffs/decisions using existing engine | Pending |
| AG-03 | Tools, plugins and skills with real capability tests | Pending |
| AG-04 | Model settings, write-only secrets, local/hosted endpoint boundaries | Pending |
| JOB-01 | Structured Jobs/Output/Problems and mode-safe terminal | Pending |
| UI-01 / UI-02 / UI-03 | Single menu, inline tabs, contextual tree and English messages | Single menu/inline tabs existed in batch 1; redundant top controls removed and primary context navigation added; full object selection, diagnostics consolidation and language/visual audit pending |
| PERF-01 | Measured baseline, schema split, viewer/resource lifecycle | Pending |
| Synthetic PS-v3 | Original corrected package, separate runner and inherited scope | Original kernels, independent endpoints, canonical perturbation and browser/server chain verified; separate synthetic scope, E3 blocked |
| Publication | Final designated repository, Wiki, Village and award registration | Owner confirmation required; no relocation/registration mutation |
| Validation | Real independent experiment, real transfer case, five novice-user sessions | Requires corresponding data/people; software fixtures are not substitutes |

Do not interpret a pending row, a passing software test or a completed job as
formal M1–M4 readiness or experimental validation.

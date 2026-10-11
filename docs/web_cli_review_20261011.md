# Web/CLI review implementation and acceptance ledger

Current Results / formula / purple-interface changes and their acceptance are
recorded in [r24](review_r24_simplification_20261012.md). The batches below retain
their historical scope; their earlier UI descriptions are not current instructions.

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

## Batch 3b: one module-status presentation and contextual problems

Graph and List now share backend-provided numerical/evidence counts and the
run-level experimental-validation assessment. A completed job is not a passed
scientific record. Missing records say Not assessed, not zero or approved. An
edited semantic workflow cannot inherit a completed badge from a previous run
with the same node identities. Input checks must match the run's project and
revision; a similarly named tool does not inherit a native stage's omissions.

The independent Diagnostic inspector tab is removed. Scientific boundaries
open Workflow's source context; the selected module explains its recorded scope.
Selected job errors and suggested actions appear in Problems, without dumping
raw diagnostic identifiers or the result payload again. Full Jobs/Assistant and
result redesigns remain pending. Two sibling workflow components had identical
React keys; they now have distinct component identities. Existing saved layouts
are preserved. Arrange modules is an explicit layout-only action, not a graph or
scientific-method edit, and frozen runs cannot be rearranged in place.

Actual browser inspection also found a stale saved-workflow selector: its cached
option could show an older revision than the editor. Options now derive from the
one current document, not another copied state. Reopening fetches the authoritative
document; a late read cannot overwrite a newer saved revision. Reopening the tab
also adopts newer backend revisions instead of unconditionally keeping stale root
state. Browser acceptance changes the same document through the real API while
the tab is closed, then verifies the new name, revision and intact graph on reopen.

Final frontend suite: 76 passed in 25 files (190.51 s), one 384-MB-bounded worker.
TypeScript and production build passed. Earlier full runs were interrupted under
low available workstation RAM, or failed because the old status test expected
the previous combined label. The updated test still requires completed job,
zero solved/ready records, missing evidence, stale input check and unestablished
experimental validation separately. No assertions or scientific gates were
removed. A targeted App rerun used a longer software-test timeout, not a changed
solver tolerance. These timings are not a controlled performance comparison.

The retained server frontend installation lacks newer build/schema/viewer
packages. A reuse-only attempt did not pass its dependency/type checks; it was
not reported as a clean Linux frontend build and no packages were installed.
Local build here used Node 24.13.1 with pinned package versions, not the specified
Windows release-builder Node 24.19.0. Clean locked release/build acceptance is
therefore still pending; this does not turn the tested wheel into a fully
verified desktop release. The own Web wheel is 3,228,824 bytes, installed with
no additional dependencies. No M1–M4 equation, parameter or backend changed in
this UI-only batch; the batch-3a server scientific regressions are unchanged.

Latest installed-wheel local browser acceptance: four passed (1.4 min), including
actual Graph/List, fan-out, drag/keyboard movement, rejected invalid edits, latest
backend revision on tab reopen, layout-only arrangement, contextual boundaries and
no created jobs. No solver ran on the workstation. This is not an updated EXE.

The first server-connected browser attempt could not connect to the expired
private forwarding session; no scientific job started in that attempt. After
restoring the owned test connection, actual kernels completed but the cold plot
missed the default five-second UI wait. A separate real-browser probe of the
recorded run rendered the actual Plotly chart in 7,235 ms after selecting E1,
without page/request errors. It measured a 4,969,017-byte Plotly chunk and a
1,089,876-byte initial API chunk; this confirms performance work remains, not
that this UI batch made plotting faster. The plot wait is now bounded at 20 seconds
for browser acceptance only; solver tolerances and scientific gates are unchanged.
Final installed-UI server browser acceptance passed (26.5 s task / 33.4 s total):
the corrected package ran original M3/M4 kernels, the actual plot rendered, exact
CSV retained all 49 recorded points, and Graph/List both showed job completion,
4/5 solved scenarios, 0/5 evidence-ready and run validation not established.
E3 remains blocked; none of these synthetic results is a formal project prediction.

No external dependency/tool was added in this batch. The prior declared installed
runtime/tools audit was 14,947,229,119 bytes. Conservatively adding the owned active
server acceptance package (11,917,527), latest frontend (10,095,231), and local test
installation (12,385,364) gives 14,981,627,241 bytes, below the decimal 15-GB limit.
This uses the documented runtime/tool scope, not total disk occupancy; inactive
source/build archives and scientific output records are not installed tools.

Official develop's batch-3a push was verified byte-identical to the source tree;
main was preserved. Full local history/source/LFS conservative accounting was
37,462,812 bytes, below the internal decimal 50-MB limit. The read-only GitLab
API reported repository storage of 5,399,861 bytes, with no LFS payloads; its
statistics are not official freeze/eligibility confirmation. The latest job
remained pending without an assigned runner, with shared runners disabled and
runner-list access denied. CI success is not established; repository-owner
runner configuration is separate from local test success.

## Batch 3c: explicit execution scope, one review action and frozen settings

The obsolete stage-step and selected-stage review shortcuts are removed. Run
through module and pause/checkpoint settings use the existing execution policy;
they do not create another plan, scheduler or scientific gate. Workflow has one
Review plan action, whether checking inputs, awaiting acceptance or revising an
accepted plan. It submits the current saved graph to the existing custom-proposal
service instead of replacing that graph with a generated template. Review is not
run submission or scientific parameter approval.

Frozen run settings now come directly from that run's immutable workflow, not
from the editable draft policy. Completed frozen runs cannot show another draft's
Start or Review action. Actual pause/cancel/retry/resume controls are retained when
appropriate. Checkpoints display module names instead of internal identifier lists.
The document title/language is English; this does not establish the remaining
whole-product language audit.

The first full software run was interrupted after abnormally long execution and
test failures; the underlying workstation interruption is not established as the
cause of every failure. A new frozen-input test also incorrectly checked an input's
own disabled property instead of its actual disabled state inherited from the
fieldset. That assertion is corrected, not removed. The targeted 12-test App and
control suite passed (93.87 s), covering the frozen snapshot, preservation of custom
dependencies/scope in review, stale acceptance and existing request-race guards.
The full frontend suite passed 80 tests in 26 files (301.07 s). TypeScript then
found two unsupported Testing Library query options in the new test; they were
corrected. The App/control suite passed again, 12 tests (58.63 s), after removing
the redundant review-eligibility prop (already determined by frozen state).
TypeScript and production build passed. Final installed-browser acceptance is
recorded below when complete. No backend,
scientific equation, biological parameter, numerical tolerance or tool changed.

Batch-3b official source/history/LFS conservative size passed at 40,323,100 bytes.
The subsequent read-only GitLab status/runner query failed with TLS EOF; current
pipeline success is not established. Previous pending/unassigned-runner evidence
cannot be reported as the latest pipeline outcome.

The latest own Web wheel is 3,228,846 bytes; installed local browser acceptance
passed four tasks (1.6 min). Beyond the prior import/editor tasks, it actually
saved the call budget and target module, reviewed that same custom graph without
template replacement, retained its two modules, and reopened the later backend
revision. No job was created, and no solver ran on the workstation. Production
installation needs no Node/Rust, but the clean locked release and updated desktop
EXE are still not validated by this batch.

No external tool/dependency was installed. Using the same declared audit baseline
and conservative active acceptance additions, the new total is 14,981,628,197 bytes
(server package 11,917,527; current UI 10,095,710; local installed package 12,385,841),
below 15,000,000,000 bytes. This is the runtime/tools scope, not total disk usage.

The latest installed-UI server browser task passed (37.6 s / 44.8 s total): it
edited the call budget and target module, reviewed/accepted the exact current
workflow, ran original synthetic M3/M4 kernels, rendered the real Plotly curve and
exported all recorded CSV points. The recorded run displayed its frozen budget
and target as disabled, with no draft Start/Review action. Graph/List retained
4/5 solved, 0/5 evidence-ready, not-established run validation and blocked E3.
These are actual server computations within explicitly synthetic scope, not
wet-lab validation or completion of formal M1–M4/ER inputs.

The final read-only GitLab query succeeded after bypassing the workstation's
environment proxy for this private diagnostic only. The prior UI batch did not
fail tests: GitLab reports `stuck_pending_no_matching_runners`, no assigned runner,
about 3,963 s queued and an empty job trace. The latest code job is pending, again
without an assigned runner; shared runners are disabled. This establishes a runner
scheduling failure, not a source-code failure or successful CI run. It does not
establish whether a group runner can be enabled. A repository/runner administrator
must provide an eligible runner; no runner was registered, installed, enabled or
given private compute access in this task. Latest reported repository storage is
5,540,361 bytes with zero LFS; it is not official freeze/eligibility confirmation.

## Remaining review acceptance tasks

| ID | Required outcome | Current status |
|---|---|---|
| WEB-01 | Authenticated same-origin local Web package, Linux lock, container and clean startup | Local installed-wheel/browser and existing Linux closure verified; container/clean deployment pending |
| CLI-01 / ARCH-01 | Shared application services and durable CLI workflow | Core project/approval/run and persisted typed-import parity verified; remaining route/service extraction pending |
| IN-01 | Inputs first, two regions, default project and single import controller | Verified file/folder/ZIP shared transactions and installed Web first-start/browser import |
| IN-02 | Typed format registry, transactions and ambiguity handling | Required core format/recovery/relative-binding paths verified; chemical profile, SBOL/SBML and full measurement/parameter binding pending |
| IN-03 | Contextual gaps with Add/Use/Defer actions | Pending |
| IN-04 | Server-calculated asset identity, no user SHA entry | Registered typed file references obtain hashes server-side; ownership/conflicting identities still rejected |
| WF-01 | Graph/List editing of one workflow revision | Shared persisted graph/list, movement, selection/recovery, revision, backend status counts and dependency rejection verified; general typed module/binding creation and full IO compatibility pending |
| WF-02 | Versioned full method formulas, tools and parameter records | Source-preserving M1 V3/M2 V2/M3/M4 and separate ER registry, actual frozen tool/parameter snapshots and linked parameter overrides implemented; custom LaTeX versions are non-executable proposals, not new verified kernels |
| WF-03 | Save/review/run and controls only in Workflow | Existing-engine review, graph/policy stale-approval protection, one review action and explicit scope/checkpoints implemented; batch acceptance separates draft settings from frozen run settings |
| RES-01 / SCI-06 | Grouped results, independent job/numeric/evidence/validation status | Four-state summary and synthetic tables verified; general module grouping pending |
| RES-02 / SCI-07 | Pool-aware ER tables/curves and actual viewer acceptance | Typed actual-volume projection/CSV retained; actual RCSB PDB/mmCIF display, rotation/export and 20-cycle native GPU lifecycle verified; reference overlays require recorded transforms, no inferred alignment |
| AG-01 / AG-02 | Persistent conversational proposals/diffs/decisions using existing engine | Project-scoped history, typed graph/policy diff, Accept/Reject/Revise/reopen implemented; template prompts do not invent numerical patches; real external LLM account validation unavailable |
| AG-03 | Tools, plugins and skills with real capability tests | Actual registered capability catalog, existing prediction job controls, trusted isolated Python plugin import/install/disable and instruction-only Skills implemented; general tool configuration and third-party scientific jobs are not all verified |
| AG-04 | Model settings, write-only secrets, local/hosted endpoint boundaries | Private profile, Windows DPAPI, None/local/API modes and public capability probes implemented; HTTP protocol fixture is not a real model, streaming probe is not a streaming chat interface |
| JOB-01 | Structured Jobs/Output/Problems and mode-safe terminal | Existing Jobs/Problems retained, actions grouped under Jobs; raw host terminal explicitly unavailable in Web; full structured Output and embedded local PTY pending |
| UI-01 / UI-02 / UI-03 | Single menu, inline tabs, contextual tree and English messages | Single menu/inline tabs existed in batch 1; redundant top controls and Diagnostic tab removed, contextual source/problems added; full object selection, Assistant and language/visual audit pending |
| PERF-01 | Measured baseline, schema split, viewer/resource lifecycle | Standalone schemas split into lazy protocol families, actual cold-page comparison and native 20-cycle GPU measurements recorded; no universal speed/memory claim or clean locked desktop release acceptance |
| Synthetic PS-v3 | Original corrected package, separate runner and inherited scope | Original kernels, independent endpoints, canonical perturbation and browser/server chain verified; separate synthetic scope, E3 blocked |
| Publication | Final designated repository, Wiki, Village and award registration | Owner confirmation required; no relocation/registration mutation |
| Validation | Real independent experiment, real transfer case, five novice-user sessions | Requires corresponding data/people; software fixtures are not substitutes |

Do not interpret a pending row, a passing software test or a completed job as
formal M1–M4 readiness or experimental validation.

## Batch 4: methods, Assistant/extensions, actual 3D and measured loading

Scientific kernels/equations/tolerances were not replaced. The method registry
lists every original stage and retains original equalities and documented source
discrepancies. M1's undefined blockiness and M3's avidity/capacity claims remain
explicitly conditional or undefined; a metadata implementation reference is not an independent
numerical proof. ER is separately versioned and never relabels a cytosolic result.
Tools are registered/not tested until actual execution establishes otherwise.
Run inspectors use immutable run tool versions and parameters, not a live draft.

Parameter overrides create linked, unapproved candidates with reasons; saved values
and sources cannot be overwritten under the same identity. Human review reuses
the existing unit/applicability validator. Formula changes are separately versioned
LaTeX proposals, explicitly unvalidated/non-executable. Saving one does not alter
an original kernel or grant calculation authority. No expression evaluator was
introduced. Complete executable custom-method development remains a separate,
independently validated implementation task.

Assistant history and original requests are persisted. Revise records an actual
typed graph/policy diff, revokes old proposal authority and creates a new proposal
requiring acceptance. Reopening and rejection do not start jobs. Template/manual
mode remains usable without a model. Model profiles and secrets are private
workspace configuration, not project exports or browser storage. Hosted endpoints
require the deployment administrator's exact allowlist; local endpoints require
an explicitly local workspace. A changed endpoint clears the old secret. Actual
JSON capability must pass before enabling the existing hybrid planner. Connection
tests send only public text. Saved DPAPI credentials that cannot be decrypted by
another OS/user disable the model without preventing manual workspace startup.

Plugins use the existing manifest/process/venv protocol, not another scheduler.
Uploaded ZIP import inspects source without executing it. Public GitHub/iGEM GitLab
refs resolve to a pinned backend commit; hashes remain technical details. Installed
versions can be disabled/re-enabled and are retained for previous run identities.
Disabling prevents new processes, not already-running ones. A Python venv is
dependency isolation, **not an OS security sandbox**; hosted trusted installation
is disabled unless the administrator explicitly enables it. Skills are editable,
versioned plain instructions with source/license; embedded scripts are not executed
and text cannot supply scientific evidence or approve parameters.

Real display source: RCSB [1CRN entry](https://www.rcsb.org/structure/1CRN),
[PDB bytes](https://files.rcsb.org/download/1CRN.pdb),
[mmCIF bytes](https://files.rcsb.org/download/1CRN.cif),
[dataset DOI](https://doi.org/10.2210/pdb1CRN/pdb). This is real crambin geometry,
not a fusion prediction or synthetic replacement. Original chain A numbering and
the warning that B-factor is not pLDDT remain visible. Actual Edge/Molstar acceptance
rotates the image, verifies a native PNG download, switches formats and opens/closes
20 times. Native context-loss invalidation is counted alongside explicit handle
deletion; every closed view has zero still-valid measured handles. Measured heap
samples are retained, without inventing a universal memory threshold. Registered
reference overlays require recorded transforms and do not infer alignment.

The generated runtime contracts still derive from the single Python public schema.
Build-time standalone AJV validators are split into exhaustive named protocol
families; unknown/duplicate membership fails generation. Core input validation
remains synchronous, heavy result/import/tool/planning families load on demand.
No coercion, scientific default or gate was removed. Method rendering uses pinned
Temml 0.13.4, trusted-false XML MathML, with no user HTML/expression execution.

Initial same-machine samples: cold empty Inputs loaded JS decreased from
1,504,041 to 979,298 bytes, gzip from 213,987 to 174,642 bytes. Both recorded zero
extra requests over ten idle seconds. These first timing samples overlapped other
build activity; they establish asset-loading reduction, **not** a stable startup,
CPU or API-latency improvement. Molstar and Plotly remain large lazy chunks; total
installed assets are not claimed to have shrunk. A reproducible read-only measuring
script is committed at `software/dashboard/scripts/measure-workbench-performance.mjs`.

Software acceptance is distinct from scientific/experimental acceptance. HTTP
model transport fixtures are not real LLMs; plugin ref transport fixtures are not
real third-party deployments; original scientific regressions run only on the
compute deployment. Latest exact delivery counts/sizes are appended after final
acceptance. Clean release-builder Node 24.19.0, desktop EXE, full generic module/
binding creation, SBOL/SBML semantics, comprehensive Jobs/Output and the other
pending rows remain outside claims of completion in this batch.

### Final batch-4 delivery acceptance

Code commits: `613acd4` (methods/Assistant/extensions/3D) and `c9e5f26`
(initial-save race, compact generated validators and process-tree measurement).
Official corresponding code commits: `b5bef3fe` and `b5208140`, with identical
source trees and unchanged main. Subsequent documentation commits do not change
these tested kernels or executable assets.

- Frontend: 83 passed / 27 files / 49.00 s; TypeScript and Vite passed. Includes a
  delayed first-document-save regression: execution settings stay disabled until
  the document is durable, rather than discarding the proposal during a fast edit.
- Installed compact Web wheel: 7 actual Edge browser tasks passed / 1.3 min.
  All M1–M4 formulas rendered as MathML; an unvalidated separate formula version
  saved; None/model-style and actual instruction Skills survived reload. Proposal
  revise/reject/reopen, actual imports, graph/list/fan-out and both real-coordinate
  display tasks passed. No scientific job ran on the workstation.
- Backend/server full exact-source regression: 924 passed, 12 skipped / 120.49 s.
  First run had 923 passes and one mandatory-author failure because the fresh
  source archive intentionally excluded private author files. Those two original
  files were verified against independently retained bytes and linked into the
  owned server acceptance directory; the first failure was retained and the whole
  suite rerun. No oracle, tolerance or required-author flag was weakened.
- Separate native tools: 56 passed / 7.04 s, actual FreeSASA/2PDZ and original
  Mpipi/LAMMPS. New local ZIP/process lifecycle tests actually import, install,
  execute, disable, restart and re-enable a stdlib-only plugin; incompatible
  dependency-version tests retain their actual separate venv processes. These
  software plugins are not substitutes for licensed scientific predictors.
- Final server-connected actual-kernel browser: 1 task passed / 10.5 s (12.9 s
  total). It found and prompted the first-save race fix, then passed review/scope/
  acceptance → original synthetic M3/M4 calculation → actual table/Plotly → all
  49 recorded points in CSV. 4/5 solved, 0/5 evidence-ready, experimental validation
  not established; E3 remains blocked. Historical projects/runs were preserved.

Controlled sequential cold-page observations, same i7-1255U / 16,995,729,408-B RAM /
Windows 10.0.26200 / Edge 155.0.4283.45 workstation:

| Measurement | Before family split | Final compact build |
|---|---:|---:|
| Actually loaded JavaScript bytes | 1,504,041 | 979,528 |
| Locally computed gzip bytes | 213,987 | 176,370 |
| Browser heap after GC, bytes | 3,967,560 | 3,848,776 |
| 50 sequential info reads, p95 ms | 14.1 | 11.5 |
| Requests during declared ten-second idle window | 1 | 1 |

This supports approximately 35% less initial JS and 18% less gzip loading.
It remains a single sequential timing pair, not a universal speed/RSS result.
The revised measuring script includes the actual Windows Python descendants:
the first sampler measured only a venv redirector's small working set, so that
old backend-memory/CPU sample is not a valid backend comparison. Final measured
server processes are retained in private evidence; no stable backend-memory
reduction is claimed. One request appeared in each final idle window; the earlier
zero-request samples must not be substituted for these latest observations.

Latest actual Web wheel: 3,404,577 bytes, installed without new Python dependencies.
It is not an updated EXE or a clean Node-24.19.0 locked release-build acceptance.
Temml 0.13.4 is the sole newly added frontend runtime dependency in this batch.
Fresh installed runtime/tools audit: 14,752,998,991 bytes under decimal 15 GB,
including live server acceptance package, existing tools/environments/cache and
retained runtime backups, workstation dependencies and latest installed Web package.
There was no active older desktop process in this audit. PNPM file aliases are
counted once by file identity. Inactive source/release/build files and scientific
outputs are excluded consistently; this is not total disk occupancy.

Final code's conservative full Git/source accounting after normal lossless Git
packing: 12,353,379 bytes under decimal 50 MB; tracked source 7,137,393 bytes,
Git storage 5,215,986 bytes, zero reachable LFS. The earlier local check exceeded
50 MB because redundant development-fetch packs and larger generated code were
included; generated code was compacted and ordinary `git gc --prune=never` packed
objects without deleting/rewriting history. Server GitLab last reported 6,695,208
repository bytes; it is not official freeze/eligibility confirmation.

CI is **not passed**: [code pipeline](https://gitlab.igem.org/2026/software/tsinghua-t/galatea/-/pipelines/747422)
was pending, no runner assigned. The older job explicitly failed with
`stuck_pending_no_matching_runners`; shared runners remain disabled. A repository/
runner administrator is still needed. No private compute runner or shell access
was registered or exposed. Full code bundle was regenerated and blob-verified;
the final documentation revision is included in the final export.

## Batch 5: executable exploratory formulas, real model protocol and desktop

Supersedes Batch 4's "non-executable custom drafts / EXE not updated" status.
Original scientific kernels, data, equations and approval requirements remain
unchanged. One new builtin uses the existing durable workflow engine: explicit
scalar AST expressions, sourced values, SI-dimensional admission/conversion and
finite-real-domain checking. No eval, guessed LaTeX meaning, code execution or
implicit original-formula replacement. Saved versions are immutable; old
document-only versions remain readable and non-executable. See
[the supported language and workflow](custom_formula_execution.md).

Actual user flow: save separate version → Prepare exploratory workflow → review
its expression/inputs/units/sources → Accept → Start run → select the frozen
`formula` result in Results. The rendered result and authorized export retain
the exact method version, values and provenance. Evidence readiness stays false
and scientific validation remains unvalidated. A browser-discovered load race
was corrected: reviewing a not-yet-loaded saved workflow cannot fall through
to an unrelated default sequence template. Review requires an explicit loaded
workflow; input checks remain available.

Acceptance against code `c2c0242` (later test/document-only changes do not alter
the runtime): server full regression **958 passed / 12 skipped**, including
required immutable author-source regression; fresh real non-restricted tool
suite **56 passed**. New custom-expression analytic/unit/function/domain,
approval → Start → durable result/reopen tests all ran on the server. Local
AST/ownership/profile software checks: **29 passed / 14 numerical cases
deselected**. Final frontend: **84 tests / 27 files passed**. Installed real
browser package: **7 tasks passed**, including executable-version creation
without local execution, all original formula rendering, real PDB/mmCIF rotation,
image export, twenty GPU lifecycle cycles and actual WebGL-unavailable fallback.
Connected server browser: **2 tasks passed**, including reviewed scalar
calculation/result/reload and unchanged corrected PS-v3 real-kernel/Plotly/CSV
flow. The scalar and PS-v3 fixtures are not biological validation.

The actual laboratory model returned JSON and streaming responses through a
private encrypted tunnel. An actual typed semantic request was parsed (one
schema repair was needed) and missing scientific inputs blocked execution;
no fixture HTTP service is counted as an LLM. A real named tool-call request
returned HTTP 400 explicitly requiring a server tool-call parser. JSON semantic
planning does not require that feature; function-call compatibility remains
unverified until the service administrator configures and retests it. No shared
model service was restarted. No private endpoint, model identifier or key is in
source, reports, release assets or bundle. The client now allows bounded slow
model responses, rejects truncated responses explicitly and preserves that
failure instead of concealing it as a generic parse error.

Windows portable desktop rebuilt from `c2c0242` with pinned CPython 3.13.13,
Node 24.19.0, pnpm 10.30.3 and Rust 1.95.0, without weakening locks. Actual EXE
boot/authentication, GenBank import, same workspace restart, embedded asset-byte
identity and owned-child shutdown passed. Default mode is local; no laboratory
connection is bundled. Portable folder: **240,695,038 bytes**; ZIP:
**90,364,937 bytes**. Keep the whole extracted folder, not just the EXE.
Package manifest/source/ZIP bytes were verified; this is not code signing or
scientific validation. Intermediate packages were preserved, not delivered.

Fresh installed tool/runtime/dependency/current-package audit:
**14,990,320,312 bytes**, below decimal 15 GB. Existing numerical tool environments,
cache and retained runtime backups remain included. PNPM aliases are counted
once by file identity. Inactive source/releases/build intermediates and scientific
outputs remain excluded; this is not total disk occupancy. The model is an
existing external laboratory API; no model weights or new scientific environment
were installed by this delivery.

Still blocked externally: licensed SignalP/DeepTMHMM/TANGO/PASTA native/API jobs
without valid access; model function-call service configuration; official CI
without a matching Runner. The last existing GitLab job explicitly failed with
`stuck_pending_no_matching_runners`, runner unset. These are not marked passed.
The complete original biological workflow, matched wet-lab validation and all
remaining review/award criteria are not established by this batch.

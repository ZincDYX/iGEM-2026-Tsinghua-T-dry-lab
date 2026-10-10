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

## Remaining review acceptance tasks

| ID | Required outcome | Current status |
|---|---|---|
| WEB-01 | Authenticated same-origin local Web package, Linux lock, container and clean startup | Local installed-wheel/browser and existing Linux closure verified; container/clean deployment pending |
| CLI-01 / ARCH-01 | Shared application services and durable CLI workflow | Core project/approval/run parity verified; remaining service extraction and typed imports pending |
| IN-01 | Inputs first, two regions, default project and single import controller | Pending |
| IN-02 | Typed format registry, transactions and ambiguity handling | Pending |
| IN-03 | Contextual gaps with Add/Use/Defer actions | Pending |
| IN-04 | Server-calculated asset identity, no user SHA entry | Pending |
| WF-01 | Graph/List editing of one workflow revision | Pending |
| WF-02 | Versioned full method formulas, tools and parameter records | Pending |
| WF-03 | Save/review/run and controls only in Workflow | Pending |
| RES-01 / SCI-06 | Grouped results, independent job/numeric/evidence/validation status | Four-state summary and synthetic tables verified; general module grouping pending |
| RES-02 / SCI-07 | Pool-aware ER tables/curves and actual viewer acceptance | Typed actual-volume projection and CSV verified; real structure/WebGL/lifecycle acceptance pending |
| AG-01 / AG-02 | Persistent conversational proposals/diffs/decisions using existing engine | Pending |
| AG-03 | Tools, plugins and skills with real capability tests | Pending |
| AG-04 | Model settings, write-only secrets, local/hosted endpoint boundaries | Pending |
| JOB-01 | Structured Jobs/Output/Problems and mode-safe terminal | Pending |
| UI-01 / UI-02 / UI-03 | Single menu, inline tabs, contextual tree and English messages | Pending |
| PERF-01 | Measured baseline, schema split, viewer/resource lifecycle | Pending |
| Synthetic PS-v3 | Original corrected package, separate runner and inherited scope | Original kernels, independent endpoints, canonical perturbation and browser/server chain verified; separate synthetic scope, E3 blocked |
| Publication | Final designated repository, Wiki, Village and award registration | Owner confirmation required; no relocation/registration mutation |
| Validation | Real independent experiment, real transfer case, five novice-user sessions | Requires corresponding data/people; software fixtures are not substitutes |

Do not interpret a pending row, a passing software test or a completed job as
formal M1–M4 readiness or experimental validation.

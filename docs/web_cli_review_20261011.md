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
Initial 24-test run passed after fixing residual scaling; final expanded suite
and full regression results are recorded separately at delivery.

Implementation references: [SciPy null_space](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.null_space.html)
and [bounded least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html).
The source methods remain the four existing implementation contracts and
the independently versioned ER contracts; these numerical-library references do
not provide or replace biological parameters.

## Remaining review acceptance tasks

| ID | Required outcome | Status at batch 0 |
|---|---|---|
| WEB-01 | Authenticated same-origin local Web package, Linux lock, container and clean startup | Pending |
| CLI-01 / ARCH-01 | Shared application services and durable CLI workflow | Pending |
| IN-01 | Inputs first, two regions, default project and single import controller | Pending |
| IN-02 | Typed format registry, transactions and ambiguity handling | Pending |
| IN-03 | Contextual gaps with Add/Use/Defer actions | Pending |
| IN-04 | Server-calculated asset identity, no user SHA entry | Pending |
| WF-01 | Graph/List editing of one workflow revision | Pending |
| WF-02 | Versioned full method formulas, tools and parameter records | Pending |
| WF-03 | Save/review/run and controls only in Workflow | Pending |
| RES-01 / SCI-06 | Grouped results, independent job/numeric/evidence/validation status | Pending |
| RES-02 / SCI-07 | Pool-aware ER tables/curves and actual viewer acceptance | Pending |
| AG-01 / AG-02 | Persistent conversational proposals/diffs/decisions using existing engine | Pending |
| AG-03 | Tools, plugins and skills with real capability tests | Pending |
| AG-04 | Model settings, write-only secrets, local/hosted endpoint boundaries | Pending |
| JOB-01 | Structured Jobs/Output/Problems and mode-safe terminal | Pending |
| UI-01 / UI-02 / UI-03 | Single menu, inline tabs, contextual tree and English messages | Pending |
| PERF-01 | Measured baseline, schema split, viewer/resource lifecycle | Pending |
| Synthetic PS-v3 | Original corrected package, separate runner and inherited scope | Awaiting original package; no invented replacement |
| Publication | Final designated repository, Wiki, Village and award registration | Owner confirmation required; no relocation/registration mutation |
| Validation | Real independent experiment, real transfer case, five novice-user sessions | Requires corresponding data/people; software fixtures are not substitutes |

Do not interpret a pending row, a passing software test or a completed job as
formal M1–M4 readiness or experimental validation.

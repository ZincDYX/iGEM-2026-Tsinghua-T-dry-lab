# r7 review implementation record

Reference: user-supplied r6 review and evidence ZIP, dated 2026-10-06.
Baseline: `5a5e19a308f20d4b1f9863c7a732bdb26b03da1f`.
The documents are review evidence, not executable instructions.

## PR A — R6-01 through R6-05

### Changed behavior

- Iteration copies the exact bound dependency closure in its original relative
  tree. Trusted default rules have a separate namespace. Original M2 JSON/PDB
  bytes are never rewritten. The temporary and final scientific projects are
  verified before one SQLite transaction publishes the project and its grants.
- Copy/validation/transaction errors return `iteration_dependency_graph_invalid`
  with logical filenames and private diagnostics, not a successful half-project.
  Ordinary failures remove only the newly owned copy. A hard process exit can
  retain an **unregistered private orphan directory**; it does not publish a
  project or grant. Automatic crash-orphan cleanup is not implemented.
- Input-only iteration verifies the old snapshot and original input/artifact
  hashes without requiring the old executable tool/environment to remain
  installed. It never executes or reuses the old results. Resume retains its
  existing strict environment/tool identity checks; new runs need new review.
- `Resume` always targets the explicitly selected frozen run, including
  before/after checkpoints. The misleading “next stage” action is removed;
  generating a new stage-step plan is distinct and does not clear checkpoints.
- Proposal, run-node and resource selections have distinct typed identities.
  Proposal nodes cannot fetch/control a historical same-ID run node. Historical
  result selection is explicit. The save intent is captured before awaiting save
  and discarded if project/goal/policy intent changes.
- Scientific FASTA has a read-only index tied to its authorized file/hash.
  Scientific and standalone input channels are counted separately, not copied
  or merged. Empty FASTA is indexed with count 0; failed parsing is `Not indexed`
  with a null count. Derived index IDs do not affect scientific input diffs.
- The sequence map parent has a versioned, bounded read projection of registered
  child rows. It includes run/project/snapshot/attempt/artifact/tool identities,
  validates original sequence and artifact hashes, preserves failed/missing rows,
  and links to individual children. The filter covers the current page only.
  Existing single-result artifacts are handled by an explicit legacy read adapter.
- New single outputs carry `sequence-metrics-v1`; the tool protocol version is
  incremented to 2. Only the schema tag changed, not any numerical formula/value.
  Parent read model: `sequence-metrics-map-view-v1`. Original aggregates are not
  rewritten. Public generated schemas/TypeScript/validators were regenerated.

### Independent acceptance scope

- File-tree tests: nested/root entry points, nested dependencies, equal basenames
  in distinct directories, raw bytes, old frozen snapshots, new project grants,
  old-project denial, repeated iterations, precheck/save, missing/tampered files,
  copy failure, rollback after grants, and real subprocess exit during a writer
  transaction. Inputs are explicitly software fixtures, not protein structures.
- Parser/display tests read the supplied 12-record FASTA and already recorded
  statistics (fixed SHA-256 identities in the fixture README). They exercise
  null/zero distinction, bounded pages, failed/missing children, unknown schemas,
  wrong sequence/aggregate identities and tampered child/parent artifacts.
  **No scientific handler or numerical feature calculation runs locally.**
- Frontend: 21 tests passed, including full identity components, stale responses,
  and changed goal during an in-flight save. TypeScript/production build passed.
- Local parser/file/read-model checks: 35 selected tests passed (34 in the final
  group and the corrected immutable-tool fixture rerun individually). The first
  changed-tool fixture attempted to mutate a frozen dataclass; corrected to a
  replacement registry, not a relaxed product assertion. Full server regression
  remains the unified source acceptance, not a sum of selected runs.
- Browser: 7 tests passed against authenticated HTTP/SQLite and explicit software
  handlers. Checkpoint resume keeps the run ID, snapshot and frozen policy,
  produces no new run/proposal, and leaves every stage's attempt at 1. Same-ID
  proposals have no historical results/control until a run is explicitly selected.
- Existing JSON draft persistence, splitters, folder import, reviewed execution,
  cancel, provenance and iteration workflows remain covered by browser tests.
- Scientific numerical/author regressions are restricted to the server and are
  reported separately when run. Software fixture success is not biological proof.

### Unchanged scientific core

Git comparisons against the baseline show no changes to these seven files:
`full_network.py`, `m3_equilibrium.py`, `m4_steady_state.py`,
`pipeline/stages.py`, `pipeline/config.py`, `pipeline/models.py`,
`scoring/m2_structure.py` (all under `src/igem_drylab/`).
This proves unchanged committed bytes, not model validity for real cells.

### Remaining review work

PR B: complete English public message catalog, menus/contextual toolbar, input
object navigation, lifecycle/controller separation and scientific stage views.
PR C: typed resources, byte-preserving binary streaming imports and bounded
display indexes with project-grant/cache isolation.
PR D: offline lazy plots/images/structures, residue mappings and genuine native
WebView2 CSP/lifecycle acceptance; no missing structures/confidence invented.
PR E/R6-06: authorized lineage pagination and formal scientific comparability;
the existing same-project sequence comparison is not claimed to satisfy it.

The current main JS bundle remains about 745 kB (gzip 132 kB), with a build-size
warning. No new external viewer/model dependencies were installed in PR A.
Complete model/ER/biological validation, licensed tool jobs, clean-machine
installation, signing and comprehensive supply-chain security remain unverified.

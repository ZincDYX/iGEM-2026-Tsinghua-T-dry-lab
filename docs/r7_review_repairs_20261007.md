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
- Frontend: 23 tests passed, including full identity components, stale responses,
  and changed goal during an in-flight save. TypeScript/production build passed.
  The actual sequence summary component reads the recorded 12-item evidence,
  renders 12 child rows, filters/selects a child, and retains a failed row without
  substituting its old metrics or zero values.
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

### Work queued at the PR A checkpoint (historical)

PR B: complete English public message catalog, menus/contextual toolbar, input
object navigation, lifecycle/controller separation and scientific stage views.
PR C: typed resources, byte-preserving binary streaming imports and bounded
display indexes with project-grant/cache isolation.
PR D: offline lazy plots/images/structures, residue mappings and genuine native
WebView2 CSP/lifecycle acceptance; no missing structures/confidence invented.
PR E/R6-06: authorized lineage pagination and formal scientific comparability;
the existing same-project sequence comparison is not claimed to satisfy it.

At that checkpoint the main JS bundle was about 748 kB (gzip 132 kB), with a build-size
warning. No new external viewer/model dependencies were installed in PR A.

### Server acceptance follow-up

The first unified server run had 565 passed / 1 failed: the schema equality oracle
detected stale generated schema after adding parent artifact identity fields.
This was a real build pipeline omission, not a numerical failure. The contract
generator (also run automatically by production build) now exports Python schemas
from this checkout before compiling TS/AJV,
fails on export errors, and permits an explicit `FUSIONLAB_SCHEMA_PYTHON` for
environments without a repository-local venv. The equality assertion is retained.

An additional server-only regression replays these 12 source-derived sequences
using the production handler and compares all original recorded metrics exactly;
only the new explicit display schema tag may differ. Test-risk metadata separates
this numerical replay from read-only parser/display and software control tests.
Final unified runtime-source acceptance (`abc8cc1ea3f78e918fa0843026729983b216823c`):
**567 passed / 0 failed / 0 skipped, 51.78 seconds**, including required immutable
author reference and the 12-source statistical replay. Only the server ran these
numerical tests. Review data had Python 3.12.14 / Biopython 1.88; the old validation
environment had Python 3.11.15 / Biopython 1.85. Exact replay initially failed on
tool-version identity and last-bit sums. A new isolated Python 3.12.14 / Biopython
1.88 environment passed the unchanged exact assertion. No formula or tolerance
was altered. Python documents its 3.12 summation change in the
[official built-in function reference](https://docs.python.org/3.12/library/functions.html#sum).
Environment matching isolates this dataset's reproducibility, not universal
equivalence between library/Python versions or independent biological validation.

The reference environment's observed versions are pinned in
`requirements/r7_reference_reproduction.txt` (install the project itself from
the tested source; these are version pins, not wheel-hash/CVE certification).
Installed tool/environment directories including the new environment and cache
have a measured apparent total of 8,521,244,599 bytes, below 15 GB. No model
weights or viewer libraries were downloaded; pre-existing environments were not
upgraded. Matplotlib/openpyxl were required for the unchanged author scripts;
their absence caused an interim failure/collection skip that was resolved by
installing dependencies, not by disabling the tests.

Native package acceptance: real, unmocked Tauri/WebView2 bridge, anonymous 401 /
authenticated 200, MCP discovery ready, current embedded JS/CSS byte identities,
empty software-project save/restart persistence, and normal window close with
zero owned backend processes. No scientific calculation was performed locally.
Native scientific viewers, clean-machine installation and signing are not part
of this acceptance. The r7A executable/package use the tested runtime commit
`abc8cc1`; any subsequent documentation/environment-pin commit changes no runtime
source bytes.

Complete model/ER/biological validation, licensed tool jobs, clean-machine
installation, signing and comprehensive supply-chain security remain unverified.

## PR B–E continuation

Runtime source: `045c88c205f095996072ad8f73249864a6135ede`.
Implementation records: [resources and comparison](r7_resource_protocol_20261007.md)
and [workbench and viewers](r7_workbench_views_20261007.md).

- PR B: authored English public/native messages, File/View/Tools/Help menus,
  contextual commands, maintenance pages outside primary research navigation,
  real input-section navigation, captured-intent plan controller, and M3/M4
  views of existing registered values. Typed proposal/run/resource identities,
  reviewed execution and stale-result boundaries remain enforced.
- PR C: bounded binary ZIP streaming and exact original downloads, versioned
  resource/series/structure projections, indexed SQL point pages, pixel-only
  image previews and grant/hash checks before cache access. Generated public
  schemas/TypeScript/AJV correspond to these Python contracts.
- PR D: lazy local Plotly strict/Molstar, authorized images, exact plot/table
  points, PDB/mmCIF model/chain/insertion identities, source-bound FASTA and
  reference mappings, explicit confidence, representation and camera controls.
  No source-free confidence/assembly/alignment or chart-side numerical solver.
- PR E/R6-06: authorized parent-run/snapshot lineage, batched keyed comparisons,
  frozen inputs and source identities, existing formal F3 eligibility/condition/
  unit/context gates and explicit incompatibility reasons. No automatic ranking
  or approval of changed constructs from a display comparison.

Final unified server regression at this runtime commit: **593 passed / 0 failed /
0 skipped, 54.11 seconds**, requiring immutable author references and original
12-source statistics. Scientific numerical/author tests ran only on the server.
Final component tests: **23 passed**, process exit 0, no unhandled errors.
Production browser acceptance: **8 passed, 41.2 seconds**. The browser bridge is
explicitly a software fixture; genuine desktop acceptance is recorded separately.
Seven scientific-core files remain byte-identical to the review baseline.

The first viewer control checks did not assert actual colors. A supplementary
native inspection caught a real source-model/viewer-model mismatch: Molstar
renumbered PDB model 7 to 1, so annotation coloring was gray and the previous
model-index focus predicate matched nothing. The final mapping uses source frame
order/identity and the parsed model's actual number. Browser oracles now require
exactly the three atoms of B/12A and the fixed registered-42 color `#994c62`, not
just enabled controls or visible metadata. Original files and values are unchanged.

The first residue page could not be revisited after paging; the offset-0 guard
was fixed and next/previous behavior is asserted. An interim component run had
23 passing assertions but an unhandled JSDOM `scrollIntoView` error and exit 1;
only the corrected test-environment run with exit 0 counts as passing acceptance.

Remaining capabilities are tracked explicitly in the [final release acceptance
record](r7BDE_release_acceptance_20261007.md). Real final-package WebView2 acceptance
also passed exact structure color/focus, native CSP, software rendering and both
normal close/restart checks. These PRs do not establish biological validity, full supply-chain
certification, production remote access or approval of missing scientific inputs.

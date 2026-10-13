# Best Software evidence index

This is the maintained entry point, not a qualification or award claim.
Basis: [2026 official Judge Handbook](https://static.igem.org/websites/competition/2026/judging/2026-judge-handbook-digital.pdf),
Software pages 89–90. Source documents and executed evidence take precedence
over a description of intended behavior.

## Submission and licensing

| Item | Current evidence / limitation |
|---|---|
| Official software repository | [Develop](https://gitlab.igem.org/2026/software/tsinghua-t/galatea/-/tree/develop) was published on 2026-10-10. Initial complete-source commit `458b233` has the identical tracked tree to mirror `6818798`; official main `012781e7f2528a01b8bc3d8a01512c40a715280f` was preserved. Subsequent modules use normal fast-forward develop commits, not force pushes. Official submission freeze remains unverified. |
| Award eligibility | Team Village, award selection and software standard-page URL have not been supplied/verified. Using AI does not identify the Village. No eligibility claim. |
| Project license | Team approved Apache-2.0 for project-authored code. Root LICENSE/NOTICE and Python/frontend/native metadata carry it. Third-party/data/weights keep their original terms. Public GFP data are CC-BY-4.0, not Apache-2.0. |
| Size | Initial published develop: GitLab API reports repository 2,668,277 bytes and LFS 0. A fresh full-history clone (not shallow) measures 2,659,248 bytes Git storage + 7,554,580 bytes tracked source = 10,213,828 bytes conservative internal total, below 50,000,000. The mirror still references an old 127,471,861-byte LFS evidence CSV and is not the eligible repository; that history was not imported or rewritten. Recheck after every release. Portable ZIP/runtime sizes are not repository sizes. |

## Build and run

Supported release target: Windows x64, CPython 3.13.13, Node 24.19.0,
pnpm 10.30.3 and Rust 1.95.0. Exact runtime/build versions:
[release toolchain](../requirements/release-toolchain.json),
[runtime lock](../requirements/runtime-py313-windows.lock),
[build lock](../requirements/build-py313.lock), frontend pnpm-lock.yaml and native
Cargo.lock. `install_locked.py` installs these pins and checks the active
transitive wheel dependencies; `build_release.py` uses that installer, frozen
frontend install, locked custom-protocol build and the existing single packager.
The packager must match its selected runtime closure to the same release lock.

Local validation: all 51 installed runtime versions and closure match the lock;
14 release-lock/size/packaging/inventory software tests passed. This is an installed
environment check, not an independent-user installation study. The locked Windows
source build passed for mirror commit `6818798` in [run 38050926720](https://github.com/ZincDYX/iGEM-2026-Tsinghua-T-dry-lab/actions/runs/38050926720), using the shared build entry and producing the portable artifact.
The later GenBank source freeze `5aac3ba` also passed the [same locked Windows entry](https://github.com/ZincDYX/iGEM-2026-Tsinghua-T-dry-lab/actions/runs/38052245982)
and [compatibility regression](https://github.com/ZincDYX/iGEM-2026-Tsinghua-T-dry-lab/actions/runs/38052246040).
Official GitLab pipeline 746607 was pending at the latest check: shared runners
are disabled and the job has no assigned runner; runner-list access returns 403,
so availability of dedicated/group runners is unknown. No official CI pass is
claimed. Existing floating compatibility tests remain
separate and do not establish exact release reproducibility. Historical Python
3.10/SciPy 1.10.1 records are not current runtime install instructions.

Frontend production build passed. The first default-worker test run had 11
worker-start timeouts and is not a pass; rerunning with two workers passed all
58 tests in 22 files; the later GenBank batch passed 59 tests. No assertions were removed or relaxed. Locked Windows CI
uses that explicit worker budget. This is not a whole-app performance benchmark.

Verified desktop source freeze: `5aac3ba`, native embedded production assets,
authenticated owned backend/MCP, actual GenBank import/browse/original export,
saved-state restart and normal-close process cleanup passed. The test did not
mock the desktop bridge or execute scientific models. Portable ZIP about 90.15 MB,
unpacked content about 240.34 MB; this is not a signed installer. Documentation
updates after this freeze do not constitute a new binary/scientific validation.

## Real cases and external tools

- [Public GFP case](../examples/public_gfp/README.md): real canonical sequence,
  actual stdio MCP and independent ProtParam cross-check. Limited sequence
  descriptors only; the new case passed on the compute environment with actual
  stdio MCP and independent ProtParam agreement (238 residues). This is not an
  independent user study or fusion validation.
- [Glabridin author reproduction](glabridin_reference_reproduction.md): frozen
  author code, raw parameter and Source Data links, figure regressions and
  assay reanalysis. Not complete omics/MD/wet-lab reproduction or current fusion
  validation. Its historical environment is isolated from the product lock.
- [Current implementation ledger](r19_review_implementation.md): actual 888-aa
  ColabFold prediction, original full K25 author Mpipi run, actual JPred failure
  and same-job retrieval, ER independent mathematical tests and their limits.
- [Tool deployment/terms](external_tool_deployment.md) and
  [plugin extension guide](plugin_development.md): optional tools use actual
  installations or user-authorized services. SignalP/DeepTMHMM academic access
  and genuine native jobs are now verified; TANGO/PASTA deployment remains
  unverified. The dated [original-tool record](review_r27_original_tools_20261013.md)
  retains version discrepancies and failed attempts without calling them successful.
- [Complete inputs and second-round IDRs](review_r28_complete_inputs_and_IDRs_20261013.md):
  272 sequence records, including 127 IDR records / 126 distinct sequences;
  original IUPred/SEG/ProtParam observations, diagnostic PScore, 91 native full-fusion
  signal/topology jobs per tool, and 40 paired actual ColabFold models. Actual
  browser IDR pagination, tables/plot, exact export, model rotation and server
  IUPred Review/Accept/Run passed. Formal M1/M2, risk/ranking rules and experimental
  validation remain incomplete; neither the new input's reported simulation scores
  nor native-tool smoke tests substitute for those requirements. No new EXE is claimed.

## Standards, usability, experiments and performance

FASTA, native structure/confidence and table workflows exist. GenBank import now
retains original DNA/record annotations/fuzzy and compound features/strand/CDS
bindings through typed views using the existing dataset/file model, without a
second DNA copy in snapshots. Source-provided translations alone create proteins;
missing translations/bases remain gaps. Software tests check manually authored
expected metadata, protein-edit mismatch and ownership; actual built-browser
HTTP import/save/view/reload/export passed with byte-identical original export.
This preserves original records, not edited-design round-trip generation.
An independent external GenBank-tool interoperability study remains pending.
SBOL and SBML are not implemented; a partial export is not standards compliance.

UI/browser tests establish selected software behavior, not independent novice
usability. Non-developer task study, external-project fusion validation and
matched-condition project wet-lab validation remain pending. The public GFP
case cannot substitute for those studies.

The implementation ledger distinguishes mathematical tests, paper regressions,
tool execution and biological observations. Measured API profile improvements
do not establish whole-desktop memory or long-viewer performance; p95 did not
improve. Full native load/viewer profiling, coupled original occupancy extensions,
ER joint uncertainty, actual dependency reuse, formal tool-to-stage evidence
closure and feedback-triggered Agent research decisions remain unfinished.

No roadmap item becomes completed merely by appearing in this index.

## 2026-10-11 formula/model/desktop update

Separate scalar custom versions can now run after explicit workflow acceptance;
units/sources and frozen numerical results are retained. They remain exploratory,
not original-method or wet-lab evidence. The existing engine is reused. Backend
and new numerical acceptance ran on the authorized server: 958 passed / 12
skipped; native non-restricted tool suite 56 passed. Frontend 84 tests passed;
seven actual local software browser tasks and two connected server tasks passed.
The updated pinned-toolchain Windows EXE passed actual native boot, authentication,
import, restart and child-process shutdown. No scientific solver ran locally.
Real external model JSON/streaming and typed semantic parsing were observed, but
its function-call service configuration still blocks that protocol; a missing-input
response is not complete model/planner or biological validation. Restricted jobs
remain unverified without lawful access. See the dated
[Batch 5 ledger](web_cli_review_20261011.md) and
[supported custom formula language](custom_formula_execution.md).

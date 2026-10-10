# Best Software evidence index

This is the maintained entry point, not a qualification or award claim.
Basis: [2026 official Judge Handbook](https://static.igem.org/websites/competition/2026/judging/2026-judge-handbook-digital.pdf),
Software pages 89–90. Source documents and executed evidence take precedence
over a description of intended behavior.

## Submission and licensing

| Item | Current evidence / limitation |
|---|---|
| Official software repository | [Assigned GitLab](https://gitlab.igem.org/2026/software/tsinghua-t/galatea). Anonymous full clone succeeds; main was `012781e7f2528a01b8bc3d8a01512c40a715280f` when checked on 2026-10-10. It is an independently changed tree, not the current FusionLab desktop release. The user authorized a new develop branch; main will be preserved. A replacement user credential passed authentication and a develop push dry-run. Actual source synchronization/official freeze are recorded after publication, not inferred from a dry-run. |
| Award eligibility | Team Village, award selection and software standard-page URL have not been supplied/verified. Using AI does not identify the Village. No eligibility claim. |
| Project license | Team approved Apache-2.0 for project-authored code. Root LICENSE/NOTICE and Python/frontend/native metadata carry it. Third-party/data/weights keep their original terms. Public GFP data are CC-BY-4.0, not Apache-2.0. |
| Size | `scripts/check_submission_size.py` measures source, complete common Git storage, reachable large blobs/LFS payloads and submodule pins separately. The development mirror history references a 127,471,861-byte LFS evidence CSV and is not a compliant submission. The official main full clone is 1,108,062 bytes of Git storage, with 2,879,705 bytes of tracked source. Current source will be ported as a normal commit on official develop, preserving all official main history, not importing obsolete mirror archives or rewriting history. A fresh complete official clone must be remeasured after publication. 50,000,000 bytes is a conservative internal rule; official backend accounting remains unknown. Portable ZIP/runtime sizes are not repository sizes. |

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
environment check, not a clean-machine installation proof. The new locked CI
build has not yet completed. Existing floating compatibility tests remain
separate and do not establish exact release reproducibility. Historical Python
3.10/SciPy 1.10.1 records are not current runtime install instructions.

Frontend production build passed. The first default-worker test run had 11
worker-start timeouts and is not a pass; rerunning with two workers passed all
58 tests in 22 files. No assertions were removed or relaxed. Locked Windows CI
uses that explicit worker budget. This is not a whole-app performance benchmark.

Last previously verified desktop: commit `640bf75`, built native local window,
embedded production assets, authenticated owned backend/MCP, saved-state restart
and process cleanup passed. It predates this licensing/release batch; do not
mistake its successful launch for validation of this new build entry.

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
  installations or user-authorized services. SignalP/DeepTMHMM and TANGO/PASTA
  authorizations are not available; no corresponding real-job completion claim.

## Standards, usability, experiments and performance

FASTA, native structure/confidence and table workflows exist. The current
GenBank import still extracts translated CDS proteins; complete typed DNA/design
mapping and independently verified annotation round-trip are unfinished. SBOL
and SBML are not implemented; a partial export is not standards compliance.

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

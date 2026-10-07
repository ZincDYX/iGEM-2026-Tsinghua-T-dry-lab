# r8 release acceptance and remaining boundaries

Accepted runtime/source: `74d74dc8dd2f0a6986325526ed4c7888ded31e7c`.
Subsequent documentation-only commits must not be represented as a different
tested runtime. The user approved the existing GitHub destination; all r7 and
r8 implementation commits were pushed to `feature/m1-m4-markdown-contract`.

## Implemented and observed

- Sealed PDB/mmCIF coordinate/residue cache, exact paging and indexed residue
  identities, with grants and streamed original hashes rechecked on cache hits.
- Original registered rigid reference overlays, no fitted alignment. Actual
  browser and native Molstar transformed (1,2,3) to the registered (3,7,10).
- Dedicated F3 source-contract-gated scan view; incompatible records are null
  with reasons, source order is retained and no ranking or scan is executed.
- Persisted existing M5 aligned observations/predictions, source identities,
  censor bounds, quantified-only residuals and source uncertainty display.
  A fit-parameter CI is not a prediction band or approval. Old/legacy series
  are not reconstructed and legacy adapters remain non-formal.
- Declared CSV/NPZ series with explicit hash, original units/compartments and
  column meanings. No guessing, conversion or pickle. Compressed size and NPY
  headers/shapes are bounded before loading.
- AJV 8.18.0 and source-map-js 1.2.2 advisory patches. Actual license/version
  metadata produced a 631-component CycloneDX 1.6 inventory, validated against
  the official schema. OSV returned no registered matches; pnpm audit returned
  no listed frontend advisories. These are dated checks, not a security guarantee
  or complete binary/native-library/license-compliance assessment.

Implementation sequence: `1b9d7c7` coordinate cache; `1666d8c` overlay/dependency
repair; `8926857` F3/M5 views; `c16965c` CSV/NPZ adapter; `c131181` release
inventory; `74d74dc` cache regression correction. Details and declaration format
are in [implementation record](r8_remaining_implementation_20261007.md).

## Acceptance results

| Check | Result | Scope |
| --- | --- | --- |
| Full server regression, required author originals | 605 passed, 0 failed/skipped, 54.71 s | Retained scientific/author oracles; not full-paper/wet-lab validation |
| Frontend components | 27 passed, 0 failed | Software recorded samples; M5/F3 Plotly props checked, not numerical reproduction |
| Production-build browser | 8 passed, 0 skipped/flaky, 52.42 s | Real HTTP/SQLite/viewers; connection bridge explicitly a fixture |
| Packaged native WebView2 | Passed, actual bridge; anonymous 401, authenticated 200, MCP discovery ready | No mocked native connection, no local scientific calculation |
| Native software rendering | SwiftShader, source 7:B:12A selects exactly 3 atoms; confidence 42 is RGB #994c62 | Actual renderer/color, not B-factor 99 or biological confidence validation |
| Native exact plots/overlay | [0,null,2]; CSV [0,null,2.5] at [0,30,60] in min/mM; reference [3,7,10] | Original recorded display; no conversion/alignment |
| Native lifecycle | Normal close/restart; zero owned backends; saved project restored | Owned software-only test instance; existing user instances untouched |
| Package/source identity | 6,572 manifest files, 140 runtime source files, ZIP byte-equal, no loose pyc | Integrity, not code signing or universal secret detection |
| Server canonical code deployment | 500 tracked files and 13 production frontend assets verified | Old runtime preserved separately; no deletion or reinstall |

The seven r6 scientific core files remain byte-identical to baseline
`5a5e19a308f20d4b1f9863c7a732bdb26b03da1f`. M5 comparison.py has an explicit
output extension persisting its existing operations; it is not included in this
seven-file identity claim. Its analytical unit/censor oracle ran on the server.
No formula, scientific parameter or retained tolerance was replaced.

The first full CSV/NPZ extension run had one real regression: a cached JSON page
reread its whole source (604 passed, one failed). The original failing cache
oracle was retained and the implementation corrected. The final 605-pass result
supersedes it; the failed evidence is preserved privately, not hidden or redefined.

## Real external jobs, not interface-only claims

FreeSASA 2.2.1 ran through the actual stdio MCP server and deterministic external
tool handler, with dry_run=false, exit 0, nonempty output and four parsed residues.
Input is the repository's software coordinate fixture, not a fusion structure.
Its output SHA is `5d9bb9ae0ee70a804296396c8ace81d71275e06a955ab6df1ca9d5ccbe5a28ca`.

AutoDock Vina ran via the same real MCP tool route on server-only official 1iep
prepared tutorial inputs. Byte identity was checked against the official sources.
Center (15.190,53.903,16.917), box 20x20x20 angstrom, exhaustiveness 8, requested
9 poses and seed 17 were retained in the run record. It produced 3 poses, best
energy -13.242 kcal/mol, in 78.763 s. The smoke process used one allowed CPU
for scheduling only. This is not fusion activity, Kd/kcat validation, or a
claim to reproduce the tutorial's final pose/RMSD. No packages were installed.

Sources: [Vina tutorial](https://autodock-vina.readthedocs.io/en/latest/docking_basic.html),
[prepared receptor](https://raw.githubusercontent.com/ccsb-scripps/AutoDock-Vina/develop/example/basic_docking/solution/1iep_receptor.pdbqt),
[prepared ligand](https://raw.githubusercontent.com/ccsb-scripps/AutoDock-Vina/develop/example/basic_docking/solution/1iep_ligand.pdbqt).
The develop links are mutable; observed input SHA-256 values are respectively
`f13cf3b36f61d87c3b58983e0b8ecf1c3456a685eb86dfe9ccfb139c7bdc2586` and
`15fb35648d8c18c70317842f3a0631b73a19429c710a037ab07310084d579bb8`.

## Release identity

Portable directory: `FusionLab-Windows-20261007-r8-74d74dc`.
ZIP: 98,831,299 bytes, SHA-256
`fd4a55d8fe0f4166d6cebabf5e8af9278a2bede07e4db42595a5063525bade18`.
EXE SHA-256: `2e6e51241b3d8a5343cac4775754019cb6fb71d688c784150f58493457b1b6b0`.
Source TAR SHA-256: `bb92a0b7b7020a8a8bbc5b27b0f5b460baf584635ad234b6383ef02e0f395689`.
Runtime bundle SHA-256: `169758614816446df7df6505832792511c9dccdf10223ec8e3bc889d67bee375`.
SBOM and dated OSV result are shipped inside the package with matching commit.

Audited deployment/tool budget is 14,400,993,595 apparent bytes, below the
15,000,000,000-byte cap. This conservatively includes the declared server
tools/environments/ColabFold model cache (13,332,219,547), local frontend
dependencies (340,721,765), local backend environment (314,457,955), current
portable Python (258,617,234), preserved previous server runtime (145,402,344)
and current server production frontend (9,574,750). Historical source/release
archives, scientific outputs and unrelated development toolchains are outside
this deployment budget; this is not a claim about total disk use of both machines.
The server audit includes model weights, unlike the narrower historical r7
measurement. No new scientific packages or model weights were installed.

## Explicitly incomplete or not independently verified

1. Arbitrary BCIF/legacy semantic adapters; bounded identity-preserving decoder
   acceptance remains necessary. CSV/NPZ support covers the declared contract,
   not arbitrary array/object formats.
2. Arbitrary large-structure/whole-history performance and independent GPU-driver
   coverage. Current caches/pages are bounded; catalog/sidecar bounded source
   reads and large plotting/structure chunks remain. SwiftShader samples do not
   prove arbitrary large structures are interactive.
3. Matching real ER/transport/activity/kinetic/protein-abundance observations,
   calibration, parameter identifiability and genuinely independent holdouts.
   Numerical/author agreement does not supply missing biological data.
4. SignalP/DeepTMHMM/TANGO/PASTA licensing and new authorized positive jobs;
   no licenses/accounts were accepted or fabricated on the user's behalf.
5. Arbitrary plugin OS privilege sandbox; plugin_sandbox remains false. A venv
   is dependency isolation, not a host permission boundary.
6. Production authenticated remote-session provider, clean independent Windows
   machine install, commercial signing and full supply-chain/penetration review.
7. Windows native folder-picker end-to-end acceptance. A real owned native dialog
   was observed, but automation did not complete the fixed two-file fixture
   selection (wrong selection/timeout); this is NOT a pass. The successful main
   native viewer probe uses actual WebView2 with file-input injection, not manual
   OS dialog selection. The dialog test's owned process closed normally with no
   owned backend left. It is uncertain whether a product defect exists; the
   automation failure alone does not establish one.

Raw XML/scripts/environment identities and private deployment profiles remain
outside the repository in the user's private delivery evidence directory.
There is no private server host/profile embedded in the repository or desktop
default. Current desktop default stays local; disabled remote capability is not
misrepresented as an authenticated working connection.

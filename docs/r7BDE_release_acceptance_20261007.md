# r7 B–E release acceptance and remaining scope

Review: user-supplied r6 review/evidence, 2026-10-06. Tested runtime commit:
`045c88c205f095996072ad8f73249864a6135ede`. Subsequent acceptance documentation
does not change the packaged runtime. Older intermediate packages, including
`f8da3c3`, are not the final accepted release.

## Observed acceptance

| Check | Independent observation | Boundary |
|---|---|---|
| Full server regression | 593 passed, 0 failed/skipped, 54.11 s; required immutable author reference and exact 12-source statistics replay | Numerical replay, not new biological validation; server only |
| UI/build | 23 tests passed, exit 0; TypeScript and production build pass | No claim that assertion counts measure quality |
| Production browser | 8 tests passed, 41.2 s; actual HTTP/SQLite, exact plot/table points, binary identities, residue paging/focus/color | Browser connection bridge is an explicit software fixture |
| Real desktop | Unmocked Tauri/WebView2 bridge; anonymous 401, authenticated 200; local default; MCP discovery ready | Discovery is not execution of all licensed scientific tools |
| Native viewers | Actual image, Plotly and Molstar under package CSP; no observed external requests or CSP violations; SwiftShader renderer | Parser samples, not real predictions; no dedicated GPU required for this tested sample |
| Structure identity | Original model 7 -> viewer model 1; B/12A selects exactly 3 atoms; registered pLDDT 42 produces fixed RGB `#994c62`, not B-factor 99 | Source-bound display annotation, not scientific approval |
| Native persistence/exit | Saved project restored after restart; both normal closes exited with 0 owned backend processes | Empty/display-only project; interrupted scientific tasks are covered by separate workflow tests, not this native session |
| Package | 6,568 manifest files verified; 138 runtime-source files byte-identical to tested source archive; ZIP bytes verified; 0 loose pyc | Identity checks do not prove dependency safety |
| Core identity | All seven review-selected scientific files equal baseline committed bytes | No formula/tolerance/parameter change; not proof of model applicability |

Native folder input was exercised in the real WebView2 with file-input selection,
typed validation and binary upload. The interactive Windows file-picker dialog
was not manually operated or certified. Viewer GPU/React roots/blob URLs were
disposed on resource changes. Existing user instances/data were not touched.

## Fault injection and interim failures

Four mutations were applied only to an isolated source copy; release sources
were untouched. Unmodified counterparts pass the unified/browser/UI acceptance.

| Deliberate wrong implementation | Test that failed for the intended reason |
|---|---|
| Convert series null to zero | Exact page `[None, 2]` oracle observed `[0, 2]` |
| Flatten scientific dependency paths | Nested iteration rejected an invalid dependency graph instead of publishing a valid copy |
| Borrow historical same-ID run for proposal selection | Typed-selection oracle observed true where proposal/run isolation requires false |
| Put software-fixture token in binary URL | Request monitor detected token in the image-preview URL |

These are four targeted fault checks, not a mutation coverage score. The first
token probe used a dev server with production CSP and failed before reaching its
token oracle; it is not counted. The corrected production-build probe failed at
the intended token-in-URL assertion. A native probe initially connected before
WebView2 was ready; only the probe received bounded startup waiting.

The actual-color assertion exposed a product bug missed by control-only checks.
It was fixed in the tested runtime commit; acceptance predicates were strengthened,
not relaxed. Earlier intermediate artifacts remain audit evidence, not deliveries.

## Release identities

- ZIP bytes: 98,834,888; SHA-256
  `108a188f3cb640cd8c17261b0dd3adf1ed9f9db5255831d0fe50e771533879a1`.
- EXE SHA-256:
  `4870f9da3c062eb0b9590b0401c78ec4961cde309ae507e1708f18d38f9517eb`.
- Files-only tested source archive SHA-256:
  `f4d8812cd5e52a707161c30798cd93a9410dce76ea0b8d0bb411dfa6805c4dc2`.
- Runtime Markdown bundle SHA-256:
  `b1b831c0f0f12e5f3d732c53b042de5787d7c3d4705b7aceb42d7b3426ae4ac1`;
  484 tracked files (477 text, 7 binary), 6 pinned Git submodule references.
- Apparent measured tools/environments plus frontend dependency directories:
  8,821,333,226 bytes (<15 GB). This scope excludes unrelated developer toolchains,
  source/release archives and other machine data. No model weights added.

## Still not implemented or not independently verified

- Reference coordinates are shown independently; a source-transform overlay
  adapter, automatic alignment and scientific assembly inference are absent.
  Registered residue mapping/sequence identity is available, not inferred geometry.
- Dedicated full F3 scan plots and condition-matched M5 observation/prediction/
  censoring/fit-interval overlays are not implemented. Existing registered output,
  missing-data states and gated formal comparisons remain available. No substitute
  curves or experimental confidence bands are generated.
- Structured series display currently adapts registered `m4-prediction-v2` data;
  arbitrary CSV/NPZ/BCIF/legacy formats are not guessed into scientific semantics.
  Unsupported originals remain authorized attachments/downloads.
- Structure projections are bounded but not an incremental coordinate cache;
  catalog/sidecar discovery still reads bounded originals. The main JS build-size
  warning remains; lazy viewer chunks do not prove large-dataset performance.
- Complete ER/model/biological validation, condition-matched kinetic/transport/
  abundance measurements and independent wet-lab validation are not established.
  Viewer operation and synthetic formal-parser cases add no biological evidence.
- Licensor approval and real positive jobs for remaining restricted tools are
  not supplied or certified by this release. MCP discovery is genuinely exercised
  but cannot be used to claim that every external tool has an approved real job.
- Comprehensive transitive SBOM/CVE audit, clean-machine Windows installation,
  code signing, interactive OS-dialog acceptance, authenticated remote production
  transport and arbitrary-plugin permission sandboxing remain unverified/absent.
  Private settings remain local; production remote functionality stays disabled.
- Git commits are local. Push was blocked by destination approval; the explicit
  repository-destination confirmation is pending. No successful push is claimed.

## Sources and evidence

Original source-derived FASTA/recorded metrics come from the sealed user review
ZIP, with identities in [the fixture record](../tests/fixtures/r7_sequence_display/README.md).
Original author-reproduction sources and their constraints remain in the existing
reproduction records; this release does not reproduce the entire paper anew.
Raw server XML is private evidence (it can contain environment/host identity),
not a public-export artifact and not checked into the repository.

Viewer/library references and packaged licenses:
[Plotly bundle/CSP reference](https://github.com/plotly/plotly.js/blob/main/dist/README.md),
[Molstar viewer documentation](https://molstar.org/viewer-docs/),
[fflate source](https://github.com/101arrowz/fflate),
[CSP image-source reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/img-src),
[release notices](../software/dashboard/THIRD_PARTY_NOTICES.txt).
Locked direct viewer/import versions: Plotly strict 4.1.2, Molstar 5.13.0,
fflate 0.8.3. MIT notices for these direct dependencies accompany the package;
this is not a complete transitive license or security certification.

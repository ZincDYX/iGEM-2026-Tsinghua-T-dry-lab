# r8 remaining implementation

This continues the r6 review after r7 B–E. On 2026-10-07 the user explicitly
approved the existing GitHub destination; r7 commits through `4380bc7` were
successfully pushed to `feature/m1-m4-markdown-contract`. The historical r7
acceptance record remains immutable; its push-pending statement is superseded.

## Coordinate projection index

PDB/mmCIF projection bytes and residue identities are persisted in SQLite under
file ID + original SHA + coordinate-index schema. Residue pages use SQL ordinal
limits; annotation identities use an indexed exact model/chain/auth-number/
insertion lookup. Original project grant and streamed file hash are checked
before every cache hit. Sidecars and their references retain independent grants
and hashes. No scientific result reuse or evidence promotion is introduced.

Software oracle: a two-residue source with original model 7 and insertion A
must return exact next-page chain C without invoking the coordinate parser a
second time; stranger access and original-byte tampering must fail despite the
cache. Existing PDB/mmCIF/mapping/grant/metadata tests remain unchanged.

Further modules and final server/native/release acceptance are recorded below
as they are implemented. Scientific numerical regression remains server-only.

## Registered reference overlay

The dedicated hash-bound annotation sidecar can declare a reference-to-target
4x4 rigid matrix, row-major/column-vector convention, angstrom units and tool/
version/source reference. Proper rotation, affine last row and exact authorized
reference hash are required; no alignment, RMSD or assembly is inferred. The
client applies that exact matrix in Molstar and removes its owned data tree on
hide/unmount. Primary source coloring/focus remains separate from the overlay.

Independent software parser tests passed (source/hash/grants and rejection of
scale/reflection/projective transforms). A real browser Molstar assertion
verified the original matrix maps (1,2,3) to (3,7,10), with offline CSP, no external
requests and hide/dispose behavior. This is display validation, not biological
validation or acceptance of a user-uploaded annotation as scientific evidence.

## Dependency advisory repair

Read-only registry audit found AJV 8.17.1 and source-map-js 1.2.1 advisories. Direct
AJV and transitive overrides are pinned to AJV 8.18.0/source-map-js 1.2.2. Installs
ran with scripts disabled. Follow-up pnpm audit reports no listed advisories
(410 dependencies); this is a dated registry result, not proof of universal safety.
The generated public validators were rebuilt and production build passed.

Primary sources: [AJV release](https://github.com/ajv-validator/ajv/releases/tag/v8.18.0),
[source-map-js repair](https://github.com/7rulnik/source-map-js/releases/tag/v1.2.2),
[Molstar transform API](https://molstar.org/docs/plugin/superposition/).

## F3 and M5 registered result views

F3 reads the existing finite-scaffold-scan-v2 output with project/hash checks,
bounded pages and the original DesignComparisonContract. Incompatible conditions,
missing evidence or missing metrics remain null with explicit reasons. Source order
is preserved; neither backend adapter nor viewer executes a scan or ranking.
Source-reported eligibility is not proof that uploaded records were actually computed.

M5 now persists the values already canonicalized and aligned by the existing
comparison, including original units, construct/condition/replicate identities,
censor masks, LOD/LOQ, source uncertainties and quantified-only residuals.
The display uses exact recorded markers, not a new interpolation or fit.
Legacy summaries without these arrays are not reconstructed; legacy prediction
adapters remain explicitly non-formal. A parameter confidence interval is not
displayed as a prediction confidence band or interpreted as parameter approval.

The seven previously frozen scientific core files remain untouched. The M5
comparison file is extended to persist its existing operations, without replacing
their formulas or tolerances. Its independent analytic regression must run only
on the server. Local component tests use declared recorded software samples and
verify zero/null, censor bounds, residuals, units and identity refusal; they do not
invoke the numerical comparison or a solver.

## Declared CSV/NPZ series

CSV and NPZ can be displayed using a separately registered JSON declaration,
`display-series-source-v1`. It requires the exact target SHA, explicit original
time unit, column keys, species labels, compartments, units and missing token.
There is no header guessing, unit conversion or promotion to a prediction.
Both declaration and original data retain their own project grants/hash checks
on every cache read. CSV empty fields and explicitly declared NPZ NaNs map to
null, never zero. NPZ disables pickle and rejects compressed expansion, oversized
headers and forged vector shapes before any array allocation.

Example declaration (replace the SHA and source text with actual registered
source identity; this is not scientific evidence):

```json
{
  "schema_version": "display-series-source-v1",
  "target_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "source_reference": "Original measurement file and method reference",
  "format": "csv",
  "time_key": "minutes",
  "time_unit": "min",
  "missing_token": "",
  "columns": [{"key": "signal", "compartment": "extracellular", "species": "13", "unit": "mM"}]
}
```

NPZ declarations use `format: npz`, `missing_token: nan`, numeric 1D arrays
under the declared keys, and supported NPY v1/v2 headers. They are not an arbitrary
object/structured-array importer. Generic BCIF is still not enabled: a bounded,
identity-preserving binary decoder needs its own acceptance, rather than exposing
untrusted compressed input to an unrestricted parser.

The first full regression after this extension caught an unintended whole-source
JSON read on an existing cached page (604 passed, one cache oracle failed).
The adapter now reuses the sealed declaration metadata, checking grants and
streamed original hashes without reparsing either registered source. The original
cache oracle was retained; an additional CSV/NPZ parser-fail-on-cache-hit guard
protects the new paths. Final regression results supersede that failed run below.

## Release dependency inventory and dated advisory queries

`scripts/release_inventory.py` produces a CycloneDX 1.6 component inventory from
actual pnpm license output, Windows-target-filtered locked Cargo metadata and
the exact Python site-packages selected for packaging. It strips local paths,
retains declared license metadata and does not invent dependency graph edges or
claim every development component is shipped/reachable. Unknown license metadata
is not assigned an invented license. Full license compliance/legal review,
bundled native library analysis and Windows/WebView2 security remain separate.

Optional OSV batch queries send only public ecosystem/name/version tuples.
The 2026-10-07 inventory has 631 components; this query returned no registered
advisory matches. pnpm audit independently found no listed frontend advisories
after the two patches. Neither check is a guarantee of universal vulnerability
absence or proof of exploitability. The desktop packaging script can include the
dated inventory and report, and requires their commit to match the package.

Primary sources: [CycloneDX specification](https://cyclonedx.org/specification/overview/),
[OSV querybatch](https://google.github.io/osv.dev/post-v1-querybatch/).

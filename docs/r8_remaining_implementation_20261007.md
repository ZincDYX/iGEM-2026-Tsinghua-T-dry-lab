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

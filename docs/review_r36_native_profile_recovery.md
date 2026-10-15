# Native PSIPRED profile recovery

The first real full-database batch exposed an integration bug: legacy `makemat`
prepends the prefix directory to filenames from `.pn`/`.sn`, including absolute
entries. This produced a duplicated directory and prevented matrix generation,
although the original BLAST searches had completed. A finished workflow did not
mean its scientific tools succeeded; those fifteen failed attempts are retained.

The adapter now uses relative `native`/`native.chk`/`input.fasta` names in the
native working directory, matching the original author's script. One shared
post-profile function executes original `makemat`, `psipred` and `psipass2` and
validates the complete output against the exact sequence. It also records the
profile identity. There is no single-sequence fallback.

The actual recovery retained each original checkpoint, complete native BLAST
output and exact FASTA, with byte bindings to the original failed attempt. All
fifteen targets subsequently produced native full-length predictions, all had
reported profile hits, and all fifteen were parsed through the real stdio MCP
bridge into a new persistent task. The failed task was not relabeled successful.
These are full-target predictions, not invented isolated short-linker evidence.

A second integration fix applies the existing file-to-asset projection to the
allowlisted scientific MCP capability before publication. Private native paths
stay private, and the public path/secret checks remain active. Regression covers
both the legacy list-file behavior and actual stdio parsing/public asset
projection using clearly synthetic format fixtures.

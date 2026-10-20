# Project-conditioned evidence database

`project_conditioned_evidence_database.csv` is the canonical local evidence
database included with this repository for literature QA and GraphRAG. It is
stored with Git LFS because its size exceeds GitHub's normal single-file limit.

The file contains 20,567 provenance-bearing records and 564 columns. See
`database_manifest.json` for the exact byte size and SHA-256 checksum.

The database is an evidence layer. A row is not an approved kinetic,
partitioning, abundance, or phase parameter. Production M3/M4 calculations
still require typed mapping, unit/identity validation, and explicit human
approval into the Parameter Registry.

After cloning, verify that Git LFS downloaded the real file rather than a small
pointer:

```powershell
git lfs pull
Get-Item data/evidence/project_conditioned_evidence_database.csv
Get-FileHash data/evidence/project_conditioned_evidence_database.csv -Algorithm SHA256
```

Expected SHA-256:

```text
6410268f021ca6b2ca04b6bac7979e52702af4875ee346e6b6aa9328a8f4450a
```

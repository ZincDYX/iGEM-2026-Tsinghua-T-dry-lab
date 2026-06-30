# Third-party provenance

Git submodules are pinned in `.gitmodules` and the parent repository commit. Clone with:

```bash
git clone --recurse-submodules https://github.com/ZincDYX/iGEM-2026-Tsinghua-T-dry-lab.git
```

The official Mpipi supporting code is not a Git repository. It is stored locally at
`third_party/downloads/mpipi/` and intentionally ignored by Git because the archive is
about 49 MB. Provenance:

- Figshare article: `https://doi.org/10.6084/m9.figshare.16772812.v1`
- file: `supporting-code.zip`
- source URL: `https://ndownloader.figshare.com/files/31037434`
- MD5: `a18b0f5e30f15f8b5daf7b66210b663e`
- license reported by Figshare: CC BY 4.0

Run `python scripts/fetch_mpipi.py` to reproduce the local download and extraction.

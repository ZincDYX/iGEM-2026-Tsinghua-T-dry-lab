# Public GFP sequence case

This small real input is the canonical Aequorea victoria GFP sequence from
UniProt P42212 (sequence version 1; 238 residues), downloaded on 2026-10-10.
The [metadata endpoint](https://rest.uniprot.org/uniprotkb/P42212.json) supplies
the length and sequence MD5 used for input verification. Data attribution:
UniProt Consortium, [CC-BY-4.0](https://www.uniprot.org/help/license).
The [original sequence paper](https://doi.org/10.1016/0378-1119(92)90691-H)
is distinct from the Thr65-GFP crystal structure 1EMA; we do not transfer its
residue mapping or treat unknown/modified crystallographic residues as known.

With the supported backend installed, run from the source root:

```powershell
.venv/Scripts/python.exe -B scripts/reproduce_public_case.py --output outputs/public-gfp
```

The script starts a real stdio MCP server, calculates the existing M1 sequence
features, checks input identity and compares mean hydropathy against independent
Biopython ProtParam. It writes `REPORT.md` and `result.json`; no network, account,
LLM or restricted predictor is needed during execution. In the desktop, import
`P42212.fasta`, confirm the protein record and select sequence-property analysis
in Tools. The result is a fresh calculation, not a precomputed CSV.

Scope: one real sequence-property task outside the glabridin system. This does
not establish formal M1–M4 completion, fusion functionality, LLPS or general
biological predictive validity. Independent non-developer use remains untested.

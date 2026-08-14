# Immutable uploaded publication reference

`author_uploaded/` contains byte-identical copies of the supplied author files:
`simulation-network-glabridin-final.py`, `simulation-data.txt`, and `Source Data_V2.xlsx`.
They must not be edited or used as Galatea production code.

Run the reference separately:

```powershell
python scripts/run_published_reference.py
```

The adapter executes the uploaded `reaction_kinetics` function with LSODA and
author-native values. It does not convert those values to uM/h or claim that
they are Galatea measurements.

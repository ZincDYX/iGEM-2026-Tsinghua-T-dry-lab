# Scientific-model audit baseline

Baseline on `feature/scientific-model-refactor` before this refactor: 58 tests passed; 57 Python source files parsed as UTF-8 with no replacement characters or syntax errors. The pasted attachment displayed mojibake in the Codex UI, but the repository source did not.

## Actual computation

- `kinetics.phase_concentrations` and the generic cascade ODE are mass-conserving two-phase calculations.
- competitive DMT kinetics and segmented induction integration are numerical calculations.
- FreeSASA, Vina, structure-prediction, CALVADOS, and FTH1 modules parse or invoke real external outputs only when a configured executable/output exists.

## Demo/mock logic that must not be scientific evidence

The previous pipeline used scaffold/linker enumeration to generate `llps_score`; used linker-ID string length as a clash proxy; derived M3 concentration, saturation, leakage and colocalization from M2 score; and derived M4 enzyme abundance/activity from those proxies. M4 also converted Vina affinity loss to an activity multiplier. These routes are being removed from real mode. The generic ODE remains available as a demonstration utility, not as the glabridin production model.

## Configuration/documentation findings

- `oc_first_weight` and `dmt_later_weight` were configured but unused.
- The pipeline hard-coded a single-chain OC/scaffold/DMT topology and silently selected the first FASTA record as IDR when no `IDR` record existed.
- README previously described optional parsers and mock-ready paths too close to real predictions. Documentation is updated only after the corresponding implementation lands.

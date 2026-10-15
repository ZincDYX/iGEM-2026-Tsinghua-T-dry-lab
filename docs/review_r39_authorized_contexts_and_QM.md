# Authorized M1 designs, context review and QM preparation

These changes preserve the original scientific protocol and add separately
identified owner-authorized branches. They do not establish complete M1/M2
acceptance, experimentally optimal sequences or production-ready cofactor parameters.

## Fixed-backbone IDR substitution

`igem.m1.substitute_idrs` accepts typed ordered construct definitions, IDR source
records and an explicit authorization reference. A template must contain exactly
one declared IDR and a declared localization. Only that part is replaced. Protein
parts, their order, terminal tags and other backbone features remain unchanged.
Derived constructs do not inherit experimental baseline identity, coding DNA,
M1 approval or conformation-specific membrane topology. Original records remain
unchanged. This is the same implementation used by the actual stdio MCP server.

The approved project generation produced 118 IDR substitutions in each of the
cytosolic and ER backbones: 236 distinct computational fusion sequences. They
are not relabeled wet-lab constructs. Running predictors is distinct from passing
their scientific checks.

## Two short-linker protocol versions

`igem.m1.review_linker_context` requires an exact complete construct, a declared
part identity and occurrence, an unchanged linker record with the correct role,
paired ColabFold coordinates/confidence, native DSSP output and protocol approval.
It reuses existing DSSP, region confidence, FreeSASA and PAE calculations.

The original isolated-secondary-prediction branch remains `missing_evidence`.
The approved branch reports actual assignments, confidence, selected-region SASA,
inter-region PAE and CA endpoint/peptide-neighbor distances in angstroms. No reach,
burial, clash or ranking threshold is invented. Low-confidence observations never
become formal acceptance or a hard veto. This branch does not silently substitute
DSSP for an isolated PSIPRED/JPred prediction.

Actual role-bound replay used 20 existing complete model/confidence pairs from
four constructs: 90 linker-region observations for ten of the 35 short-linker
source records. All observations retained confidence uncertainty. The other 25
records still required exact full-fusion models when this replay was made. New
model jobs and their current states belong to the private execution ledger, not
to static claims of completion in this document.

## Source FASTA batches are not backbone substitutions

An exact complete-sequence audit of the separate 120-record direct-fusion FASTA
found only five previously covered records. The 236 authorized computational
designs do not silently replace those original inputs. Remaining source sequences
can be run as native batches without inventing their localization or parts.

`igem.m1.read_native_fusion_batch` reuses the existing SignalP/DeepTMHMM native
parsers, validates the original batch execution/input/output binding and retains
every original record ID. Missing or ambiguous native records remain gaps, not
zero counts. It reports observations only: no default cytosolic context, manual
reviewer signature or formal M1 pass is manufactured. Complete construct/source
annotation is still needed before context-dependent M1/M2 assessment.

## QM targets before CHARMM fitting

`igem.m2.prepare_qm_compound` rebuilds an explicitly declared model-compound
chemical graph from original CCD heavy atoms. Protonation, formal charge,
Kekule bond-order edits, cross-links and cap hydrogen counts are explicit inputs.
Cut heavy-atom bonds require explicit caps. Metal coordination is not inferred
from distance, and a CCD ion label does not decide the project's oxidation state.
RDKit hydrogen coordinates are starting coordinates, not QM observations.

`python -m igem_drylab.quantum_calculations --request REQUEST.json` runs native
PySCF/geomeTRIC optimization, SCF checks, gradients and optional Cartesian
Hessians. Atom mappings, the full request, checkpoint, native logs and results
are retained in a new attempt directory. CPU and CUDA are explicit backends;
failure does not trigger an undisclosed method or hardware substitution. Signed
harmonic wavenumbers retain imaginary modes. Constrained clusters retain the
raw Hessian without presenting unconstrained frequencies as validated modes.

Project starting models include oxidized lumiflavin, two His protonation
alternatives of a bicovalent lumiflavin/His/Cys compound, and a pre-O2 FeII/2OG
target cluster with explicit capped His/Asp boundaries. A model compound is not
a truncated production protein. Neither formal graph charges nor QM population
charges are automatically adopted as CHARMM partial charges.

The FAD extension follows [Aleksandrov 2019](https://doi.org/10.1002/jcc.26061)
for its B3LYP/6-31G(d) model-compound starting method, with the Gaussian-compatible
`B3LYPG` definition and an explicitly recorded density-fitting approximation.
The target metal cluster uses an explicitly new B3LYPG/def2-SVP gas-phase
high-spin candidate protocol, not an alleged reproduction of a published target
metal parameter set. Its fixed cap boundaries, omitted protein embedding and
coordination-water alternatives remain part of the validation scope.

Geometry convergence and a Hessian are QM targets, not completed parameters.
CHARMM-compatible water-interaction charge fitting, bonded PES fitting,
independent QM/MM validation, microstate assessment and full target-topology
integration remain necessary before holo MD. Organic
[published 2OG parameters](https://doi.org/10.1021/jacs.9b09236) alone do not
provide an Fe/2OG metal center. See the
[CHARMM fitting guidance](https://mackerell.umaryland.edu/cgenff_lsfit.php).

## Isolated installation and tests

No model weights, licensed tools, private sequences, credentials or deployment
addresses are shipped in this repository. Optional QM dependencies are not part
of the desktop runtime or executable.

For the tested Linux Python 3.11 / CUDA 12 research environment:

```sh
python3.11 -m venv .venv-qm
. .venv-qm/bin/activate
python -m pip install -r requirements/qm-gpu-py311-linux.lock
PYTHONPATH=src python -m pytest tests/test_quantum_calculations.py
CUDA_VISIBLE_DEVICES=0 FUSIONLAB_QM_GPU_TEST=1 PYTHONPATH=src \
  python -m pytest tests/test_quantum_calculations.py
```

Native CPU/GPU tests use an explicitly synthetic H2 numerical oracle: independent
same-geometry CPU energy, variational energy decrease, gradients, Hessian symmetry
and a positive stretch. Those tests do not validate cofactor chemistry. Real
project calculations retain their own outputs separately. Tool references:
[PySCF optimization](https://pyscf.org/user/geomopt.html),
[PySCF Hessians](https://pyscf.org/pyscf_api_docs/pyscf.hessian.html),
[GPU4PySCF](https://github.com/pyscf/gpu4pyscf).

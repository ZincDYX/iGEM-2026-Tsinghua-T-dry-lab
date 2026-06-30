# Literature and code audit

Checked on 2026-06-30. GitHub popularity and activity values are time-dependent and may change.

## Attachment-by-attachment findings

| Attachment | Public code found | What it can do | What it cannot justify |
|---|---|---|---|
| Chemical Reactions regulated by Phase-Separated Condensates (Phys. Rev. Research 6, 043092, 2024) | No code/repository statement was found in the supplied PDF or arXiv record. Equations are reimplemented in this repository. | Relate phase volume, client partitioning, diffusion and reaction rates; search for an optimal condensate volume. | It does not predict protein-scaffold binding poses, linker sequences, enzyme expression order, or a Corelets construct that realizes the optimum. |
| DiffDock-PP (ICLR MLDD 2023) | `ketatam/DiffDock-PP`, official paper code; 236 stars/43 forks; last push 2023-12-29; no repository license detected. | Rigid protein-protein docking and confidence ranking. | Not protein-small-molecule docking; not flexible-linker ensemble modeling. Missing license means reuse/redistribution permissions are uncertain. |
| Physics-driven coarse-grained model for biomolecular phase separation with near-quantitative accuracy (Mpipi) | Official Figshare dataset `10.6084/m9.figshare.16772812.v1`, CC BY 4.0, with LAMMPS scripts/parameters. | Coarse-grained sequence-dependent LLPS simulations and phase diagrams. | Not an enzyme activity predictor and not a direct linker-design tool; calibration and substantial simulation cost are required. |
| Predicting protein condensate formation using machine learning (PSAP) | Paper code `Guido497/phase-separation`; installable author-lab package `vanheeringen-lab/psap` (MIT, PyPI/Bioconda). | Sequence-level probability that a protein belongs to the training concept of phase-separating proteins. | Cannot identify an insertion site, design a linker, predict droplet volume, or validate a chimeric scaffold mechanistically. Generalization from the human-biased training set to engineered yeast fusions is uncertain. |
| Corelets (Cell 2018) | No standalone analysis repository was identified in the supplied paper; MATLAB/ImageJ are listed and construct details are provided. | The paper provides phase-diagram, valency and lever-rule measurements plus plasmid/construct information. | Fluorescent reporters are not necessarily inert spacers. Replacing them with SH3/PDZ changes size, valency and phase behavior and must be remapped experimentally. |
| Dueber et al. synthetic scaffolds (Nat. Biotechnol. 2009) | No software repository; this is an experimental construct paper. | Establishes SH3/PDZ/GBD recruitment, repeat-number control, nine-residue Gly/Ser linkers and a biphasic scaffold-concentration effect. | Its optimal G1S2P2 architecture in E. coli cannot be transferred numerically to OC/DMT in yeast without calibration. |
| Engineered Optogenetic Circuits in Yeast with Self-Sustained Outputs (Adv. Sci. 2026) | The paper states that supporting data are in the supplement; no public code repository statement was found. | Supports an OptoQS/positive-feedback control concept in yeast. | Does not supply a validated quantitative model for the proposed Corelets-enzyme circuit. |

## Selected upstream repositories

These are included as Git submodules at fixed commits so provenance remains visible.

| Repository | Reliability evidence | Role here | Caveat |
|---|---|---|---|
| `google-deepmind/alphafold3` | Official DeepMind code; Apache-2.0; 8276 stars; active in June 2026. | Structure prediction and AF3 output format reference. | Model parameters and compute setup have separate requirements; predictions of long flexible linkers remain uncertain. |
| `ccsb-scripps/AutoDock-Vina` | Official Scripps project; Apache-2.0; 1018 stars; active in 2026. | Enzyme-small-molecule docking. | Docking score is not a catalytic free energy and should not be called a rigorous Delta G. |
| `mittinatten/freesasa` | Published FreeSASA implementation; MIT; 195 stars; active in 2026. | Pocket SASA. | Results depend on atom radii, probe radius and residue selection. |
| `zwicker-group/py-pde` | Maintained MIT project; 463 stars; active in June 2026. | Optional reaction-diffusion/phase-field extension. | A spatial PDE model needs measured diffusion and boundary/partition parameters. |
| `vanheeringen-lab/psap` | Author-lab implementation, MIT, available through PyPI/Bioconda. | Reproduce PSAP sequence scoring. | Only 4 stars and last pushed in 2022; retained because it is paper-author code, not because of popularity. |
| `ketatam/DiffDock-PP` | Official paper code; 236 stars and 43 forks. | Optional protein-protein comparison. | No detected license and not the correct method for substrate docking. |

## Deliberately not adopted as a dependency

- `Mpipi-T` has only 3 stars and is a later thermoresponsive extension; the exact supplied-paper code is taken from the official Figshare record instead.
- `LinkCraft` is directly relevant and has a 2026 Journal of Molecular Biology methods paper, but it is very new and its GitLab endpoint could not be cloned during this audit. It is recorded as a future evaluation target, not a current dependency.
- Random zero-star Mpipi helper repositories were excluded.

## Missing project inputs

The following are required before any project-specific ranking or “best ratio” is defensible:

1. OC and DMT amino-acid sequences/UniProt accessions and intended subcellular localization;
2. catalytic pocket residue numbers and reference structures;
3. exact substrate 10/11 identities plus SMILES/SDF and protonation state;
4. candidate ligand tags, domain order and linker sequences;
5. measured or literature `kcat`, `Km`, enzyme abundance, degradation and toxicity data;
6. Core/IDR/enzyme partition coefficients and an experimentally reachable Corelets phase diagram in yeast.

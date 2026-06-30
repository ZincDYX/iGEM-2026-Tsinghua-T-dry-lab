# Modeling notes and corrected decision rules

## 1. Static structure screen

- Pocket SASA: compare the same residues and the same FreeSASA parameters in wild type and fusion. A 15% cutoff is a project heuristic, not a literature-established universal threshold.
- Pocket RMSD: first align the enzyme backbone, then calculate pocket heavy-atom RMSD. A 1.5 Å cutoff is also a heuristic; catalytic geometry may require residue-specific distance/angle checks.
- PAE: summarize both enzyme-to-tag and tag-to-enzyme blocks. High PAE is compatible with flexibility but may also mean poor prediction or insufficient evolutionary information; it is not a positive score by itself.
- Distance: calculate against an assembled FTH1 24-mer, not an isolated FTH1 monomer. Radial clearance is an approximation; minimum atom distance and sampled linker conformations are more useful for steric exclusion.
- AF3 seeds: compare multiple random seeds. A single predicted pose is not a conformational ensemble.

## 2. Linker candidates

Start with a small factorial library rather than claiming a single designed optimum:

- lengths: `(GGGGS)1`, `(GGGGS)2`, `(GGGGS)3`, and the nine-residue Gly/Ser linker used by Dueber et al.;
- both N- and C-terminal enzyme tags where catalytically permissible;
- reject candidates with pocket occlusion or consistent cage/domain collision across seeds;
- advance the best two or three to explicit-solvent MD and experimental activity assays.

PSAP cannot choose a linker. It uses global sequence-derived features to classify condensate-forming proteins and does not model the 3D geometry of a fusion or an insertion site.

## 3. Condensate volume and enrichment

Let `phi` be condensate volume fraction and `P_X = [X]_dense/[X]_dilute`. For a conserved cell-average concentration `X_bar`:

```text
[X]_dilute = X_bar / ((1 - phi) + phi * P_X)
[X]_dense  = P_X * [X]_dilute
```

The cell-average reaction rate is the volume-weighted sum of dense- and dilute-phase rates. This is why enrichment cannot simply multiply `Vmax`.

The 2024 reaction-condensate paper treats condensate volume as a control parameter and predicts an optimum produced by enrichment competing with dilution. In Corelets, `phi` is experimentally tuned indirectly by total core concentration, IDR:core valency, expression, illumination intensity/duty cycle, and the IDR sequence. IDR design changes the binodal and dense-phase concentration, but does not uniquely set a desired volume or droplet radius. The appropriate workflow is to map a phase diagram, use the lever rule to predict `phi`, and then optimize kinetics over the experimentally reachable region.

## 4. Order and ratio

A two-step ODE can predict the expression allocation that maximizes product or minimizes toxic intermediate accumulation once `kcat`, `Km`, degradation, partition coefficients and enzyme abundances are measured. It does not prove molecular “first-then-second” ordering inside a condensate. Spatial order would require explicit architecture or distance-resolved modeling; kinetic order follows from the reaction network itself.

For yeast, convert the predicted abundance ratio into promoter/5'UTR/copy-number/degradation-tag designs, then calibrate protein abundance experimentally. Do not use a bacterial RBS Calculator as the final design layer.

## 5. OptoQS-Corelets compatibility

The two light layers do not automatically solve each other's persistence problem. OptoQS can convert a short light input into sustained gene expression through quorum sensing/feedback, but the original iLID-SspB Corelets interaction itself remains light dependent and the supplied Corelets paper reports dissolution after illumination is removed. Sustained abundance of Corelet components therefore does not imply sustained assembly.

At least one of the following must be designed and tested:

- keep a low-duty-cycle illumination schedule that maintains iLID-SspB binding;
- let OptoQS drive a condensate module whose assembly no longer requires light;
- introduce a separately validated biochemical memory/latch for assembly;
- accept transient droplets and model pulsed production explicitly.

This is a system-architecture decision, not a parameter that the current ODE can infer.

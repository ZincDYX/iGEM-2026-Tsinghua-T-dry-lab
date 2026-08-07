# LLPS-LKD-AI Agent protocol implementation map

This document maps protocol dry-lab sections 5.1-5.6 to concrete local code.

## Summary

The current implementation is a protocol-aware local agent layer over the existing
literature database. It uses the real local CSV evidence database by default and
does not fabricate literature records.

Default evidence source:

```text
essay/project_conditioned_evidence_database.csv
```

Core implementation:

```text
CatalystOptimizationSystem/core/lkd_agent.py
```

HTTP API implementation:

```text
CatalystOptimizationSystem/api/app.py
```

## 5.1 Literature crawling and evidence database

Implemented by the existing extraction pipeline plus the evidence QA layer.

Main code:

```text
CatalystOptimizationSystem/core/extractor.py
CatalystOptimizationSystem/core/literature_qa.py
CatalystOptimizationSystem/core/lkd_agent.py
```

Agent methods:

```python
LkdAgent.status()
LkdAgent.evidence(question, top_k, filters)
```

HTTP API:

```text
POST /agent/status
POST /agent/evidence
POST /literature-qa
```

Returned evidence keeps row index, DOI, title, metric, value, unit and evidence text.

## 5.2 LLPS component candidate library

Implemented as a deterministic component library seeded from the protocol and
linked to evidence retrieval.

Agent method:

```python
LkdAgent.components(query, top_k, include_defaults)
```

HTTP API:

```text
POST /agent/components
```

Included component classes:

```text
FTH1/Corelet seed
FUSn low-complexity IDR
iLID-SspB
CRY2
SH3/PDZ/GBD scaffold
GS linker family
EAAAK linker family
```

The module records name, category, sequence if known, source, evidence, yeast use,
LLPS evidence, reversibility evidence, growth risk and recommended use.

## 5.3 Linker and fusion topology library

Implemented as a first-round construct enumerator for DMT-first recruitment.

Agent method:

```python
LkdAgent.constructs(enzyme, top_k, include_oc, sbd_candidates)
```

HTTP API:

```text
POST /agent/constructs
```

The output schema follows the protocol:

```text
construct_id
enzyme
tag_position
linker_sequence
llps_component
recruitment_module
expected_effect
risk_note
```

Current rule:

```text
DMT is the first recruited enzyme.
OC fusion is conservative and C-terminal only unless explicitly requested.
```

## 5.4 Structure safety screen

Implemented as a rule-based triage layer. It can score candidates immediately
from supplied metrics and reports which strict structural inputs are still needed.

Agent method:

```python
LkdAgent.structure_screen(candidates, top_k)
```

HTTP API:

```text
POST /agent/structure-screen
```

Supported metrics:

```text
pocket_sasa_ratio
pocket_rmsd_angstrom
interdomain_pae_mean
d_center_nm
clash_score
linker_length_aa
```

Important boundary:

```text
This does not run AlphaFold3 automatically.
It is a decision layer for metrics from AF3 or other structure tools.
```

## 5.5 LLPS propensity and phase-diagram pre-screen

Implemented as a sequence-feature heuristic for first-pass triage.

Agent method:

```python
LkdAgent.llps_score(sequences)
```

HTTP API:

```text
POST /agent/llps-score
```

Features:

```text
IDR proxy
low complexity
aromatic sticker score
RGG/RGR motif count
charge fraction
hydrophobic fraction
hydrophobic penalty
```

Important boundary:

```text
This is not a replacement for PSAP, Mpipi or measured phase diagrams.
It identifies first-pass candidates and controls.
```

## 5.6 Recruitment, partition and local concentration model

Implemented as a mass-conserving partition model.

Agent method:

```python
LkdAgent.partition_model(enzyme_total, phi_values, kp_values, free_activity_threshold)
```

HTTP API:

```text
POST /agent/partition-model
```

Model:

```text
[E]_dilute = [E]_total / ((1 - phi) + Kp * phi)
[E]_dense  = Kp * [E]_dilute
```

Output fields:

```text
Kp_assumption
phi
dense_DMT
dilute_DMT
dense_fraction_of_total
saturation_risk
diffusion_risk
leakage_risk
```

## Integrated design endpoint

The integrated endpoint calls sections 5.1-5.6 in order and returns evidence,
recommended components, recommended constructs, partition priors and wet-lab
decision gates.

Agent method:

```python
LkdAgent.design(question, top_k)
```

HTTP API:

```text
POST /agent/design
```

## Not yet automated

The following are still external or future work:

```text
AlphaFold3 structure generation
small-molecule docking for SBD candidates
Mpipi/PSAP execution
closed-loop wet-lab result ingestion
automatic plasmid/GenBank generation
```


# New-environment setup

## 1. Clone code and Git LFS data

Install Git LFS before cloning, or run `git lfs install` once afterwards.

```powershell
git clone --branch develop https://github.com/ZincDYX/iGEM-2026-Tsinghua-T-dry-lab.git
cd iGEM-2026-Tsinghua-T-dry-lab
git lfs install
git lfs pull
```

The canonical evidence database is:

```text
data/evidence/project_conditioned_evidence_database.csv
```

Its expected size and checksum are recorded in
`data/evidence/database_manifest.json`.

## 2. Create a Python environment

Python 3.10-3.12 is recommended. Use a fresh environment so compiled NumPy,
SciPy, and Pydantic components all target the same Python interpreter.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test,plot]"
```

Optional FreeSASA support:

```powershell
python -m pip install -e ".[sasa]"
```

## 3. Configure optional providers

```powershell
Copy-Item .env.example .env
```

Fill only the providers used locally. Never commit `.env`, `API.txt`, or raw
keys. Qwen and DeepSeek use separate key, endpoint, and model variables.

## 4. Verify the database and build the graph

```powershell
Get-FileHash data/evidence/project_conditioned_evidence_database.csv -Algorithm SHA256

igem-drylab literature build-graph `
  --evidence data/evidence/project_conditioned_evidence_database.csv `
  --output outputs/project_evidence_graph.json
```

The graph is generated locally and is not committed. Its evidence fingerprint
prevents a graph built from an older database from being silently reused.

## 5. Start GraphRAG QA

Deterministic BM25 + graph retrieval:

```powershell
igem-drylab literature serve-qa `
  --evidence data/evidence/project_conditioned_evidence_database.csv `
  --graph --graph-path outputs/project_evidence_graph.json
```

Open `http://127.0.0.1:8765/`.

Enable embedding retrieval as a fourth configured component only after setting
the `QA_EMBEDDING_*` variables:

```powershell
igem-drylab literature serve-qa `
  --evidence data/evidence/project_conditioned_evidence_database.csv `
  --semantic --graph --graph-path outputs/project_evidence_graph.json
```

## 6. Run the scientific and Agent checks

```powershell
pytest -q
igem-drylab pipeline validate configs/m1_m4_example.yaml
igem-drylab agent dry-run examples/agent/validate_config_task.json
```

Run the provider/architecture baseline matrix after configuring API variables:

```powershell
python scripts/run_agent_baseline_matrix.py `
  --benchmark benchmarks/agent_orchestration_heldout_v2 `
  --output-root results/agent_baseline_matrix `
  --jobs 5
```

The matrix compares rule-based, direct Qwen, direct DeepSeek, Hybrid Qwen, and
Hybrid DeepSeek under the same frozen cases and scorer. Missing providers are
reported as skipped unless `--strict` is supplied.

# iGEM Tsinghua-T Literature Knowledge Design AI Agent

This repository contains the dry-lab literature extraction and evidence-grounded design-support code for the iGEM Tsinghua-T project. The system focuses on literature mining for Yeast, Glabridin biosynthesis, LLPS/condensate regulation and enzyme-catalysis design.

## What This Project Does

- Builds a candidate literature pool from Elsevier, Web of Science and open full-text routes.
- Extracts multi-record experimental evidence with JSON Schema constraints and dynamic ICL examples.
- Normalizes units, validates required/non-zero fields and keeps DOI/title/evidence provenance.
- Expands evidence from full text, SI, supplementary tables and data files.
- Provides a local web UI for extraction, cleaning, imputation, optimization and literature QA.
- Adds an optional DeepSeek-Pro grounded-answer layer that only writes answers from retrieved evidence rows.

## Repository Layout

- `CatalystOptimizationSystem/`: main application package.
  - `api/app.py`: local HTTP API server.
  - `core/extractor.py`: literature search, prompt construction, LLM extraction and CSV output.
  - `core/schema_config.py`: schema loading, field rules and unit constraints.
  - `core/icl_selector.py`: dynamic ICL example retrieval.
  - `core/literature_qa.py`: evidence retrieval and DeepSeek-grounded QA.
  - `core/lkd_agent.py`: LLPS-LKD design-support agent modules.
  - `ui/`: static web frontend with the iGEM-styled Literature QA page.
  - `docs/`: schema files, ICL examples and gold examples.
- `scripts/`: batch workflows for literature collection, PDF/SI processing, high-recall extraction, LLM QC, database aggregation and visualization.
- `tools/`: Windows helper scripts for environment checking, server startup and software-copyright export.
- `docs/`: project-structure and implementation notes.

Large runtime outputs are intentionally not committed. These include `essay/`, `outputs/`, `uploads/`, PDFs, CSV databases, supplementary files and API keys.

## Setup

```powershell
cd D:\文献抽取igem
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item API.example.txt API.txt
```

Fill your local `API.txt` with keys. Do not commit `API.txt`.

```text
ELSEVIER_API_KEY='YOUR_ELSEVIER_API_KEY'
DEEPSEEK_API_KEY='YOUR_DEEPSEEK_API_KEY'
WOS_API_KEY='YOUR_WEB_OF_SCIENCE_API_KEY_OPTIONAL'
```

## Start The Web App

PowerShell:

```powershell
cd D:\文献抽取igem
& C:\Users\zhaol\AppData\Local\Programs\Python\Python313\python.exe -m CatalystOptimizationSystem.api.app
```

Windows cmd:

```cmd
cd /d D:\文献抽取igem
C:\Users\zhaol\AppData\Local\Programs\Python\Python313\python.exe -m CatalystOptimizationSystem.api.app
```

Open:

```text
http://127.0.0.1:8080/
```

If port 8080 is occupied:

```cmd
cd /d D:\文献抽取igem
C:\Users\zhaol\AppData\Local\Programs\Python\Python313\python.exe -m CatalystOptimizationSystem.api.app 127.0.0.1 8090
```

## Literature QA

The `Literature QA` tab works in two modes:

- Local retrieval + rules: retrieves project-conditioned evidence and returns deterministic recommendations.
- DeepSeek grounded answer: sends only the retrieved evidence package and local rule summary to DeepSeek, then returns a Chinese answer with row/DOI citations.

The LLM layer is optional and disabled by default to avoid accidental API usage.

## Schema-first Extraction Example

```powershell
python -m CatalystOptimizationSystem.core.extractor `
  --elsevier-key YOUR_ELSEVIER_KEY `
  --keyword "phase separation metabolic engineering enzyme" `
  --count 20 `
  --schema CatalystOptimizationSystem/docs/schemas/glabridin_enzyme_catalysis.schema.json `
  --icl-bank CatalystOptimizationSystem/docs/icl_bank.default.jsonl `
  --icl-top-k 3 `
  --domain glabridin_enzyme_catalysis `
  --llm-key YOUR_LLM_KEY `
  --llm-base https://api.deepseek.com/v1/chat/completions `
  --llm-model deepseek-chat `
  --out extracted_schema.csv
```

## Data And Secret Policy

The repository keeps code and reusable prompt/schema assets only. It excludes:

- `API.txt`, `.env`, keys and tokens.
- `essay/`, `outputs/`, `uploads/`.
- downloaded PDFs and supplementary files.
- generated CSV/TSV/JSONL databases.
- Word/Excel/PDF project documents and cached full text.

Share large databases through releases, object storage, Git LFS or a separate data archive rather than normal Git commits.

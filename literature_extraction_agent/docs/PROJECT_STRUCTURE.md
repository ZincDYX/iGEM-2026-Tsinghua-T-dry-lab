# Project Structure

## Main Package: `CatalystOptimizationSystem`

- `api/app.py`: local HTTP API server for extraction, cleaning, imputation, optimization, evidence QA and LLPS-LKD agent endpoints.
- `core/extractor.py`: Elsevier search, full-text retrieval, prompt building, LLM calls, multi-chunk extraction and resumable CSV output.
- `core/schema_config.py`: JSON Schema loading, field rules, unit normalization and cross-field constraints.
- `core/icl_selector.py`: dynamic ICL retrieval from the example bank.
- `core/literature_qa.py`: evidence retrieval plus optional DeepSeek grounded-answer generation.
- `core/lkd_agent.py`: design-support modules for evidence retrieval, component selection, construct planning, structure screening, LLPS scoring and partition modeling.
- `core/validator.py`: structured-record cleaning and validation.
- `core/imputer.py` and `core/imputation_workflow.py`: missing-value evaluation and imputation workflow.
- `core/optimizer.py`: Bayesian optimization and experiment recommendation logic.
- `docs/icl_examples.default.json`: default ICL examples.
- `docs/icl_bank.default.jsonl`: dynamic ICL example bank.
- `docs/gold_examples.default.jsonl`: small gold set for scoring and regression checks.
- `docs/schemas/*.schema.json`: domain schemas, units, required fields and constraints.
- `ui/`: static frontend. The current user-facing title is `iGEM Tsinghua-T Literature Knowledge Design AI Agent`.
- `tests/`: lightweight unit tests.

## Batch Scripts: `scripts`

Literature pool and full text:

- `collect_candidate_literature_20000.py`
- `collect_candidate_literature_year_slices.py`
- `continue_candidate_literature.py`
- `direct_pdf_candidates_20000.py`
- `openalex_pdf_candidates_20000.py`
- `download_pdf_candidates.py`
- `download_elsevier_article_pdfs.py`
- `cache_downloaded_pdf_text.py`

Supplementary and data extraction:

- `download_supplementary_for_current_database.py`
- `cache_supplementary_texts.py`
- `run_supplementary_until_limit.py`

Evidence mining and database construction:

- `mine_numeric_evidence_records.py`
- `clean_numeric_evidence_database.py`
- `build_high_recall_structured_database.py`
- `aggregate_structured_records.py`
- `merge_aggregated_databases.py`
- `merge_clean_databases.py`
- `optimize_experimental_database.py`

LLM QC and completion:

- `llm_complete_d_result_only_with_fulltext.py`
- `llm_qc_high_recall_structured.py`
- `llm_qc_enrich_broad_database.py`
- `llm_normalize_clean_database.py`
- `llm_upgrade_rule_c_with_context.py`
- `llm_upgrade_rule_c_groups_with_context.py`
- `fulltext_pro_field_completion.py`

Visualization:

- `generate_modified_project_visualization_v6.py`
- `generate_project_story_takehome_visualization_v5.py`
- `generate_morandi_publication_visuals.py`
- `generate_nature_style_vector_pdf_en.py`
- `generate_known_visualization_report_en.py`

## Local Runtime Outputs

The following are intentionally excluded from GitHub:

- `API.txt`
- `essay/`
- `outputs/`
- `uploads/`
- `archive/`
- `*.pdf`
- `*.csv`
- `*.tsv`
- `*.jsonl` outside approved docs assets
- `*.docx`, `*.xlsx`, `*.xls`
- Python caches and local IDE files

These files may contain API keys, copyrighted papers, full-text caches, supplementary materials or large generated databases.

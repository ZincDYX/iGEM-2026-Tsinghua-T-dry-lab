# 代码结构说明

## 主系统：CatalystOptimizationSystem

- `api/app.py`：内置 HTTP API 服务，包含健康检查、优化建议和文献抽取接口。
- `core/extractor.py`：文献检索、prompt 构建、LLM 调用和抽取结果输出。
- `core/schema_config.py`：JSON Schema 加载、字段规则、单位规范化和跨字段约束。
- `core/icl_selector.py`：动态 ICL 示例选择，根据文本、domain、metrics 和关键词匹配示例。
- `core/validator.py`：结构化字段校验和基础清洗。
- `core/imputer.py`、`core/imputation_workflow.py`：缺失值插补评估与交互式插补流程。
- `core/optimizer.py`：贝叶斯优化/实验建议相关逻辑。
- `core/scorer.py`：gold examples 对比评分。
- `docs/icl_examples.default.json`：兼容旧流程的 ICL 示例。
- `docs/icl_bank.default.jsonl`：动态 ICL 示例库。
- `docs/gold_examples.default.jsonl`：抽取评分用小型 gold set。
- `docs/schemas/*.schema.json`：领域 schema、单位、必填字段和约束。
- `ui/`：前端静态页面。
- `tests/`：轻量单元测试。

## 批处理脚本：scripts

### 候选文献与全文

- `collect_candidate_literature_20000.py`：早期候选文献收集。
- `collect_candidate_literature_year_slices.py`：按年份切片扩展候选文献池。
- `continue_candidate_literature.py`：候选文献续跑。
- `direct_pdf_candidates_20000.py`、`openalex_pdf_candidates_20000.py`：开放 PDF 候选链接发现。
- `download_pdf_candidates.py`、`download_elsevier_article_pdfs.py`：PDF 下载。
- `cache_downloaded_pdf_text.py`：PDF 全文转文本缓存。

### SI/data 补充材料

- `download_supplementary_for_current_database.py`：从 DOI landing page、全文链接和 Elsevier XML 中发现并下载 supplementary/data 文件。
- `cache_supplementary_texts.py`：把 xlsx/csv/zip/docx/pdf/txt 转为统一文本缓存。
- `run_supplementary_until_limit.py`：全量编排脚本，按 DOI 批次执行下载、转文本、证据挖掘、清洗、结构化、聚合和优化。

### 证据挖掘和数据库构建

- `mine_numeric_evidence_records.py`：高召回数值证据挖掘，支持断点续跑。
- `clean_numeric_evidence_database.py`：规则清洗明显噪声。
- `build_high_recall_structured_database.py`：把候选证据映射为 schema 字段。
- `aggregate_structured_records.py`：按 DOI、结果指标和证据上下文聚合为实验记录。
- `merge_aggregated_databases.py`：合并主分析库和 SI/data 聚合库。
- `optimize_experimental_database.py`：最终去重、分层和 Excel-friendly 核心库生成前处理。

### LLM 质控和补全

- `llm_complete_d_result_only_with_fulltext.py`：对 D_result_only 记录用全文上下文补全。
- `llm_qc_high_recall_structured.py`：对高召回结构化记录做 LLM 质控。
- `llm_normalize_clean_database.py`：二次规范化清洗。
- `llm_upgrade_rule_c_with_context.py`、`llm_upgrade_rule_c_groups_with_context.py`：对 RULE_C/C_partial 记录做上下文升级。

## 本地运行产物

以下目录/文件为运行产物，默认不提交 GitHub：

- `essay/`
- `outputs/`
- `uploads/`
- `*.pdf`
- `*.csv`
- `*.xlsx`
- `*.docx`
- `API.txt`

这些文件可能包含 API key、版权文献、全文缓存、补充材料或超大数据库。

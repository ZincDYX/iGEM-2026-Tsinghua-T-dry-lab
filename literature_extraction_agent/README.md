# 文献抽取 iGEM 项目

这个仓库整理了面向光甘草定酶催化、代谢工程和 LLPS/凝聚体调控方向的文献抽取流程。项目包含模块化抽取系统、动态 ICL 材料、JSON Schema 约束、候选文献检索、全文/补充材料下载、数值证据高召回挖掘、结构化聚合和最终数据库分层优化。

## 代码结构

- `CatalystOptimizationSystem/`：主系统代码，包含抽取、schema、动态 ICL、校验、插补、优化和 API。
- `scripts/`：批处理脚本，覆盖候选文献收集、PDF/SI 下载、文本缓存、证据挖掘、结构化、聚合、合并和最终优化。
- `tools/`：Windows 环境检查、API server 启动和软著材料导出脚本。
- `docs/`：项目结构、运行流程和软著相关说明。
- `CatalystOptimizationSystem/docs/`：ICL 示例、gold examples 和 schema 文件。

大型运行产物不进入 GitHub，包括 `essay/`、`outputs/`、PDF、补充材料、全文缓存和最终 CSV 数据库。真实 API key 保存在本地 `API.txt`，不要提交。

## 环境准备

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item API.example.txt API.txt
```

然后在 `API.txt` 中填入本地 API key。

## 常用入口

启动模块化 API：

```powershell
powershell -ExecutionPolicy Bypass -File tools/run_api_server.ps1
```

运行 schema-first 抽取：

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

继续全量 SI / supplementary table / data 补抽：

```powershell
python scripts/run_supplementary_until_limit.py `
  --limits 2500,3000,3500,4000,4500,5000,5275 `
  --cache-python "C:\Path\To\Python\python.exe" `
  --workers 8 `
  --final-each-limit
```

## 输出说明

本地运行后主要输出位于 `essay/` 和 `essay/supplementary_current/`，这些文件可能很大，默认被 `.gitignore` 排除。常见关键产物包括：

- `optimized_experimental_database_with_supplementary.csv`
- `optimized_core_experimental_database_with_supplementary.csv`
- `optimized_core_experimental_database_with_supplementary_excel_friendly.csv`
- `supplementary_current_download_manifest.csv`

如果需要共享数据库，建议使用 release 附件、网盘、对象存储或 Git LFS，不建议直接提交普通 Git。

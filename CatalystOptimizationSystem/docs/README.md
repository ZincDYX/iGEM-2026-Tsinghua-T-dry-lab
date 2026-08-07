# CatalystOptimizationSystem

A minimal modular layout for catalyst data cleaning, imputation, and Bayesian optimization.

Structure
- core/: algorithms (validator, imputer, optimizer)
- utils/: config, logger, simple visualization
- api/: built-in HTTP server (no FastAPI)
- tests/: lightweight tests
- docs/: this README

Quickstart
- Cleaning: python -m CatalystOptimizationSystem.core.validator path/to/input.csv
- API: python -m CatalystOptimizationSystem.api.app 127.0.0.1 8080
  - GET /health
  - POST /suggest with JSON {"csv_path": "FinalCleanedDatabase.csv"}

Python 3.10. External deps: pandas, numpy, scikit-learn, scipy, matplotlib (optional for utils.visualizer).

Windows Python note
- On this machine, bare `py` may select Python 3.13 free-threading (`python3.13t.exe`), which breaks numpy/pandas imports.
- Use stable CPython explicitly:
  - Check environment: `powershell -ExecutionPolicy Bypass -File tools/check_python_env.ps1`
  - Start API server: `powershell -ExecutionPolicy Bypass -File tools/run_api_server.ps1`
  - CLI form: `py -3.13 -m CatalystOptimizationSystem.api.app 127.0.0.1 8080`
# 新增：提取工作流（用户输入 API/关键词/数量/指标/ICL）

## CLI（命令行）
python -m CatalystOptimizationSystem.core.extractor \
  --elsevier-key <YOUR_KEY> \
  --keyword "CO2 hydrogenation methanol" \
  --count 25 \
  --metrics co2_conversion methanol_selectivity methanol_yield \
  --icl CatalystOptimizationSystem/docs/icl_examples.default.json \
  --llm-key <OPENAI_COMPATIBLE_KEY> --llm-base https://api.deepseek.com/v1/chat/completions --llm-model deepseek-chat

- --icl 可选；不提供则使用内置默认 ICL JSON。
- --llm-key 可选；不提供则只构建检索表，不做 LLM 抽取。

## API（无需 FastAPI）
POST /extract
{
  "elsevier_key": "...",
  "keyword": "CO2 hydrogenation methanol",
  "count": 20,
  "metrics": ["co2_conversion","methanol_selectivity","methanol_yield"],
  "icl_path": "CatalystOptimizationSystem/docs/icl_examples.default.json",
  "llm_key": "...",
  "llm_base": "https://api.deepseek.com/v1/chat/completions",
  "llm_model": "deepseek-chat",
  "out": "extracted.csv"
}

返回：{ "output_csv": "extracted.csv" }

## 代码位置
- 核心逻辑：CatalystOptimizationSystem/core/extractor.py
- API 扩展：CatalystOptimizationSystem/api/app.py（新增 POST /extract）
- 默认 ICL：CatalystOptimizationSystem/docs/icl_examples.default.json
注意：指标与列名仅支持英文、数字与下划线（ASCII）。
- CLI 会对 --metrics 参数进行校验，不符合将报错。
- API /extract 与 /suggest 也会在请求时校验 metrics 与 columns。
## 插补评估与参数建议（新增）

- 运行评分（可选用 LLM 提出候选参数）：
  python -m CatalystOptimizationSystem.core.imputation_workflow --csv cleaned.csv --mask-frac 0.1 --repeats 3 --llm-key YOUR_LLM_KEY --llm-base https://api.deepseek.com/v1/chat/completions --llm-model deepseek-chat

- 仅用默认候选（不调用 LLM）：
  python -m CatalystOptimizationSystem.core.imputation_workflow --csv cleaned.csv

- 查看命令输出中的评分摘要，并打开保存的 JSON 详情（imputation_eval_*.json）。

- 按用户选择与参数（手动输入）执行最终插补：
  python -m CatalystOptimizationSystem.core.imputation_workflow --csv cleaned.csv --apply --final-method knn --final-params '{"n_neighbors":7, "weights":"distance", "metric":"nan_euclidean"}' --out imputed_knn.csv

说明
- 评分方法：随机掩蔽一部分真实值，使用不同方法/参数插补后与真值比较，汇总 NRMSE（越小越好）。分数 = -NRMSE（越高越好）。
- 三种方法：median / knn / mice（IterativeImputer+BayesianRidge）。
- LLM 只负责“提出候选参数并参与评分”，最终采用的模型与参数由用户手动决定并输入 --final-method/--final-params。
## 交互式插补工作流（更新）

- 运行（默认交互模式，会先显示 LLM 建议与评分，然后允许你无限次修改参数，输入 run 执行）：
  python -m CatalystOptimizationSystem.core.imputation_workflow --csv cleaned.csv --llm-key YOUR_LLM_KEY

- 非交互直通（保持旧行为）：
  python -m CatalystOptimizationSystem.core.imputation_workflow --csv cleaned.csv --apply --final-method knn --final-params '{"n_neighbors":7, "weights":"distance", "metric":"nan_euclidean"}'

交互命令说明
- 输入 median/knn/mice 选择模型并按提示输入参数（回车可接受建议默认值）。
- 输入 run 执行并进入后续流程（输出最终插补数据集）。
- 输入 q 退出不执行。

执行后会在控制台打印：
- LLM 给出的候选参数与各自评分（-NRMSE 分数，越高越好）。
- 最终执行的模型与参数，并写出 CSV。

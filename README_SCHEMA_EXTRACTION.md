# Schema-first 文献抽取改进说明

这个文件夹是从 `25-python-\code` 复制出的文献抽取副本，并加入了三个改进点：

1. Schema-first：用 JSON Schema 统一字段、单位、约束、清洗列和优化映射。
2. 动态 ICL：从 ICL bank 中按当前文本、metrics、domain 自动选择最相关示例。
3. Evidence + scoring：每个抽取值保留证据句，并提供 gold set 评分脚本。

## 新增文件

- `CatalystOptimizationSystem/docs/schemas/co2_hydrogenation.schema.json`
  - 定义 metrics、单位、标准化规则、跨字段约束、清洗字段、优化映射。
- `CatalystOptimizationSystem/docs/icl_bank.default.jsonl`
  - 动态 ICL 示例库，每行一个样例，带 `covered_metrics`、`units`、`keywords`、`context`、`output`。
- `CatalystOptimizationSystem/docs/gold_examples.default.jsonl`
  - 小型人工标注集，用于评分。
- `CatalystOptimizationSystem/core/schema_config.py`
  - schema 读取、单位标准化、跨字段约束。
- `CatalystOptimizationSystem/core/icl_selector.py`
  - 动态 ICL 选择。
- `CatalystOptimizationSystem/core/scorer.py`
  - 抽取结果评分。

## CLI 抽取示例

```powershell
python -m CatalystOptimizationSystem.core.extractor `
  --elsevier-key YOUR_ELSEVIER_KEY `
  --keyword "CO2 hydrogenation methanol" `
  --count 20 `
  --schema CatalystOptimizationSystem/docs/schemas/co2_hydrogenation.schema.json `
  --icl-bank CatalystOptimizationSystem/docs/icl_bank.default.jsonl `
  --icl-top-k 3 `
  --domain co2_hydrogenation `
  --llm-key YOUR_LLM_KEY `
  --llm-base https://api.deepseek.com/v1/chat/completions `
  --llm-model deepseek-chat `
  --out extracted_schema.csv
```

如果传入 `--schema` 且不传 `--metrics`，系统会自动使用 schema 中定义的全部指标。

## API 请求新增字段

`POST /extract` 现在支持：

```json
{
  "schema_path": "CatalystOptimizationSystem/docs/schemas/co2_hydrogenation.schema.json",
  "icl_bank_path": "CatalystOptimizationSystem/docs/icl_bank.default.jsonl",
  "icl_top_k": 3,
  "domain": "co2_hydrogenation"
}
```

## 输出 CSV 新增列

每个 metric 会输出：

- `<metric>_value`
- `<metric>_unit`
- `<metric>_evidence`
- `<metric>_norm_value`
- `<metric>_norm_unit`
- `<metric>_violations`
- `<metric>_confidence`

行级新增：

- `schema_id`
- `selected_icl_ids`
- `metric_violations`
- `cross_violations`
- `confidence`

## 评分示例

```powershell
python -m CatalystOptimizationSystem.core.scorer `
  --gold CatalystOptimizationSystem/docs/gold_examples.default.jsonl `
  --pred extracted_schema.csv `
  --schema CatalystOptimizationSystem/docs/schemas/co2_hydrogenation.schema.json `
  --out score_report.json
```

评分脚本会输出：

- presence accuracy
- value accuracy
- unit accuracy
- evidence rate
- per-metric breakdown

## 迁移到其他体系

优先复制并修改：

1. `docs/schemas/co2_hydrogenation.schema.json`
2. `docs/icl_bank.default.jsonl`
3. `docs/gold_examples.default.jsonl`

尽量不要再把字段、单位和约束直接散落到 Python 文件里。

# 本轮输入和验证方式

运行仅在 air-lab，生产 Python 为 `/mnt/data/dyx/miniconda3/envs/drylab-m1m2/bin/python`。项目 `/mnt/data/dyx/drylab-m1m4-runtime`；旧入口 symlink 不变。

## 湿实验条件

WetLabResult.assay_conditions 为对象，必填 condition_id、source_reference、raw_data_sha256、verified_by；实际报告的 host、strain、temperature_c、pH、assay_system 与可选 phase/酶序列/活性酶浓度定义/cofactor_conditions 原样保留。缺项可记录，但不能正式审批。verified_by 是来源审核声明，不替代用户核验原始数据。

同一结果中的测量条件不同时，在 measurement_conditions 以 condition_id 保存真实条件记录，在 measurement_condition_ids 用 `protein_abundance.OC`、`enzyme_activity.DMT` 等 source_field 引用。partition_measurements 的每项也可提供 assay_condition_id。机制拟合的时间序列可用 `metabolites` 引用实验条件。悬空/冲突引用拒绝，不从目标 ProjectConfig 填测量事实。

正式审批仍用既有 CLI/MCP/状态入口，但先做正式 resolver 适用性检查。M3/M4 的目标条件用 canonical_m4_condition_id，与生产路径一致；enzyme sequence、活性酶浓度定义、辅因子和 phase 不符合时提前拒绝。

## F2/F3

已有 analyze-m4/scan-designs 命令和真正 MCP server 接线不变。FiniteDesignPlan 现在必须提供 decision_scope（formal_conditional_mechanism、software_fixture_only 或 exploratory_sensitivity）。正式计划还必须提供 comparison_contract 和明确 varying_design_factors。

comparison_contract 对应 DesignComparisonContract：model_kind/formula_version、metric_definition/metric_unit、normalization、measurement_compartment、assay_mode/expression_mode、input_boundary/input_definition、assay_conditions、动态 interval_h 或 steady_state_observation_reference。input_definition 核对实际初始供料/通量、门控、体积/运输或原稿分泌定义，不仅比较 condition_id。

M4Config 新字段 measurement_compartment 应由实际方案声明。实际 prediction_contract 携带同一实验合同及目标 assay_conditions；未提供的正式比较输入明确阻断。动态 productivity 定义为 net_15_generated_cell_volume_equivalent/interval_h（uM/h），原稳态 yield_abs 为 15 生成通量/8 输入通量（1）。不同单位或模型不能混排。

empirical 默认 discrete inverse ECDF，重复样本保留权重。确需连续插值时显式 distribution=interpolated_empirical 并提供 interpolation_reference、source_reference、reviewed_by。相关参数不能用独立边际 LHS 冒充联合分布。

## air-lab 验收

```bash
export PATH=/mnt/data/dyx/drylab-tools/node-v24.21.0-linux-x64/bin:$PATH
cd /mnt/data/dyx/drylab-m1m4-runtime
/mnt/data/dyx/miniconda3/envs/drylab-m1m2/bin/python -m pytest -q --require-author-reference --junitxml=/absolute/new-results/full-tests.xml
/mnt/data/dyx/miniconda3/envs/drylab-m1m2/bin/python scripts/audit_numeric_mutations.py --output /absolute/new-mutation-output
```

故障输出目录必须是新目录；脚本只改临时副本，并检查生产源码哈希未变。缺 Node 时 UI JS 行为测试失败，不静默 skip；缺原作者输入时必跑 reference job 失败/blocked。XML 数量是软件用例数，核心风险和真实观测数另列。

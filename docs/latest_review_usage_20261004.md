# 本轮新增功能的调用与边界

配置和原始输入仍走既有审核/身份/单位门控。下列命令在 air-lab 的生产环境运行；参数文件由实际数据提供，不附任何为跑通程序捏造的生物参数。

## M3

m3_concentration.phi_source 为 measured（实测 Φ）、lever_rule（S4）或 compare（两者比较）。lever_rule/compare 的参数记录需提供 c_total_scaffold、c_sat_scaffold、c_dense_scaffold，统一 uM 及 entity_basis，并绑定构建和条件。target_enzyme_ratio_parameter 与 design_decision_id 同时声明后，将已审核设计目标传入原 E8/E9；输出只是条件性 rho_star。

## F2 与 F3

```bash
igem-drylab pipeline analyze-m4 prediction.json analysis-plan.json analysis-result.json
igem-drylab pipeline scan-designs finite-design-plan.json design-output
```

analysis-plan 对应 M4AnalysisConfig。仅局部敏感度时提供 local_parameter_names（partition_x8..partition_x15）；无需虚构不确定度。LHS 必须提供 ranges（uniform 的实际上下界或 empirical 的真实样本）、source_reference、parameter_ids、reviewed_by、independence_evidence_reference、standard_deviation_ddof。既有生产 M4 配置 analysis 字段调用同一实现；当前原稿 F2 仅支持原稳态模型，动态轨迹不会偷换成稳态产率。

有限扫描的每个候选提供 config_path、candidate_id、site_ratio（1/2/3/4/6）、design_evidence_reference、synthesized；整个计划明确 objective、objective_reference、decision_id 及可选 minimum_metrics/maximum_metrics。每个实际配置完整重跑 M1–M4，以对应 M2 位点和 M3 分配验收。未覆盖/不通过的候选保留原因，不把一个字段的变化冒充新构建。

## Kp 直接测量与回放

WetLabResult.partition_measurements 逐物种记录 dense/dilute 浓度、原始哈希、标准曲线/回收率/相体积来源。MeasurementMapping 的 source_field 使用 partition_measurements.9、target_stage=m3、target_requirement_name=partition_x9、unit=1；输出 validated 候选仍需人工批准。approved 后重跑 M3/M4；不能将有效比值冒充野生型与融合体均通用。

两种 replay 适配器支持 partition_x8..15 前向变化，保持记录的公式/求解器/环境。改变 Φ、总酶量、支架、ORF/IDR/位点应沿依赖重算，不支持以旧局部酶浓度单字段覆盖。

## 冻结与留出

```bash
igem-drylab pipeline freeze-prediction prediction.json parameters.yaml freeze-plan.json frozen.json
igem-drylab pipeline validate-holdout frozen.json new-dataset-id independent-data.json holdout-report.json
```

freeze-plan 显式提供 freeze_id、construct_id、condition_id、claim_scope 和 calibration_datasets（训练数据 ID 到 wetlab JSON 路径）。claim_scope 仅支持 software_fixture_only、conditional_mechanism、published_reference_reproduction。不覆盖既有 frozen/holdout 文件；无实际留出数据时保存 pending，不输出“已验证”。

真实机制留出须声明 assay_mode、expression_mode、input_boundary，稳态观测还需 steady_state_confirmation_reference；时间序列不得拿稳态值直接验证。报告每个被预测代谢物的原单位换算与 LOD/LOQ、量化点残差和误差指标，不使用独立数据重新拟合。

## MCP / Agent

真正的 stdio server 与 Agent 本地工具注册表共用以下绑定：

- igem.m4.analyze_prediction
- igem.design.scan_scaffolds
- igem.research.freeze_prediction
- igem.research.validate_holdout

继续使用 igem.compute.run_tool 执行实际外部工具，显式声明 input_files/expected_outputs；没有安装/授权/版本解析的预测器仍不能冒充已运行。FreeSASA 完整残基 JSON 与 stdout 摘要分开保存。

实际服务器证据位于 /mnt/data/dyx/glabridin-reproduction/results/latest-review-20261004。科学方程、软件夹具、历史论文复现、真实工具 smoke 与未来生物学预测验收分别报告。

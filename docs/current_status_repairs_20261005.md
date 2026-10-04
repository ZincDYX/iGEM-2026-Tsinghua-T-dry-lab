# 当前状态评审与测试审计修复（2026-10-05）

输入：`iGEM_current_status_review_20261004.md`、`iGEM_test_quality_audit_20261005.csv`。基线 `3de29cd89830c7cdb0775c183e23e073dbee1605`。计算与测试仅在 air-lab。

## 条件传播

- 新增明确来源、原始哈希和核验人的 AssayConditions。每项测量可以引用独立条件记录，悬空或冲突引用拒绝。不从 ProjectConfig 补实测事实。
- 直接测量和机制拟合候选传递实际条件；缺条件的候选可审阅但正式审批阻断。正式审批预检与生产 resolver 共用门控，保留 weak_match、序列和辅因子要求。
- 拟合分组隔离不同测定条件，指纹包含测定条件。原 M5 目标函数、单位及拟合公式未改。
- air-lab：32 passed（conditions-verified.xml）。范围为条件契约与 M5 软件回归，不是生物学验证。

## F2/F3

- `decision_scope` 必填；正式候选需要 prediction 与 M3 context 两层 evidence_ready、conditional_mechanism 作用域和允许的证据等级。demo/author-native 不回流正式 r_target。
- comparison_contract 比较实际模型与公式、指标定义/单位、归一化/区室、测定条件、供料初值/通量、门控、体积、运输边界、观察时间或稳态证据。不同条件标签可保留，实际条件必须可比。
- 约束拼写错误或缺指标明确失败，拒绝记录保留；只在明确可比且合格的候选内排名。不将有限扫描称为全局最优。
- empirical 使用离散逆 CDF，重复值保留权重。连续模式为显式 interpolated_empirical，必须说明依据；独立性声明和原稿差分、1/σ 未改。
- air-lab：设计边界、F2 和独立数值断言合计 27 passed（design-oracles-final.xml）。F3 边界单测明确 mock 上游，不冒称真实湿实验。

## 待完成

定向故障审核、其他审计列出的测试调整和最终全套验证仍在实施。真实校准/留出实验数据、正式运输证据、完整 ER 与稳态稳定性不得因软件测试通过改为完成。

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

## 历史基线的未完成状态（不是最终 HEAD 状态）

未收到本轮对应的真实校准/独立留出数据、核验构建与 OC/DMT-only 10 喂料协议及完整动力学来源。active-subnetwork 仍待接入，不能从 missing 动力学填 0。正式运输证据、完整 ER、稳态稳定性/多根/非平衡扩展仍未完成。此前论文原始输入、矛盾及复现结论保留，不以本轮软件测试替代。

上述段落记录本轮早期基线；截至后续发布 357b0c0，已实现核验缺席活动子网络、正式运输适配、原式局部稳定性及有限多起点。完整 ER/任意非平衡扩展和实际项目真实标定/独立验证仍未完成。最新 review A–C 及科学前端接线见 review_abc_repairs_20261005.md，最终 HEAD/验收以发布记录为准。

## M2 正向证据链暴露的实际缺陷

新增完整资源正例发现，四类资源在循环内都与 model artifact_sha256 比较，而非各自 digest。已修复为逐资源 SHA-256。完整不同字节/哈希的资源现在进入实际 run_m2 并消费指标；任一资源篡改均拒绝。原来只有错序列/篡改负例无法保护这个问题。

air-lab closure-m2-final.xml：35 passed，包含 M2 正反路径、机制拟合到正式 resolver、MCP 审批。文件字节是明确的软件夹具，不是结构有效性或酶活证据。

## 独立数值与实际软件集成

- MU01 初速 0.41776315789473684 uM/h，忽略新 Kp 时约 0.39999996，独立断言拒绝。
- MU02 手给提取口径 4.75 uM，错误相加得到 5，独立断言拒绝。胞内/胞外分别为 2/3 uM。
- MU03 残差 [-1,3,2] uM，RMSE=sqrt(14/3)、MAE=2、bias=4/3；固定 RMSE=0 被拒绝。混合删失、时间/浓度单位与插值另验。
- 故障只在新建隔离副本运行，每次一个，原生产文件哈希未变。correct 通过；MU01/MU02 各 1 个数值断言失败，MU03 2 个数值断言失败；没有导入/setup 错误充当检错。仅为指定风险，不算全系统变异分数。
- 实际 F3 两次 M1–M4 重算，无 mock 管线，检查独立 E2 二次方程根、M2 几何标识/位点、参数来源 ID、M3 守恒和 M4 原竞争初速。探索性比例不回流正式 r_target。
- 旧快照、租约/恢复、插件隔离、12类运输交互与原稿公式测试保留。测试重命名/表格替换映射见 `test_quality_changes_20261005.md`。风险元数据见 `test_risk_manifest.yaml`；未逐项分类旧测试如实标 regression。
- air-lab 全套：440 passed，50.13 s，0 failed/error/skipped；`--require-author-reference` 强制原作者输入存在。作者端点通过不是整篇论文验证。最终字节一致发布后还会重跑发布验收。
- 不新增安装，使用已有 Node 24.21.0。本轮真正 stdio MCP 实际运行 FreeSASA 且生产 parser 读取非空输出；五个工具部署根实际共 11,079,683,786 bytes，低于 15,000,000,000。它是两链 PDB 的工具夹具，不是当前融合体实验验证。受许可工具未新增任务。

## 模块提交

- ff7e936：M5 实测条件传播及正式审批门控。
- a329688：F2 经验抽样与 F3 准入/比较合同。
- d8c14a4：M2 各资源独立哈希实际缺陷。
- ee7b7fa：M5 拟合/审批到正式 resolver 全链路。
- ea51f83：F3 实际 M1–M4 数值产物与身份。
- 662ec92：独立数值 oracle、隔离故障审核、风险清单及测试映射。

均逐次 commit 并 push 至 feature/m1-m4-markdown-contract。最终交付元数据的提交和哈希由交付校验 JSON 记录，避免报告嵌入自身哈希。

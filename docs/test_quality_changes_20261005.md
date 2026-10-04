# 测试风险与旧项映射

本轮使用用户提供的 354 函数静态审计清单定位风险，不按断言数量计算质量分数，也不把软件用例数称为独立科学证据。核心风险由根目录 test_risk_manifest.yaml 显式记录，JUnit properties 携带风险、oracle、作用域、单位与容差。未逐项分类的旧测试保持 regression 标记，不假装全部已完成独立 oracle 审核。

| 原风险或旧测试 | 新测试/处理 | 证据范围 |
|---|---|---|
| Kp replay 名称声称全部底物、实际 Φ=0/15=0 | 改名 homogeneous control，比较实际活跃 13；新增 independent_numeric_oracles 的 MU01 与 kcat/Km/两相 activity 四类活跃初速 | 两相原公式的软件解析夹具 |
| 同 helper 自生成观测再断言零残差 | 改名 observation_roundtrip；MU02 手给浓度和不同体积，各区室分别核验 | 观测口径，不是实验拟合 |
| holdout 只检查零误差 | 保留冻结、重标、篡改；MU03 独立非零正负残差、混合删失、min/h、mM/uM、非原网格点 | 软件统计与身份，不是实际留出验证 |
| direct/fit 只检查候选状态 | experimental_condition_chain、final_closure、pre_data_contract_closure、review_m4_m5 传条件到批准/写盘/正式 resolver；缺条件与序列变化拒绝 | 条件契约 |
| F3 全 mock 包装检查 | 原包装测试保留；design_decision_contract 准入/可比性正负例；fresh_design_integration 实际完整两次 M1–M4，用独立 E2 根和初速核验 | 边界 mock 与实际软件集成分开 |
| empirical 无原子/重复权重保护 | [1,1,3] 固定分位点、300 LHS 的 200/100 权重、种子与显式插值模式 | 分布语义 |
| F2 实际求解却是零酶活/零产率 | 保留零通路；新增活跃非零产率，以独立标量质量平衡及原 1%/.5%/.25% 差分核验 | 无生物参数的算法夹具 |
| M3 守恒只看自报 residual | 独立有限位点二次方程根；从 dense/free/bound/dilute 重算总量 | E1–E6 原公式 |
| M4 通量 key/yield 范围/自报 residual | 独立逐物种计量平衡、竞争 OC 两底物手算通量、Phi 加权及产物去向 | 竞争 MM 与物理守恒 |
| real_metrics 原项实际上 M1 阻断 | 准确改名、非空候选 ID/数量；新增资源正例进入实际 run_m2，四资源分别篡改拒绝，并发现/修复错误共用模型哈希 | 文件字节证据契约，不是结构有效性 |
| M1 passes 名称而实际 blocked | 改名 unbound external declarations；保留 new_review_m1 中真实字节绑定正例 | 不放宽原始证据门控 |
| M1 特征、M2 Kabsch 与错映射 | 原独立测试保留；M1 明示 10 种等频、GS=2/10、FWY=3/10、log₂10 | 独立几何/整数计数 |
| 单 MM 神秘端点常数 | 写明 S+ln S=-9、1-W(exp(-9))，三求解器与显示网格/开关边界保留 | 单反应夹具，不改项目竞争网络 |
| MCP 多工具长串粗断言 | 公开协议表，SASA 手算 136/150、docking 差 .7、零酶活明确预期；数值内核与实际 stdio 测试独立保留 | 接口与 parser，非工具执行/生物验证 |
| QA 页面固定 CSS、函数名、180ms | 删除这类非公共需求快照；保留公共入口及 HTTP；实际执行 JS 渲染恶意文本，使用拒绝 HTML sink 的严格 DOM double | 非完整浏览器安全审计 |
| no network 没有关闭网络 | 明确 socket connect/create_connection 拦截；实际软件夹具路由测试与独立定量链路分列 | Python 进程离线边界，不冒称子进程防火墙 |
| legacy registry 只有 DOI/缺项 | 准确改名 legacy availability；完整正式审批另走 typed requirement | 不提升 name-only inspection |
| 作者端点与原文 parser 混称论文复现 | parser 函数名原本已是 source_table，明确仅解析；必跑 --require-author-reference 下原始输入缺失失败/blocked | 作者原生端点回归，非整篇论文复现 |
| pipeline_skeleton 与 integration | 前者改名 artifact manifest smoke；后者保留不同的离线/QC 路由；不为了压例数删除不同边界 | smoke 与集成 |

没有删除 12 种不等体积运输交互、快照损坏、并发/租约、恢复、插件依赖隔离、M5 共同尺度/平坦/边界/分块、单位/LOD/LOQ/来源/作用域等独有负例。原 QA 快照函数的公共入口风险由新入口测试承接，文本安全由独立 JS 行为测试承接。原 MCP 长函数拆为表格行，不是独立科学风险数增长。

## 本轮不能据此宣称完成的事项

- 审计清单不是逐函数变异验证。本轮只定向验证 MU01–MU03，不输出整体变异分数。
- 完整论文 S5/S18、组学/MD/湿实验及真实项目预测沿用既有复现报告，不因作者端点通过改为完成。
- 未收到真实、条件匹配、冻结后独立采样的校准/留出数据，真实验证 pending。
- 实际 OC/DMT-only 10 喂料协议缺少本轮提供的核验构建/原始条件与完整动力学数据。正式 active-subnetwork 版本仍待接入，不从 missing 动力学自动填 0；ER、正式运输与稳态稳定性保持未完成。

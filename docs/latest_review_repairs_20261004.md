# 最新评审修复记录（2026-10-04）

依据用户提供的 `iGEM_latest_review_and_best_model_20261004.md`，起点 `455c305`。本轮软件夹具只检验算法，不能充作实验输入、真实工具执行或生物学预测验证。所有数值测试仅在 air-lab 运行；作者原文件、公式及科学参数不改。

## 1. M5 数值尺度和旧比例拟合

- 机制拟合使用由实际观测与已计算预测共同确定的单个残差尺度；全部残差除以同一个常数，不引入物种权重、噪声方差或新生物参数。原量纲 residual/RMSE/SSE 保留，另存尺度来源、缩放目标和优化状态。
- 从初值和较优剖面点重启；输出 estimated 前比较已计算剖面，明显较差则 solver_failed，不生成参数候选。有限剖面不是全局唯一性证明。
- 比例拟合改为有界解析未加权最小二乘，并明确是描述性比例；无信息、边界不给 best_fit/CI。默认取消 IID bootstrap；只有明确独立样本或真实重复块才重采样。
- air-lab 定向验证：20 passed，XML `results/latest-review-20261004/m5.xml`。覆盖共同缩放 1/1e-3/1e-6/1e-12、非单调局部停滞、全零、边界和重采样声明。旧测试的区间请求改为显式独立软件样本，未绕过正式数据约束。

## 待实施 / 待真实证据

## 7. 实际工具执行与输出完整性

- 外部 runner 增加实际执行文件、明确输入文件、输出文件及 stdout/stderr 哈希；超时/执行失败保留 manifest，不抹去失败链。mock/dry_run 不赋予真实执行身份；哈希不是不可伪造的执行证明。
- FreeSASA 输出绑定真实 PDB、包版本、显式默认 Parameters、分类器/结构选项及配置哈希；不改变此前默认 SASA 方法。
- 实际 stdio MCP 重跑已部署 FreeSASA 并调用生产 parse_freesasa_json。发现并修复 stdout 摘要覆盖残基 JSON 的实际问题；旧失败作业目录保留，最终作业为 actual-freesasa-mcp-final。
- air-lab：17 passed（tool-records.xml）加真实工具/解析验收。重新审计五个部署根含历史兼容环境，共 11,079,683,786 字节 < 15,000,000,000；无新安装。
- 工具输出格式依据 [FreeSASA 官方 Python 文档](https://freesasa.github.io/python/classes.html)。这只是工具 smoke，不是实际融合 ORF 的 M2 生物学验证。SignalP/DeepTMHMM/TANGO/PASTA 本轮未执行，也未解除自动解析/许可缺口。

## 全套回归发现的附加修复

首次全套 394 passed / 1 failed：M5 新诊断中的 numpy.bool 不能写入 JSON；已显式转换 Python bool，30 项 M5/生产 M4→M5 回归通过，XML m5-serialization.xml。保留 first 日志/XML，不删除失败记录或放宽验收。

## 6. 标定—冻结—留出

- 新增 research_validation 和 CLI/MCP：冻结真实求解器设置、完整 kernel_inputs、源码哈希、环境版本、参数文件哈希、训练数据清单/哈希/观测身份和结论范围。
- 留出数据不重拟合；拒绝训练 ID/同文件改名/同记录重新排版、冻结内容变更、构建条件错配与时间范围外数据；原单位/LOD/LOQ 规则保留。
- 报告 quantified 残差/RMSE/MAE/bias，无预设“通过阈值”；无观测时间戳时明确前瞻性未确认。迭代产生新 freeze，不覆盖旧预测。
- air-lab：24 passed，XML validation.xml。仅软件流程验证，没有新增实际留出实验，因此真实预测验收仍 pending。

## 5. 实验模式与竞争/回收报告

- 显式 assay_mode、expression_mode、投喂身份/边界/时间、稳态平台证据；正式缺项阻断，当前仅支持已实现的零时批次或原稳态连续输入，不假装支持任意脉冲/生长。
- 报告严格增加 q10→11=FR3/(FR3+FR6)、q9→13=FR5/(FR2+FR5)。动态用同区间自适应累计通量，稳态用原通量；分母零为 None，不补 0。指标不是单分子通道化概率。
- 分列胞内/外 13/15、净新生 15、总流出/回流/净外排和剩余初始非产物池。15 回收与 8–14 中间体流出不混成同一损失，13 不当死端。
- 确认遗传缺席只记录身份依据；当前十反应版本不以缺失动力学填零，声明缺席则阻断并要求明确子网络版本。该功能仍是边界能力不足，不宣称已完整支持无 PTR/PT 的功能实验。
- air-lab：17 passed，XML assay.xml，验证分支、零分母、竞争反应及正式边界。未改速率方程、作者参数或项目生物数据。

## 4. F2/F3 和有限设计决策

- 独立 design_analysis 模块通过生产 M4 配置、CLI 和真实 stdio MCP 接入。局部严格使用原稿 1% 前向差分，附 0.5%/0.25% 步长诊断；Spearman 单列，绝不称偏导。
- LHS 默认原稿 256 样本；每个变量必须声明经审核的真实范围或经验样本及来源，联合独立性依据和 σ 的 ddof 必须显式提供，不从 SEM 推范围。相关参数的联合抽样当前不支持，不能用独立抽样替代。
- robustness 严格为 1/σ，零方差报告非有限倒数而不是虚假确定值；失败样本保留，部分有效样本的统计量标作条件统计。没有噪声模型，不给伪置信区间。
- IDR 链使用全部原稿系数/物种描述子/适用域来源，在声明的映射点重新求原方程与差分，不将实测点导数乘另一个映射点 Kp。缺映射不生成谱。
- F3 对 {1,2,3,4,6} 中用户提供的真实配置逐次重跑 M1→M2→M3→M4，核对该候选 M2 位点数，不复用原 3:1 几何。保留待合成标志、配置哈希、招募/产物/失败。无成本模型则明确成本未计算，不发明表达负担公式。
- 有限外层决策只用显式目标及约束选择现有可行候选，输出 decision_id 与 r_target，供审核回流 E8/E9；不是全球最优，也不代表湿实验验证。
- air-lab：26 passed，包含公式解析夹具、失败/常数秩相关、原稿稳态求解、映射点、逐项目重算及真实 stdio MCP，XML analysis.xml。
- 实现方法依据：[SciPy LatinHypercube](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.qmc.LatinHypercube.html)、[Spearman](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html)。实际发布环境及随机种子另行锁定，不把当前网页版本当服务器版本。

## 3. 直接 Kp 与依赖失效

- 实测分配记录要求 dense/dilute 浓度及原数据哈希、校准、回收率、相体积来源；按明确物种映射形成未批准 Kp 候选，审核后才入库，不用 logP 或胞外比例代替。
- 两种版本化回放增加 partition_x8..15 的前向扰动，重新求解相内底物；Φ 和酶分配仍明确拒绝单字段回放，须回到 M3 重算。此修改不宣称自动反演 Kp9 已经过真实数据验证。
- ProjectState 参数审核/构建变更使依赖阶段失效并保留旧产物与原因；流水线重新执行时逐阶段重算，不复用旧局部酶浓度。
- air-lab 24 passed，XML dependencies.xml；原参数审核测试另纳入最终全套验证。

## 2. M3 S4 与条件性目标回流

- Config/统一 requirements/正式 run_m3 接通 measured、lever_rule、compare；两种相图浓度缺任一项阻断，单位走同一 uM 换算，组装基准与 M2 一致，不插入 24 倍系数。
- 正式 S4 要求匹配融合构建、真实相图来源及 entity_basis；保留 measured Φ 与 S4 Φ 差值，不替换实测值或凭差值宣称实验验证。
- 目标酶比需要独立审核参数记录及 design_decision_id，传入 E8/E9，保存条件性 rho_star；不是无收敛的 M3/M4 循环，也不是把位点比当酶比。
- S4 两相区合法性检查保留原方程，不在相图输入非法时外推。
- air-lab：18 passed，覆盖三条流水线路径、目标/缺项、原 M3/MCP 和候选隔离；XML m3.xml。尚无新增真实融合相图，不能宣称项目闭环验证完成。

后续逐模块记录实际实现及验收；未记录完成的模块仍属待办。实测相图、真实构建/膜侧、工具授权及原始作业、独立留出结果不足时不补造数据，不提前宣称闭环验证完成。

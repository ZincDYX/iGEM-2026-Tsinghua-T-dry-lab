# 未完成项的可实施部分（2026-10-05）

基线 `6f0b370ca404d3ea234b185ae291981d194d1d53`。仅在 air-lab 执行模型和测试。没有新增生物参数或更改原 M3/M4 方程。

## 原式稳态局部稳定性与有限多起点搜索

共享原 RHS 求值器，解析求导每个相、同酶完整竞争分母及原 `ksec*C_dilute`，报告 Jacobian（1/h）、完整复特征值、谱横坐标和数值判别阈值。有效根自动报告局部线性化；零/近零特征值标记 inconclusive，不宣称渐近稳定。失败或 blocked 不给稳定性结果。

`igem.m4.analyze_steady_state` 已接入官方 MCP server、工具目录和 workflow allowlist。输入显式提供 `steady_state_input`、`initial_guesses_um`、`root_merge_atol_um`、`root_merge_rtol`、`eigenvalue_tolerance_per_h`。保留每个起点、失败原因、根归属和各根结果。有限起点不能证明所有根已找到、全局唯一性或无根；原根发布门槛未放宽。

软件验收：非零竞争两相 Jacobian 独立中心差分，单纯分泌的手算根/对角谱，稳定/不稳定/中性分类，实际自由池根族及 blocked 记录，真正跨进程 stdio MCP 多起点作业。air-lab `stability-transport-02.xml` 共 53 项通过（还包含原稳态和运输回归），其中新增稳态分析 8 个运行例。不以这些夹具代替实验验证。

算法与实现参考：[SciPy least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)、[SciPy eigvals](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.eigvals.html)。具体 Jacobian 来自原稿竞争公式的求导，而非换用另一种动力学。

## 正式运输证据适配

新增 `transport_evidence`，以固定 parameter_id 绑定一个已实现的可逆一阶运输模型：总速率、胞内有效反应体积、胞外培养基体积和 8–15 每个物种的比值。全部通过正式 resolver 的来源、审批、构建、条件、单位和物种检查；原始来源 SHA-256、区室和定义也必需。volume 新增显式 L/mL/uL 转换，不把体积当成浓度。

速率定义必须为 `forward_plus_reverse_first_order_coefficients`，归一化为 `cell_volume_equivalent_flux`；比值必须为 `C_outside/C_accessible_inside_at_zero_net_flux`，access 明确 `cell_average` 或 `dilute_phase`。没有同定义的测量就拒绝，而非把分泌常数或胞外/胞内的任意比值代入。保留现有 k+=K*k/(1+K)、k-=k/(1+K) 和 Ve/Vi 物质量守恒；这不是新运输公式。

M4 正式 pipeline 已接入，旧字符串 source_reference 不替代证据。配置数字与已审核记录不一致时阻断；成功输出保留全部绑定记录和 parameter_id。air-lab `transport-pipeline-03.xml`：16 passed，包含真正正式路径消费、非零运输初速、不同 access、不等体积守恒及缺来源/错单位/错方向/错区室/错条件负例。所有输入仍为标记的软件夹具，没有冒充项目运输实测。

稳态 pipeline 输出也接入局部稳定性，F2 分析不会覆盖这一记录。

## 经核验缺席的活动子网络

新增明确版本 `galatea-oc-dmt-verified-absence-v1-2026-10-05`，仅支持 physical 动态、OC/DMT-only、10 号底物在 t=0 的 batch 功能实验，M3 必须 finite_site。配置 `network_variant=oc_dmt_verified_absence` 并声明 PTR/PT 缺席和 `absence_evidence`（artifact、sha256、reviewed_by）。

artifact 为真实审核 JSON：construct_id、condition_id、host、strain、source_reference、verification_method、reviewed_by，以及 `confirmed_absent_enzymes={"PTR":"genetic_and_background_activity_absent","PT":"genetic_and_background_activity_absent"}`。构建没有外源基因不自动证明宿主背景无对应活性；必须由核验记录说明。程序核对字节哈希/身份/审批声明，不能自动证明该记录的生物真实性。

移除 R1/R2/R8/R9 和 PTR/PT 丰度、分配、动力学及活性需求，不给缺失动力学填零。保留 R3/R4/R5/R6/R7/R10 与 OC/DMT 全竞争分母、8–15 相分配、浓淡相活性、产物、运输、单位及观测。未选反应通量的显式 0 是网络拓扑输出，不是伪造参数。M3 背景分配不再计算不存在的酶；M4 核对 M3 的版本/缺席证据；支持同版本冻结内核与参数回放，缺当前活跃反应输入仍阻断。13 在这个 PT 缺席版本无 13→14 活动反应，输出不再沿用完整网络的“非死端”标签。

air-lab `active-contracts-02.xml`：33 passed（含数据契约/稳定性/运输回归），新增活动子网络 6 个例子：真实 M3/M4、独立 R3/R6 初速、与完整网络结构性零酶对照、原始守恒、非零 15、活跃参数回放、错版本/缺反应/篡改/错构建/仅构建缺席但背景未证实的拒绝。旧十反应版本未被改写为子网络；未收到本项目实际缺席证据或实验输入，不宣称项目复现完成。

## 科学边界（项目数据和模型假设）

ER 腔/膜/胞质的完整机制未有本项目确定方程和交换/活性证据，不能自动编造“完整 ER 模型”。未获得真实独立数据，不宣称项目标定或验证完成。工具许可证、下载凭证与真实 ORF 仍须对应具体工具核验。

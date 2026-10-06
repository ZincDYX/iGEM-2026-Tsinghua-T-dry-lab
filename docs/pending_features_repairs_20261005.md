# 未完成项的可实施部分（2026-10-05）

基线 `6f0b370ca404d3ea234b185ae291981d194d1d53`。仅在 validation host 执行模型和测试。没有新增生物参数或更改原 M3/M4 方程。

## 原式稳态局部稳定性与有限多起点搜索

共享原 RHS 求值器，解析求导每个相、同酶完整竞争分母及原 `ksec*C_dilute`，报告 Jacobian（1/h）、完整复特征值、谱横坐标和数值判别阈值。有效根自动报告局部线性化；零/近零特征值标记 inconclusive，不宣称渐近稳定。失败或 blocked 不给稳定性结果。

`igem.m4.analyze_steady_state` 已接入官方 MCP server、工具目录和 workflow allowlist。输入显式提供 `steady_state_input`、`initial_guesses_um`、`root_merge_atol_um`、`root_merge_rtol`、`eigenvalue_tolerance_per_h`。保留每个起点、失败原因、根归属和各根结果。有限起点不能证明所有根已找到、全局唯一性或无根；原根发布门槛未放宽。

软件验收：非零竞争两相 Jacobian 独立中心差分，单纯分泌的手算根/对角谱，稳定/不稳定/中性分类，实际自由池根族及 blocked 记录，真正跨进程 stdio MCP 多起点作业。validation host `stability-transport-02.xml` 共 53 项通过（还包含原稳态和运输回归），其中新增稳态分析 8 个运行例。不以这些夹具代替实验验证。

算法与实现参考：[SciPy least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)、[SciPy eigvals](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.eigvals.html)。具体 Jacobian 来自原稿竞争公式的求导，而非换用另一种动力学。

## 正式运输证据适配

新增 `transport_evidence`，以固定 parameter_id 绑定一个已实现的可逆一阶运输模型：总速率、胞内有效反应体积、胞外培养基体积和 8–15 每个物种的比值。全部通过正式 resolver 的来源、审批、构建、条件、单位和物种检查；原始来源 SHA-256、区室和定义也必需。volume 新增显式 L/mL/uL 转换，不把体积当成浓度。

速率定义必须为 `forward_plus_reverse_first_order_coefficients`，归一化为 `cell_volume_equivalent_flux`；比值必须为 `C_outside/C_accessible_inside_at_zero_net_flux`，access 明确 `cell_average` 或 `dilute_phase`。没有同定义的测量就拒绝，而非把分泌常数或胞外/胞内的任意比值代入。保留现有 k+=K*k/(1+K)、k-=k/(1+K) 和 Ve/Vi 物质量守恒；这不是新运输公式。

M4 正式 pipeline 已接入，旧字符串 source_reference 不替代证据。配置数字与已审核记录不一致时阻断；成功输出保留全部绑定记录和 parameter_id。validation host `transport-pipeline-03.xml`：16 passed，包含真正正式路径消费、非零运输初速、不同 access、不等体积守恒及缺来源/错单位/错方向/错区室/错条件负例。所有输入仍为标记的软件夹具，没有冒充项目运输实测。

体积/各物种比值也已进入统一 M4 requirement catalog，可通过同一正式审批路径按 volume/dimensionless 与物种检查；不只在求解器前临时放行。正向实际 pipeline 另核对这一目录，重复来源计数未增加。

稳态 pipeline 输出也接入局部稳定性，F2 分析不会覆盖这一记录。

## 经核验缺席的活动子网络

新增明确版本 `galatea-oc-dmt-verified-absence-v1-2026-10-05`，仅支持 physical 动态、OC/DMT-only、10 号底物在 t=0 的 batch 功能实验，M3 必须 finite_site。配置 `network_variant=oc_dmt_verified_absence` 并声明 PTR/PT 缺席和 `absence_evidence`（artifact、sha256、reviewed_by）。

artifact 为真实审核 JSON：construct_id、condition_id、host、strain、source_reference、verification_method、reviewed_by，以及 `confirmed_absent_enzymes={"PTR":"genetic_and_background_activity_absent","PT":"genetic_and_background_activity_absent"}`。构建没有外源基因不自动证明宿主背景无对应活性；必须由核验记录说明。程序核对字节哈希/身份/审批声明，不能自动证明该记录的生物真实性。

移除 R1/R2/R8/R9 和 PTR/PT 丰度、分配、动力学及活性需求，不给缺失动力学填零。保留 R3/R4/R5/R6/R7/R10 与 OC/DMT 全竞争分母、8–15 相分配、浓淡相活性、产物、运输、单位及观测。未选反应通量的显式 0 是网络拓扑输出，不是伪造参数。M3 背景分配不再计算不存在的酶；M4 核对 M3 的版本/缺席证据；支持同版本冻结内核与参数回放，缺当前活跃反应输入仍阻断。13 在这个 PT 缺席版本无 13→14 活动反应，输出不再沿用完整网络的“非死端”标签。

validation host `active-contracts-02.xml`：33 passed（含数据契约/稳定性/运输回归），新增活动子网络 6 个例子：真实 M3/M4、独立 R3/R6 初速、与完整网络结构性零酶对照、原始守恒、非零 15、活跃参数回放、错版本/缺反应/篡改/错构建/仅构建缺席但背景未证实的拒绝。旧十反应版本未被改写为子网络；未收到本项目实际缺席证据或实验输入，不宣称项目复现完成。

## 科学边界（项目数据和模型假设）

ER 腔/膜/胞质的完整机制未有本项目确定方程和交换/活性证据，不能自动编造“完整 ER 模型”。未获得真实独立数据，不宣称项目标定或验证完成。工具许可证、下载凭证与真实 ORF 仍须对应具体工具核验。

## 外部工具核查（本轮没有成功的新许可预测作业）

- [SignalP 6.0i fast 的官方学术下载](https://services.healthtech.dtu.dk/cgi-bin/sw_request?packageversion=6.0i&platform=fast&software=signalp&version=6.0) 要求机构邮箱/信息和接受学术许可；没有代机构填写、签署或下载安装，也未将许可程序打入公开 bundle。
- [DeepTMHMM 官方许可说明](https://services.healthtech.dtu.dk/services/DeepTMHMM-1.0/) 区分线上服务与自建部署，不能一律说需要付费。[BioLib 官方 Python 文档](https://biolib.com/docs/using-applications/python/) 提供登录和 API token 路线；服务器 pybiolib 已安装，未配置 BIOLIB_TOKEN（不等于已证明所有身份入口都不可用）。官方 CLI 帮助可用；对 DTU/DeepTMHMM 的帮助请求直连 40 秒、按用户 proxy 路线 45 秒均超时，没有成功预测或版本专用原始输出。原因尚不能确定，不能误称已经证实是许可证错误。
- [TANGO 官方入口](https://tango.crg.eu/) 提供学术/商业许可，需用户已有的合法包/授权；没有接受机构条款或下载非官方二进制。[PASTA 2 原站](https://protein.bio.unipd.it/pasta2/) 本轮访问超时，不能确认当前部署/API可用。

不以公共夹具、旧 smoke 或手工虚构格式声称上述新作业成功；现有按实际字节人工审核路径和未解析阻断保留。本轮无需新增安装。

## 还需提供的真实输入

1. 对应当前构建和宿主背景的 PTR/PT 缺席审核记录及原始依据；10 喂料剂量、时刻、测量区室、培养/胞内有效体积和协议。
2. 对应构建/条件的招募、Kp、酶量/活性、运输及时间序列原始来源，以及未用于标定的独立批次。
3. 若要量化 ER：确认区室/膜侧、相应方程和需要估计的交换/定位/活性参数，再提供其来源。仅有 ER 定位意图不能产生定量模型。
4. 已获得的 SignalP/TANGO 等许可包及服务器路径，或通过服务器安全配置 BioLib 身份；不要在聊天发送密钥。

## 提交与验证定位

`a19ecf4`：原式局部稳定性与多起点 MCP；`977b19f`：正式运输证据及实际 pipeline；`5890f91`：核验缺席活动子网络。均分别 commit/push，后续目录接线与发布证据提交在最终交付 JSON 记录。最终 validation host 全套结果、源码/bundle 逐字节一致性、故障审核和部署大小以同轮交付 JSON/证据包为准，旧评审记录保持历史版本，不覆盖原论文输入。

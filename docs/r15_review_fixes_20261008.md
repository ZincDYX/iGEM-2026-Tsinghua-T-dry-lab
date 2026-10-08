# r15：真实 M1/M2 检查、修复与未完成项

日期：2026-10-08。运行冻结提交：`b62073df5f47dbbe4f5fd4af504b9e35e432c497`。后续仅记录报告的提交不改变运行源码。

## 结论与范围

S01 多模型混算和 S02 不完整 SASA 映射误判已修复。真实 stdio MCP、IUPred、SEG、JPred、ColabFold、FreeSASA 都产生了相应实际输出；安装检测与真实运行分开记录。原生 Windows EXE 通过可选 HTTPS API 在服务器运行了 IUPred 和 ColabFold，并验证了关闭/重启后的持久化结果，没有替换原生桥接或上游工具。

**这不是完整 M1/M2 生物学通过报告，也不是九项界面要求全部完成报告。** 11 个 M1 对象的正式结论均为 blocked；25 个 M2 模型是完整序列预测，不是口袋、酶活、结合或自组装通过证据。完整 Q1–Q4 自动流程、多文档管理等仍未完成，见独立验收表。

科学数值计算、作者回归、真实外部预测及最后的冻结源码重新解析全部在服务器执行。本机只做源码/软件测试、打包、展示、文件比较及资源测量；表格直接整理服务器已有数值，没有在本机重算科学指标。CSV 使用电子表格技能的 artifact-tool 生成并回读检查，空单元格对应 unavailable/null，不代表 0。

## 输入可信度与所用构建体

用户 ZIP 缺失中央目录，不能正常整包解压；根据前部文件头恢复后，原 FILE_INVENTORY 的 125 项中 123 项与原声明字节/摘要一致。旧嵌套 SOURCE_ARCHIVE 损坏、包内 current_status_review.md 未恢复；使用用户另外提供的 review。主分析输入已独立核验，不把两个失败项自动导入。原 ZIP 未改动。

| 主构建体 | 长度 | 分析身份 |
|---|---:|---|
| OC_deltaN_SH3_cytosolic | 533 aa | ΔN OC 510 aa + 12-aa linker + 11-aa SH3 ligand |
| DMT_PDZ_C_terminal | 380 aa | DMT 361 aa + 12-aa linker + 7-aa C-terminal PDZ ligand |
| FUSn_SH3x3_PDZ_FTH1_cytosolic | 796 aa | 实际 FUSn→SH3×3→PDZ→FTH1 顺序及五个骨架 linker |

3 条主 CDS 完整翻译和模块边界重拼一致。这是设计序列核验，不是湿实验测序确认。ER/mScarlet 辅助构建体未混入主分析。M1 另检查 FUSn_1_214 和七条实际 12-aa linker，共 11 个对象。M2 还使用 OC WT 541 aa、ΔN OC 510 aa、DMT 361 aa 的未融合基线；OC WT→ΔN 的变化不能归因于融合。

## 科学修复与真实工具

| 条目 | 修复和实际证据 | 仍不能得出的结论 |
|---|---|---|
| S01 | PDB 多模型必须显式选择；altloc 必须明确选择；保留 model、auth chain、有符号编号和 insertion code；mmCIF 另保留 label 身份。真实 2PDZ 的 15 个模型分别解析，与 Biopython 独立解析比对 | 不能合并 NMR 模型后报告单一几何值；模板不是融合装配 |
| S02 | 完整且一一对应的 SASA 选择/映射；缺残基、重复或非有限记录不产生 ratio/pass；真实 0 与缺失区分，参考分母 0 为 undefined。15 个 2PDZ 模型分别执行 FreeSASA；另与独立 PDBIO/FreeSASA 单模型结果比对 | 本项目未提供完整且经审核的酶口袋，故没有正式 pocket retention |
| ColabFold 解析 | 实际批处理暴露了旧解析器跨 candidate/rank 选文件以及 pLDDT 列表漏算的问题；现在按 candidate、rank、model、seed 精确配对 PDB/score JSON，校验有限 pLDDT/PAE、完整序列及长度 | 不把全矩阵 PAE 平均数当 interdomain PAE，不把 pTM 当 ipTM |
| M1 证据绑定 | IUPred/SEG 实际运行记录绑定完整序列和原文件；JPred 的 `.jnet` 无序列时显式绑定实际 `.seq` 文件，不截短/补齐；运行来源仍由后端记录，不宣称密码学执行证明 | 自动记录不是湿实验验证；合法授权与完整必要输出仍需提供 |
| S03（部分） | 共用现有私有工具 adapter 和 SQLite workflow ledger；IUPred/SEG/ColabFold 新诊断节点保存任务与结果，Tools 页可准备运行、检查真实输出并打开文件；不是另一套全局执行器 | 尚未自动完成所有 M1 预测→判定、M2 Q1–Q4→正式证据发布 |

原 Kabsch、严格 heavy-atom `distance < cutoff`、SASA(fusion pocket)/SASA(reference pocket) 和 0.70 边界没有修改。256×1024 的精确距离分块替代全 N×M 临时矩阵；不是近似算法。完整方法边界见 [scientific_method_diff.md](scientific_method_diff.md)。

与既有科学核心提交 `5a5e19a308f20d4b1f9863c7a732bdb26b03da1f` 比较，full_network.py、m3_equilibrium.py、m4_steady_state.py、pipeline/stages.py、pipeline/models.py、scoring/m2_structure.py 的提交字节不变。pipeline/config.py 只增加工具 verified_version 元数据，未更改方程或参数。计算目录部分文件与冻结档仅换行字节不同；最终 M1/M2 又由冻结源码的真实 stdio MCP 重新解析，不能用运行目录名称冒充冻结身份。

### M1 真实结果

- Biopython ProtParam 1.88、IUPred 0.1.2、真实 NCBI SEG CLI：11 个完整对象执行并解析。
- IUPred 上游固定源提交为 655d42c28c571cc42e12f93588bab4dd727a48cf，使用其真实数值实现和实际运行记录；上游 CC-BY-NC-ND 许可需遵守非商业等限制，未把上游改写代码打进 Windows 包。不是伪造 predictor，也不是零分填充。
- JPred4 / jpredapi 1.5.6：FUSn_1_214 真实 job jp_z1QBBuy 完成，214 个位置可解析；12-aa linker 原样提交被实际服务以低于 20 residues 拒绝。客户端退出码虽为 0，但没有有效 job/output，**不算成功**。
- FUSn_1_214 的 IUPred mean = 0.804039887850467、disordered fraction = 1、longest disordered run = 214 residues；JPred ss_fraction = 0、longest SS run = 0。它们是预测，不是 LLPS 实验结论。
- 三个 full fusion 和八个 part 的正式 verdict 均为 blocked；缺 SignalP、DeepTMHMM、TANGO/PASTA 对应的完整融合输出。七条短 linker 还缺适用且有效的 SS 预测。
- 未提供禁止限制性位点/功能 motif 列表，故基础输出中的空 motif 数组不表示“已筛查无禁忌”。charge_blockiness、multivalency_density 和 rank_score 的算法/归一化/权重未经确认，继续为 null；没有自行排序。

### M2 真实结果

ColabFold 1.6.2，AF2-PTM，公开 MMseqs2 MSA，5 models、3 recycles、1 seed、random seed 0，使用已有权重。五条未截短序列产生 25 个 PDB，每个模型和对应 confidence 文件精确配对，独立 PDB 序列检查全长一致。未加入 relaxed、对接、MD 或未声明的生物学条件。

| 批处理 rank 1 | 长度 aa | mean pLDDT（0–100，显示四舍五入） | pTM（0–1） |
|---|---:|---:|---:|
| OC WT design reference | 541 | 92.07 | 0.90 |
| OC ΔN unfused | 510 | 95.39 | 0.94 |
| DMT unfused | 361 | 92.07 | 0.92 |
| OC ΔN SH3 fusion | 533 | 92.84 | 0.92 |
| DMT PDZ fusion | 380 | 88.53 | 0.87 |

完整精度在 m2_decisions.csv 和原 JSON 中保存。2PDZ 15 个单模型的 FreeSASA 结果只用于真实工具和格式检验。2FHA assembly 的 24 个蛋白 label chain/auth 身份单独核验；模板与本项目 FTH1 存在已知序列差异，不默认为同一融合装配。

OC 的 I293/T295→ΔN I262/T264 及 DMT N303 是功能锚点，**不是完整口袋**。pocket_definition.json 标记 needs_review；core RMSD、pocket SASA retention、interdomain PAE、docking affinity、体积/共占据/动态参数不冒充已计算。缺审核后的 receptor/cofactor/protonation/box 等条件，未运行本项目 OC/DMT docking。

另做了与项目结论严格分开的 [Meeko/Vina 官方 1IEP 教程](https://autodock-vina.readthedocs.io/en/latest/docking_basic.html) 部署检查：Meeko 0.7.1、官方 Vina 1.2.7 Linux CLI 经真实 stdio MCP 完成受体准备、配体准备、对接、SDF 导出；6 个真实姿态解析成功，best score -13.25 kcal/mol。教程原文件固定在上游提交 3c65c0b3e6c2c1d183f6a175ecb65e3c5ba91645；使用其 box/center/exhaustiveness，seed 42 只作为例子的重现控制，不是项目生物学参数。初次真实 Meeko 调用发现 RDKit/Gemmi/ProDy 缺失，保留失败记录后补齐 RDKit 2025.9.6、Gemmi 0.7.5。ProDy 2.6.1 的 pyparsing 3.1.1 使用工具专用 overlay，未降级共享 pyparsing、NumPy、ColabFold。安装后 pip check 及真实 FreeSASA 10 项复验通过。此分数没有写入 OC/DMT 的空 docking 字段，不能据它声称本项目口袋或活性验证完成。

原生窗口又独立运行一次 DMT PDZ 的五模型预测，rank 1 mean pLDDT = 88.50836842105264。这与批处理值不完全相同；两份 MSA 的有效序列行比较相同，不能将差异解释为 MSA 内容变化。尚未完成 GPU 确定性/随机 key 逐项定位，**不确定原因，不声称位级复现**。两次完整输入/模型长度均相符；native IUPred 的全部 214 个分数与批处理逐位相等。

## 软件与原生验收

冻结源码服务器完整回归：715 passed / 1 skipped；该 skip 是回归环境未安装 FreeSASA。科学工具环境单独运行同组 10 个测试全部通过，覆盖真实 2PDZ/FreeSASA。包含原作者数据的回归启用了 require-author-reference，不是缺数据自动跳过。

本机前端串行测试 20 files / 54 tests passed；production Playwright 12 passed；TypeScript/Vite/Rust 构建通过。并行前端测试曾遇 worker 启动失败和超时，早期类型、fixture/环境及语义测试失败均保留，不用最终通过覆盖失败记录。

原生 EXE 验证采用真实 WebView2/Tauri、认证 HTTPS、私有 CA，未关闭 TLS 验证或改用 bridge mock：

1. 默认 Local；HTTPS 为显式可选项，访问令牌不从 getter 返回，输入框清空且 Windows 本地加密保存。
2. 普通界面创建项目，导入 3 个 main fusion 后再追加 IDR；保存后仍有 4 条序列，没有覆盖。
3. Prediction tools→Prepare→Accept→Start 执行真实服务器 IUPred 和 DMT ColabFold；结果页显示实际 214 位曲线和 5 行 380-aa 模型。
4. 关闭/重启后，两项 completed run 和结果仍保留，未重新运行；浏览器未直接携带上游 token 请求远程地址，无 page errors；正常退出无遗留自有后端。

这证明真实预测任务路径，不代表已有完整 scientific_project、original-method 子步骤及完整 M1/M2 验收。运行环境/账号/部署地址仅在用户本地/私有服务器配置，不进入仓库，不成为默认。

验收临时 HTTPS 服务和自有隧道已关闭，测试明文令牌和临时 TLS 私钥已删除；它们不是常驻生产 API。实际项目、运行/原始输出、公开证据和旧 runtime 保留，没有删除用户实验数据。重新验收应创建新凭据，不能复用已撤销的临时测试设置。

### U01–U09 独立结果

| 项目 | 整体验收状态 | 本轮已验证的子项 | 未完成项 |
|---|---|---|---|
| U01 统一导入/项目对象 | 未修复（整体） | FASTA 追加在真实 EXE 实测；同 ID 冲突显式处理、旧值保持和异步 epoch 通过定向测试 | 统一文件夹分类/对象 Explorer、所有类型一个入口与自动类型映射 |
| U02 原步骤 Workflow | 未修复 | 真实诊断任务使用同一持久化 ledger、接受后明确 Start | 原 M1/M2 Step/Q1–Q4 子步骤和工具依赖视图，策略表单减负 |
| U03 结论/主要证据 Results | 未修复（整体） | 真实 IUPred 曲线/ColabFold 模型表；未定义工程优先分数列去除 | 结构/表格/来源共享选择和完整文档式结果；原始资源入口仍用编号，数值显示精度及版面需改进 |
| U04 实际 Tools 工作区 | 未修复（整体） | 三个已选预测节点可用性与真实运行/解析分开；native IUPred/ColabFold 实测，SEG 实际 MCP 运行 | 所有工具类别统一 Required/access-required/配置流程；真实授权工具未配置 |
| U05 Method/Parameters/Decision | 未修复 | 原公式/参数 authority 与冻结运行边界保留 | 完整逐步 Method/Input/Output/Decision 面板及 draft 参数差异→replan 联动 |
| U06 文字/颜色层级 | 已修复仅定向验证（子项） | cutoff 标签、无定义分数列、部分缺失值展示已改；native 截图已检查 | 全工作区层级、冗余点串与对比度/键盘任务式完整审查仍未完成 |
| U07 首次启动/任务输入 | 未修复 | 新建项目、普通导入和真实诊断运行实测，无演示生物学数值 | Start/New project 的任务式向导、按 M1/M2 所选步骤隐藏无关 M3/M4 表单 |
| U08 持久多文档 | 未修复 | 资源选择的轻状态保留，隐藏重视图卸载 | 真实 openDocuments/activeDocumentId、去重/关闭/草稿/五文档任务、camera/selection 恢复尚未实现 |
| U09 内存与响应 | 尚待实际环境（完整验收） | 精确科学距离分块、显示降采样/ResizeObserver、隐藏重视图卸载、重复 state_version 过滤；实际 EXE 2FHA 24-chain 配对测量 | 硬件 GPU/现有用户场景与全任务测量；切换重载仍有明显成本，不能称全面改善 |

X01 筛选改为后端先 kind 过滤再分页，>50 混合资源、完整 total、授权/缓存篡改定向测试通过。X03 Workflow 文件读取的 stale promise 被 epoch 拦截，定向 race 测试通过。X02 2D/3D 保留并实际显示 24-chain 结构，但完整结果产物链未完成。X04 不增加第二套计算或 provenance authority，但大型 shell 的职责拆分仍未完成。X05 认证、TLS、冻结 run、splitter、disclosure 边界保留。

## 实际资源数据与局限

同一机器、相同 SwiftShader 软件渲染和 BLAS 线程控制，启动自有 r14/r15 EXE，导入真实 2FHA assembly，20 秒可见 idle、五次 Inputs↔Resources、20 秒隐藏 idle；记录 FusionLab/自有 Python/WebView/GPU-process 整个进程树 RSS/CPU、CDP 请求和传输。没有本机科学计算。RSS 是进程 Working Set 之和，含共享页重复，不是独占 RAM；CPU 列是采样首尾累计 CPU 秒差，不是整机 CPU 百分比。GPU-process CPU/RSS 不是物理 GPU 利用率。

| 可比较阶段 | r14 | r15 |
|---|---:|---:|
| 隐藏后仍存在的结构 canvas | 1 | 0 |
| 可见 idle mean tree RSS | 1,128,355,840 B | 1,141,974,747 B |
| 隐藏 idle mean tree RSS | 1,012,891,355 B | 957,856,329 B |
| 隐藏 idle CPU 秒/采样秒 | 6.55 / 18.24 | 0.59 / 17.90 |
| 五次切换阶段 peak tree RSS | 1,125,818,368 B | 1,256,984,576 B |
| 五次切换阶段 CPU 秒/采样秒 | 192.89 / 27.63 | 191.31 / 47.57 |

隐藏闲置开销下降，但视图重建增加等待、峰值内存和结构重新传输；新版本切换阶段新增约 22.6 MB CDP 编码传输，旧版持续保留 viewer 时基本没有新增结构传输。必须进一步以真实文档状态管理解决，而不是宣称全部优化。没有物理 GPU 利用率、绝对完整启动网络或统计显著性结论；启动是采样窗口，不能当严格 wall-clock benchmark。

旧版两次本机 backend startup 超时、第三次及最终可比较组成功；失败原因尚未充分定位，不能推断由新版代码解决。一次早期测量脚本用了不正确的 canvas selector，原记录保留但不作为 canvas 结论；最终两组都改用实际 structure-canvas 并验证可见 canvas = 1。详细原始 samples/phase/proof 和限制见验收证据包，native_profile.csv 只是整理后的摘要。

最终声明部署大小（含新补齐的 docking 依赖）：服务器 14,002,050,609 B + 本机去重已安装文件 912,318,612 B = **14,914,369,221 B < 15,000,000,000 B**，余量约 85.6 MB。同时保留不去重路径上界 15,501,318,858 B，不能隐瞒 PNPM alias/hardlink 重复计数差异。范围包括选定工具/环境/模型缓存、当前及保留服务器 runtime、本机依赖和当前 portable；不包括非活动发布压缩档/科学输出/无关构建工具链，也不等于整机空间。原生测试临时实例已结束；旧发布和服务器旧 runtime 可回退，未删除用户输入。此前未补 docking 依赖的 14.58 GB 记录不再作为最终预算。

## 交付与可追溯性

- FusionLab-Windows-20261008-r15-b62073d/FusionLab.exe 和同名 ZIP：默认 Local、可选已有 HTTPS API；新鲜安装并不自带全部科学工具，也不会自动连任何服务器。
- 冻结 runtime bundle、source tar、EXE/backend manifest 同属 b62073d；556 个提交文件、6 个 pinned submodule；portable 148 个允许的源码文件逐字节核对，6,626 个 manifest 文件核验。运行身份仅存在后台/报告，未要求用户在前端输入摘要。
- 发布清单 633 个组件，OSV 查询的日期/范围单独记录，未检出匹配 advisory 不等于证明永远安全或许可证全部满足。
- FusionLab-r15-real-M1-M2-frozen-evidence.zip：原始科学输出、核验输入、分开的 m1_part_screens/m1_fusion_screens 和 needs_review pocket_definition。JSON/日志中私有部署路径为标明的公开投影，原始未脱敏记录保留在服务器；manifest 分别记录源/交付文件，不冒充完全原始字节。
- FusionLab-r15-native-real-artifacts.zip：实际 native 发起的 IUPred/ColabFold 原文件与重复运行比对。
- FusionLab-r15-official-docking-smoke.zip：官方示例原输入、真实执行/解析/导出、来源及依赖失败记录；它不是项目 docking 数据。
- m1_features.csv（11 行）、m1_decisions.csv（11 行）、m2_decisions.csv（25 行）、tool_readiness.csv（29 类工具）、native_profile.csv；所有缺失科学数值留空/null。
- source_links.md：逐文件下载来源、原文/论文、作者数据、真实执行工具的官方来源及未执行工具入口；不是把安装页面当作真实完成证明。
- 验收证据包：最终/失败测试记录、真实 native screenshots、restart/lifecycle、两版 profile 原始数据、包身份和预算范围。

## 下一轮修复记录：不能藏到“全部已完成”里

可由代码继续完成：真实多文档生命周期与 camera/selection 恢复、统一输入对象/文件夹分类、原方法子步骤调度与结果链、工具配置 UX、M1/M2 任务式输入、结果可读名称/精度/共享选择、进一步减少重复读取/重建。它们不是许可问题，不能声称已完成。

需要用户/方法来源：SignalP/DeepTMHMM/TANGO/PASTA 有效授权和实际完整输出；短 linker SS 方法适用性的明确决定；禁用 motif 列表；完整 reviewed enzyme core/pocket/mapping、化学条件、cofactor/protonation/box；真实 scaffold-relative placement/conflict graph、volume 与 dynamics 条件；未定义评分/归一化/权重来源。不能用模板、锚点、padding、均值 PAE、空列表、mock 输出或未经允许的“化简”代替。

资料来源以用户本次输入包的原文和规范为方法 authority，外部执行事实以真实运行记录为准。科学结论停在实际证据范围内；本报告明确的未知原因和未完成项不因回归测试通过而消失。

# R26：R24 简化 review 实施记录

日期：2026-10-13。依据团队提供的 `current_status_review_r24_remove_artifacts_and_simplify_20261012.md`。这是分项实施及验收记录，**不是整份 review 全部完成声明，也不是非专业用户测试或生物学验证**。最终 Windows 包以其 PACKAGE_MANIFEST 的提交与同名源码归档为准；后续只追加验收文档的提交不改变该运行代码。

## 本轮实现

| 要求 | 已实现的行为 |
|---|---|
| 文件与目录 | 删除独立 Resources/Artifacts 工作区及无用目录组件。Inputs/Results/工具输出直接打开具名可关闭文件标签，关闭不删除文件。项目、运行授权和源哈希校验仍在后台。 |
| Inputs | 一个 Import 主动作及文件夹选项，真实歧义集中处理；FASTA/PDB 按文件分组，不默认铺全部序列。配置只列一个计划摘要，具名构建在摘要内打开；部件序列按选择展示。Add design 从真实已导入蛋白记录选择顺序，不要求逗号分隔 ID。 |
| Assistant 与状态 | 仅一份对话、composer 和当前提案卡，Accept/Reject/Modify；删除 Inspector/Evidence 镜像。未发送文字与科学输入、工作流、审批状态分离，按项目保留；关闭面板不删除文字，浏览器刷新恢复文字。Modify 意图不跨完整刷新保存。 |
| 工作流 | Graph/List 共用持久化文档，列表三列；节点/边操作按选择出现。Create plan/Review changes/Run/Stop 对应实际状态。保存科学修改使旧审批失效，但不删除编辑对象。刷新恢复上次打开的文档，不自动选择不相关最新草稿。 |
| 公式与参数 | 标量按已准入执行 AST 生成数值位置；重复变量共用绑定，Enter 保存、Escape 取消、无变化不建版本、显示舍入不改存储精度。原方法完整方程/假设/步骤仍在 Method。明确支持的 M3 finite-site、M4 physical markdown steady-state 输入有确定性映射；未显示/歧义量保留最小参数表。固定常数、派生输出、历史结果不变成编辑点。 |
| 版本与 ER | 已支持的 typed ScientificQuantity 同步更新参数记录及实际模型引用，保留原记录/来源并标记 pending review。审核复用 ER 的真实身份、条件、单位、来源门控，不等于模型整体批准。无可靠编辑映射的反应绑定继续只读。Edit as new run 克隆原运行拥有的模型及输入授权，而不是当前最新草稿。 |
| Results | 一个当前对象的主结果；M1 Features、M4 Fluxes/Checks/Sensitivity、M5 Data/Residuals/Fit 按需查看。未知格式明确不支持显示并可导出，不用 JSON 树冒充结果。E1 文件入口继承当前 series；CSV 集中在 Results Export。 |
| 3D | 默认模型及必要控件；只有实际可用着色，B-factor 不当作 pLDDT。Residues 显式加载，关闭销毁请求/React/WebGL。 |
| Jobs/Tools/Settings | Jobs 一份任务列表；Output 可读级别日志，Problems 只放实际错误及修复。Tools 按所选工具要求数据，注册不等于可用，Review task 与 Run 不混称。插件/Skills 一个 Add 入口；统一 Settings 的 Appearance/Assistant/Connection，Save and test 测实际保存配置。密钥不进项目。 |

本轮没有替换 M1–M4 科学内核、化简原方程或更改数值容差。M4 新增的是已知模型单位/体积基准的输出元数据，旧结果缺单位时不补猜测单位。推送后 CI 暴露旧守恒基算法在 SciPy 1.12 空矩阵上的兼容错误：没有活动反应/交换/边界列时，按定义返回完整单位基；非空矩阵仍用原 SVD，不修改 RHS、反应网络或容差。Python 3.13 构建测试缺 setuptools 也补入 test extra，并在 CI 复用固定构建锁。依据 [SciPy 1.12 null_space 定义](https://docs.scipy.org/doc/scipy-1.12.0/reference/generated/scipy.linalg.null_space.html)及其[实际实现](https://github.com/scipy/scipy/blob/v1.12.0/scipy/linalg/_decomp_svd.py)，不跳过失败测试或放宽断言。

## 已实际验证的范围

- 前端 27 文件、82 项测试通过，TypeScript 与生产 Web 构建通过。
- 本机仅执行软件/数据契约检查：43 项后台绑定、导入、权限、历史克隆及 ER 审核元数据检查通过；没有运行本机科学求解器。
- 安装后的 Web 包，7 条浏览器任务通过：真实 GenBank 导入/原文导出、歧义导入恢复、缺文件追加、完整原方法显示及保存、工作流 fan-out/非法修改拒绝/重新打开、真实 PDB/mmCIF 的旋转/PNG导出/20次关闭重开及 WebGL 不可用替代路径。
- 科学执行只在授权服务器：标量 `x/(k+x)` 的新版本实际由 0.5 变为 0.25，原运行保持 0.5；重复变量、Enter/Escape/no-op、刷新、新旧版本拥有关系均检查。此为软件数学验证，不是生物学预测。
- 服务器实际运行修正后的 PS-v3 合成包，E1 默认产物15、所选 dilute/quantity 在文件标签与返回后保留；CSV 来自 E1 本身；E3 缺 ER 数据继续 blocked。合成演示不算实验验证。
- 真实 3 FASTA + 3 PDB 浏览器导入只列 6 对象，FASTA 内记录数取原文件；原始 2FHA 一击显示模型，无前置目录/默认残基表，关闭保留选中输入。

服务器完整数值回归、最终 EXE 同提交验收、大小与已知私密信息检查的结论，在交付验收补记中记录；不以此前 r25 的通过代替当前版本。

## 明确仍未完成 / 未验证

1. **全部模型输入的统一编辑尚未完成。** 原始 ER/network 文件中的非 typed reaction 参数、自定义 ODE、其他 M3/M4 模式/部分配置字段没有完整版本化编辑映射；保留只读并要求导入有证据的新模型，不通过解除 readOnly 伪装接通。
2. **正式多候选结果的上下文传递未全部完成。** 本轮验证合成 E1，不能据此宣称所有正式 M4 候选/轨迹的选择都跨文件标签持久化。Compare 已有入口和适用性检查，但条件/参数 before→after 可读值展示仍不足，不能把改动字段路径当作完整条件比较。
3. **选中测量表的 Map columns 工作流仍需补齐。** 后端解析映射仍在；本轮未恢复/验收一个完整的选中对象映射编辑入口。未提供真实 F3/M5 独立数据，不声称扫描/拟合生物学验收完成。
4. 工具输入继承尚未覆盖全部复杂绑定；新 Tools 界面的完整真实 IUPred 作业、插件安装/权限失败、模型 Save and test 失败恢复、新设计完整任务等组合分支仍需专项验收。已有真实外部工具回归不等于每个新 UI 路径已验收。
5. 完整 M1/M2 仍有科学缺项：完整融合序列的受许可预测、其他正式预测证据、风险/排名工作流连接和通过 M1 的完整融合结构结果。SignalP/DeepTMHMM/TANGO/PASTA 仍无团队授权，不绕过许可，也不填造结构/口袋结果。
6. 软件请求/WebGL 生命周期已检查，但没有同机器前后完整性能基准，不能断言风扇/CPU改善或仅凭源码删行证明提速。尚无真实非专业用户独立任务测试，不能声明达到软件奖全部效果。

## 复查入口

Inputs 点击文件 → 具名标签 → 关闭；Workflow 选模块 → 数值位置/Method → 新版本；历史运行 → Edit as new run；Results 选 E1 → Data → 关闭 → Export；Tools → 选工具 → Review task → Assistant Accept → Run。无需独立资源目录、参数标签页或重复 Inspector。

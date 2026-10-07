# r11：剩余软件功能、非受限验证与桌面交付

继续处理 r8 review 和 r10 修复记录中的未完成项。用户确认目前没有 SignalP/DeepTMHMM、TANGO/PASTA 授权，本轮只完成软件和非受限验证，不代为接受许可证、不伪造工具作业或生物证据。

冻结运行源码：`c5733b87d256fc290fe1f12d86278057706c5f62`。后续修复记录/README 提交只改文档；运行 TAR、便携 EXE 与冻结 bundle 对应该版本。原 review 是需求及审核材料，不自动构成对其中所有操作的授权。

## 完成的后续项

| 原来未完成 | 本轮行为与验收边界 |
| --- | --- |
| 空项目无 YAML 创建科学配置 | 从已保存的普通序列资产，逐项填写原后台合同的模型控制，校验、预览、明确确认后保存。温度/pH、参数、初始浓度等保留真实空缺；创建不运行科学阶段。复杂相对路径依赖仍可使用已有目录导入。 |
| 少见输入字段仍依赖高级 JSON | 复用后台 Pydantic schema 和单一递归类型化编辑器，补充构建/参数的少见字段、模型控制和其他输入声明。没有另建参数或审批模型；审批字段只读。不是所有字段组合都经过人工遍历。 |
| 缺项仅跳转大表单 | 保留具体构建/条件/原字段路径，自动展开目标区域并聚焦；缺失参数只预填合同中的名称，不填写值、单位、来源或批准状态。存在多个匹配对象时要求显式选择。 |
| 编辑原记录可能留下旧审批 | 主表单保留原失效流程；补充编辑器修改 construct record 后撤销该记录的 approval/M1 review，其他记录与仅排序时的审批保留。保存若因原设计引用失效而拒绝，仍要求真实重新审核，不悄悄保留旧批准。 |
| M5 超过 100,000 点后无法访问后段 | 图的精确区间切换独立于 100 行表格分页；图/残差点击回指原 source ordinal。100,002 点案例覆盖后段；0/null 保留，不降采样、不补点、不重算 comparison。 |
| 实际 M5 产物未贯通原生页面 | 注册服务器真实 `run_m5` 已保存的完整 `M5ComparisonSeries`，共享现有 M5View；必须具有原合同的所有字段，不为旧摘要补单位或数据。原生 Plotly 实际展示预测、观测及残差，原件与源嵌套记录一致。其输入是明示合成的软件实验，不是独立生物验证。 |
| 原生目录弹窗验收缺失 | 使用新 EXE 的真实 Windows 目录选择和 WebView 上传确认，选中嵌套科学文件夹，预览并保存 typed project；没有注入 filechooser 或用 setInputFiles 代替目录选择。 |
| 真实 FTH1 大结构未验收 | 非受限公共 3AJO biological assembly 1 原始 mmCIF 经资产入口进入真实 Molstar：41,136 原子、24 链，链选择/残基导航可用；未知置信度不填造。是坐标浏览，不证明融合设计、自组装或 LLPS。 |

接口预览复用原 ProjectConfig 验证、资产所属/哈希检查及既有保存流程；禁止携带私有 run/tools 配置或自动授予审批。没有增加通用插件框架、替代科学公式或第二套全局状态。新增 M5 资源只投影持久化结果，不建立另一个拟合器。

## 验证与可声称范围

| 检查 | 最终结果 | 解释 |
| --- | --- | --- |
| 服务器全 Python/作者数值回归 | 652 passed，0 failed/error/skip，60.15 s；要求作者原文件 | 科学数值、作者回归及真实阶段计算全部只在服务器执行；不是所有生物假设均已验证。 |
| 本机定向软件/API/解析检查 | 76 passed | 只用已有持久化合同和软件输入，不执行本机科学求解或标定；最终补丁只改前端，后台源码未变。 |
| 前端组件 | 40 passed | 包括修改记录撤销审批、排序保持身份、空数值非零、精确区间及缺项导航。组件渲染替身不是原生科学验证。 |
| 生产 dist + 真实 HTTP 浏览器 | 11 passed，0 failed/skipped/flaky | 浏览器桥为明示替身；不把它作为 EXE 验收。 |
| 真实新 EXE + 本地后台 | 通过；15 个内置资产逐字节核对；正常退出及重启后自有后台均为 0 | 原生桥、M5/F3 实际来源、公开 FTH1、无 YAML 创建、重启恢复；不执行本机科学阶段。 |
| 真实新 EXE Windows 目录选择 | 通过；2 个原始嵌套文件一致、typed preview/save 成功、作业数 0、退出后自有后台 0 | 操作仅限本轮自有窗口/目录；既有用户软件实例保持不动。 |
| 原科学核心 | 7 个文件与 baseline `5a5e19a308f20d4b1f9863c7a732bdb26b03da1f` 字节相同 | 仅检查指定文件，不用其哈希代替科学正确性证明。 |

核心文件范围（相对 `src/igem_drylab/`）：`full_network.py`、`m3_equilibrium.py`、`m4_steady_state.py`、`pipeline/stages.py`、`pipeline/config.py`、`pipeline/models.py`、`scoring/m2_structure.py`。实际完整路径与 blob 对照保存在私有证据清单。

服务器实际有限扫描经过公开边界，正式 `r_target` 等指标仍为 null，拒绝原因保留；软件夹具不得升级为正式候选排名。M5 实际阶段输出来自构建/条件匹配的合成软件实验，不等于真实湿实验，显示器不授予任何参数审批。

## 数据源头链接与使用范围

1. 本轮公开结构：[RCSB 3AJO](https://www.rcsb.org/structure/3AJO)、[PDB DOI](https://doi.org/10.2210/pdb3AJO/pdb)、[原论文 DOI](https://doi.org/10.1016/j.bbrc.2010.08.017)、[官方 assembly 1 mmCIF gzip 下载](https://files.rcsb.org/download/3AJO-assembly1.cif.gz)。下载在服务器完成；gzip 952,767 字节，SHA-256 `c80306d80f94ccae3274de62910ccf1de1da7e84d0a4cdb643ed9e7002462088`；解压原件 4,822,508 字节，SHA-256 `dfe0864d42ff7e3fd3f565cd7f40889ba225f6bfea626c8e56de8fdadf58bbca`。坐标含水/异源残基，不把所有坐标 residue identities 当作氨基酸数。原生截图是选择链后聚焦视图，不是全组装球体全景。
2. 本轮实际 M5 软件产物：[固定源码的实际集成生产测试](https://github.com/ZincDYX/iGEM-2026-Tsinghua-T-dry-lab/blob/c5733b87d256fc290fe1f12d86278057706c5f62/tests/test_scientific_integration.py)。原反馈 SHA-256 `f668a9f26201815f6376b9dcdbc62e1c08434b86bdde947e9e972bebc6a77b88`，其原嵌套 series 导出 SHA-256 `58a12047328fc3291f5c1a5fc483abe0612645ea766f6492258836de53703074`。夹具来源与参数在代码中明示，不援引外部论文充当这些人工观测的来源。
3. 实际 F3 软件产物：[固定源码的 fresh design 集成测试](https://github.com/ZincDYX/iGEM-2026-Tsinghua-T-dry-lab/blob/c5733b87d256fc290fe1f12d86278057706c5f62/tests/test_fresh_design_integration.py)。原公开报告 SHA-256 `80249a9e7efd43913fe7e074b29e692100d41ae3587f4ff4ba77918568873e45`；非正式 claim scope 保留，原资产 UUID 导致不同执行的报告字节可不同，不声称逐次报告 SHA 必然相同。
4. 本轮作者回归使用此前封存的[作者原 RHS](https://ndownloader.figshare.com/files/55079462)及[作者参数文件](https://ndownloader.figshare.com/files/55079456)，发布记录为 [Figshare v1 DOI](https://doi.org/10.6084/m9.figshare.29221010.v1)。SHA-256 分别为 `bbd12e1c631e4f68923ab202ba81393c6620dd163712360401894f5b14c8eaa1`、`d5821b0d8d299f57b8a204b6986daf044599135c8a9a31371e41712fb4690c56`。本轮核验封存文件并运行回归，不声称重下载和重新复现整篇论文。
5. 光甘草定原文、全部已用附件、实测工作簿、原组学入口和先前数值诊断，完整来源索引见[既有复现报告](glabridin_reference_reproduction.md)和[机器可读来源清单](glabridin_reproduction_sources.json)。论文：[Nature Communications](https://www.nature.com/articles/s41467-026-68881-8)；实测工作簿：[Source Data_V2.xlsx](https://ndownloader.figshare.com/files/60449912)。先前未复现的组学/长 MD/湿实验，本轮仍未补出结果。

## 发布、证据与失败保留

便携目录名 `FusionLab-Windows-20261008-r11-c5733b8`；必须保留目录全部内容并启动其中 `FusionLab.exe`，不要单独复制 EXE。默认内含本地 Python/后台及 SQLite，不默认连接任何服务器。仓库不包含私人部署地址、SSH 账号或验收工作区路径。

冻结运行 bundle 含 523 个文件（516 文本、7 二进制、6 个固定 submodule 引用），SHA-256 `5aff6279b798f4828282f295613db036fdcf3e2ce6ae5a0be1c9345d935a7bb1`；从 bundle 解出的源码 TAR SHA-256 `86ca70e2e4529e1451d9c5a6735a9faf51b39eaf6acfb6b94bb8580b50125557`。完整主 bundle 后续还包含本文档，只增加文档，不替换冻结运行产物。

- EXE SHA-256：`87235afd9f1537c9a506cc3cc1fdeee2bb41e5a466fd4f2e3753b646fb09a74d`。
- ZIP 98,866,091 字节，SHA-256 `8e85367b474cfacf2ddfd9214291ec6d80016fcfd5427826700b922ff2024835`；manifest 解包记录 271,224,654 字节。6,574 清单项、142 运行时源码及 ZIP 内容全部逐字节核验；没有散落 pyc 或开发 tests 目录。私有标识扫描仅限运行源码，不证明识别任意秘密。
- 原生 FTH1 单次 metadata 预热、SwiftShader 显示探针约 6,262 ms，不是冷启动或通用 GPU 性能承诺；120,289 ms 是整套功能验收时长，不是程序启动时长。
- 本轮保守合并部署 **14,761,235,097 字节 < 15,000,000,000**：声明服务器环境/工具/权重/缓存、保留运行版本和当前生产资产 13,560,995,718；本机前端依赖 340,722,110；后台环境 314,488,562；当前便携目录遍历 272,520,999；仍开着的旧用户便携目录遍历 272,507,708。PowerShell 目录遍历口径可重复计入链接别名，因而与 manifest 解包字节不同，这里不减去别名以保守计量。历史非活动发布/源码归档、科学输出和无关构建工具链不在此部署口径；不是总磁盘占用或安装硬配额。

依赖未变、未安装新科学工具或权重。631 项 [CycloneDX 1.6](https://cyclonedx.org/specification/overview/) 组件清单通过官方 schema；2026-10-07 UTC 的 [OSV querybatch](https://google.github.io/osv.dev/post-v1-querybatch/) 631 个版本查询记录随包保存。这种版本数据库检查不是完整安全、法律许可或未知漏洞证明。

失败均保留，未计入最终通过：非法 null 预测测试夹具、未声明 schema 的组件 API 替身、浏览器创建面板被误关、预校验缺技术 run identity、首次 Rust home 路径错误、原生坐标测试调用了错误导入路由、option 的测试 matcher 与原生 disabled 属性差异、链选择无精确无障碍标签、目录选择后仍需真实 WebView 上传确认、晚期 CDP resource tree 为空，以及瞬时 Git 服务失败。修正相应产品代码或验收脚本，不修改科学容差/方程。当前并发测试通过不能确定所有机器时序都不存在问题。

原始证据包含测试/部署路径，只交付用户的私有 evidence ZIP，不提交仓库。旧发布目录、源码 bundle、失败日志和用户已有数据保留；服务器更新前确认旧入口没有活动后台，不终止其他作业。

## 仍未完成：不能统称为授权问题

- SignalP/DeepTMHMM、TANGO/PASTA 许可及实际作业：按用户最新决定暂缓。现有可用性/证据检查不会将“已配置命令”当作真实已完成作业。
- 真实条件匹配的 ER/运输、相内活性、表达量和动力学测量，真实标定、可辨识性及真正独立留出：尚缺配套数据。本轮公共 FTH1 和软件 fixture 不能补齐。
- 原文完整组学、长 MD 和湿实验：未完成；需要实际数据/计算资源及 MD 初始结构、拓扑等，并非仅增加代码即可确认。
- 任意不可信插件的 OS 文件/网络权限沙箱：未实现；venv 仅依赖隔离，不是权限隔离。
- 正式认证远程会话/通用 SSH 桌面模式：未验收/交付；不能启用匿名绕过或写入私有服务器默认地址冒充完成，需要先明确真实鉴权/部署合同。
- BCIF、任意旧版语义自动迁移、每种科学表单组合、全历史/多 GPU 性能：未确认全覆盖，不造解码或补科学缺项。
- 独立干净 Windows 安装、商业代码签名、完整渗透/原生库/供应链审计：未完成；当前机器真实原生验收不代表这些认证。

本轮把可独立验证的软件路径补齐；以上外部数据、授权、环境和未支持功能仍在修复记录中明确保留，不宣称“全部剩余工作已完成”。

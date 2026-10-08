# FusionLab r12：日常界面简化与 BinaryCIF 导入

日期：2026-10-08。继承 r8 review 和用户要求；科学计算/作者回归仍只在服务器执行。此文的验收项目在发布前逐项核实，不能用软件夹具证明生物学结论。

## 本轮实施

- 从日常输入、资源、运行、Agent、序列表、M2/M5 和结构/曲线来源面板移走长指纹、资产 UUID、诊断编号及重复公式/schema 版本。显示原文件名、逻辑目录、冻结运行名称、保存版本、完整性状态及必要来源、单位、条件和缺失项。
- 共用 JSON 展示过滤已知技术元数据，不删原对象、不改 API 或审计导出，不对任意十六进制字符串做全局替换；例如 64 个 A 的真实序列必须保留。前端展示不是保密或权限边界。
- 常用/少见表单和输入检查显示短字段标签；程序定位仍用原字段路径。已有记录修改后撤销审批的规则不变。部分屏幕阅读器标签仍为技术路径，未声称全部无障碍/文案设计完成。
- 后台运行摘要/迭代信息从冻结输入取项目名称。编辑当前草稿不会改掉历史运行名称；不是增加第二套状态仓库。
- 新增 `.bcif` 二进制导入，沿用同一资产、项目授权、原件下载和结构显示投影。仅解码允许的原子列，不把 B-factor 当 pLDDT，不算新叠合、活性、自组装或相分离。
- 复用 Python-IHM 2.11 的七类 codec；薄适配器按实际展开长度限制压缩列，并保留缺失掩码。坐标使用已解码数值的字符串，不经三位小数格式化。普通 mmCIF 不因 BCIF 新依赖而改变解析路径。
- 新依赖固定为 `ihm==2.11` 与 `msgpack==1.2.3`，实际安装在服务器验证环境和 Windows 便携包中；不新增大型预测器或模型权重。

保留后台内容绑定、冻结输入、原件完整性、来源关联和项目授权。结构查看器仍有少量前端异步结果身份检查，避免旧请求/旧注释混入新结构；它们不显示指纹，也不替代后台校验。不能把“移走日常显示”说成“前端源码完全没有身份字段”。

## 验证

最终运行代码：`153e53c`。模块分开提交并推送：界面清理 `2adf599`、BCIF 导入 `6e7f0dc`、依赖修复及最终界面验收 `153e53c`。

| 检查 | 结果与范围 |
| --- | --- |
| 服务器全 Python/作者回归 | 668 passed，0 failed/error/skip，60.79 s；强制提供封存作者原件。不是整篇论文/全部生物参数验证。 |
| 本机定向解析/元数据测试 | BCIF 15 passed；运行名称与读取合同 4 passed。不在本机运行科学求解器。 |
| 前端组件 | 42 passed，0 failed。保留数值零、null、单位、DOI、构建/条件名及原对象；移走技术指纹。 |
| 生产 dist + 真实 HTTP 浏览器 | 11 passed，0 failed/skipped/flaky。浏览器桥是明示软件替身，不等于 EXE 验收。 |
| 科学核心 | 指定 7 个文件与原 baseline 字节相同；该检查本身不能证明全部计算正确。 |
| 公开格式比较 | RCSB 3AJO 非对称单元 BCIF/mmCIF：1,714 原子，8 项原子身份字段逐行相同，x/y/z 最大绝对差均为 0 Å。不是旧验收中的 24 链 assembly。 |
| 新 EXE + 实际原生桥/本地后台 | 通过；4 份原件下载字节一致，实际 M5/F3、24 链结构和 1,714 原子 BCIF 可用；15 个内置资产逐字节一致。默认检查页面无原件长指纹、UUID 或完整配置路径，匿名访问拒绝；未在本机执行科学阶段。 |
| 原生关闭/重启恢复 | 正常退出，重启后保存项目恢复，两次自有后台残留均为 0，原用户窗口保持不动。109,523 ms 是整套功能探针时长，不是软件启动时间。 |
| 原生 OS 目录选择 | 通过；操作实际系统对话框和 WebView 上传确认，2 个嵌套原件一致，typed preview/save 可用，作业数和正常退出后的自有后台均为 0；没有替代为 setInputFiles。 |

科学核心范围：`src/igem_drylab/full_network.py`、`m3_equilibrium.py`、`m4_steady_state.py`、`pipeline/stages.py`、`pipeline/config.py`、`pipeline/models.py`、`scoring/m2_structure.py`。

## 来源及实现取舍

- 公共结构来源：[3AJO 条目](https://www.rcsb.org/structure/3AJO)、[PDB DOI](https://doi.org/10.2210/pdb3AJO/pdb)、[BCIF 原件](https://models.rcsb.org/3ajo.bcif)、[对应 mmCIF 原件](https://files.rcsb.org/download/3AJO.cif)、[RCSB 官方下载说明](https://www.rcsb.org/docs/programmatic-access/file-download-services)。两份原件在服务器取得并保存；坐标比对在服务器执行。
- 继续验收的大结构为先前封存的 [3AJO assembly 1](https://files.rcsb.org/download/3AJO-assembly1.cif.gz)，41,136 原子、24 链；与新非对称单元明确区分。来源论文 [DOI](https://doi.org/10.1016/j.bbrc.2010.08.017)。本轮不重新复现该结构论文的湿实验。
- 解析依赖：[Python-IHM 2.11](https://pypi.org/project/ihm/2.11/)、[固定版本源码](https://github.com/ihmwg/python-ihm/blob/2.11/ihm/format_bcif.py)、[BinaryCIF 接口文档](https://python-ihm.readthedocs.io/en/latest/format_bcif.html)。IHM 采用 MIT；适配器使用其固定版本内部 codec map，升级需要重新验证，不能宣称公共 API 的跨版本稳定性。
- [msgpack 1.2.3](https://pypi.org/project/msgpack/1.2.3/) 采用 Apache-2.0。初选 1.1.2 的版本审计命中了[官方漏洞公告](https://github.com/msgpack/msgpack-python/security/advisories/GHSA-6v7p-g79w-8964)，因此升级后重新运行回归和打包，旧候选发布不作为最终交付。
- 实际 M5/F3 图表输入来自本次服务器运行的 `tests/test_scientific_integration.py` 与 `tests/test_fresh_design_integration.py`。它们是合成软件实验产生的真实阶段产物，不是外部湿实验数据；显示不授予审批、不补正式扫描指标。
- 作者回归使用封存的 [RHS 原文件](https://ndownloader.figshare.com/files/55079462)、[参数原文件](https://ndownloader.figshare.com/files/55079456)、[Figshare v1 DOI](https://doi.org/10.6084/m9.figshare.29221010.v1)。原文 [Nature Communications](https://www.nature.com/articles/s41467-026-68881-8)、[实测工作簿](https://ndownloader.figshare.com/files/60449912) 和全部之前使用的来源，见 [既有复现报告](glabridin_reference_reproduction.md)及[来源清单](glabridin_reproduction_sources.json)。本轮不把原文组学、长 MD、湿实验宣称已复现。

## 发布与保留的限制

默认本地便携桌面；不默认连接服务器，不包含私人服务器配置。完整代码主 bundle 更新，并保留旧 bundle、旧发布和既有用户数据。冻结运行 bundle 包含 528 个文件（521 文本、7 二进制）和 6 个固定 submodule 引用。完整指纹仅保存在后台/机器证据清单，不要求用户在日常界面复制核对。

633 项 CycloneDX 1.6 清单通过官方 schema；最终 OSV 版本查询无命中。它只是有日期的版本数据库匹配，不是未知漏洞、安全性或法律合规保证。新包保留两项依赖的许可证原文。

最终 ZIP 99,181,976 字节；便携清单 6,621 项、143 份运行时源码及 ZIP 内容全部逐字节核验，没有散落 pyc。私有部署标识检查仅限运行时源码，不是任意秘密格式识别保证。

部署预算沿用前次口径：声明服务器工具/环境/权重/缓存及保留运行版本，本机前端依赖、后台环境、当前包和仍打开的旧用户包；历史非活动发布/源码归档、科学输出及无关工具链不计入，故不是机器总占用。本轮保守合计 14,784,103,750 字节 < 15,000,000,000。目录遍历保守计入链接别名，故不与便携清单解包字节混用。

失败记录不抹去：早期浏览器定位同名阶段按钮歧义、旧断言期待显示指纹、首次包使用旧依赖、服务器代理不可达，以及 PowerShell 传输 shell 脚本末尾 CR 导致退出非零。科学测试 XML 实际为全通过；部署后另做目录、manifest 和后台冷导入核实，不能仅凭该非零 shell 返回声称部署失败或成功。目录验收旧脚本两次未找到属于本轮进程树的对话框；实际对话框在 UI 树中属于本轮 Tauri 窗口但使用另一进程，改为严格核对 UI 窗口祖先后验收通过，未放宽到任意系统对话框。

仍未完成的项目必须分开说明：

- 受许可预测工具真实作业：用户暂无许可证，按要求暂缓。
- 真实条件匹配的 ER/运输、相内活性、表达/动力学测量，标定和独立留出：缺配套数据；公共结构不能替代这些数据。
- 完整组学、长 MD 与湿实验：缺完整实际输入/资源，仍未复现。
- 不可信插件的 OS 权限沙箱、正式认证远程会话：仍未交付；venv 不是权限隔离，远程模式不通过匿名访问冒充可用。
- 结构注释的可视化创建/自动文件绑定工作流尚未完成；现有导入的合格 sidecar 可用，隐藏技术字段并不等于已自动生成所有科学证据绑定。
- BCIF 当前限单数据块、单 `_atom_site`、20 MB 原件和 200,000 原子等既有显示预算；不是任意 BCIF 归档、旧版语义自动迁移或全恶意输入安全证明。
- 独立干净 Windows、商业代码签名、完整渗透与原生供应链审计：未完成。商业签名不属于日常科学输入，界面无需展示签名代码。

不得将本轮完成的软件路径统称为“所有剩余功能或生物学验证完成”。

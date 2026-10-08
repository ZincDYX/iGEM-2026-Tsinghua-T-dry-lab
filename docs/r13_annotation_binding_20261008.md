# FusionLab r13：后端管理结构注释文件关联

日期：2026-10-08。继续用户“完成能完成的剩余项、移走日常签名/SHA 编号”的要求；本轮不更改科学方程、不在本机进行数值或作者复现。

## 使用方式与实现

1. 正常导入并保存目标 PDB/mmCIF/BCIF、原注释 JSON；涉及参考残基或原矩阵时导入参考结构，涉及全融合位置时导入 FASTA。
2. Inputs → Import files → Link structure annotation source。按原文件名选择来源、目标和所需依赖；FASTA 有多条记录时填写明确记录名，不填写哈希。
3. Check annotation file links 由后端计算/核对文件身份并验证来源，生成关联文件预览。Confirm import into draft → Save 后，既有结构查看器使用该文件。

原件与关联后的文件分开保存；原注释、坐标、序列字节不改。已有来源绑定与所选文件冲突会报错，不覆盖原值。位置、部件、置信度、口袋和矩阵仍来自原注释；不从 B-factor、文件名或几何自动推测。已有一套不同注释不会静默替换，当前需在新项目中保留不同注释版本。

输入仅含文件选择、保存版本和明确序列记录名。SHA 的生成及来源/权限校验在后端，不要求用户复制这些码。调用使用现有 ImportView 与草稿确认流程，不增加另一套运行/审批状态；相同有效关联重复操作返回已有文件，前端不重复添加同一文件。

提取并复用同一注释验证函数，已有 sidecar 读取和新绑定预览都使用它：模型/链/残基/插入码、参考残基身份、序列位置和氨基酸、置信度语义/工具版本、原始刚体矩阵、授权和封存字节。缓存命中仍验证源与依赖，没有以显示标签代替后台身份规则。

## 已完成的验证

最终运行代码 `3307a72`，功能模块 `cbafa54` 及前端测试类型修复 `3307a72` 分别提交推送。

| 检查 | 可声称结果 |
| --- | --- |
| 服务器全 Python/作者数值回归 | 683 passed，0 failed/error/skipped，63.74 s；强制提供封存作者原件。全部科学数值仅在服务器执行。 |
| 本机定向软件/格式验证 | 52 passed；其中新增绑定 15 项，包括原件、确认/幂等、冲突绑定、越权、旧版本、篡改、错误序列/残基、错误矩阵/语义和已有不同注释拒绝。未运行求解器。 |
| 前端组件 | 44 passed；文件名可读、不要求 SHA、显式序列记录名、忙碌/未保存时不绑定。 |
| 生产 dist + HTTP 浏览器 | 12 passed，0 failed/skipped/flaky；实际完成文件选择、预览、确认保存、原来源下载一致与已登记置信度零值保留。浏览器原生桥是明示替身，不能代替 EXE 验收。 |
| 科学核心 | 指定 7 个科学文件与原基线字节相同。不是科学正确性的替代证明。 |

新增科学来源为明确声明的解析软件样本，不援引论文充当人工 pLDDT、残基注释或矩阵的来源。新发布继续复核本次服务器真实阶段 M5/F3 产物（合成软件实验，不是湿实验）与此前公开结构；其来源见下一节。

## 来源链接

- 注释合同与新绑定测试：[冻结代码测试](https://github.com/ZincDYX/iGEM-2026-Tsinghua-T-dry-lab/blob/3307a72c0ac28ffbaac2338150154bee04d6afba/tests/test_r13_annotation_binding.py)。人工样本明确标识 SOFTWARE/PARSER_FIXTURE；不冒充工具真实预测。
- M5 与 F3：[实际生产集成测试](https://github.com/ZincDYX/iGEM-2026-Tsinghua-T-dry-lab/blob/3307a72c0ac28ffbaac2338150154bee04d6afba/tests/test_scientific_integration.py)、[有限扫描集成测试](https://github.com/ZincDYX/iGEM-2026-Tsinghua-T-dry-lab/blob/3307a72c0ac28ffbaac2338150154bee04d6afba/tests/test_fresh_design_integration.py)。原嵌套 M5 序列不重新拟合，非正式 F3 指标保持 null。
- 公开结构：[RCSB 3AJO](https://www.rcsb.org/structure/3AJO)、[PDB DOI](https://doi.org/10.2210/pdb3AJO/pdb)、[原结构论文 DOI](https://doi.org/10.1016/j.bbrc.2010.08.017)、[24 链 assembly 1 原件](https://files.rcsb.org/download/3AJO-assembly1.cif.gz)、[BCIF 非对称单元原件](https://models.rcsb.org/3ajo.bcif)、[对应 mmCIF 原件](https://files.rcsb.org/download/3AJO.cif)。复用服务器封存原件，分别为 41,136 原子/24 链和 1,714 原子/1 链，不混称同一 assembly。
- 作者回归：[原 RHS](https://ndownloader.figshare.com/files/55079462)、[参数原件](https://ndownloader.figshare.com/files/55079456)、[Figshare v1 DOI](https://doi.org/10.6084/m9.figshare.29221010.v1)。原文 [Nature Communications](https://www.nature.com/articles/s41467-026-68881-8)；[实测工作簿](https://ndownloader.figshare.com/files/60449912)；全部先前来源索引见[复现报告](glabridin_reference_reproduction.md)和[源清单](glabridin_reproduction_sources.json)。本轮是封存原件回归，不是重新复现整篇论文。

## 发布边界与仍需补充的工作

默认本地；私人服务器、账号和凭据不进仓库。完整主 bundle 和便携 EXE 更新，保留旧版本和旧 bundle。技术指纹在后台及机器可读证据，不要求人在默认界面检查它们。前端仍存在少量异步显示身份比较，不宣称源码彻底没有 SHA 字段；它们不是密码或授权规则。

这一版完成“选择文件、后台生成关联”，不是任意科学注释的可视化创作器或自动映射器。不同注释的项目内切换/替换、任意旧版语义迁移、每种科学表单组合和独立干净 Windows 未确认完整覆盖。

受许可工具按用户决定暂缓；真实条件匹配的 ER/运输、相内活性、表达/动力学测量、标定/独立留出和完整组学/长 MD/湿实验仍需真实输入或资源。任意不可信插件的 OS 权限沙箱未实现；venv 仅依赖隔离。用户现已选择 HTTPS API + 访问令牌，作为下一模块实现；本 r13 不通过匿名连接或私人地址默认值冒充完成。

不声称商业签名、完整安全/法律许可审计或所有生物学验证完成。633 项依赖版本清单、官方 CycloneDX 1.6 校验与 OSV 无版本匹配只是有日期的数据库检查，不是完整安全证明。

## 最终桌面与交付验收

最终 EXE 使用真实原生 IPC，不替换连接。实际注释表单完成源文件上传、保存、选择、关联预览、确认与登记；原 JSON 字节一致，登记 pLDDT=0 保留，未产生科学审批或本机求解。继续验证 M5/F3、24 链公开结构与 BCIF 四种来源，15 个嵌入资源字节一致，默认页不显示原始哈希/UUID/配置路径，无 CSP 违规、外部请求或页面异常。

正常退出和重启后均为 0 个自有残留后台，项目保存状态保留。功能探针总时长 125,293 ms，不能用作纯启动速度基准。独立真实 Windows 文件夹选择另验：仅操作自有 Tauri 窗口关联的系统对话框，未拦截 filechooser、未 setInputFiles；原两份嵌套文件、入口选择、类型化预览、保存通过，运行数 0。

发布目录 `FusionLab-Windows-20261008-r13-3307a72`，ZIP 99,184,642 字节；机器清单 6,622 项，144 个运行源码逐字节验证，无散落 pyc。冻结运行 bundle 含 534 个跟踪文件；源包与前端 16 个 dist 文件在服务器部署后逐字节检查。旧服务器目录保留为备份，不删除数据。

部署范围合计 14,527,171,760 字节，低于 15,000,000,000 字节。范围包含服务器工具/环境/缓存、运行目录及其备份、本机前端环境、venv 和当前便携包；不包含未启用历史发布归档、科学结果及无关工具链，因此不是整台电脑和服务器的全部占用量。本次未检测到启用的旧便携实例，未关闭用户窗口。

首次浏览器测试因默认 Workflow 页未选择 Inputs 而超时，显式选择后通过；组件测试补齐必需 fixture 字段，桌面构建测试回调补为 Promise<void> 后通过。没有通过修改生产科学默认值绕过测试。短时 SSH 断开按原目标重查后重试，最终部署与全回归均验明。失败日志和最终机器证据分别保留。

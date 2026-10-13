# 原始工具对齐与真实调用记录（2026-10-13）

## 结论与范围

SignalP 和 DeepTMHMM 原工具已完成真实服务器计算，并完成软件工作流调用。
这补齐了三条现有完整融合蛋白的信号肽和跨膜检查，**不是完整 M1/M2 验收**。
待用户提供最新输入和要求后再启动依赖构建体版本及实验条件的新计算。
本文不分发工具、权重、私有安装配置、账号资料或下载凭据。

## 实际结果

保持原始序列完整，未补齐、裁剪、替换氨基酸或使用缩减模型。

| 输入构建体 | 长度（aa） | SignalP：信号肽且明确切割位点 | DeepTMHMM：跨膜螺旋数量 |
|---|---:|---|---:|
| OC_deltaN_SH3_cytosolic | 533 | 未检出 | 0 |
| DMT_PDZ_C_terminal | 380 | 未检出 | 0 |
| FUSn_SH3x3_PDZ_FTH1_cytosolic | 796 | 未检出 | 0 |

以上是预测结果，不能证明实际细胞定位、无聚集、自组装或相分离。
SignalP 使用用户确认的 `eukarya`，原始完整 `slow-sequential` 模型。
DeepTMHMM 使用原版学术独立包、原始五模型及作者指定依赖，CPU 执行；
选择硬件没有更换模型或减少模型数量。

## 执行与故障证据

- 分别通过真实 stdio MCP 的 `igem.compute.audit_deployment` 和
  `igem.compute.run_tool` 执行两个工具，解析原工具原生输出。
- 在持久化软件工作区创建独立诊断项目及新私有运行配置，保留旧项目和配置。
  工作流逐条执行两种预测，共六个真实作业成功并解析；绑定实际输入序列，
  保存工作流、原生文件和调用记录，不使用测试夹具冒充预测。
- SignalP 下载标签为 **6.0i**，包元数据为 **6.0+h**，CLI 报 **6.0h**。
  差异原因尚不确定，未修改原工具，也不将版本一致性写成已验证。
- 前两次 BioLib 云端作业报输入文件缺失；SDK/平台的具体根因尚未确定，
  不计为成功。后续成功来自官方学术独立包，不是云端问题已修复。
- DeepTMHMM 首次独立包调用失败是我方适配器将虚拟环境入口解析到基础
  Python，丢失依赖。修复入口保留方式后成功；失败作业保留，回归覆盖真实
  符号链接。另一个薄适配仅协调原 CLI 要求输出目录不存在的契约：保留
  `native` 结果并复制三份小型原生结果文件，不改上游源代码、权重或计算。

SignalP MCP 证据使用代码 `cd826cf`，DeepTMHMM MCP 和六个软件作业使用
`55a32a6`。完整调用、环境锁定、输入身份及失败记录保存在私有验证环境；
公共源码不含服务器连接信息。

## 代码改动

- 部署审计支持显式 `budget_bytes: null`，仍统计实际大小；省略参数仍按
  15,000,000,000 字节检查。用户取消的是服务器上限，不是本地上限。
- 工具目录标记不再将原方案保留步骤误当作可省略步骤，区分原 catGRANULE、
  新版本、PScore 和 PSPredictor，不自动以蒸馏替代原方法。
- DeepTMHMM 薄适配与虚拟环境入口修复；模型计算不变。
- 未修改科学公式、阈值、归一化或模拟长度，未新增另一套作业系统。

## 未完成项及人工输入

| 项目 | 目前实际状态 | 仍需解决 |
|---|---|---|
| TANGO/PASTA | 尚无已验证的原工具安装及正式融合检查 | 原工具许可/下载；有依据的 pH、温度、离子强度、端基，以及热点分数阈值和连续长度。用户将提供最新要求，尚未自行设置。 |
| PSIPRED/JPred | PSIPRED 原版编译成功；JPred 有历史真实 smoke 结果 | PSIPRED 正式 profile/序列数据库路线尚未完成；JPred 不接受小于 20 aa 的输入，不能为短 linker 补齐或截取其他序列代替。 |
| IUPred、SEG、ProtParam | 有已有接口及部分历史真实证据 | 与最新输入逐条对齐，并区别“程序可启动”和“当前软件已调用且有可用输出”。 |
| FuzDrop、原 catGRANULE | 未全部接通真实自动链 | 核实原服务/原模型可用路线，不用 catGRANULE 2 或未确认的同名包替代。 |
| PScore/PSPredictor | 存在作者 PScore 实现及适配；不等同于 PSPredictor | 新输入真实作业及适用范围检查；PScore 对人工融合/裁剪片段属于未验证外推，不能直接认作 LLPS 概率或正式综合排序。 |
| Mpipi/CALVADOS | 有原 Mpipi 接口及历史原生 smoke；不是完整项目模拟 | 明确体系、条件、采样长度等，运行并验证原协议；不能以 smoke 或缩短模拟算完成。 |
| M2 | 已有 ColabFold、FreeSASA、Vina/Meeko 接口及历史真实 smoke | 当前项目完整结构、置信度、口袋/结合位点、装配和招聘几何检查尚未完整完成；参考结构不是当前融合蛋白结构。 |
| 构建体版本 | 已计算的是现有 FASTA | 现有 scaffold 单个末端 FTH1 与原文双端示例不同，等待用户确认最新输入，不自行重排。 |

下载工具、编译成功或历史示例成功不代表表中未完成项已经完成。
本轮没有更新 EXE，也没有把旧后台服务称为已升级；软件真实作业验证使用
明确的新源码及私有配置。科学计算仅在服务器执行。

## 验证

适配器及部署审计的软件单元测试：9 项通过，包含真实符号链接回归；
没有在本机运行科学预测。

源码 `55a32a6` 的两项 GitHub CI 均成功：
[科学契约与安装包](https://github.com/ZincDYX/iGEM-2026-Tsinghua-T-dry-lab/actions/runs/38361788426)、
[锁定依赖的 Windows 源码构建](https://github.com/ZincDYX/iGEM-2026-Tsinghua-T-dry-lab/actions/runs/38361788410)。
这不是官方 GitLab runner 已执行通过的证明。

服务器完整科学及作者回归：**967 项通过、12 项跳过**；独立原生工具环境
回归：**56 项通过**。12 项跳过中，9 项是主环境没有 FreeSASA，这 9 项
已在原生工具环境逐项通过；另外 3 项是 Windows 专属桌面入口测试，
Linux 服务器不适用。不将跳过写成通过，也不将原生 smoke 写成项目完整模拟。
本机另查 Windows 入口：1 项通过、2 项跳过（当前 shell 缺少测试所需的
完整指定版本工具链）；本轮未重新验收桌面构建或更新 EXE。

## 公共原始来源

以下仅列公开来源，不含注册邮件、临时下载链接或服务器地址。

- [SignalP 官方说明及学术分发](https://services.healthtech.dtu.dk/services/SignalP-6.0/)。
- [DeepTMHMM 官方说明](https://services.healthtech.dtu.dk/services/DeepTMHMM-1.0/)、
  [BioLib Python 调用文档](https://biolib.com/docs/using-applications/python/)。
- [PSIPRED 原作者源码与 README](https://github.com/psipred/psipred)，本次编译
  源码提交 `4e8d136076bc0af1534cac053cb54d1ee641571a`；正式 profile 路线
  需要额外检索工具与数据库，原 README 提醒单序列路线不可靠。
- [TANGO 官方许可](https://tango.crg.eu/licensing-and-services)、
  [官方运行参数文档](https://tango.crg.eu/documentation)。示例参数不自动成为本项目条件。
- [PScore 作者在线实现 README](https://github.com/haocai1992/PScore-online/blob/master/README.md)、
  [Vernon 等原始论文](https://elifesciences.org/articles/31486)。
- [原 catGRANULE 服务入口](https://service.tartaglialab.com/new_submission/catGRANULES)、
  [FuzDrop 官方服务](https://fuzdrop.bio.unipd.it/)。服务入口存在不代表原方法已执行。
- [Python 独立运行时官方发行](https://github.com/astral-sh/python-build-standalone/releases/tag/20241002)，
  本次仅用于隔离原 DeepTMHMM 所需 Python 3.8.20。

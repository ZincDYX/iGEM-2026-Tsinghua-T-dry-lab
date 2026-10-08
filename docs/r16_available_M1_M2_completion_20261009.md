# r16：可实际执行的 M1/M2 补齐结果与剩余条件

日期：2026-10-09。科学运行、服务器部署及 Windows 包的冻结运行源码为 `99a8df935a92bb35c6645582666a59f801060894`。后续测试脚本和报告提交不改变这一运行源码。科学数值计算和作者回归全部在服务器运行，本机仅做软件测试、展示、文件核对和打包。

## 结论

本轮完成了原方案中已有明确规则、已有真实工具或输入的下一批步骤：M1 原始硬筛查的持久化调度、JPred 提交与取回、原始 PScore-online 作业、M2 区域置信度/暴露/真实域间 PAE，以及全长主干上下文中的 IDR 检查。没有更换原公式、补长序列、替代受限预测器、猜测实验条件或自动批准证据。

**仍不能宣称完整 M1/M2 已通过。** 11 个 M1 对象均为 blocked；两种融合酶共 10 个模型的新增区域观察也是诊断结果，不是完整 Q1–Q4 验收或湿实验验证。未完成的工具作业、计算条件和功能范围在下文明确列出，不用测试通过来覆盖它们。

## 已完成的代码与实际运行

### M1

- 复用原 DAG、SQLite、快照和原计算函数，增加“便宜否决 → 实际 IUPred/SEG/JPred → 逐条判定”的流程；每条序列 fan-out，判定只接受已登记的上游结果，不接受浏览器填入的任意文件路径或假观察值。
- 便宜硬否决的片段不执行后续工具。序列用途必须明确选择，不通过名称猜测。界面可选择 IDR、酶–配体 linker、主干 linker、rigid linker 和完整融合蛋白。
- JPred 保存每个节点的远程作业号，重试时可继续取回同一作业。客户端退出码 0 不代表已经预测成功：必须取得实际 `.jnet` 和 `.seq`，核对完整输入序列后才能解析。实际遇到 REST 状态接口空响应时，从同一作业的官方已发布结果文件取回，记录取回途径，不换数据。
- 真实运行七条 linker、一个 IDR 和三个完整融合蛋白；片段 IUPred/SEG 有实际原始输出。IDR 和 20-aa linker 的 JPred 原始结果均完成，α/β fraction = 0、longest structured run = 0。其余六条 12-aa linker 不满足 JPred 的长度要求，不能算已完成 SS 预测。
- 接入并实际运行 JFK lab 公开的 **PScore-online 原始实现**，固定源提交 `c919ad5951b0c0ada0a38840065fd151c25f8a4f`。调用原计算函数和原数据库，未修改公式、常量或查找表；仅部署 Python 3 实际需要的作者文件，没有安装不使用的 Python 2 查找表和网页素材。88 个原文件逐一核对，约 56.90 MB。
- 软件工具页现在有 IUPred、SEG、ColabFold、PScore、JPred 五种实际作业入口。配置、凭据、原始运行记录和文件摘要留在后台；前端显示用途、执行状态、结果和缺项，不显示长提交摘要作为用户操作要求。新安装未配置外部工具时，仍明确显示未配置。

| 完整输入 | PScore 原始全局分数 |
|---|---:|
| FUSn_1_214 | 10.79 |
| OC_deltaN_SH3_cytosolic | 0.19 |
| DMT_PDZ_C_terminal | 0.77 |
| FUSn_SH3x3_PDZ_FTH1_cytosolic | 11.32 |

这不是 LLPS 概率、共识排名或实验结果。作者明确提醒：人工序列和蛋白任意片段属于未验证的外推，不能将融合蛋白或截取 IDR 的分数当作已校准的相分离证据。[PScore-online 方法、适用范围和许可证](https://github.com/haocai1992/PScore-online)，[原论文](https://elifesciences.org/articles/31486)。

原始 PScore 逐残基输出末尾有重复编号。未擅自修复；本轮只解析原始全局分数，不把该表作为完整逐残基定位结果。我尚不能确定这是作者输出格式问题还是计算实现问题，也没有独立复现其训练集评估。未声称执行了失效下载链接所指的离线压缩包。

### M2 和主干上下文

- 对 OC 和 DMT 的五个完整序列模型分别计算，共 10 个模型，没有将不同 model 的原子混合，没有裁切序列替代真实融合预测。
- 对酶、linker、配体分别计算 pLDDT、完整上下文 SASA、相同构象下独立选定区域的 SASA 和保留比；这里的独立区域不是实验游离态或另一参考结构，因此不能冒充 Q1 的 pocket reference 比较。
- 对真实区域间的 PAE 子矩阵分别计算两个方向及合并平均，而不是使用全蛋白 mean PAE 充当域间不确定性。
- 核对完整模型序列、完整区域选取、实际 scores/PDB 配对及 PDB pLDDT 的两位小数舍入。无 reviewed burial cutoff 时，burial verdict 保持 null。
- 在正式 M1 被阻断时也能保留明确标记的区域诊断，但不会因此升级 M2 或放行 M3。结果写入已有 M2 记录，前端提供逐模型区域和 PAE 表。
- 实际配体段置信度很低：DMT 的五个配体均值约 21.8–28.7。即使 SASA 保留比看起来很高，也不能据此认定配体正确暴露、能够结合，或据单个低置信构象认定掩埋失败。
- 对完整 796-aa 主干重新运行 IUPred。其 IDR 1–214 的上下文 mean = 0.7992526915887859，disorder fraction = 1，longest folded run = 0。与此前孤立 IDR mean = 0.804039887850467 分开记录。无序预测不证明 FTH1 24-mer 已形成，也不证明 LLPS。

方法来源为用户原始 M1 V3、M2 V2 文档及闭环规范。实际工具来源：[IUPred 作者实现](https://github.com/saezlab/iupred)，[JPred 官方 API](https://www.compbio.dundee.ac.uk/jpred/api.shtml)，[SEG](https://www.ncbi.nlm.nih.gov/IEB/ToolBox/)，[ColabFold](https://github.com/sokrypton/ColabFold)，[FreeSASA](https://freesasa.github.io/python/classes.html)。实际科学工具环境：Python 3.11.15、Biopython 1.85、IUPred 0.1.2、FreeSASA 2.2.1、ColabFold 1.6.2、jpredapi 1.5.6；独立全量回归环境为 Python 3.12.14/Biopython 1.88，未混称为一个环境。

## 更正和真实失败记录

- r15 报告把七条 linker 都描述为短 linker，不准确：实际上六条为 12 aa，主干最后一条为 **20 aa**，序列 `GSTSSGGGGGSGGSGGSGGS`。本轮按实际 20-aa 输入完成了 JPred 作业 `jp_LWHfviG`；原 IDR 作业为 `jp_z1QBBuy`。不是通过补长得到的结果。
- 早期工作目录回归失败包括遗漏测试所需 data/schema、合同文件和前端合同文件；完整冻结源码重新测试后通过。原失败日志保留，不把不完整源码目录的失败归咎于论文数据。
- 一次真实检查脚本错误地导入已安装旧源码，跑到旧统计流程，没有得到新的 M1 判定；修正源路径后，使用冻结源码重新实际执行。失败运行不作为新流程验证证据。
- JPred 状态接口曾返回空响应；官方原始结果文件可取回并核验。其接口为什么间歇返回空响应尚未确定。
- 初次打包使用包含目录项的 Git tar，与现有“bundle 文件成员”打包契约不匹配；保留失败目录，改用逐字节核验的 bundle 文件 tar。没有删除旧发布。
- 首次 native smoke 脚本等待旧的 `backend-*.json` 文件，而现有启动已使用父进程管道。该失败不能证明 EXE 未启动；修正测试后实际验证 API 就绪、认证和进程清理。随后一次启动轮询请求超时也保留，最终测试通过。

## 验证和交付

- 冻结服务器全量回归：**727 passed、2 skipped**，包含要求作者原始参考文件的回归；两项 FreeSASA 测试在无 FreeSASA 的回归环境跳过，不宣称该环境已验证它们。
- 实际工具环境相关测试：**23 passed、0 skipped**，包含真实 FreeSASA 和新区域计算。协议夹具测试不冒充生物学或真实预测验证；真实工具作业另有原文件和运行记录。
- 前端：**56 tests / 21 files passed**；生产构建交互测试 **12 passed**。它们证明软件契约/交互，不证明生物学结论。
- 新 Windows EXE 已构建，完整便携目录实际启动本地 Python、随机 loopback 接口、拒绝匿名请求；关闭 owned desktop 后 Python 后台结束。默认仍是 Local，可选已有 HTTPS API。没有在源码仓库加入私人服务器信息。
- 部署预算：服务器 14,074,814,039 B + 本机独立文件 911,044,366 B = **14,985,858,405 B < 15,000,000,000 B**。不去重路径上界仍为 15,572,808,042 B，保留 PNPM 重复 alias 的计数区别。范围包括指定工具、环境、模型缓存、当前和保留服务器 runtime、本机依赖及当前便携包；不含非活动发布压缩档、科学输出和无关构建工具链，不是整机磁盘占用。
- `FusionLab-Windows-20261009-r16-99a8df9/FusionLab.exe`：需要完整目录，不能只移动 exe；不是带全部预测器/模型权重的科学工具合集。
- `FusionLab-r16-real-evidence-20261009.zip`：239 个记录文件、真实模型/输入/输出及成功和失败日志。JSON/日志中的私人部署路径为明确标记的公开投影；原记录在服务器保留。源码运行 snapshot 和完整 SQLite 账本不冒充无敏感信息的公共文件。
- `iGEM-drylab-codebundle-r16-runtime-99a8df9.md`：冻结运行源码，567 个文件、6 个 pinned submodule；主 `iGEM-drylab-codebundle.md` 更新到最终报告/测试提交，所有运行代码相同。

## 仍需要解决，不能称作完整复现

| 部分 | 当前缺项或不能直接下结论的原因 |
|---|---|
| M1 完整融合筛查 | SignalP、DeepTMHMM、TANGO/PASTA 的实际完整序列输出；实际 DNA 的禁用位点清单及对应审查 |
| 短 linker SS | 六条 12-aa 原序列不适用于当前 JPred；不能用不可靠单序列 PSIPRED、padding 或拼接自动替代 |
| 风险和共识排名 | 尚无全部 FuzDrop/catGRANULE/PSPredictor 等真实输出，以及原方案未明确的风险方向、归一化/评分规则；PScore 一项不等于整条排名链完成 |
| Q1 | 完整 reviewed core/pocket/residue mapping、明确参考构象；功能锚点不是完整口袋。现有 RMSD/SASA 计算器不通过填锚点伪造完整计算 |
| Q2 | 已有真实区域观察，但低置信配体及缺少明确掩埋判据不能产生通过结论；完整主干各招募域还需适用构象 |
| Q3/Q4 | 真实融合的 24-mer 适用性、模板放置/相对位置、具体位点冲突图和构象证据；现有几何/精确 co-occupancy 工具不能用假位置自动构造“成功组装” |
| 项目 docking/体积/动力学 | 对应底物、cofactor、质子化、box、体积定义、溶液/粗粒化条件和适用构象；不把官方 Vina 例子的条件填进本项目 |

这些既有数据/授权缺项，也有未完成的自动化链；本轮没有把所有未完成项都解释成许可证问题，亦没有声称完整 Q1–Q4 自动化已完成。多文档生命周期等 r15 已列出的界面事项也不由本轮科学测试自动关闭。

DeepTMHMM 不是一律需要购买商业许可证：官方公开服务可免费使用，学术本地副本有相应获取途径；本项目缺的是可实际执行的对应路由/账户或安装资料，不能把软件包存在当作授权和作业成功。[DTU 官方说明](https://services.healthtech.dtu.dk/services/DeepTMHMM-1.0/)，[BioLib Python 使用方式](https://biolib.com/docs/using-applications/python/)。SignalP/TANGO/PASTA 等仍须遵守各自条款；未提供可用材料时不伪造输出。

论文及参考数据来源继续使用原输入包逐文件下载记录和 r15 `source_links.md`，包括[光甘草定论文](https://www.nature.com/articles/s41467-026-68881-8)、[作者公开数据目录](https://api.figshare.com/v2/articles/29221010)、[仿真原代码](https://ndownloader.figshare.com/files/55079462)、[仿真原数据](https://ndownloader.figshare.com/files/55079456)、[1CKB](https://www.rcsb.org/structure/1CKB)、[2PDZ](https://www.rcsb.org/structure/2PDZ)、[2FHA](https://www.rcsb.org/structure/2FHA)。下载或采用结构不等于已经验证其适用于当前全部融合设计。

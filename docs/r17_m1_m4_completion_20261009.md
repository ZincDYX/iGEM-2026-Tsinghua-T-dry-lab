# M1–M4：补齐的计算流程，以及需要人工提供的材料

日期：2026-10-09。依据用户提供的 M1 V3、M2 V2、M3 LLPS 和 M4 原方案。科学计算和数值回归只在服务器执行；本机只做界面、打包和启动检查。

## 先说结论

本轮把已有明确定义的下一批缺失流程写成了可调用代码，并接入真实 stdio MCP 和项目计算链。**不是所有原方案项目作业都已经完成，也没有得出完整通过 M1–M4 的候选。** 缺少原始工具输出、实验数据或计算定义的地方仍明确阻断，未填假值，未换模型，未把合成测试当作实际工具作业。

| 模块 | 本轮补齐 | 当前不能直接宣称完成的部分 |
|---|---|---|
| M1 | SignalP 6、DeepTMHMM 1、TANGO 原生文件解析；全长融合体三类工具持久化作业节点；实际命令执行记录；软风险计数；四种原始预测器的审核后归一化、共识和三键排序；linker 独立 checklist，不造总分；原始文件随项目保存 | 三种全长工具真实作业尚未执行；完整四预测器输出不齐；部分风险/评分定义不明确；12-aa linker 不能交给最短 20-aa 的 JPred |
| M2 | Q1 同一核心对齐后的 core/pocket RMSD 和同参 FreeSASA；Q2 尾部/配体诊断；Q3 实际融合单体向组装模板扩展；Q4 双模板变换移动整个酶、真实原子碰撞、上下文口袋 SASA、物种特定冲突图与精确共占位；多构象分别保留；计算请求接入项目 | 缺完整、确认过的核心/口袋和编号映射、实际组装适用性及几何判读规则。功能锚点不能替代完整口袋，模板扩展不能证明实际 24 聚体形成 |
| M3 | 原 S1–S5/E1–E10 求解器基础上，接入有真实来源的多价修正和表达/浓度不确定性传播；同一参数登记表绑定；能量单位换算；保留未通过样本 | 缺同构建、同实验条件的蛋白浓度、相分数、Kd/Kfree、体积定义及必要多价修正数据。原容量缩放和守恒矛盾未擅自修复 |
| M4 | 原 10 反应竞争分母、分相通量和稳态求解器基础上，完成匹配的 H0/仅招募/定向分配三对照、逐样本 H0 相对产率、LHS 不确定性、原灵敏度和稳健性、1/2/3/4/6 整数支架重跑 M3 后扫描、候选 Kp 可实现性原始报告 | 缺完整适用动力学/Kp、底物输入和真实出口条件；表达成本公式未定义。原 PTR/PT 浓度基准歧义及新增分相活性模型的 H0 不明确，不能自动假设 |

以上扩展复用既有求解器、工具执行适配器、参数登记表和持久化工作流；没有另造评分引擎、调度器或前端校验码系统。预测器或构象诊断不自动升级正式候选状态，M4 不输出所谓“最佳设计”结论。

## 实际验证，和不应混淆的测试

- 服务器全量回归：749 passed、9 skipped，要求作者原始参考文件可用。9 项是该回归环境缺少可选 FreeSASA 的测试，不能当作通过。
- 在已装真实科学工具的另一个环境，相关测试 52 passed、0 skipped，包括真实 FreeSASA 计算和真实 stdio MCP 调用。合成坐标/输出格式夹具只验证程序逻辑，不是 SignalP/DeepTMHMM/TANGO 真实预测。
- 原全长 796-aa 支架新增真实 ColabFold 作业，五个配对完整结构和置信度文件。用真实 stdio MCP 对五个模型计算区域 pLDDT、SASA 和域间 PAE。SH3 与 FTH1 区域置信度较高；全段 PDZ_extended 均值约 60.8–64.1；IDR/linker 低置信，不能因此硬淘汰，也不能据此认定组装姿态正确。PDZ_extended 含延伸段，均值不能直接当作折叠核心置信度。
- 本轮曾发现并修复两个真实代码错误：M1 原始 PScore 解析覆盖其他预测器字典；M2 误把构建名称当作 ColabFold 文件前缀。后者在实际支架计算中暴露，修复后仍核对完整序列及 scores/坐标文件配对。
- 最后补上预测参考本身的 core/pocket 置信度检查；低置信参考不能因融合体高置信而通过 Q1。该判据有独立合成置信度 oracle，未伪装成真实预测。
- 一次全量测试没有在 PATH 加入已安装的 Node，失败日志保留；补正确测试环境后重跑。未修改科学规则以让测试通过。
- 外部工具和缓存没有新增安装。本轮不包含项目特异的小分子 docking、长时间 MD、原始 Mpipi 相图作业、许可预测器真实作业或湿实验复现。

## 软件交付与实际作业状态

- 运行源码冻结在 `cc2e8eb38d0765751d390495f3f00314a8b1294c`。此后的报告更新不改变运行代码。最终冻结服务器回归为 749 passed/9 skipped 和实际工具环境 52 passed/0 skipped。
- 实际 M1 DAG 已重跑，11 个对象仍 blocked；原始 PScore 的 IDR/OC/DMT/全长支架结果分别为 10.79/0.19/0.77/11.32。不能把这些预测值说成 LLPS 概率或完整排名。该批实际作业及区域计算执行源码为本轮较早的 `96e1a6a`，与最终新增的预测参考 Q1 置信度回归分开记录。
- 前端 56 项测试、12 项生产构建交互测试通过。Windows 原生包实际启动本地 Python、随机 loopback API；匿名访问被拒绝；关闭 owned desktop 后后台退出。默认仍为 Local，已有 HTTPS API 和访问令牌只作用户自选配置。
- 服务器 runtime 已按冻结源码更新，583 个源码文件与 16 个前端资源逐字节核对。没有在仓库加入私人服务器地址、别名或路径。
- 本轮先核对旧备份无运行进程，再压缩、验证后退役两个旧 runtime 目录；完整恢复归档保留，未删除用户科学数据。一个仍被使用的更早备份未动。部署大小与最终便携包核验另见发布验证文件，范围不含非活动发布压缩档、科学输出和无关构建工具链，不是整机占用。
- 主 `iGEM-drylab-codebundle.md` 包含最终提交的后端、科学计算、MCP、工作流、前端、桌面壳、测试与说明；冻结运行 bundle 另留，避免把仅报告的新提交误说成实际科学作业源码。

## 你需要人工做什么

### 1. 先提供三类全长筛查工具的合法材料或原始结果

**不必同时购买所有工具。** 你可以选择“给本地软件包”或“在官网跑后下载原始结果”，我负责后续配置和导入。提交的必须是实际完整融合序列，不能只跑 linker。

| 工具 | 你最少需要做什么 | 给我的材料 |
|---|---|---|
| SignalP 6 | 到 [DTU 官方页面](https://services.healthtech.dtu.dk/services/SignalP-6.0/) 使用网页预测；本地包需在 [官方学术申请表](https://services.healthtech.dtu.dk/cgi-bin/sw_request?packageversion=6.0i&platform=slow_sequential&software=signalp&version=6.0) 填姓名、职位、大学/机构邮箱和单位，并自行阅读、接受协议，下载链接发往该邮箱 | 原始 `prediction_results.txt`、实际输入 FASTA 和版本；或者将合法安装包放到许可允许的私有部署位置，提供路径。不要只给截图，不要公开转发原包或提交仓库。许可不自动允许商业平台服务或跨机构再分发 |
| DeepTMHMM 1 | 可先用 [官方 BioLib 网页](https://dtu.biolib.com/DeepTMHMM/) 跑完整序列；若要账户 API 自动作业，按 [BioLib 官方说明](https://biolib.com/docs/using-applications/python/) 登录并创建 token，只配置在用户私有环境 | 原始 `predicted_topologies.3line`、输入 FASTA、实际版本；或可用的私有 API 访问配置。公开服务免费用于学术和商业；商业自托管另有许可，不是所有情况都要买许可证，见 [DTU 说明](https://services.healthtech.dtu.dk/services/DeepTMHMM-1.0/) |
| TANGO 或 PASTA 2（二选一） | 优先按 [TANGO 官方许可入口](https://tango.crg.es/licensing-and-services) 获取学术/非营利研究材料并接受对应协议；PASTA 可经 [ELIXIR 官方服务目录](https://www.elixir-italy.org/services/pasta/) 找入口，但其当前下载站与条款未确认 | TANGO 合法可执行程序及原始逐残基输出，或 PASTA 原始结果待人工审核。PASTA 原生版本解析/自动作业仍未验证，不能承诺给账号就已跑通 |

TANGO 还需你确认实际 pH、温度、盐条件、N/C 末端状态和“高聚集分数/连续长度”的判读定义。原方案没有完整定义这组阈值，不能擅用官网经验值替你批准。账户密码和 token 不要发在聊天或写入仓库。

### 2. 原始 IDR 排名还缺输出和明确的规则

- [FuzDrop 原始服务](https://fuzdrop.bio.unipd.it/tutorial)：提供真实原始结果及实际输入；官方稳定自动 API 本次未确认。
- [原 catGRANULE 2016](https://service.tartaglialab.com/static_files/shared/tutorial_catGRANULES.html)：提供原始结果；没有用 catGRANULE 2 偷换原模型。
- PSPredictor/PScore 二选一时，原始 PScore 已能实际使用，不需要你再下载；它不支持小于 140 aa 的原始序列。
- [原始 Mpipi 论文与代码声明](https://pmc.ncbi.nlm.nih.gov/articles/PMC7612994/) 指向 [作者 Figshare](https://doi.org/10.6084/m9.figshare.16772812)。本次该下载 API 返回 403，是否暂时故障不确定。原始 LAMMPS 参数、运行脚本和项目温度/盐/链数/盒子/模拟时长/重复及分数定义仍需确认；只支持外部命令并不等于已完成原始 Mpipi 的项目模拟链。若你能打开入口，给作者原包即可，不要求购买第三方实现。
- 需要确认尚未明确的风险方向、charge blockiness/多价密度算法、归一化区间、权重、共识阈值及三项排序键顺序。现有政策输入支持这些明确规则，但不擅自决定科学定义。
- 12-aa linker 的二级结构方法需单独确认；不能靠 padding、拼接或改成另一个预测器的分数解除原方法缺项。

### 3. M2–M4 主要缺科学输入，不是账号

- 最终真实蛋白/编码 DNA、构建对应关系和禁用 DNA 位点清单。没有 DNA 就不能做真实禁用位点审查。
- M2：酶/招募域/组装核心的完整残基选择、参考编号映射、完整口袋、适用参考结构/构象、实际 24 聚体的依据，及碰撞/掩埋/体积的明确方法。新增代码已经接受显式映射，不需要你写几何代码。
- 如做项目 docking：实际底物 SDF/SMILES、cofactor、质子化和 box 定义。Vina 已可用，不必另外注册账户；对接分数不是 Kd。
- M3：蛋白实际浓度、相分数或饱和/稠相浓度、结合 Kd、游离分配系数、占位/组装证据和体积；qPCR 不能当作蛋白浓度代入。
- M4：10 个反应对应的 kcat/Km、代谢物 Kp、底物输入、出口/回流等原方案条件，以及来源、单位、构建和实验环境。不能拿论文示例值替代当前构建。更正：r17/r18 并没有完整 ER 锚定求解器；现有胞内/胞外运输代码不是 ER 模型。ER 的膜几何、招募及代谢耦合需要独立实现，也需要匹配的区室、运输及活性数据，不能仅归为缺数据。

这些材料不一定全要你从零测量：可先提供团队已有表格、论文依据或原始文件，由我整理成现有输入格式；缺少适用数据的项目则确实需要实验或你确认允许的假设，不能由软件编造。

## 开发者入口（你不用手写这些）

- M1 原生结果：`igem.m1.import_fusion_results`；审核政策排名：`igem.m1.prioritize`。
- M2：`igem.m2.compare_enzyme`、`igem.m2.expand_fusion`、`igem.m2.place_recruitment`、`igem.m2.recruitment_ensemble`。项目 `stages.m2_fusion.calculation_requests_file` 的数组元素为 `{kind, candidate_id, payload}`；kind 取 `enzyme_comparison`、`assembly_expansion`、`recruitment_geometry`、`recruitment_ensemble`，payload 与相应 Pydantic/MCP schema 相同。相对文件路径基于请求文件目录，原始依赖随运行 snapshot 保存。
- M3：`igem.m3.solve_equilibrium`、`igem.m3.ensemble`；项目可选 `avidity_sh3/avidity_pdz` 绑定经过审核、同 binding_pair 的参数记录，`uncertainty` 明确数据范围和独立性来源。
- M4：`igem.m4.report` 复用 `igem.m4.solve_steady_state`；选填实际整数支架设计和完整候选 Kp 谱，不自动给设计排名。
- 后台私有 runtime profile 才能配置外部命令与工具版本，浏览器和 Agent 不能发任意安装/执行命令。原生导入写文件接口不加入任意前端工具白名单。

工具和结构来源：[ColabFold](https://github.com/sokrypton/ColabFold)、[FreeSASA](https://freesasa.github.io/python/classes.html)、[JPred](https://www.compbio.dundee.ac.uk/jpred/api.shtml)、[SignalP 原生格式](https://github.com/fteufel/signalp-6.0/blob/main/installation_instructions.md)、[TANGO 原生说明](https://tango.crg.eu/documentation)、[1CKB](https://www.rcsb.org/structure/1CKB)、[2PDZ](https://www.rcsb.org/structure/2PDZ)、[2FHA](https://www.rcsb.org/structure/2FHA)。原文复现依据仍为 [光甘草定论文](https://www.nature.com/articles/s41467-026-68881-8)、[作者数据目录](https://api.figshare.com/v2/articles/29221010)、[作者代码](https://ndownloader.figshare.com/files/55079462)、[作者数据](https://ndownloader.figshare.com/files/55079456)。采用这些来源不等于证明它们适用于当前全部设计。

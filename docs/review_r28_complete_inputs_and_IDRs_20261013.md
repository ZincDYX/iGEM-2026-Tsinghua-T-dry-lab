# 完整输入、第二轮 IDR 与实际计算记录（2026-10-13）

## 结论

第二轮输入包的 **120 条新 IDR 和 5 条参考 IDR**已加入 M1，保留来源关系，
没有修改、补长、重复或截断序列。加上原输入中的 2 条 IDR，共 **127 条记录、
126 条不同序列**；相同序列的别名不当作独立实验重复。
它们已完成服务器上的原版 IUPred、SEG、描述子及 ProtParam 计算，
并取得原作者 PScore 原始分数。**这些不是完整 M1 通过或正式排序结果。**

科学计算与数值回归只在服务器运行。下载程序、权重、原始研究数据、
私有运行配置及连接信息不进入源码、bundle 或公开发布包。
本机只构建前端、运行软件/格式检查、读取导出文件及检查浏览器显示。

## 输入范围和身份

| 输入 | 实际处理 | 不作出的推断 |
|---|---|---|
| `M1_M2_linker_candidates_complete_20261013.zip` | 校验原包清单；568 个原文件保留；配置、构建体、基线、IDR、linker 及来源关系共同导入，147 条项目序列 | 不重复绑定历史预测目录中的 FASTA；不把文件名当成蛋白身份 |
| `secondround-wetlab(1)(1).zip` | 18 个原文件保留；120 条新增 IDR 的 FASTA 与工作簿氨基酸列逐条一致；5 条参考 IDR 从工作簿明确列提取，新增125条项目序列 | 不把包中模型分数、优先名单或 CALVADOS 报告当成本轮原工具复现或湿实验验证 |
| 两包合并 | 272 条项目序列；127 条 IDR 记录 | 不把127条记录说成127条不同序列 |
| 第二轮蛋白 GenBank | 按文件声明的蛋白类型解析，保留蛋白特征 | 不误读为 DNA，不编造 CDS |

第二包的120条完整融合、优先/备用子集和对照也保留原始文件；本轮按用户要求
绑定其 IDR，不将重复子集再次当作独立 IDR，不自行启动120条新融合的 GPU 预测。
原始构建体文件名与实际蛋白不一致的情况同时保留原文件与序列身份。
部分原 ZIP 中文文件名显示异常，原 ZIP 字节未改写；此处不声称已确认文件名编码，
不以异常文件名决定序列身份。

## 真实完成的计算

| 计算 | 完成数量 | 结果范围 |
|---|---:|---|
| 描述子、Biopython ProtParam | 272 条 | 采用输入包的 M1 描述子定义；分子量、理论 pI 和组成等原始观察 |
| 作者原版 IUPred，long 模式 | 272 条 | 原生逐残基输出、解析值和执行记录均保留 |
| 原版 NCBI SEG，默认参数 | 272 条 | 原生掩蔽结果、低复杂度位置和比例均保留 |
| 作者 PScore | 127 条 IDR | 原始分数；不解释为 LLPS 概率，不生成正式排名 |
| 原版 SignalP 完整模型与原版 DeepTMHMM 五模型 | 各91条完整融合 | 完整序列真实调用并解析；SignalP 使用已确认的 eukarya；不代表聚集或湿实验定位验收 |
| ColabFold 1.6.2 原生 GPU 预测 | 8个主构建/基线，40个模型与置信度文件配对 | 精确完整序列，原生五模型，不减少模型数量；未启动73条 linker 候选融合的大规模 GPU 后筛选 |
| 原版 DSSP 4.5.8、区域 SASA/PAE | 40个实际模型 | 完整融合上下文辅助证据，明确禁止用其替代孤立片段的正式 M1 二级结构否决 |
| 实际完整融合的24聚体坐标准备 | 3个 scaffold ×5模型 | 15份全原子融合副本，按所给模板和逐残基映射变换；仅条件构型，不证明真实自组装或 ER 膜兼容性 |

IUPred 下载采用官网当前直接指向的作者 GitHub 路线；用户已接受学术条款，
没有虚构不存在的注册表单。PScore 作者明确说明人工序列和任意截取片段属于
未验证外推，因此本轮只保留原始分数及适用性说明。
[IUPred 官方下载](https://iupred2a.elte.hu/download_new)、
[PScore 原作者 README](https://github.com/haocai1992/PScore-online/blob/master/README.md)。

SignalP 的下载标签/包元数据/CLI 版本差异仍未确定原因，沿用原工具记录，
详见[上一轮工具记录](review_r27_original_tools_20261013.md)，不修改原程序。

## 结果交付与软件实际验收

私有结果包 `M1_IDR原始结果_20261013.zip` 包含：

- 127条 IDR 的汇总 CSV：来源、同序列别名、原始计算值和氨基酸序列。
- IUPred 逐残基 CSV，以及每条 IDR 的 IUPred、SEG、PScore 原生文本。
- 126条不同序列的描述性分布图，紫色显示；没有人为归一化、加权或排序。
- 使用说明和公开来源链接。程序、权重、账号及服务器连接信息不在其中。

汇总 CSV 的每个数值与持久化后台记录逐项一致，没有先四舍五入再导出。
新工作区保留旧运行快照和配置，另选整合后的私有运行配置，使已安装工具可以
被当前软件调用；没有将配置安装到公开源码。

真实浏览器验收已完成，而非仅单元测试：

- 查看120条 IDR FASTA，分别确认100条与20条分页和最后一条候选。
- 查看127行实际结果表和真实数据分布图。
- 从软件导出汇总表，下载字节与服务器产出的 CSV 完全一致。
- 导入40个真实 ColabFold 模型及其40个置信度文件；打开实际模型并鼠标旋转，
  验证图形画布产生变化。坐标显示不推断活性，也不把未链接的 B-factor 当成 pLDDT。
- 在工具页选择新增 IDR `NL_LOCAL90_001`，完成 Review → Accept → Run，
  原版 IUPred 在服务器真实执行并显示完成，无浏览器脚本错误。
- 用真实 MCP stdio client/server 调用 `igem.m2.secondary_context` 处理实际
  项目模型及原生 DSSP 输出，结果与已保存的原生计算完全相同。

浏览器验收使用源码 `523361d` 与本轮构建的前端；后续 `8d934e3` 只将实现
指纹留在后台 provenance，并将源代码运行版本改成可读标签，另有服务器回归。
本轮没有更新 EXE，也没有将旧 EXE 称为已包含本轮修复。

## 代码修复和失败记录

- 有选择地合入原 IUPred、GPU 准备及 ER 定位传递补丁；冲突的旧补丁未盲目覆盖。
- 合并完整输入使用同一个持久化导入事务；支持实际包的文件数量和总大小，
  不增加另一套导入/作业系统。证据附件保存原始内容，预览不回显私有执行路径。
- 蛋白 GenBank 解析修复和相应软件测试，避免把蛋白当 DNA。
- 已有软风险实现接入明确提供的策略，缺少科学策略时返回具体缺项；
  不新增权重、热点阈值或默认综合排名。
- 原生 M2 比较计算的已算指标进入正式指标输入，缺少的 Q3/Q4、口袋体积、
  招募/膜约束等仍为空；多模型选择不偷偷取最后一条或最好的一条。
- 完整融合 DSSP、实际融合模板副本和候选口袋准备提供真实 MCP 接口；
  候选口袋需要有来源的姿态、接触规则和审核，不能以功能锚点代替完整口袋。

本轮真实验收暴露并修复了证据预览泄露运行路径、蛋白 GenBank 类型误判、
源代码环境没有安装分发元数据却被版本读取要求的问题。扩大合理上传容量后，
旧测试仍写死20MB拒绝门槛；改为检查当前上限之前即拒绝读取，保留原安全意义。

装配准备先后遇到 CIF 多字符链名不能写成 PDB 单字符链名、按部件起点换算映射
偏一位的问题。最终采用明确链名映射及输入包逐残基位置，逐位核对氨基酸身份。
失败/错误映射的旧尝试保留但不作为有效结果；最终坐标恢复原 CIF 链身份，
不擅自放置膜平面、厚度或方向。

## 验证与未完成项

源码 `8d934e3` 的服务器完整科学及作者回归：**985通过、13跳过**；
独立真实工具环境回归：**58通过**。跳过不计为通过；本轮前端源码构建成功。
这不是完整项目 M1/M2 科学通过，也不是官方 GitLab CI 已通过的证明。

| 仍未完成 | 当前缺项/下一步 |
|---|---|
| 完整 M1 二级结构证据 | 127条 IDR 的正式 PSIPRED/JPred 结果未取得；12 aa linker 与大于800 aa完整融合不允许补长或截断；DSSP上下文仅辅助 |
| TANGO/PASTA | 仍需可用原工具；实验/文献条件和热点分数/连续长度未定稿，不采用示例值 |
| 原 FuzDrop、原 catGRANULE 与全部原方案 LLPS 步骤 | 未完成当前输入的真实自动链；不能以新版本、输入包上游排名或 PScore 替代 |
| 风险与组合排序 | 用户明确选择先跑确定性数据；软风险方向、归一化、权重和聚集热点仍待定稿 |
| 正式 M2 | 完整 M1、审核过的口袋、配体/伙伴姿态及招募几何、ER膜坐标/体系等尚未齐备；已有模型/SASA不能替代这些证据 |
| 项目原 Mpipi/CALVADOS 模拟 | 完整协议和物理条件尚未确定、当前项目全链未运行；历史smoke与包内报告不算本轮复现 |
| 更新 EXE及桌面验收 | 本轮未执行；已有桌面包不代表最新源代码 |

因此本轮可以交付原始计算结果和真实可用的软件调用路径，不能宣称已经筛出
可直接用于湿实验的最优 IDR 或已经证明 ER 锚定自组装可行。

## 公共原始来源

用户提供的两个 ZIP 是本轮序列及构建/来源关系的直接输入，原件保留在私有
工作区；公开源码不包含这些原始研究数据。公开工具与参考结构来源如下：

- [IUPred 官网](https://iupred2a.elte.hu/download_new)、
  [本轮固定作者版本](https://github.com/doszilab/iupred2a/tree/ab0115546af598c4a85807616620ea462ea95983)。
- [NCBI SEG 源码](https://www.ncbi.nlm.nih.gov/IEB/ToolBox/C_DOC/lxr/source/algo/seg/)。
- [Biopython 1.85 ProtParam](https://biopython.org/docs/1.85/api/Bio.SeqUtils.ProtParam.html)。
- [PScore 原作者实现](https://github.com/haocai1992/PScore-online)、
  [原始论文](https://elifesciences.org/articles/31486)。
- [SignalP 6 官方](https://services.healthtech.dtu.dk/services/SignalP-6.0/)、
  [DeepTMHMM 官方](https://services.healthtech.dtu.dk/services/DeepTMHMM-1.0/)。
- [ColabFold 原作者源码](https://github.com/sokrypton/ColabFold)、
  [DSSP 官方源码](https://github.com/PDB-REDO/dssp)、
  [FreeSASA 原作者源码](https://github.com/mittinatten/freesasa)。
- [RCSB 2FHA](https://www.rcsb.org/structure/2FHA)、
  [2PDZ](https://www.rcsb.org/structure/2PDZ)、[1CKB](https://www.rcsb.org/structure/1CKB)。
- [JPred 官方 API](https://www.compbio.dundee.ac.uk/jpred/api.shtml)、
  [PSIPRED 作者源码](https://github.com/psipred/psipred)、
  [FuzDrop 原服务](https://fuzdrop.bio.unipd.it/)、
  [原 catGRANULE 服务](https://service.tartaglialab.com/new_submission/catGRANULES)。
- [TANGO 原工具](https://tango.crg.eu/)。这些待完成步骤的链接不是已成功执行的证明。

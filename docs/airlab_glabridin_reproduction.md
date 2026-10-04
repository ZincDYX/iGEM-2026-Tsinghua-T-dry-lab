# 光甘草定论文计算复现、来源追溯与问题诊断报告（2026-10-04）

## 摘要与结论

本报告对应 Zhang 等的 *Discover the maze-like network for glabridin biosynthesis*（Nature Communications 17, 2215；DOI 10.1038/s41467-026-68881-8）。已完成公开计算模型的轨迹/诱导扫描复现、12 组酶动力学重拟合及 Fig. 4d/e/f/i 已发表实测数据的重分析；**不是整篇论文的完整复现，也不是重新完成湿实验**。

独立使用作者原始参数读取器后，其参数与项目解析器全部一致，作者 `one_step` 与项目适配器全部状态逐点差为 0，Fig. 4h 源表最大浓度差约 3.047e-13 M。现有证据不支持“我们把作者原始模型抄错/读错”的判断；也不能由此证明生产 M1–M4 模型的科学有效性。

作者发布材料存在可确认的文字/代码/标注不一致；运输参数的编号映射高度可疑，但到底源表标签错还是模型参数错仍不确定。没有足够证据认定原始湿实验数据错误。本报告撤回旧版对 S5i 单位的误判，并明确动力学拟合误差的比较口径。

原始计算部署基准提交：`5136799ae6ca5cc60d2c65c79668cc871cc0b052`。本次报告及诊断脚本的提交由当前 Git 历史和 bundle 页首记录，避免报告内嵌自身提交哈希的循环依赖。

## 计算位置与版本

所有本次正式复现、拟合、后端测试、前端构建和 MCP 实际作业均在 **air-lab** 执行；本机仅编辑、传输和记录代码/报告。

- 新版完整项目源码：`/mnt/data/dyx/drylab-m1m4-runtime`，包括 M1–M5、工作流、MCP、插件运行时、React/TypeScript、Tauri 源码、测试、配置和示例。
- 旧入口 `/mnt/data/dyx/lkdagent/drylab` 指向新版；两个旧代码目录以时间戳归档至 `/mnt/data/dyx/drylab-code-archives/`。原有 Git 工作改动、`.env`、输入和约 8 GB 输出保留，不删除实验数据。
- 原文文件与计算结果：`/mnt/data/dyx/glabridin-reproduction/`。
- 隔离的原文数值环境：`/mnt/data/dyx/drylab-envs/glabridin-reference`。使用 Python 3.11、NumPy 1.24.4、SciPy 1.10.1、Matplotlib 3.7.5、OpenPyXL 3.1.5；实际传递依赖见服务器 `environment.lock.txt`。
- 作者方法记录的是 Python 3.8.5；本次没有声称解释器版本或结果逐比特一致。
- 正常项目环境仍是 `/mnt/data/dyx/miniconda3/envs/drylab-m1m2`，新版源码通过 editable 安装指向当前运行目录。

第三方 Git 子模块的地址和提交保留在源码/部署清单中；未把所有可选第三方项目、数据库和模型重新下载为离线镜像。已有工具、ColabFold 权重和环境保留。Tauri 源码已部署，但本次没有编译服务器桌面壳、生成 Windows 安装包或执行浏览器端到端测试。

## 数据源头链接、用途与不可变性

论文：[正文页面](https://www.nature.com/articles/s41467-026-68881-8)、[DOI](https://doi.org/10.1038/s41467-026-68881-8)、[正文 PDF](https://www.nature.com/articles/s41467-026-68881-8.pdf)。若页面因 cookie 限制打不开，可用[出版社页面的兼容入口](https://www.nature.com/articles/s41467-026-68881-8?error=cookies_not_supported)。

### A. Figshare 作者发布包（版本 1，9 个文件）

记录：[固定版本 DOI](https://doi.org/10.6084/m9.figshare.29221010.v1)、[公开记录页面](https://figshare.com/articles/dataset/_b_Discover_the_Maze-like_Pathway_for_Glabridin_Biosynthesis_b_/29221010)、[元数据 API](https://api.figshare.com/v2/articles/29221010)。原始 API 元数据保存在服务器 `raw/figshare_metadata.json`。

| 原始文件及直链 | 本次实际用途/状态 |
| --- | --- |
| [simulation-network-glabridin-final.py](https://ndownloader.figshare.com/files/55079462) | 原样导入作者 RHS；独立调用原始读取器和 `one_step`；未修改 |
| [simulation-data.txt](https://ndownloader.figshare.com/files/55079456) | 原始 E、Km、kcat/Km、K、诱导参数；未修改 |
| [Source Data_V2.xlsx](https://ndownloader.figshare.com/files/60449912) | 仿真曲线、12 组动力学、已发表实测重复；48 张工作表均列入清单 |
| [Fig. S14-GgOC1-G.tif](https://ndownloader.figshare.com/files/60449915) | 获取/校验原始图像；未重新完成显微实验或定量分析 |
| [Fig. S14-GgOC1-M.tif](https://ndownloader.figshare.com/files/60449918) | 同上 |
| [Fig. S14-GgOC1-R.tif](https://ndownloader.figshare.com/files/60449921) | 同上 |
| [Fig. S14-GgPT1-G.tif](https://ndownloader.figshare.com/files/60449924) | 同上 |
| [Fig. S14-GgPT1-M.tif](https://ndownloader.figshare.com/files/60449927) | 同上 |
| [Fig. S14-GgPT1-R.tif](https://ndownloader.figshare.com/files/60449930) | 同上 |

直链是官方元数据提供的入口，不代表当前网络一定能直接下载。此前受限文件使用用户已有不可变副本/ZIP 成员，逐文件核对官方 MD5；未把本地重建数据冒充官方下载数据。

### B. 出版社全部附件（包括 Source Data）

下列名称与正文 Supplementary information / Source data 区对应；获取不等于完成附件涉及的实验复现。

| 官方附件直链 | 本次用途/状态 |
| --- | --- |
| [Supplementary Information：MOESM1 PDF](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-68881-8/MediaObjects/41467_2026_68881_MOESM1_ESM.pdf) | 核对 S5 图轴/参数、S18、Table 9 及表注 |
| [Peer Review file：MOESM2 PDF](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-68881-8/MediaObjects/41467_2026_68881_MOESM2_ESM.pdf) | 已获取并记录；不作为本次数值计算输入 |
| [Description of Additional Supplementary Files：MOESM3 PDF](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-68881-8/MediaObjects/41467_2026_68881_MOESM3_ESM.pdf) | 附件目录；不作为本次数值计算输入 |
| [Supplementary Data 1：MOESM4 XLSX](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-68881-8/MediaObjects/41467_2026_68881_MOESM4_ESM.xlsx) | 已获取/记录；未重新处理其组学数据链 |
| [Supplementary Data 2：MOESM5 XLSX](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-68881-8/MediaObjects/41467_2026_68881_MOESM5_ESM.xlsx) | 同上 |
| [Supplementary Data 3：MOESM6 XLSX](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-68881-8/MediaObjects/41467_2026_68881_MOESM6_ESM.xlsx) | 酶基因 accession 来源；未由原始测序重新验证 |
| [Supplementary Data 4：MOESM7 XLSX](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-68881-8/MediaObjects/41467_2026_68881_MOESM7_ESM.xlsx) | 已获取/记录；不宣称完整重建其结果 |
| [Reporting Summary：MOESM8 PDF](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-68881-8/MediaObjects/41467_2026_68881_MOESM8_ESM.pdf) | 研究设计记录 |
| [出版社 Source Data：MOESM9 XLSX](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-68881-8/MediaObjects/41467_2026_68881_MOESM9_ESM.xlsx) | 与 Figshare 工作簿逐单元格比对，排查版本差异 |

### C. 原始组学、代谢组学与模型参数背景入口

| 数据入口 | 本次状态 |
| --- | --- |
| [BioProject PRJNA1390709](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1390709)；[对应 SRA 检索](https://www.ncbi.nlm.nih.gov/sra/?term=PRJNA1390709) | 核对公开存储入口/规模；未执行完整原始测序处理 |
| [基因组 BioSample SAMN54196976](https://www.ncbi.nlm.nih.gov/biosample/SAMN54196976) | 正文给出的基因组样本入口；未重跑组装 |
| [转录组起点 SAMN54221758](https://www.ncbi.nlm.nih.gov/biosample/SAMN54221758)、[终点 SAMN54221940](https://www.ncbi.nlm.nih.gov/biosample/SAMN54221940)、[项目样本检索](https://www.ncbi.nlm.nih.gov/biosample/?term=PRJNA1390709) | 正文记载的 accession 范围；未逐样本复现，未假定编号范围中的记录都已核实 |
| [WGS JBTAOT000000000](https://www.ncbi.nlm.nih.gov/nuccore/JBTAOT000000000)；[组装 GCA_054507355.1](https://www.ncbi.nlm.nih.gov/datasets/genome/GCA_054507355.1/) | 已定位组装入口；不是重新组装得到的结果 |
| [MetaboLights MTBLS13519](https://www.ebi.ac.uk/metabolights/MTBLS13519) | 正文所列代谢组学入口；未完成原始 LC–MS 到峰鉴定/定量的重建；动态网页可访问不等于所有原始文件已成功下载 |
| [Kroll 等，2021，Km 预测论文，正文参考文献 68](https://doi.org/10.1371/journal.pbio.3001402) | 模型 Km 的引用背景；本次没有重跑其预测，也不能确定作者生成 Table 9 的完整输入/单位转换链 |

本次检索未确认到可直接用于完整重跑的 MD 初始结构、拓扑、全部力场输入、随机种子和原始轨迹包，不能凭正文方法或 Figshare 图像宣称这些材料齐全。

### D. 本次直接用到的工作表与原始单元格

以下均来自上方 Figshare `Source Data_V2.xlsx`，不是另一个未说明的数据集。

| 结果 | 源工作表/位置 | 转换与缺失处理 |
| --- | --- | --- |
| Fig. 4h、4g | `Fig. 4h` / `Fig. 4g` 的原始时间及浓度列 | 保留数字字符串表示的时间点；完整 1000 点，不丢弃为零的数值 |
| S18b/c | `Supplementary Fig. 18b` / `Supplementary Fig. 18c` | 比较时分别记录浓度单位；不把时间误差混入浓度误差指标 |
| 12 组动力学 | `Supplementary Fig. 5`；表头行 2、16、30、43，各行块内 3 组数据 | 每个原始重复值保留；源单元格在 `kinetic_observations.csv` |
| Fig. 4d/e | 对应同名工作表；Fig. 4d 的 `N5` 缺失 | 按实际有效重复计算均值/样本 SD；不补零、不插补 |
| Fig. 4f | `B3:G48`；化合物 10/14 为 `D3:E48` | 按实际样本数统计胞外比例 |
| Fig. 4i | 对应同名工作表的原始菌株重复 | 实际有 4 个重复的组按 n=4 记录，不为了图注 n=3 删除数据 |

### E. 原始文件校验

[Figshare 官方记录](https://doi.org/10.6084/m9.figshare.29221010.v1) 的在线 API 元数据与文件 MD5 已核对：

| 文件 | 官方 MD5 |
| --- | --- |
| simulation-network-glabridin-final.py | 43195d5a0ffef38aef774be6e174aa22 |
| simulation-data.txt | 66efd25bea2fe3c4e6d095c44fcb944e |
| Source Data_V2.xlsx | ca6192d3a4c11bc1af975ad24d4a0d37 |

九份 Figshare 文件均有来源记录，下载受限的文件由用户已有 ZIP 提供并与在线官方 MD5 核验；正文、补充信息及补充数据另从出版社下载。19 个文件的 SHA-256、大小、来源 URL 与已有获取方式在仓库 `docs/glabridin_reproduction_sources.json`，服务器对应为 `source_manifest.json` / `results/source_checks.json`。这些是此前获取时的文件版本记录，不意味着本次重新下载了全部文件。

对 Figshare 与出版社 Source Data 的 48 个工作表逐单元格核对：缓存值差异仅在 Supplementary Fig. 2d（出版社补充 63 个系统发育序列信息单元格），本次模拟和动力学数据没有缓存值差异。原始文件不修改。

## 实际复现范围与结果

`scripts/reproduce_glabridin_paper.py` 直接导入作者 `reaction_kinetics`，不复制或重写反应方程。作者 `one_step` 与适配求解结果逐点一致（差异 0）。保留原始 E、Km、kcat/Km、运输参数、诱导门控和初始条件；不将负浓度裁剪为零。

| 发布数据 | 比较范围 | 最大浓度绝对差异 |
| --- | --- | --- |
| Fig. 4h | 1000 个时间点、9 条浓度曲线 | 3.047e-13 M |
| Fig. 4g，GgDMT1，作者既有无门控分支 | 1000 个时间点、9 条曲线 | 1.456e-13 M |
| Fig. 4g，NhPDA1，作者既有无门控分支 | 1000 个时间点、9 条曲线 | 2.426e-13 M |
| Supplementary Fig. 18b | 1000 个时间点、6 个诱导时刻 | 8.972e-10 mM |
| Supplementary Fig. 18c | 完整 500 点诱导时刻网格 | 1.997e-08 mM |

Fig. 4g 匹配需要使用作者代码已有的负诱导时刻分支（`time_ratio=-1`）。这不在文档声明的 `[0,1)` 范围内，**不是**擅自将文档的 `time_ratio=0` 替换后宣称文档正确。两种设置均运行并保存：文档设置的最大浓度误差分别为 4.491e-5 M、1.471e-5 M。这是明确的文档/代码矛盾，实际作者当时使用的运行参数尚不能确定。

对 Supplementary Fig. 5 全部 12 组数据按 `v=Vmax*S/(Km+S)` 做未加权非线性最小二乘拟合：保留每个真实重复值、源单元格和源速度单位；同时输出浓度点均值拟合和全部重复值拟合。参数非负，`curve_fit` 的 `maxfev=20000`，`ftol=xtol=gtol=1e-12`；拟合不是强制匹配论文值。

| S5 面板 | 点均值拟合 Km（µM，四舍五入） | 全部重复观测拟合的 Km 标准误（µM） | 原图 Km 标注（µM） |
| --- | --- | --- | --- |
| a | 32.778 | 4.257 | 32.78 ± 4.26 |
| b | 46.538 | 5.200 | 46.54 ± 5.20 |
| c | 17.385 | 1.513 | 17.38 ± 1.51 |
| d | 182.725 | 47.733 | 186.53 ± 47.10 |
| e | 41.681 | 3.418 | 41.68 ± 3.42 |
| f | 42.369 | 6.042 | 42.37 ± 6.04 |
| g | 30.230 | 4.303 | 30.23 ± 4.30 |
| h | 14.266 | 2.809 | 14.27 ± 2.81 |
| i | 33.815 | 6.049 | 33.82 ± 6.05 |
| j | 21.097 | 4.398 | 21.17 ± 4.68 |
| k | 13.814 | 1.841 | 13.814 ± 1.84 |
| l | 23.333 | 4.538 | 23.33 ± 4.54 |

完整拟合全部重复值与拟合点均值的参数在本数据的平衡重复设计下数值接近，但残差/自由度不同，协方差标准误不同。多数面板的“±”可由全部观测的拟合标准误重现；这支持统计口径解释，不证明作者确实使用了相同软件设置，也不能将拟合 SE 当成生物重复 SD。d、j 剩余差异原因仍未确定，可能涉及未公开的拟合设置/数据选择；差异本身不足以认定原始数据错误。未凭不完整的活性酶定量链推导 kcat。

单位核查与旧报告更正：

- **撤回旧结论**：S5i 的 medicarpin/GgDMT1 图轴与源表均为 µM/h；旧报告将图轴误读为 µM/min，是我们的报告错误，不是论文矛盾。
- **实际存在的标注冲突**：S5f/g 源表头为 µM/min，原图纵轴为 µM/h。f 的拟合 Vmax=0.114205（源数值），若按图轴 µM/h 换算为 M/s，为约 3.172e-11，与图注 3.17e-11 一致；按源表 µM/min 则大 60 倍。因此更像源表表头误标，但仍需作者确认。未修改源表、生产参数或静默统一单位。

重新绘制并统计 Fig. 4d/e/f/i 实测数据（不等于重新做湿实验）：

- Fig. 4d 单元格 N5 缺失，因此该点有效 n=2，不填零、不伪造第三个重复。
- Fig. 4i 部分组有第四个重复，按实际可用 n 记录；光甘草定 Strain IV 均值为 0.5663 mg/L（n=3）。
- Fig. 4f 按实际各组样本数重算 Kruskal–Wallis 和 Dunn；原文未说明 Dunn 校正方法，分别输出未校正值和 Bonferroni 敏感性值，不声称全部 P 值与图注一致。

## 未擅自修正的科学问题

1. 正文的竞争/线性化方程与发布代码的逐反应 Michaelis–Menten 方程不一致。原文复现使用不可变发布代码；项目凝聚体生产模型仍独立，不拿原文复现代替生产模型验证。
2. 作者默认 LSODA 容差下最低状态浓度为 **-1.014e-6 M**。同一 RHS 改用 `rtol=1e-8, atol=1e-12` 的诊断最低值约 -9.231e-13 M，终点产物由 5.85767e-5 M 变为 5.80342e-5 M。两个结果都保存，默认设置不被替换。
3. 完整 500 点网格的最大终点产量时刻：默认容差 **4.15 d**，紧容差 **4.17 d**。这是该模型/网格下的计算结果，不是已验证的湿实验唯一最佳诱导时间。
4. Fig. 4f 化合物 10、14 的胞外均值分别为 **26.5009%、8.1740%**，参数文件却对应 **8.174%、26.5%**；化合物 11 测得 **12.4378%**，模型设为 0。可能存在标注或参数映射错误，但原因不能确定，未经确认不调换 K 值。
5. 作者 16 个状态的无权重总和近似守恒，不等同于含不同细胞内外体积的物质量守恒。Supplementary Table 9 未提供完整参数单位/酶定量到模型的校准链，本次不将作者本征参数改标为已核定的物理量。

## 原因定位：代码问题、发布材料问题与尚不确定之处

### 已独立排查的复现适配问题

新增 `scripts/diagnose_glabridin_reference.py` 原样导入作者模块，使用其原始 `DataLoader`；仅在内存中将读取器期待的 `data.txt` 路径指向作者实际发布的 `simulation-data.txt`，不改写任何作者文件。随后独立调用作者 `one_step` 并捕获全部 16 个状态，与项目适配器和发布源表交叉比较。这避免仅以项目同一个参数解析器两次运行作为自证。

参数全部一致、状态差为 0，说明已检查的适配链路正确执行了作者代码；成功拟合发布曲线只能证明数值可重现，不能自动证明模型物理有效、数据真实或所有软件模块正确。

### 确认属于作者发布材料/数值实现的差异

- **诱导定义**：Table 9 与作者数据注释说 `time_ratio=0` 为组成型表达。代码此时的有效 DMT 酶量为 `E*min(0.8,0.8*t)`；固定同一状态测试，t=0、0.5、1、2 天的 DMT 通量相对于负值分支分别为 0、0.4、0.8、0.8。负值分支是作者既有代码，不是本次新增；能匹配 Fig. 4g 仍不能证明作者当时确实用了 -1。
- **运输映射**：源表 `D3:E48` 的 10/14 均值与参数表数值交叉对应，高度疑似映射交换。但源表编号与参数表谁有错不能确定；11 的 12.4378% 对模型 0 也可能是未说明的忽略/建模处理，不能擅自归为同一种错误。胞外物质量比例与浓度比的转换还依赖细胞内外体积/归一化定义。
- **负浓度**：在独立作者调用中最低值仍是 -1.014327e-6（按发布曲线标注为 M），发生于胞内化合物 11，约 t=4.874875 天。同一方程只收紧容差后最低值约 -9.231482e-13，终点产物下降约 0.9262%。证据支持数值容差造成显著的负值越界，而非测量数据出现负值；没有裁剪。
- **方程描述**：正文式(2)为 `v=Vmax*S/Km`，作者代码为 `v=E*kcat*S/(Km+S)`，没有实现正文式(1)的完整共享酶竞争项。正文式(3)为 `dSout/dt=ktrans*(Sin-Sout)`，代码为 `kf*Sin-kr*Sout`，其中 `kf=K*rate/(K+1)`、`kr=rate/(K+1)`。两者一般不等价。可以确认方法与实现不同，但不能只因一个使用更完整的单底物 MM 而判定全部反应数据错误。

### 属于我们报告/比较口径的修正

撤回 S5i 单位矛盾；补充全部观测拟合 SE，不用点均值拟合 SE 的不同去指控原文；保留 d/j 未解释差异。此前数字字符串时间点导致只读出部分轨迹的问题已在正式复现前修正，最终 1000 点比较不使用该错误中间结果。

组学、长时间 MD、湿实验没有完成是范围缺口，不是数据错误证据。生产凝聚体 M4 的运输证据、稳态稳定性与预测有效性仍需独立验证。

## 服务器验收

后端全套 **316 项 pytest 通过，无跳过**，前端 TypeScript/Vite 构建与 **3 项 Vitest 通过**。作者文件接入后，之前在干净克隆中因缺文件而跳过的作者回归测试也实际运行通过；原始证据见 `server-verification/pytest.xml` / 日志。官方 SDK stdio 客户端发现 18 个 MCP 工具并真实调用 M1、部署审计和外部 FreeSASA，产生输出及作业清单，FreeSASA 退出码 0。

新一轮合并逻辑文件大小审计包括项目 Python 环境、ColabFold 权重、独立复现环境、Node/pnpm、安装缓存、前端 node_modules 和已有工具：**11,212,705,318 字节**（约 11.21 GB）小于十进制 15,000,000,000 字节。该值是本次切换前的实测快照，不是磁盘硬配额；以后安装需重新审计。原始论文数据/旧实验输出不冒充外部工具大小。

复现命令（只在 air-lab 运行）：

```bash
/mnt/data/dyx/drylab-envs/glabridin-reference/bin/python \
  /mnt/data/dyx/drylab-m1m4-runtime/scripts/reproduce_glabridin_paper.py \
  --sources /mnt/data/dyx/glabridin-reproduction/raw \
  --output /mnt/data/dyx/glabridin-reproduction/results
```

输出包括逐点 CSV 残差、JSON 指标、全部 500 点双容差结果、12 组拟合、湿实验原始重复统计、缺失值清单、6 张重新计算的 PNG 和服务器环境记录。

追加诊断命令（同样仅在 air-lab，stdout 为 JSON）：

```bash
PYTHONDONTWRITEBYTECODE=1 /mnt/data/dyx/drylab-envs/glabridin-reference/bin/python \
  /mnt/data/dyx/drylab-m1m4-runtime/scripts/diagnose_glabridin_reference.py \
  --sources /mnt/data/dyx/glabridin-reproduction/raw \
  --repository /mnt/data/dyx/drylab-m1m4-runtime
```

### 结果证据目录

根目录 `/mnt/data/dyx/glabridin-reproduction/results/`；以下都是服务器计算/核对产物，不是作者原始数据链接。

| 证据文件 | 内容 |
| --- | --- |
| `source_checks.json`、`source_workbook_versions.json`、`sheet_inventory.json` | 原始文件校验、两版工作簿差异与48张表清单 |
| `numerical_comparisons.json`、各图 `*_comparison.csv` | 逐点轨迹/扫描误差，时间与浓度分开 |
| `solver_diagnostics.json`、`induction_tolerance_sensitivity.csv` | 默认/紧容差对照与完整500点扫描 |
| `kinetic_fits.json`、`kinetic_observations.csv` | 12组拟合及每个真实重复值/源单元格；旧 JSON 的点均值 SE 不能代替新增诊断的全部重复拟合 SE |
| `wet_measurements.json`、`wet_timecourse_observations.csv` | 实测数据重分析、实际n与缺失值 |
| `transport_measurements.json` | 实际样本量、胞外比例、Kruskal–Wallis/Dunn及校正敏感性 |
| `reference_diagnosis_20261004.json` | 此次独立作者读取器/适配器检查、门控测试、12组不同拟合口径和紧容差复核 |
| `execution_environment.json`；上级 `environment.lock.txt` | 原文复现环境记录；追加诊断 JSON 另含实际解释器/NumPy/SciPy版本 |
| `reproduction_summary.json` | 既有复现摘要；本报告和新增诊断记录补充其统计/单位说明，未覆盖旧证据 |

`server-verification/` 保存此前 pytest、前端构建、MCP/FreeSASA 与部署记录；本次仅增加诊断并更新报告，不冒充重新完成全部测试或真实外部工具验证。

## 代码 bundle 与交付记录

完整源码 bundle 为 `E:/Desktop/activity/iGEM/drylab-doc/iGEM-drylab-codebundle.md`；由提交后的完整 Git 树机械导出，每个文件包含路径、Git blob、字节数与 SHA-256，并进行逐文件解码回验。此次报告、数据来源清单和独立诊断脚本纳入快照；bundle 页首保存实际源提交与文件/子模块数量。

bundle 包含全部已提交项目源文件，不包含凭据、安装环境、模型权重、受忽略的原始大数据或全部第三方子模块源码；不能将其称为免下载的完整离线环境包。原始作者文件在 air-lab 保持不可变，本报告提供来源直链与校验清单。

报告副本置于 `E:/Desktop/activity/iGEM/drylab-doc/光甘草定论文复现报告_20261004.md`。报告、来源清单、诊断脚本及 bundle 同步到 air-lab；具体交付 SHA-256 由同步校验记录保存，避免报告嵌入自身内容哈希。

## 不得称为“整篇论文完整复现”

本次完成的是 **公开原文计算模型和已提供实测数据的重分析**。未完成从原始测序到组装/注释/共表达的重建、原始 LC–MS 全链处理、对接/长时间 MD 重跑、或湿实验重复，也没有完成凝聚体的运输证据/稳态稳定性实验验证。原文对应 [BioProject PRJNA1390709](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1390709) 显示约 0.91 TB 的原始序列数据；15 GB 是工具部署预算，不能据此误称原始数据违反工具预算。若继续全组学/MD，需要另行确定原始数据、计算资源、可获得的初始结构/拓扑/参数、随机种子与验收目标，不生成替代结果填补这些缺口。

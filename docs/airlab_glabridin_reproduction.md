# air-lab 原文计算复现与新版部署（2026-10-04）

## 计算位置与版本

所有本次正式复现、拟合、后端测试、前端构建和 MCP 实际作业均在 **air-lab** 执行；本机仅编辑、传输和记录代码/报告。

- 新版完整项目源码：`/mnt/data/dyx/drylab-m1m4-runtime`，包括 M1–M5、工作流、MCP、插件运行时、React/TypeScript、Tauri 源码、测试、配置和示例。
- 旧入口 `/mnt/data/dyx/lkdagent/drylab` 指向新版；两个旧代码目录以时间戳归档至 `/mnt/data/dyx/drylab-code-archives/`。原有 Git 工作改动、`.env`、输入和约 8 GB 输出保留，不删除实验数据。
- 原文文件与计算结果：`/mnt/data/dyx/glabridin-reproduction/`。
- 隔离的原文数值环境：`/mnt/data/dyx/drylab-envs/glabridin-reference`。使用 Python 3.11、NumPy 1.24.4、SciPy 1.10.1、Matplotlib 3.7.5、OpenPyXL 3.1.5；实际传递依赖见服务器 `environment.lock.txt`。
- 作者方法记录的是 Python 3.8.5；本次没有声称解释器版本或结果逐比特一致。
- 正常项目环境仍是 `/mnt/data/dyx/miniconda3/envs/drylab-m1m2`，新版源码通过 editable 安装指向当前运行目录。

第三方 Git 子模块的地址和提交保留在源码/部署清单中；未把所有可选第三方项目、数据库和模型重新下载为离线镜像。已有工具、ColabFold 权重和环境保留。Tauri 源码已部署，但本次没有编译服务器桌面壳、生成 Windows 安装包或执行浏览器端到端测试。

## 官方来源与不可变性

论文：[Discover the maze-like network for glabridin biosynthesis](https://www.nature.com/articles/s41467-026-68881-8)，DOI `10.1038/s41467-026-68881-8`。

[Figshare 官方记录](https://doi.org/10.6084/m9.figshare.29221010.v1) 的在线 API 元数据与文件 MD5 已核对：

| 文件 | 官方 MD5 |
| --- | --- |
| simulation-network-glabridin-final.py | 43195d5a0ffef38aef774be6e174aa22 |
| simulation-data.txt | 66efd25bea2fe3c4e6d095c44fcb944e |
| Source Data_V2.xlsx | ca6192d3a4c11bc1af975ad24d4a0d37 |

九份 Figshare 文件均有来源记录，下载受限的文件由用户已有 ZIP 提供并与在线官方 MD5 核验；正文、补充信息及补充数据另从出版社下载。SHA-256 与获取方式在服务器 `source_manifest.json` / `results/source_checks.json` 中。

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

对 Supplementary Fig. 5 全部 12 组数据按 `v=Vmax*S/(Km+S)` 做未加权非线性最小二乘拟合：保留每个真实重复值、源单元格和源速度单位；同时输出浓度点均值拟合和全部重复值拟合。多数 Km 与图中标注接近，但 **GgPTR2/medicarpin** 为 182.725 µM（图注 186.53 µM），GgDMT1/vestitol 为 21.097 µM（图注 21.17 µM）；没有强制拟合为论文值。拟合协方差 SE 并不等同于生物重复 SD，也未宣称重现论文全部误差条或未说明的拟合加权。源表 medicarpin/GgDMT1 的单位为 µM/h，图轴显示 µM/min；没有静默统一。未凭缺失的活性酶浓度推导 kcat。

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

## 不得称为“整篇论文完整复现”

本次完成的是 **公开原文计算模型和已提供实测数据的重分析**。未完成从原始测序到组装/注释/共表达的重建、原始 LC–MS 全链处理、对接/长时间 MD 重跑、或湿实验重复，也没有完成凝聚体的运输证据/稳态稳定性实验验证。原文对应 [BioProject PRJNA1390709](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1390709) 显示约 0.91 TB 的原始序列数据；15 GB 是工具部署预算，不能据此误称原始数据违反工具预算。若继续全组学/MD，需要另行确定原始数据、计算资源、可获得的初始结构/拓扑/参数、随机种子与验收目标，不生成替代结果填补这些缺口。

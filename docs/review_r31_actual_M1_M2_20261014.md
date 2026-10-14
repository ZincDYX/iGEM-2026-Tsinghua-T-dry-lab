# M1/M2 实际计算与未完成项（2026-10-14）

结论：本轮有真实新增结果，不只是接口或单元测试；但完整 M1/M2 尚未完成。
用户提供的参数文档按 F/L/P/R/C/U 来源类别保留。采用其中可计算的 R 推荐时，
明确标注为新版本描述性方法，不冒充原方案公式、实验条件或实测结果。
用户已明确暂不组合不同文献的温度、pH、离子强度；项目 CG 模拟因此未启动。
随后收到新版第24节补充协议，用户明确将其作为正式干实验协议采用；下文早期状态仅说明本轮既有结果的条件，
后续计算可按新版具名参考条件推进，仍不称项目实测值。

## 实际结果

| 项目 | 已完成 | 适用范围和限制 |
|---|---|---|
| 完整输入 | 同一软件项目272条输入，127条IDR来源记录、126条唯一IDR；保留原名、来源和同序列别名 | 不重新采用旧17条验收子集，别名不是独立重复 |
| 原始M1证据 | 核对复用原IUPred/SEG/ProtParam、PScore、catGRANULE全部IDR结果 | 已有结果不等于所有原方案步骤都完成 |
| 名义序列指标 | 全部127条的原localCIDER 0.1.21 κ、SCD、FUS Tyr/Arg描述量；真实stdio MCP调用验证 | κ原生−1保留为不适用；KR/DE名义电荷不等于实际胞内电荷；Tyr密度不是结合价态 |
| 原JPred | 110条唯一序列，对应111条来源记录，完整序列与原文件匹配 | 16个已受理作业原文件取回HTTP403，原因未确定，未重复提交 |
| 原FuzDrop | 43条唯一序列，对应44条来源记录，全局pLLPS和完整逐残基曲线进入软件持久化作业及后续证据 | 2次提交无确认响应，未重复；其余81条尚未提交。服务内部模型版本未公开，不虚构版本 |
| 描述性比较 | 同长度/相同实际工具覆盖率分组、别名去重、中秩百分位和Pareto层级；实际127条表格已输出 | 不是原四工具加权公式；rank_score仍空，不跨缺项组比较；κ风险方向未知，risk_complete仍false |
| 24聚体区域观察 | 3种实际融合×5个模型=15组完整24聚体；4560条逐链/逐区域SASA和置信度观察 | 在完整结构中先计算SASA再选区域；条件静态刚体cage不证明真实组装或ER定位 |
| 冻结apo核心比较 | 三组各5×5=75组；先依据全部5个未融合基线DSSP和pLDDT>70交集冻结核心，再比较融合 | OC融合、DMT融合、OC截短效应分别记录；不使用融合结果挑核心；不是完整口袋/Q1/酶活证明 |
| 静态原子体积 | 8种蛋白×5个实际模型=40组球并集体积；0.5/0.25 Å网格比较全部达到1%数值目标 | 显式RDKit元素半径；1.4 Å水尺度探针，不代表代谢物11；没有补氢/辅因子/配体，不自动输入M3 |
| 原CALVADOS | 固定作者源版本，5组原作者完整势能测试通过；原生GPU合成作业及轨迹解析完成 | 合成三残基软件测试，不是项目IDR/相分离结果或缩短版作者复现 |
| 原Mpipi | 2021原引擎及未修改40类型力场完成实际合成作业；101帧轨迹解析、逐帧质量守恒核对 | 不是项目轨迹、LLPS分数或完整项目模拟 |

apo核心冻结的实际保留数为ΔN OC 294、DMT 191、WT OC 293残基，排除位置和覆盖率也保存。
所有5×5模型配对保留，不能将25个配对当作25个独立实验重复。
体积同时保留原子中心凸包，并明确其包含溶剂/空腔空间，不能当作实体排除体积。

## 代码与运行边界

- 复用已有工作流、外部进程适配器、后端证据存储、几何计算和MCP服务器，未另建调度器或数据库。
- FuzDrop驱动只操作原网页普通表单，保存提交意图和原响应；不绕过验证码或验证拦截。
  已知完整响应可恢复解析，未知提交不能自动重试。站点job token、原网页诊断留在私有后台。
- TANGO保留原始百分数曲线与最大连续热点。文档R条件为>5%且连续≥5残基，
  另列≥6残基敏感性；≥2处热点仅提示复核，不将热点个数直接当作实验聚集结论。
- 新增原PSIPRED经典profile路线，完整输入→原blastpgp三轮→makemat→原psipred/psipass2→SS2校验。
  不静默回退单序列、不补长、不截断；同源证据不足不能成为已校准的硬淘汰证据。
  原NCBI旧版工具已获取，UniRef90 2026_03数据库下载/校验/建库仍在进行；尚无本轮真实PSIPRED预测。
- 原CALVADOS/Mpipi项目入口要求显式物理条件、起始结构/力场和时长。
  CALVADOS完成记录可复用；中断的checkpoint续跑仍要求审核，没有实现任意中断无缝恢复。
  Mpipi项目作业要求新输出目录，不能把重复执行伪装成继续已有轨迹。
- 轨迹只输出原生单位转换、质量密度、质量加权Rg。相区/时间窗口由调用者明确指定，
  无自动平衡判定、相识别或bootstrap置信区间；不再把密度分位数/对数变换伪装成LLPS分数。

### 可复用执行入口

在单独安装原模型和依赖的计算环境运行；请求JSON字段由对应Pydantic输入类定义。
不能直接使用本报告生成缺失项目条件。工具安装、模型、数据库、请求与输出均在用户私有目录。

```bash
# 准备完整原模型输入；同一条命令去掉 --prepare-only 才执行实际原引擎
python -m igem_drylab.coarse_grain_project --engine calvados --request reviewed-job.json --prepare-only
python -m igem_drylab.coarse_grain_project --engine mpipi --request reviewed-job.json --prepare-only

# 原DCD或LAMMPS dump的轨迹观察，不生成虚构相分离分数
python -m igem_drylab.cg_trajectory_analysis --engine calvados --request reviewed-analysis.json
python -m igem_drylab.cg_trajectory_analysis --engine mpipi --request reviewed-analysis.json

python -m igem_drylab.mcp.server
```

新真实MCP路径包括 `igem.m1.nominal_descriptors`、`igem.m1.analyse_phase_profile`、
`igem.m2.compare_core`、`igem.m2.structure_volume`，并扩充已有组装/上下文/口袋/证据工具白名单。
名义指标、描述性比较、相区观察、实际核心及体积均做了真实stdio调用；
核心/体积调用值逐项等于已经保存的实际计算结果。15组cage计算通过服务器原计算函数运行，
不将它们全部表述成已通过MCP逐组执行。
长作业可通过已有外部命令适配器运行；本轮原CG作业实际由独立原模型环境CLI执行，
尚不宣称所有CG项目作业已经完成软件端到端调度验收。

### 可选依赖与许可

`sequence-descriptors`固定localCIDER 0.1.21；`official-forms`固定Playwright 1.63.0。
它们不是默认桌面/软件运行时依赖，不把浏览器、原工具、模型权重或数据库塞入EXE。
部署时单独安装、记录完整环境版本并遵守原工具许可。Apache-2.0仅覆盖团队自有源码，
不重新授权localCIDER、CALVADOS、Mpipi、PSIPRED或服务结果。

## 验收与交付

- 所有科学数值、作者测试和原模型作业只在计算服务器运行。
- 最新服务器完整回归：1003通过、16跳过；另有原工具环境专项回归86通过。
  跳过不是通过，不靠测试数目替代完整科学验收。
- 前端84项测试通过，构建通过；实际软件项目导入127条IDR结果、75组核心比较及体积补充。
- 实际浏览器核对结果表、统计图、原ColabFold结构旋转和导出CSV字节一致；未使用假结构截图。
- 便携结果包含科学表格、图和原JPred结果；原FuzDrop响应仍在私有后台，包内曲线是显式导出。
  研究输入、结果包、原程序/权重、账户/站点令牌、私人部署资料均不进入公共仓库或源码bundle。
- 本轮Windows EXE没有更新，不能以源码完成代替新的EXE验收。

## 仍未完成：区分原因

1. **服务/许可未打通**：TANGO原站注册/许可路径重试仍失败；服务器看到代理TLS错误，
   本地请求超时，无法确定原因，不能据此断言官网全球故障。尚未成功提交申请/取得工具。
   PASTA按用户要求取消，不再列为当前必须运行工具。
2. **已有作业响应不完整**：JPred16个403；FuzDrop2个未确认提交、81个未提交。
   需继续核实服务响应，不盲目重复未知提交。没有拿缺项当零或默认通过。
3. **部署尚在进行**：UniRef90数据库需完整下载、MD5核对、解压建库，再跑原PSIPRED。
   完整短linker/长融合的适用性仍需审核；既有ColabFold+DSSP只作用户批准的上下文辅助。
4. **参考协议已补齐，执行尚未完成**：新版第24节及输入包提供温度/pH/盐、预算、重复seed、端基、
   ER方向/组成和膜配方，用户明确正式采用。接下来核验原作者环境并生成项目专属输入，
   不再要求湿组先提供轨迹/拓扑。正式CALVADOS3力场表不能用beta表或未审核原生默认值代替。
5. **化学/几何准备仍不完整**：完整holo口袋、辅因子/底物正确化学态、来源一致的招募姿态、
   ER实际膜坐标/朝向/厚度/胞质侧、PPM定位及约束集合、孔道连通性、构象集合仍未完成。
   功能锚点不能顶替完整口袋；天然锚段拓扑不能直接断言融合后酵母膜侧。
6. **代码/流程还需工作**：完整项目CG恢复与不确定性、完整M2 assessment输入整合、
   全部项目真实作业端到端验收、正式结合/共占位及稳定性/长时间MD尚未完成。
   这些不是全都能归因于“缺授权”；条件齐全后还需继续实现和执行。
7. **科学判定未定稿**：κ软风险方向、原四工具归一化/权重、动态碰撞/埋藏与招募结论的审核策略仍缺。
   本轮R描述性比较是可读的中间结果，不替代完整M1正式排序或原方案通过结论。

## 数据与方法来源

项目序列来自用户完整linker输入包、第二轮wetlab输入包；采用的条件/方法类别来自
`M1_M2_数据标准参数与来源_20261014.md`。具体私有原路径只留在后台来源记录。

- [原JPred接口](https://www.compbio.dundee.ac.uk/jpred/api.shtml)
- [原FuzDrop服务](https://fuzdrop.bio.unipd.it/predictor)及[2022方法原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC9252777/)
- [原catGRANULE服务](https://tools.tartaglialab.com/new_submission/catGRANULES)
- [localCIDER原代码](https://github.com/Pappulab/localCIDER)、[名义SCD原文](https://doi.org/10.1063/1.4929391)
- [TANGO许可入口](https://tango.crg.es/licensing-and-services)、[方法文档](https://tango.crg.es/documentation)
- [PSIPRED原脚本](https://github.com/psipred/psipred/blob/master/runpsipred)
- [NCBI原经典2.2.26工具](https://ftp.ncbi.nlm.nih.gov/blast/executables/legacy.NOTSUPPORTED/2.2.26/blast-2.2.26-x64-linux.tar.gz)
- [UniRef90原发布信息](https://ftp.uniprot.org/pub/databases/uniprot/uniref/uniref90/RELEASE.metalink)
- [原2FHA模板](https://www.rcsb.org/structure/2FHA)、[FreeSASA](https://freesasa.github.io/python/intro.html)
- [RDKit显式元素半径接口](https://www.rdkit.org/docs/source/rdkit.Chem.rdchem.html#rdkit.Chem.rdchem.PeriodicTable.GetRvdw)
- [本轮原CALVADOS固定版本](https://github.com/KULL-Centre/CALVADOS/tree/69815423632cb9b9b08f4b0aea34d8ba43a057c4)
- [正式CALVADOS3作者参数表](https://github.com/KULL-Centre/_2024_Cao_CALVADOSCOM/blob/main/src/residues_pub.csv)
- [原Mpipi2021作者归档](https://doi.org/10.6084/m9.figshare.16772812)、[原残基类型映射](https://github.com/josephresearch/MpipiStructureScript/blob/main/aa_types_one_letter.txt)

网络服务/数据库状态是本轮观察，不保证未来持续可用；不同文献条件未被合成为项目协议。

## 交付前收到的新补充包

收到新版参数文档及`M1_M2_CG_MD_reference_inputs_20261014.zip`后，已将原包完整同步到私有计算环境，
未放入公共仓库。实际157个文件；8个主目标、120条新IDR、7条优先IDR和2条FUS上下文均与已有软件项目逐条匹配。
7条优先直接融合是新背景对象，尚不存在于已有项目，不能复用旧融合M2结果。
核对13组ER亚基链分配的计数、互斥和24链覆盖；正式CALVADOS3参数表包含20种氨基酸。
新版MD模板的步长/步数对应1/5/50/500/700 ns，未发现启用pull字段。
以上是输入核验，未执行包内脚本、grompp或项目生产模拟，也未独立验证全部膜拓扑化学。

第24节新增303.15 K、pH7.2、有效离子强度0.15 M的参考协议及膜/端基情景。
它在附件中写“已授权”，曾与用户刚才明确的“不组合条件，等项目参数”冲突，
因此先核验并询问，没有仅靠附件声明启用。用户随后明确“24节的就当正式干实验数据”，
正式采用该参考协议，已启动作者环境安装，未把它称为项目实测。这不是还要求湿组提供轨迹或拓扑；
项目初态、拓扑和轨迹属于后续计算输出。新协议的作者CALVADOS3快照及OpenMM7.6.0环境
与此前验收的CALVADOS0.9/OpenMM8.4环境不同，不能将先前GPU成功直接算作新协议已经验收。

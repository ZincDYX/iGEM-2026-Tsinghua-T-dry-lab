# M1 M2 实际作业与最新项目条件

## 当前结论

本轮补齐了一批真实输出，但没有完成整套 M1/M2，也没有将缺工具、缺口袋或未收敛的计算标为通过。所有科学计算和数值测试在服务器执行；本机仅用于阅读补充文档、软件构建和浏览器验收。输入、原工具、模型权重、作业访问标识、凭据和部署地址不进入源码仓库或代码 bundle。

用户最新确认的参数优先级是：最新项目 DOCX 提供的字段优先；未提供的字段沿用之前参数文档；若新离子数据能唯一换算有效离子强度则使用换算值，否则暂用旧值。参数来源在私有作业请求中记录，不静默混用。

## 已完成的实际输出

| 工作 | 实际输出 | 不能据此宣称的结论 |
| --- | --- | --- |
| 原 JPred 恢复和绑定 | 127 条 IDR 来源记录、126 条唯一序列有完整二级结构证据；同一批原作业取回剩余 16 项 | 二级结构覆盖齐全不代表全部 M1 工具或风险规则齐全 |
| 原 FuzDrop | 44 条唯一序列、45 条来源记录有原概率和逐残基曲线 | 3 个提交响应不确定，80 条未提交；缺项不是零分 |
| 新增完整融合的原 M1 工具 | 7 条精确完整融合 × IUPred、SEG、SignalP、DeepTMHMM = 28 次实际运行并解析成功；SignalP 使用已确认的 eukarya | 工具完成不等于正式 M1 通过 |
| DMT 招募准备 | 3 个支架 × 5 个支架模型 × 5 个 DMT 模型 × 15 个原 2PDZ NMR 构象 = 1125 个姿态；首项真实 stdio MCP 与共享函数一致 | 单支架亚基的刚体准备，不是完整催化口袋、完整 cage 共占位、ER 膜约束或亲和力验证 |
| 最新 OC 家族模板准备 | 下载 3FW7、3FW8、3FW9、3FWA；分别检查 8 个原 altloc；3886 行暂定序列映射和 3970 行最近 FAD 重原子距离 | 暂定映射与原模板距离不等于项目 GgOC1 的完整口袋或双共价 FAD 几何 |
| 原 Mpipi 参考作业 | 8 条唯一 IDR × 3 随机种子，共 24 个原引擎作业，保留原力场和 5 ns 平衡加 40 ns 生产预算 | 原固定电荷和屏蔽模型没有外部 pH/盐参数；不能冒称已经模拟最新细胞完整离子条件、达到收敛或得到 LLPS 相图 |
| 原 CALVADOS3 适配验收 | 原 OpenMM 7.6.0 环境，原作者势函数，独立键能与排除规则检查；CUDA 合成三残基轨迹 110 帧，真实逐帧 Rg/Re 导出 | 合成软件验收不是项目轨迹验证或缩短版项目实验 |
| GROMACS 2025.0 CUDA | 原源码构建成功；初次原回归 91/92 组通过；资源不兼容的 3 个案例在兼容资源调用下对应 6 个原测试全部通过 | 不声称初次 92 组一次全绿；没有修改原物理参数或放宽断言 |
| 原 S59 裸膜参考准备 | 使用官方 CHARMM36 July 2022 原子类型恢复 1313 项质量；12000 水分子后正常加离子；原生 EM 最大力 915.01935 kJ/mol/nm，低于声明目标 1000；没有使用 maxwarn | 该膜组成与最新项目 DOCX 不同，只是历史参考准备，不代表新项目膜已构建，更不是锚定 MD 完成 |

JPred 缺项的一个根因确认为**我们的解析代码错误**：旧正则截断作业 ID 内部的下划线/连字符，用错误 ID 取回产生失败。现在从原受理页面的规范链接保留完整 ID，并修复持久状态中的这一特定截断；不同作业身份冲突仍明确报错。没有重新提交这 16 个作业。旧失败日志保留；不能继续把此前失败笼统归因于服务或论文数据。

## 最新条件与仍在执行的作业

胞质 pH 使用新文档的 6.8。温度 303.15 K、原单链完整预算、种子和采样间隔沿用此前已确认协议。新文档只给出 K 浓度范围，没有确定值；总磷酸根没有完整的离子形态比例，因此不能唯一换算单个离子强度。暂用之前协议的 **0.15 M 有效 CG 离子强度**，不将它写成新离子浓度的精确换算，也不声称隐式屏蔽模型包含各个胞内离子的化学作用。

此前 pH 7.2 的 8 个在运行作业已停止，数据和检查点仅保留作历史记录；不会把这些检查点续接成 pH 6.8 结果。新建 24 个 pH 6.8 的原 CALVADOS3 单链作业，每项完整执行 150 ns 平衡和 1000 ns 生产，并使用可用 GPU。独立后处理会在原预算实际完成后导出全部原生逐帧 Rg/Re，平衡和生产分别标记；没有完成则不导出成“完整结果”。

孤立 IDR 参考链保留原作者游离肽端基。它不是融合内部 IDR 的端电荷模型，不因项目“无端基修饰”就给内部片段加两个游离端电荷。完整融合及多链 slab 不会被单链结果替代。

新增 7 条精确完整融合的 ColabFold 原作业也已提交到持久软件流程，保留 5 个原模型及各自配对置信度，不补长、不重复、不截断输入。初次工具未配置诊断已保留，维护者配置真实原环境后才新建实际作业；工作流状态成功但 `tool_status=not_configured` 不计为工具运行完成。

PSIPRED 的完整官方 UniRef90 数据库仍在下载准备中。使用官方发布大小、范围响应及发布校验值确认完整数据库后，才能建立真实检索库；没有拿残缺库或单序列弱替代路线冒充原正式路线。

## 完成标准与未完成项

仍需完成：新条件的完整单链轨迹及采样收敛检查，后续多链/完整融合 CG；新增完整融合模型及配对置信度的解析、区域与几何后处理；剩余 FuzDrop、TANGO 许可与真实作业；完整催化口袋及 OC 招募肽的审核映射；FAD 双共价与 Fe/2-OG 化学准备；按最新磷脂组成构建 ER 膜，具体脂质、其他组分和麦角固醇比例需要明确选择与来源；膜中锚段位置/朝向、平衡及正式重复 MD；最终 M1/M2 assessment。

最新文档提供 AtMSBP1 N 端在 ER 腔、C 端在胞质的项目定位声明，可用于标注预期朝向，但“TM 位于前 40 aa”不是精确的膜插入坐标，不能随意补膜厚或空间位置。I293/T295、N303 是给定功能线索，不是完整口袋。

描述性 κ/SCD/Tyr 比较继续使用此前明确方案，不自动变成通用软风险方向或未定义的加权总分。工具缺项、低置信区域、姿态未审核或采样不足均保留在结果状态中，不能被 agent 的文字解释覆盖。

## 代码与复现入口

原 CALVADOS3 环境单独安装，不把它及模型打包到应用。其作者源码由用户依法单独准备，固定到下列原提交。项目适配器可由这个原 Python 3.8 环境直接执行单文件，不强迫原环境安装现代应用的全部依赖：

```text
<original-python> src/igem_drylab/calvados3_author_runner.py --request <private-request.json>
```

请求显式包含原源码位置、提交、全序列、温度、pH、有效离子强度、时间步、摩擦、AH/DH 截断、孤立端基状态、盒子、种子、GPU、平衡/生产步数和保存间隔。恢复必须匹配原请求、检查点和已保存帧数，不能重复步数或将不同 pH 作业拼接。完整原轨迹的 `export_observations` 使用原实际 bead 质量，以 nm 和 ns 导出；不生成未经定义的相分配、csat 或 M1 结论。

裸膜参考准备是后端独立 CLI，不是新膜设计的替代方案：

```text
python -m igem_drylab.gromacs_er_reference_prepare --request <private-request.json>
```

原数据目录保持不变。请求指定标准质量力场原包、EM 设置、盒子、含水量、盐浓度、显式离子放置种子和原生 GROMACS 路径。源码不内置项目服务器信息。

DMT 姿态准备经 `igem.m2.prepare_recruitment_poses` 真正连接 stdio MCP，并接入 `recruitment_pose_preparation` 结构计算请求。原完整招募几何接口继续要求完整口袋与已审核接触定义；公共坐标变换实现只保留一份。准备结果 `formal_verdict=not_assessed`、`m3_ready=false`，不伪装成完整评估。

服务器完整回归：1025 passed、16 skipped。实际科学工具环境补充测试：48 passed。跳过项不是完成证据；原生作业验收单独核对输入序列、真实工具状态、解析状态及原输出。此前一次完整回归发现两项旧协议测试用了非规范受理字符串，已将这些合成 fixture 改成规范链接；不是通过放松真实身份校验解决失败。

实际软件验收已完成：通过服务器现有软件导入 10 个当前结果附件，浏览器确认 127 行 IDR 表、28 行原工具作业表、DMT 姿态表及实际统计图可见；IDR 表下载与后台导出逐字节一致；包含完整支架亚基和完整 DMT 融合的真实准备结构可旋转，浏览器没有页面错误。可视化选的是首个枚举姿态，不是通过筛选的最佳姿态。原始浮点坐标保留在后台 JSON；展示 PDB 的标准 0.001 Å 序列化精度已核对，不拿展示文件替代原数值评估。

## 所有外部数据与方法源头

- [JPred 原 API 与客户端](https://www.compbio.dundee.ac.uk/jpred/api.shtml)
- [FuzDrop 原服务](https://fuzdrop.bio.unipd.it/)，[FuzDrop 方法原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC9252777/)
- [SignalP 6 官方服务和学术渠道](https://services.healthtech.dtu.dk/services/SignalP-6.0/)
- [DeepTMHMM 官方服务](https://services.healthtech.dtu.dk/services/DeepTMHMM-1.0/)
- [IUPred 官方渠道](https://iupred.elte.hu/)
- [原 PSIPRED](https://github.com/psipred/psipred)，[官方 UniRef90 文件](https://ftp.ebi.ac.uk/pub/databases/uniprot/current_release/uniref/uniref90/)
- [原 CALVADOS3 提交](https://github.com/KULL-Centre/CALVADOS/tree/51564e0edd126c44d6a7299fbe4414c579394ef4)
- [原 Mpipi 数据与代码](https://doi.org/10.6084/m9.figshare.16772812)
- [ColabFold 原项目](https://github.com/sokrypton/ColabFold)
- [GROMACS 2025.0 原源码包](https://ftp.gromacs.org/gromacs/gromacs-2025.0.tar.gz)，[原回归说明](https://manual.gromacs.org/2025.0/dev-manual/regressiontests.html)
- [CHARMM36 官方力场](https://mackerell.umaryland.edu/charmm_ff.shtml)
- [2PDZ 原 NMR 模板](https://www.rcsb.org/structure/2PDZ)
- [3FW7 原 H104A 模板](https://www.rcsb.org/structure/3FW7)，[3FW8 原 C166A 模板](https://www.rcsb.org/structure/3FW8)，[3FW9 原野生型家族模板](https://www.rcsb.org/structure/3FW9)，[3FWA 原 C166A 底物复合模板](https://www.rcsb.org/structure/3FWA)
- [IUPAC 离子强度定义](https://goldbook.iupac.org/terms/view/I03180)

项目原始输入来源是用户提供的完整 M1/M2 输入、第二轮湿实验序列、参数与 CG/MD 参考输入包以及最新项目 DOCX。原字节和来源关系保存在私有实验工作区，不在公共源码报告中嵌入这些输入或下载许可链接。膜参考原包由用户提供；其 200 脂质、7938 水和原 HMR/离子配置逐项保留在原始数据中。新派生准备不覆盖原件，亦未冒称参考原包已经符合最新膜组成。

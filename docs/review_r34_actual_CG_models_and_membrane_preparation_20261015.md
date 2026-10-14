# r34：补充包、真实轨迹与新增结构

整套 M1/M2 尚未完成。本轮所有科学计算和数值测试仍只在服务器执行；本机接收结果、编辑源码及更新 bundle。原工具、用户输入、模型权重、轨迹、部署信息与凭据不进入公共仓库。

## 实际完成

- 补充包有 216 个文件，215 条文件清单全部核验。最新 DOCX 字段优先，缺少项沿用已批准的旧协议：胞质 pH 6.8、303.15 K、有效 CG 离子强度 0.15 M。后者不是由不完整离子表精确换算所得。
- 7 条精确完整融合的 35 个 ColabFold 模型和各自配对置信度均完成；原生 DSSP、SASA 和区域 PAE 后处理产生 140 条区域记录并导入软件。没有补长、重复或截断预测输入。
- 35 个模型的全部原配对 pLDDT 已通过既有后端注释格式注册，逐残基核对展示值与原 JSON 一致；没有由 B-factor 猜测置信度。只有来源明确的 IDR 区域标注，未猜测其他片段的折叠域或完整口袋。
- 这 35 个完整模型的 FTH 片段与已有来源片段逐字一致且唯一出现；由此转移原具名残基映射，完成 35 组完整融合的 24 亚基模板坐标准备。每组保留完整原子、24 个变换和核心 CA RMSD。模板复制不是自然组装证据，没有正式 M2 通过。
- 截至本轮结果快照，16/24 条原 CALVADOS3 pH 6.8 单链作业跑满 150 ns 平衡及 1000 ns 生产。每条导出全部 9200 保存帧，8000 生产帧。其余 8 条在运行；改正后的自动后处理等待原预算完成，不改动 GPU 模拟。
- 24/24 条原 Mpipi 参考作业导出原生 image flags 对应的质量加权 Rg 和端到端距离。保持原 5 ns 平衡及 40 ns 生产；稀疏保存约 20 帧，不能冒充微秒级项目验证或相分离证据。
- 28 组 Rg/Re 的自相关、块误差、分段漂移和独立重复区间已计算；8 组满足本轮声明的检查条件，其他组重复未齐或采样未达标。尚未完成不同块长的误差平台及 slab 有限尺寸检查，因此不宣称充分收敛。
- 新接口 `igem.m1.assess_cg_sampling` 真正注册并接通 stdio MCP；用 FUS 三条真实独立轨迹调用，与共享后端函数逐项一致，不是工具名占位或合成 smoke test。
- 软件浏览器验收：28 行 CG 汇总、140 行区域表、真实统计图可见；CG 导出与后台逐字节一致；实际完整融合模型身份核对后可旋转，页面无脚本错误。模型可展示不等于科学判定通过。

## 修复的代码问题

原生矩形盒保存角度为 90°。MDTraj 用单精度 cos(90°) 重建向量，85 nm 盒产生约 3.7×10⁻⁶ nm 非对角舍入量；旧导出器的固定容差误报为非直角盒。现在核验保存角度并直接使用保存边长，没有放宽实际非直角盒、改变原坐标、质量或势函数。无效盒与真实非直角盒的拒绝测试仍保留。

FuzDrop 原服务存在“表单已可交互而页面加载事件仍未结束”的情况。改为正常页面访问后等待真实可见输入；保存 POST 前后状态，不处理 CAPTCHA、注入验证令牌或重提未知作业。网页可见已经实际验证，随后自动执行仍出现偶发的表单加载超时；仅确认尚未 POST 的失败可以恢复。不能称剩余预测已完成。

FuzDrop 初始账本按 126 条唯一序列互斥统计：44 完成、2 提交不确定、80 未提交或提交前失败，对应 127 条来源记录。旧“44+3+80”混合不同状态、超过分母，已修正。后台新尝试不预先计入成功数。

恢复后的第二份固定快照有 **67 条唯一序列完成、2 条提交不确定、57 条未提交或提交前失败**；比初始快照新增 23 个真实结果。67 个原分数对应 68 条来源记录，已重新连接 127 条 IDR 的 M1 原始结果及描述性比较，并经实际 stdio MCP 运行。该固定账本和结果使用同一批成功输出，不能把后续仍在增长的成功数混到旧表分母中。

CALVADOS 来源链接原来误写为另一个仓库。实际使用的六份物理源码与正确原提交全部一致，故只更正来源链接，未替换参数、势函数或正在运行的模拟。

## 四个获准参考膜

全部 11 种脂质的原 CHARMM-GUI 构象库已取得；各脂质原生 C36 单分子拓扑检查通过，完整计数和净电荷与四份配方一致。每个配方 2000 脂质、每叶 1000；未知“其他 10%”被排除，必须保持独立参考分支身份。

首次直接网格排布产生跨分子原子重叠。GROMACS 虽正常退出，EM 最大力为非有限值、未达到 1000 kJ/mol/nm 目标，明确判失败，不启动后续 MD。之后原 PACKMOL 周期排布保持全部原脂质、原构象、原力场和水/离子设置；第一次角度约束排布部分不收敛，原失败目录保留。当前改用头基位置和原远端碳的叶层方向几何约束继续初态构建。所有 PACKMOL 约束只用于坐标构建，不是 MD 势或锚定结论。

初始化面积与头基平面来自原独立参考坐标，未冒称测得的新膜厚。2 Å 排布距离来自 PACKMOL 初始构建建议，不是改变 C36 的原子半径或截断。最大力必须实际有限且达到声明目标后，才能进入下一阶段。四个新膜的平衡、正式重复 MD、蛋白插入和 ER 锚定尚未完成。

## 计算方法与复现

```text
<original-python> src/igem_drylab/calvados3_author_runner.py --request <private-request.json>
python -m igem_drylab.cg_trajectory_analysis --engine mpipi --request <private-observation-request.json>
python -m igem_drylab.reference_membrane_builder --request <private-reference-recipe.json>
python -m igem_drylab.mcp.server
```

CALVADOS 导出允许指定独立观察输出目录，不覆盖原模拟。采样分析使用可选独立环境 `requirements/sampling-py311.lock`；原 Python 3.8/OpenMM 7.6 势函数环境和桌面依赖不被升级。统计后处理在 CPU 执行。

自相关使用 PyMBAR 4.0.3 的非 fast、非 FFT 估计；以 ceil(g) 为等长块，保存全部生产均值及末尾不足整块的样本信息。块误差用 Student-t 区间，分段漂移用 Welch 区间；独立重复区间的样本是三个种子均值，不是数千相关帧。95% 相对半宽 10% 沿用已批准参数文档第 21 节，是报告精度目标，不是新的 M1 风险阈值。未检出漂移不证明稳态或相分离。

## 仍需完成

最新完整服务器回归为 **1040 passed、16 skipped**，包含原作者参考与已配置原生工具回归。真实轨迹 MCP 和浏览器值/导出/旋转验收单独核对；单元测试数量不替代上述实际作业。两次不完整测试启动曾漏掉 Node/Git 路径，失败日志保留；使用既有完整环境入口修正启动后通过，未放宽断言或将失败算作成功。

剩余单链轨迹和完整收敛检查；原多链 slab、有限尺寸与完整融合 CG；剩余 FuzDrop、TANGO 实际作业和适用范围内的 PSIPRED；完整口袋、项目 OC 招募肽而非不同序列模板的验证、双共价 FAD/Fe/2-OG 化学与拓扑；参考膜正式平衡与 ER 锚定；完整 M2 联合 assessment。TANGO 未取得合法原程序，PASTA 已按用户决定取消；PSIPRED 的完整官方数据库仍在下载，未用残缺库冒充。

软风险方向和组合权重仍未定稿，按用户要求先计算确定性数据；不自行加入权重、热区阈值或默认通过。功能锚点仍不等于完整口袋，固定模板准备与预测低置信区不能据此正式淘汰。

## 数据与方法源头

- [CALVADOS3 正确原提交](https://github.com/KULL-Centre/_2024_Cao_CALVADOSCOM/commit/51564e0edd126c44d6a7299fbe4414c579394ef4)
- [原 Mpipi 代码与数据](https://doi.org/10.6084/m9.figshare.16772812)
- [PyMBAR 自相关方法](https://pymbar.readthedocs.io/en/stable/timeseries.html)
- [ColabFold](https://github.com/sokrypton/ColabFold)、[DSSP](https://github.com/PDB-REDO/dssp)、[FreeSASA](https://freesasa.github.io/)
- [2FHA 原生物组装](https://www.rcsb.org/structure/2FHA)、[2PDZ 原 NMR 复合物](https://www.rcsb.org/structure/2PDZ)
- [1CKA](https://www.rcsb.org/structure/1CKA)、[1CKB](https://www.rcsb.org/structure/1CKB)：保留沉积序列与缺失坐标；不把不同项目肽当作精确实验复合物
- [3FW7](https://www.rcsb.org/structure/3FW7)、[3FW8](https://www.rcsb.org/structure/3FW8)、[3FW9](https://www.rcsb.org/structure/3FW9)、[3FWA](https://www.rcsb.org/structure/3FWA)：家族模板，原连接距离不是目标共价键力常数
- [CHARMM-GUI 原脂质库](https://charmm-gui.org/?doc=archive&lib=lipid)、[CHARMM 官方力场](https://mackerell.umaryland.edu/charmm_ff.shtml)
- [PACKMOL 21.2.3](https://github.com/m3g/packmol/releases/tag/v21.2.3)、[PACKMOL 初态构建手册](https://m3g.github.io/packmol/userguide.shtml)
- [FuzDrop 原服务](https://fuzdrop.bio.unipd.it/)、[原 PSIPRED](https://github.com/psipred/psipred)、[官方 UniRef90](https://ftp.ebi.ac.uk/pub/databases/uniprot/current_release/uniref/uniref90/)

项目序列、最新条件、四份配方、化学候选定义和原作者参考输入来自用户本轮补充包及此前已批准文件。清单完整与坐标准备不能代替真实实验验证。未证实的项目膜组分、化学状态和模拟结论保持未确定。

# 2026-10-04 代码审查第一版修复记录

依据 `iGEM_code_review_20261004.md`，审查基线为 `6f27641`。本次是接口、证据边界和数值正确性的第一版修复，不代表 M1–M5 全部科学要求或外部工具部署已经完成。测试序列、参数和测量数据均为软件夹具，没有写入项目科学参数库。

## 逐项对应

| 问题 | 本版修改及验收边界 |
| --- | --- |
| F01 | 新增 `m4-prediction-v2` 契约，保存模型类型、公式版本、单位、区室、归一化基准、完整内核输入和求解设置。十反应动态/稳态模型各用原求解器回放拟合；胞内、上清、总提取通过明确的观察算子比较。稳态必须由用户确认 `observation_kind=steady_state`；不支持的模型/区室返回不足数据。 |
| F02 | 动态运输改为体积守恒版本；非零胞外初值或启用运输要求显式两区室体积，不推断体积。验证不同体积、运输访问方式和分配模式下的骨架当量守恒。正式运输的体积及平衡适用性注册表适配仍未接通，正式路径明确阻断。 |
| F03 | 分开 `numerically_solved`、`evidence_ready`、`claim_scope`；正式物理计算不接受假设参数、缺失条件、unity 活性或旧有效富集映射。作者复现/机制敏感性不升级为校准预测。新增界面说明，用户上传反应通路计算默认属于未审核机制计算器。 |
| F04 | 审核完整融合序列及每个 IDR/linker；支持有序多 linker 和多 ORF 设计。M2/M3 使用设计级结果，多 ORF 的单条结构通过不能代替装配级证据。 |
| F05 | 构建注册表转换保留序列、IDR、linker、顺序和来源；内嵌序列可用于输入，重复或冲突 ID 明确报错。保存 OC 截短映射，但尚未自动获取并验证参考序列。 |
| F06 | baseline 不再绕过 M1；失败 baseline 只保留为回顾对照，不能进入生产 M2/M3/M4。 |
| F07 | 十反应模型执行完整配置的 PT/OC/DMT 门控、活动倍率及自定义运输参数名；阶跃门控在切换点分段求解。不支持的降解/初值/门控组合在配置层拒绝；物理和作者单位路径分离，物理路径的反应表只需身份列。尚未将所有模型配置拆成独立类型。 |
| F08 | 正式参数要求明确的目标宿主、温度、pH、测定上下文、构建及条件范围；非精确匹配不作为正式可用证据。动力学/活性参数绑定实际酶 ORF 哈希、辅因子和酶浓度定义。初始状态必须有时刻零、区室匹配的注册表证据。完整文献跨体系转移人工审核模型尚未实现。 |
| F09 | 校验预测完整输入、设计 ORF、链序列哈希及结构/参考/SASA/几何资源文件的实际字节哈希。跨域硬否决需要 PAE、独立构象和有来源的几何审核，局部 pLDDT 单独不够；未增加未经批准的 PAE 阈值。 |
| F10 | 先判定 M1 科学资格，再使用 top_n 计算预算；预算不足输出 budget_deferred，不伪装成科学拒绝。 |
| F11 | 净产物扣除初始产物；产率分母明确为初始可转化 8–14 骨架当量。零通量分数输出 null，不使用 epsilon 伪造为零。R5 累计反应量、胞外 13 净累积与终点池分开命名；总外排/回流积分尚未实现。 |
| F12 | 两个积分路径改用 SciPy trapezoid，消除 NumPy 2 专有接口；Python 3.10 枚举/时区兼容；规则资源随 wheel/sdist 构建，安装后无需源码 configs 目录。新增最低/当前数值版本 CI、独立安装 smoke 和 Windows Python 3.10 验证锁文件。锁文件不是全平台或外部工具环境锁。 |
| F13 | 拟合指纹包含规范化观测、时间、误差、删失、原始重复数据、区室/体积基准、模型输入及参数范围；JSON 排版不改变科学数据身份。原文件字节哈希单独保留。不同区室不能混合拟合；拟合候选仍需人工批准，不伪造独立时间点置信区间。 |

## 明确版本的公式修改

原 M3 方程及稳态 `ksec × dilute concentration` 分泌定义未改。本次按审查建议修正的动态运输使用 `galatea-dynamic-volume-v2-2026-10-04`：

```text
dCin/dt = reaction_rate - J
dCout/dt = (Vi / Ve) * J
backbone_amount = Vi * sum(Cin) + Ve * sum(Cout)
```

J 保留原前向/反向运输形式，按胞内体积归一化。物理浓度为 uM、体积为 L 时，物质量单位为 umol。守恒检查是该网络的骨架当量，不是元素质量守恒证明。无运输且胞外初始全零时不需要推断实际体积。

```text
equivalent_species = Cin + (Ve / Vi) * Cout
net15 = equivalent15(t_end) - equivalent15(0)
initial_convertible = sum(equivalent8_to_14(0))
target_yield_fraction = net15 / initial_convertible  # 分母为零时 null
```

这是一项明确的新指标定义，不再将预存产物算为新生成量；不是实测产率或胞外滴度。`final_15_total` 等旧兼容字段现在表示胞内体积等效总浓度，区室实测比较必须走预测契约。通量积分仍是采样轨迹数值积分，不是外排/回流累计量。

稳态保留原 unity 活性版本 `m4-step0-step8-2026-09-27`；仅当显式相活性倍率不为 1 时，标为 `m4-step0-step8-phase-activity-v2-2026-10-04`。该扩展把已选活性倍率乘入对应相竞争速率，没有将结构分数映射为活性。

## 测量输入与适用性

新模型测量需要 `measurement_compartment` 和 `concentration_basis`：

| 区室 | 基准 | 附加条件 |
| --- | --- | --- |
| intracellular | cell_volume | 细胞体积归一化观测 |
| extracellular | medium_volume | 模型实际输出培养基区室 |
| total_extract | extraction_volume | 模型 Vi/Ve 和测量 extraction_volume_l 全部显式 |

作者无绝对物理单位的输出不能与 uM 测量拟合；稳态模型尚未预测胞外浓度，不能用终点常数冒充动态时间序列。用户提供的体积或来源字符串本身不等于经审定的正式证据。

仍未实现/验证：M3 S4、r_target 及联合占位模型接入；ER 区室模型；完整跨条件证据转移审核；OC 截短参考序列核验；稳态稳定性/多根分析；累计总外排和回流；全模型配置类型拆分。本次没有真实运行 ColabFold/FreeSASA/Vina/CALVADOS/Mpipi，没有确认全部第三方工具可部署，没有重建 Tauri 安装程序。

## 验证记录

- 源码环境：Python 3.13.13 / NumPy 2.5.3 / SciPy 1.18.1，**312 passed，1 skipped**，140.35 秒。
- 非 editable wheel 环境：Python 3.10.11 / NumPy 1.24.4 / SciPy 1.10.1，**312 passed，1 skipped**，152.76 秒；确认导入路径位于独立环境 site-packages。
- 最后补充原文件哈希来源记录后，两套环境分别重跑 23 项 M4/M5 回归，全部通过；最低版本 wheel 重新构建、安装并在源码目录外通过规则资源和本地 MCP 注册表调用 smoke。
- 前端：3 项 Vitest 测试通过；TypeScript 检查和 Vite 生产构建通过。没有重新打包桌面安装程序。
- 覆盖生产 M4→M5 比较/拟合、新证据边界、体积守恒、零通量、规范化指纹等。一个既有测试依赖未提供的私有作者参考文件，跳过不能解释为通过。MCP smoke 是本地规则工具验证，不是全部外部科学工具/服务器可用性证明。

积分兼容依据：[SciPy 1.10.1 trapezoid](https://docs.scipy.org/doc/scipy-1.10.1/reference/generated/scipy.integrate.trapezoid.html)、[NumPy trapezoid](https://numpy.org/doc/stable/reference/generated/numpy.trapezoid.html)。CI 已配置但本地执行不等于远端 CI 已完成。

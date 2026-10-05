# 未完成项的可实施部分（2026-10-05）

基线 `6f0b370ca404d3ea234b185ae291981d194d1d53`。仅在 air-lab 执行模型和测试。没有新增生物参数或更改原 M3/M4 方程。

## 原式稳态局部稳定性与有限多起点搜索

共享原 RHS 求值器，解析求导每个相、同酶完整竞争分母及原 `ksec*C_dilute`，报告 Jacobian（1/h）、完整复特征值、谱横坐标和数值判别阈值。有效根自动报告局部线性化；零/近零特征值标记 inconclusive，不宣称渐近稳定。失败或 blocked 不给稳定性结果。

`igem.m4.analyze_steady_state` 已接入官方 MCP server、工具目录和 workflow allowlist。输入显式提供 `steady_state_input`、`initial_guesses_um`、`root_merge_atol_um`、`root_merge_rtol`、`eigenvalue_tolerance_per_h`。保留每个起点、失败原因、根归属和各根结果。有限起点不能证明所有根已找到、全局唯一性或无根；原根发布门槛未放宽。

软件验收：非零竞争两相 Jacobian 独立中心差分，单纯分泌的手算根/对角谱，稳定/不稳定/中性分类，实际自由池根族及 blocked 记录，真正跨进程 stdio MCP 多起点作业。air-lab `stability-transport-02.xml` 共 53 项通过（还包含原稳态和运输回归），其中新增稳态分析 8 个运行例。不以这些夹具代替实验验证。

算法与实现参考：[SciPy least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)、[SciPy eigvals](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.eigvals.html)。具体 Jacobian 来自原稿竞争公式的求导，而非换用另一种动力学。

## 科学边界

ER 腔/膜/胞质的完整机制未有本项目确定方程和交换/活性证据，不能自动编造“完整 ER 模型”。未获得真实独立数据，不宣称项目标定或验证完成。工具许可证、下载凭证与真实 ORF 仍须对应具体工具核验。

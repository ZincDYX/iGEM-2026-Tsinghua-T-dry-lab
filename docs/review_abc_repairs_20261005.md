# 最新 review A–C 修复记录（2026-10-05）

评审基线：357b0c0；依据用户提供评审第 10 节，历史章节不重复当成当前问题。计算、HTTP/MCP 集成及前端发布验收均在 validation host；本机通过 SSH 转发显示服务器页面。

## A：实际观测条件

共同入口在 observe_prediction，机制拟合在启动优化前调用同一检查。使用 conditions_for("metabolites") 的逐测量条件，比较宿主、菌株、pH、温度、体系及模型声明的相/序列/浓度定义/辅因子限制；沿用正式精确适用策略，不新设数值容忍范围。不同批次来源、原始 hash、核验人与记录身份不作为科学条件匹配键。

conditional_mechanism 冻结要求明确条件和实验模式，顶层与 prediction_contract 内条件矛盾拒绝。显式 demo/软件夹具保持数值回归路径，不升级为真实验证；未声明科学条件的旧数字夹具不用于 conditional_mechanism 留出。

RMSE、单位转换、删失、原动力学公式、冻结不重拟合均未改。旧不可辨识拟合测试补齐软件夹具条件，使原数学断言继续可达，并新增错 pH 的拟合前拒绝断言。

## B：确认版本

服务器计划绑定保存后的项目 revision、规范化输入 SHA-256 和 workflow SHA-256。普通与自定义流程均提交 confirmation；缺少绑定拒绝，变化后返回 409，要求重新生成审阅。SQLite BEGIN IMMEDIATE 在同一事务内取得项目、核对绑定并保存不可变运行快照；并发保存不能产生旧批准/新输入快照。

前端区分 saved/draft。编辑立即撤销旧方案，确认按钮要求有效绑定；保存/计划/运行/自定义审核响应受项目编辑 generation 保护，切换或编辑后的旧响应不覆盖当前项目。已有快照、恢复、克隆及 artifact 哈希语义保留。

## C：结果契约

从不可变 workflow 解析真实 tool_id，不按节点/parent 名称选择科学类型；已知稳态结果增加 schema_version/model_kind。M4 stdio MCP 的 {ok,result} 与普通通路输出分开解析，版本/公式/数值字段运行时验证。未知、旧版、缺字段显示原始 artifact，不补零；blocked/solver_failed 不显示有效预测。局部错误边界避免结果异常清空工作台。

同名序列记录比较显示版本和实际 sequence SHA-256；序列不同明确标记非相同构建，文本 ID 不作为正式 F3 身份。

## typed 科学项目接线

新增显式服务器配置路径检查/预览/确认入口；ProjectConfig、参数审批和已有 stage 原样复用。M1–M5 每个阶段作为独立持久节点接线，前序 records 经对应 typed model 校验；配置、规则、数据、M2 引用原始资源绑定 SHA-256，创建/恢复/每阶段执行前核验。配置文件路径所需依赖必须在 validation host 上存在；当前不是任意本机文件夹一键上传器。远程来源保持声明性 provenance，不把未获取的远程文件冒充本地 bytes 证据。运行中由外部进程改变文件的 OS 隔离不在本轮提供。

科学结果展示独立 status/numerically_solved/evidence_ready/claim_scope、缺失项、M3 free/bound/dilute/比例/容量与计量基准，以及 M4 分区室原单位时间序列与运输/残差/分析 artifact。WetLabResult JSON 使用显式类型导入并运行现有 QC，可人工指定为 M5 输入；普通 CSV/TSV 不冒充 typed 测量。保留人工审批，不从导入或数值接近自动批准。

F2/F3 已有配置及原始分析输出可以随管线使用和审阅；专门的候选设计编辑器、冻结留出交互向导、完整工具原始文件导入与完整 ER 页面仍是后续产品工作，不标为全部完成。

## 科学边界

软件与契约验收不是湿实验验证；实际项目条件、正式证据、校准与独立留出数据仍需提供。完整 ER/相关分布/任意通道化未扩展。本次不修改原文动力学公式、不新增虚构生物参数。

最终发布验收另记录实际 HEAD、测试数量、浏览器结果、部署容量及 bundle/证据校验值，失败或未验收项不记为完成。

服务器浏览器部署遵循 [Playwright 官方浏览器说明](https://playwright.dev/docs/browsers)：锁定现有 1.63.0 的 headless Chromium/FFmpeg，在工具目录下部署；8 个缺失 Ubuntu 动态库只解包用户目录并用 LD_LIBRARY_PATH，不安装到系统。下载所用私有网络配置保留于仓库外的原始验收记录；部署新增容量计入 15GB 审计。

实际浏览器检查曾发现初始化异步覆盖新建项目、StrictMode cleanup 后预览永不回显，均已修复；真实 stdio MCP 测试严格按 list_tools 发现的 inputs 包装调用，不将内部 helper 的扁平参数伪装成公共接口。最终三条浏览器流程必须全部通过才发布。

# FusionLab：通用融合蛋白与自组装平台（初版）

本版是可运行的平台基础，不代表已经验证了所有融合蛋白、自组装体系或任意动力学模型。Galatea 原始 M1–M4 公式与计算模块保留；平台只负责编排、输入管理、持久化和展示。

## 架构决策

采用本地模块化单体，不引入微服务。Project 是人工确认的结构化输入；Workflow 是带类型的输入绑定和依赖关系；Run 保存不可变的输入、流程、工具和环境快照；Artifact 保存文件哈希及上游节点。Scientist/Developer 两种视图共用这些对象。

| 原问题 | 本版实现 | 边界 |
| --- | --- | --- |
| DAG fan-out | 静态分支、动态 map、按输入顺序 gather，线程池有界并发 | 暂无分布式队列或自动扩缩容 |
| 中断恢复 | SQLite WAL、节点执行前持久化参数、心跳租约、逐 shard 恢复 | 已完成节点不重复；中断的非幂等调用必须先人工核对外部任务 |
| 字符串匹配 | 结构化错误码、判别联合输入、JSON Schema/Pydantic 校验 | 工具 ID、能力标签及字典键依然是字符串，但不根据自然语言错误消息决定重试 |
| 插件依赖冲突 | 每个内容哈希独立 venv、独立进程、带哈希的 requirements lock | venv 不是安全沙箱，只支持主动信任的插件 |
| stage 耦合 | 节点仅收到解析后的输入和 run/node/workdir；不接收活的 Project 全局状态 | 原有参考 pipeline 保留兼容，未声称已把它所有 stage 重写为通用模型 |

Agent 与 Executor 分离：初版使用人工确认的目标模板，任务说明只记录，不冒充已连接 LLM。Developer 可编辑并校验 workflow。已有科学工具通过真实 stdio MCP server 调用，不把本地函数调用伪装成 MCP 接入。

## 本地运行

在仓库根目录安装：`python -m pip install -e ".[software,test]"`。启动 API：`igem-drylab software serve --host 127.0.0.1 --port 8780`。

在 `software/dashboard` 运行 `pnpm install --frozen-lockfile`，然后 `pnpm dev --host 127.0.0.1`。浏览器访问 Vite 输出的地址。默认 API 数据位于 `outputs/platform`，不是前端 localStorage；localStorage 只记住当前项目、运行和显示模式。

创建项目 → 导入 FASTA/含 CDS translation 的 GenBank → 预览并确认 → 生成流程 → 确认执行 → 查看结果/历史。CSV/TSV 导入保存实验记录，并不自动拟合或批准科学参数。JSON 导入用于下述显式通路格式。

前端依赖和包管理器版本已锁定：使用 pnpm 10.30.3，不使用 `latest` 重新解析生产依赖。测试浏览器默认使用已有 Edge；可用 `FUSIONLAB_BROWSER_CHANNEL` 改为已有 Chrome。执行 `pnpm test` / `pnpm test:e2e`。

## 桌面模式

在 `software/dashboard` 运行 `pnpm desktop`；开发模式由 Tauri 启动 Vite。运行 `pnpm desktop:build` 构建含本地前端的桌面程序。需要 Tauri 官方的 Rust/系统构建依赖；没有额外 LaTeX/LLM/云端服务要求。

这是 source-first 桌面封装，**不是已经包含 Python 和所有科学工具的免安装发行包**。默认使用仓库根目录 `.venv`，先安装 `.[software]`。可设置 `FUSIONLAB_PYTHON` 指定 Python 环境、`FUSIONLAB_ROOT` 指定源码根目录、`FUSIONLAB_DATA_DIR` 指定数据目录；默认数据库和插件保存到操作系统应用数据目录。

Rust 只监督 Python 后端和提供连接信息，不承载科学公式。后端使用随机 loopback 端口和每次启动不同的会话令牌。Windows Job Object 负责关闭桌面后同时终止后端及其工具进程；若关闭时有任务，之后需依据持久状态恢复。Linux/macOS 原生打包和子进程回收未在本次 Windows 环境验证。

原生 smoke 命令：`scripts/smoke_desktop.ps1 -Executable <已构建exe> -DataDir <独立测试目录>`。不会打开可见窗口，也不使用正式项目数据库。

## 自定义反应通路

`examples/workflows/user_pathway.json` 给出完整输入。物种/酶/反应名称不绑定 Galatea；用户必须提供化学计量、参数、单位、来源、相分配和初始猜测。

当前唯一速率律：`two_phase_competitive_mm_v1`。每个反应一个消耗系数为 −1 的底物；同一酶的底物在同一个竞争分母中，不能把互相竞争的反应当成独立 MM。多底物、Hill、质量作用律、SBML 任意模型尚不支持，会拒绝而不是偷偷转换。该通路功能是新增的明确模型，不取代 Galatea 原文 Step 0–8，也不凭空定义通用产率。

具体计算为：稀相浓度 `S_l = S_avg / (1-phi+phi*Kp)`，浓相 `S_d=Kp*S_l`；每相 `v_r=kcat_r*E_phase*(S_phase/Km_r)/(1+sum(S_phase/Km))`；总体速率 `phi*v_d+(1-phi)*v_l`；稳态残差 `J_in + N*v - ksec*S_l`。外排项按原契约使用未乘稀相体积分数的稀相浓度。`phi=0` 时浓相记录为零。结果有效性由求解器状态和所有残差共同判断；无稳态时不能解释为有效预测。

## 复现与限制

快照包含实际输入、模型标识、精确特征定义、工具版本/源码哈希、插件哈希、输入文件哈希、Python 和主要数值包版本。恢复前核验输入、结果文件和运行环境；不一致时拒绝拼接新旧结果，应创建新的运行。当前内置计算无随机采样，因此不伪造随机种子；未来随机工具必须把 seed 放入显式输入契约。

恢复提供幂等调用的至少一次执行，不承诺外部副作用 exactly-once。暂停/取消是协作式的：不再发新任务，已执行任务结束后保存结果。旧 `/api/dashboard` 路由仅兼容保留，仍是原始内存 ledger；新界面不使用它，应使用 `/api/platform`。

尚未完成的产品能力应单独实现和验收：LLM 自动规划、通用结构预测及 LLPS 证据整合、自动湿实验参数拟合/审批、SBOL/SBML、非可信插件 OS sandbox、跨机器任务恢复、完整无 Python 安装包。不能将组成或分子量核验称为自组装成功预测。

新界面现有显式 typed 科学项目入口：在“项目数据”检查服务器已有 ProjectConfig YAML、预览配置/证据 SHA-256 并确认保存；在“分析流程”选择“M1–M5 原式科学项目管线”，审阅后运行。各模块作为持久化 DAG 节点复用原有 stage，展示缺失项与科学状态；不把未审批参数或裸 MCP 数字求解器升级为正式项目。MCP 科学工具仍通过真实 stdio 连接；原有 pipeline/CLI 保留。

选择 WetLabResult JSON 类型可校验测量并显示 QC/条件/来源，再人工指定 M5 输入，不自动批准或拟合普通表格。配置路径及其依赖当前须在服务器存在；不是本机目录一键上传器。专用 F3 候选编辑器、冻结留出向导、完整 PDB/预测器原始文件导入和工具目录传递依赖追踪尚未全部实现。参见 review_abc_repairs_20261005.md。

plans/custom plans 返回 project revision、规范化输入 hash 和 workflow hash；runs 必须携带 confirmation。在单个 SQLite 写事务中校验并创建快照；编辑草稿撤销旧方案，变化返回 409。结果按工具身份和 schema/公式版本渲染；未知版本保留原始 artifact，不能按节点名称猜类型。

## 工具许可证

授权/许可证是作者规定的使用和分发条件，不等于所有工具都收费，也不等于需要 API key。

- SignalP 6：学术 portable 下载与非学术使用不同，按 [DTU 官方页面](https://services.healthtech.dtu.dk/services/SignalP-6.0/) 获取许可和程序；平台不能代用户接受机构许可。
- DeepTMHMM：官方说明服务供学术和商业用户免费使用；商业用户在自己服务器运行需商业许可，学术用户不需要购买商业许可。[官方说明](https://services.healthtech.dtu.dk/services/DeepTMHMM-1.0/)
- TANGO：研究用途向学术及非营利机构免费提供学术许可；商业用途联系作者；提供编译程序而非源码。[官方许可](https://tango.crg.es/licensing-and-services)
- PASTA 2：作者下载页面要求机构邮箱、PI/资深研究者提交，并接受许可；本次未确认完整许可正文，商业使用和再分发权限仍不确定，不能直接随安装包分发。[作者下载页](https://protein.bio.unipd.it/downloads)

安装成功、许可已取得、工具可调用、科学输入适用是四个不同条件，需要分别核验。

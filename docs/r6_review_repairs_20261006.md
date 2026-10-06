# r6 review 修复记录

依据：用户提供的 `FusionLab_r5_current_status_review_20261006.md`，基线 `1cc1b56`。未取得文中独立证据 ZIP；不把审核里的缺陷复现用例当产品通过证据。

## A：输入与公开错误

- IO-01：去除 blob 路径对 asset 的唯一归属；显式导入创建独立逻辑 ID，内容仍可去重。旧 SQLite 自动迁移并保留全部既有 ID/归属/hash。解析文件身份在写事务中认领，跨项目下载仍拒绝，篡改仍拒绝。
- IO-02：服务器登记科学 bundle 根；入口不再把 `configs/` 当全部授权范围。仅包根和两份明确随软件发行的 M1 规则文件可读。M2 结构、参考、几何和 SASA 文件沿原目录绑定，不重写原文件。
- ERR-01：公开错误 DTO 包含诊断 ID、白名单原因/字段、逻辑缺文件名与修复动作。私有绝对路径不公开；前端保留诊断上下文。
- PL-01：示例只公开 Python 版本，隔离解释器路径由私有子进程 oracle 检查。两插件实际安装互不兼容的本地 wheel 并核对各自版本，未放宽隐私门控。旧 MCP 测试保留 `-B` 与秘密环境隔离断言。

验证：输入/安全/既有提案软件回归 22 通过；插件协议、真实示例隔离与 MCP 环境专项 8 通过；TypeScript/Vite 生产构建通过。曾出现测试包缺少必填 run 和篡改状态码旧预期，已按实际合同修正并重跑，未通过降低产品约束求绿。

科学核心七文件不改动；尚不声称正式科学预测、真实外部工具或完整原生发布验收通过。

## B：执行状态与审阅

- EX-01：queued/paused/interrupted 且无 worker 的取消，事务内直接进入 cancelled；重复取消不变，不能恢复；保留旧产物。running/有 worker 仍协作取消，不强杀求解器；最终写入与 cancel 竞态也以取消终态收敛。dispatcher 跳过已取消队列项。
- EX-02：默认执行必须引用 accepted proposal。接受绑定输入、DAG、工具版本/实现 hash、环境与私有 profile 的不透明 hash；插入运行的同一事务再次查接受状态与 profile 身份。接受不批准科学参数。
- 旧 `/plans` 与 `/plans/custom` 保留，但返回 `review_id`，客户端必须先调用 `/proposals/{review_id}/decision` 接受，再显式提交 `execution_type=manual_review` 和 `manual_review_id`。省略审阅不再兼容；这是审阅安全迁移，不以 development 模式绕开。行动账本记录 `manual_plan_confirmed`。幂等请求只有一次执行记录。
- EX-03：clone 返回 status=proposed 的新提案与旧/新 review identity；不创建或启动运行，用户接受新范围后才能执行。旧快照不修改。

初轮软件回归 32 通过，覆盖实际工作线程的暂停/取消、队列取消、工具变化、clone、取消/恢复并发、幂等以及原 crash/non-idempotent 测试。profile 与显式手动审阅追加专项及提案回归 16 通过。

用户再次确认：科学数值/作者回归只在服务器运行，本机不运行这些测试。

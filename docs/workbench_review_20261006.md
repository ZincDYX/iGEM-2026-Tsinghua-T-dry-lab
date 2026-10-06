# 2026-10-06 工作台与安全审核修复记录

基线 `a886a9a`。按用户提供 review 的 PR 1–4 顺序实施，不修改科学公式、默认生物参数、求解器、审批或原式容差。本轮不访问真实服务器、不读取已有 API/SSH 凭据、不在本机复现论文；软件夹具使用明确假标记。旧 Git 历史和私有审计原文不改写。

## PR 1：公开边界与认证

新增明确 public view 和独立私有 runtime profile 存储。项目/节点/运行/产物视图不返回工具命令、部署目录、原始节点输入、内部数据库行或绝对路径。文件通过登记的逻辑身份与项目归属核验。原科学文件/hash 保留，秘密或私有路径原文件的下载被隔离，不通过字符串替换伪造原 hash。

运行 profile 由维护者私有集成接口写入，HTTP 科学项目不接受 `tools` 运维字段。profile identity 单独进入运行绑定，版本变化要求新运行。旧记录保留，公开读取经投影；没有迁移真实凭据。

节点和 HTTP 错误返回安全 code、说明与 diagnostic_id，原文留私有诊断。受信任插件的环境能力需要维护者按源码 hash 单项授权，不自动兑现 `secret_env`。实际子进程、ensurepip/pip 都使用最小环境；已知秘密输出不发布为有效产物。venv 仍不是 OS 沙箱，没有声称阻止恶意插件读取同账户主机数据或外传。

默认后台必须认证；匿名开发模式需显式 `--dev-anonymous`，只能绑定回环。移除 artifact query session token，下载改带认证头的 fetch/Blob，并校验项目归属。远程桌面尚无受控认证会话提供者，因此明确阻断，不能以 SSH/匿名 HTTP 成功宣称生产可用，也不访问实际 SSH 配置来完成本轮测试。

基础后台不再同步等待 MCP discovery；能力异步显示 checking/ready/unavailable。Tauri 自定义 commands 使用 AppManifest 和仅限内置 main 窗口的能力文件，不授权 remote origin/shell/fs。参考 [Tauri capabilities 官方说明](https://v2.tauri.app/security/capabilities/)。

发布脚本改运行时允许列表；完整源码/测试仍在 code bundle，不全塞入程序。import check 禁止写 pyc；在清单前固定文件，不在清单后修包。最终包仍须另行实际验收，不能把脚本修改当成包已经重建成功。

实际软件测试：6 项 HTTP/公开边界与文件身份测试、3 项真实标准库插件反例、9 项前端原有测试通过。首次 pytest 因默认 Temp 权限在 setup 阶段失败，换全新独立目录后暴露一项跨平台路径检查缺陷，加入 POSIX/Windows 双路径判据后上述安全断言通过；没有删断言。TypeScript 编译通过。后续批次会添加运行控制、分页和完整工作台 E2E。

## 尚在实施

PR 2：正式上游 artifact 来源绑定、全局资源准入、真实边界控制。

PR 3：轻量摘要/增量事件/按需结果、无重叠轮询和短写事务。

PR 4：三栏工作台、结构化 Agent 提案、统一 durable 账本、阶段控制与迭代。

真实模型 API、受控远程会话、OS 级不可信插件沙箱、完整科学参考回归与最终发布包验收，不由这些软件夹具测试证明。

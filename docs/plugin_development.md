# Plugin Development Guide（protocol 1）

完整示例：`examples/plugins/sequence_composition`。它不引用 Galatea 或项目 Python 包，使用真实独立 venv 和进程。示例仅统计序列组成，不是 LLPS/聚集预测器。

## Manifest

入口是 `plugin.json`，由 `workflow.plugins.PluginManifest` 的 Pydantic/JSON Schema 校验。必需字段：`id/name/description/version/capability/license/entrypoint/input_schema/output_schema`。运行时目前为 `python_venv`；可选 `repository/requirements_lock/permissions/secret_env/timeout_seconds/idempotent/resource`。

`permissions` 是 `network/gpu/filesystem` 声明，不是 OS 强制限制。前端必须先展示来源、内容哈希、许可和权限，再由用户确认信任。确认后重新核验哈希，禁止用已经变化的源代码替换预览版本。源码内容决定安装目录和注册 ID：`plugin.<id>.<hash前12位>`，新版本不覆盖旧运行所依赖的版本。

有第三方依赖时，提供 pip 的完整 `--require-hashes` lock 文件，包含全部传递依赖、固定版本与 SHA-256。每个版本创建独立 venv，不使用主程序的 site-packages。不接受无锁的 requirements 自动解析。安装失败的环境不会注册；只有完整安装标记才允许复用。

## 进程契约

入口被执行为：`<独立venv的python> -I <entrypoint> --input <JSON文件> --output <JSON文件>`。

从 input 读取 JSON 对象，按 output schema 写入 JSON 对象，正常完成返回退出码 0。stdout/stderr 用于日志，不能代替输出文件。每次 attempt 有独立工作目录，避免重试误用旧输出。主程序按 JSON Schema 校验输入及输出；超时、非零退出、源码哈希变化都有明确错误。主环境秘密不默认继承，只有 manifest 的 `secret_env` 明确列出的变量会传入；这些变量名本身也需要用户审查。

`idempotent=false` 的外部提交/收费 API/实验执行，进程中断后不会自动重发，必须核对原任务。当前还没有通用 external-job reconciliation UI，因此插件应尽量先提供幂等计算接口。随机工具把 seed 作为显式输入，不读隐藏的全局随机种子。

venv **不是安全沙箱**。可信 Python 可以访问宿主文件和网络；不要安装未经审查的远程代码。OS/container sandbox 是后续独立能力，不能用权限标签冒充。

## 验收和贡献

先调用 `/api/platform/plugins/inspect`，再带 `trusted=true/expected_hash=<检查所得哈希>` 调用 install。在单一工作区的 Workflow 中使用返回工具 ID，并通过 `/api/platform/workflows/validate` 校验。

贡献至少提供输入输出样例、许可、固定依赖、独立进程 smoke test、失败/超时测试和科学适用范围。不得输出伪造预测值，缺少证据应明确返回。大文件模型不要提交到 Git；记录下载来源、版本、哈希和合法获取方式。

GitHub 下载入口 `/api/platform/plugins/github` 只接受公开仓库 URL 与完整 40 位 commit；下载根目录必须含 `plugin.json`。下载/解压阶段不执行代码，检查路径穿越和 symlink，再返回源码供预览。每个代码归档限 256 MB，不用于下载大模型。私有仓库 OAuth、完整更新/卸载管理、OS sandbox 尚未实现。

`GET /api/platform/schemas` 返回 Project、Workflow、Pathway 和 PluginManifest 的 JSON Schema；Pydantic 类是唯一 schema 定义源，不维护另一套手写副本。

用户已于 2026-10-04 把预算更新为十进制 15 GB。插件目录注册前按 15,000,000,000 字节检查总量，但这是该目录的检查：不是整个 validation host 外部工具的合并预算，也不对 pip 安装过程的临时占用提供 OS 硬配额。部署验收仍必须合并审计所有外部环境、程序、模型和缓存。

"""Allowlisted public diagnostics; raw exceptions stay in the private ledger."""
from .models import Contract


class PublicError(Contract):
    code: str
    message: str
    diagnostic_id: str
    field_paths: list[str]
    logical_files: list[str]
    actions: list[str]


ERROR_GUIDANCE = {
    "scientific_project_missing_local_dependencies": ("科学包缺少依赖文件，请按原相对目录补齐后重新检查。", ["scientific_project.evidence_files"], ["补齐列出的文件", "重新上传科学包"]),
    "scientific_file_outside_authorized_workspace": ("依赖文件越出已上传科学包；请移入包内并使用相对路径。", ["scientific_project.config"], ["检查依赖相对路径", "重新上传科学包"]),
    "invalid_upload_identity": ("上传文件路径重复或不安全。", [], ["保留唯一的包内相对路径"]),
    "file_project_mismatch": ("此文件未授权给当前项目。", ["files"], ["在当前项目重新导入文件"]),
    "file_identity_changed": ("文件内容与已登记的 SHA-256 不一致。", ["files"], ["重新导入并审阅修改后的文件"]),
    "project_revision_conflict": ("项目已被其他操作更新。", [], ["重载项目并核对草稿"]),
    "runtime_settings_not_scientific_input": ("科学包不能包含私有工具运维配置。", ["scientific_project.config"], ["移除 tools 运维配置"]),
    "proposal_not_accepted": ("该提案尚未接受，不能开始执行。", [], ["审阅并接受当前提案"]),
    "plan_input_or_workflow_changed_regenerate_and_review": ("输入或计划已变更，原审阅不再适用。", [], ["重新生成并审阅提案"]),
    "run_is_terminal": ("该运行已终结，不能恢复。", [], ["创建迭代并重新审阅"]),
    "accepted_proposal_binding_required": ("执行必须引用已接受且身份一致的审阅记录。", [], ["审阅并接受当前提案", "旧客户端请显式提交 manual_review 身份"]),
    "reviewed_tool_or_profile_changed": ("工具或运行配置身份已变化，原审阅不再适用。", [], ["生成新提案并核对身份差异"]),
}

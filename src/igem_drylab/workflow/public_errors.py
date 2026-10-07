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
    "iteration_dependency_graph_invalid": (
        "The iteration dependency graph could not be verified. No new project was published.",
        ["scientific_project.evidence_files"],
        ["Check the listed package files and their hashes", "Reimport the complete original directory tree"],
    ),
    "scientific_project_missing_local_dependencies": ("Scientific dependencies are missing. Restore the original relative directory tree and check again.", ["scientific_project.evidence_files"], ["Attach the listed files", "Reimport scientific package"]),
    "scientific_file_outside_authorized_workspace": ("A dependency is outside the uploaded package. Use an authorized relative path.", ["scientific_project.config"], ["Check relative dependency paths", "Reimport scientific package"]),
    "invalid_upload_identity": ("Duplicate or unsafe upload path.", [], ["Use unique package-relative paths"]),
    "file_project_mismatch": ("File is not authorized for this project.", ["files"], ["Import into this project"]),
    "file_identity_changed": ("File content differs from the registered SHA-256.", ["files"], ["Reimport and review changed files"]),
    "project_revision_conflict": ("Project revision changed in another operation.", [], ["Reload the project and review the draft"]),
    "runtime_settings_not_scientific_input": ("Scientific packages cannot contain private runtime tool settings.", ["scientific_project.config"], ["Remove runtime tools settings"]),
    "proposal_not_accepted": ("Accept the reviewed proposal before execution.", [], ["Review and accept the current proposal"]),
    "plan_input_or_workflow_changed_regenerate_and_review": ("Inputs or workflow changed; previous review is no longer applicable.", [], ["Regenerate and review the proposal"]),
    "run_is_terminal": ("Terminal run cannot be resumed.", [], ["Create and review an iteration"]),
    "accepted_proposal_binding_required": ("Execution requires an accepted review with matching identity.", [], ["Review and accept the current proposal", "Legacy clients must provide explicit manual_review identity"]),
    "reviewed_tool_or_profile_changed": ("Tool or runtime identity changed; review again.", [], ["Generate a new proposal and inspect identity differences"]),
}

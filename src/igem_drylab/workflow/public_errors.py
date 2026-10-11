"""Allowlisted public diagnostics; raw exceptions stay in the private ledger."""
from .models import Contract, WorkflowError


class PublicError(Contract):
    code: str
    message: str
    diagnostic_id: str
    field_paths: list[str]
    logical_files: list[str]
    actions: list[str]


ERROR_GUIDANCE = {
    'trusted_plugin_install_requires_deployment_authorization': ('This hosted workspace does not permit trusted-code installation.', [], ['Use a trusted local workspace or ask the deployment administrator to install the reviewed plugin']),
    'assistant_private_secret_unavailable': ('The saved model credential is unavailable in this OS user context.', [], ['Configure the optional model again in your current private workspace; never copy credentials into a project']),
    'parameter_source_record_immutable': ('This saved parameter value or source cannot be overwritten.', ['scientific_project.config.parameters'], ['Create a linked Override candidate, explain the reason, then review it separately']),
    'assistant_endpoint_requires_administrator_allowlist': ('This hosted workspace has not authorized that model endpoint.', [], ['Ask the deployment administrator to authorize its exact endpoint or use a local workspace']),
    'assistant_local_endpoint_requires_local_workspace': ('A local model requires your own local workspace.', [], ['Start fusionlab serve locally; a hosted server cannot connect to your computer through its localhost']),
    'assistant_requires_chat_completions_endpoint': ('Enter the complete compatible chat completions endpoint.', [], ['Use the provider endpoint ending in /chat/completions']),
    'assistant_provider_disabled': ('The Assistant model is disabled.', [], ['Keep using deterministic tools or configure an optional model first']),
    'assistant_endpoint_request_failed': ('The saved model endpoint did not accept the connection test.', [], ['Check the provider, model, endpoint and private credential; scientific tasks were not started']),
    'assistant_response_invalid': ('The model returned an incompatible response.', [], ['Use manual/template planning or a model that passes the public JSON test']),
    'skill_revision_changed': ('This instruction Skill has changed since it was opened.', [], ['Reload its latest revision before editing']),
    'skill_name_description_trigger_version_source_license_required': ('The Skill is missing required frontmatter.', [], ['Supply name, description, trigger, version, source and license as text']),
    'formula_domain_or_nonfinite_result': ('This formula has no finite real result for the supplied inputs.', ['workflow.nodes.inputs.spec'], ['Check division by zero, logarithm/square-root domains and exponent overflow; no substitute result was generated']),
    'method_draft_has_no_execution_spec': ('This formula version contains a document only, not an executable expression.', [], ['Create a new version with an explicit scalar expression, sourced inputs and result unit']),
    'assistant_response_truncated': ('The model response ended before its JSON was complete.', [], ['Shorten the planning request or check the model service; no incomplete plan was accepted']),
    'plugin_disabled': ('This trusted plugin version is disabled.', [], ['Enable the reviewed version or choose another tool; no plugin process was started']),
    'duplicate_node_id': ('Two modules have the same identity.', ['workflow.nodes'], ['Use distinct identities for distinct modules']),
    'unknown_policy_node': ('Execution scope still refers to a removed module.', ['workflow.execution_policy'], ['Review the target and checkpoints before deleting this module']),
    'tool_not_in_execution_authorization': ('This tool is outside the workflow execution scope.', ['workflow.execution_policy.allowed_tools'], ['Explicitly review the changed tool scope']),
    'memory_limit_not_supported_by_process_backend': ('This backend cannot enforce a hard process memory limit.', ['workflow.execution_policy.memory_limit_mb'], ['Do not claim an unenforced limit; use an administrator-managed isolated runtime']),
    'workflow_definition_required': ('A new workflow document needs an executable workflow definition.', ['workflow'], ['Choose a method or create a proposal first']),
    'workflow_layout_references_missing_node': ('The saved layout or selection refers to a module that no longer exists.', ['layout','selected_node_id'], ['Reload the latest workflow and select an existing module']),
    'workflow_cycle': ('These connections create a circular dependency.', ['workflow.nodes'], ['Remove the connection that returns to an upstream module']),
    'unknown_dependency': ('A remaining module still refers to a removed or unknown upstream module.', ['workflow.nodes'], ['Keep the required upstream module or explicitly revise all affected input bindings']),
    'unknown_tool': ('The selected tool is not registered in this workspace.', ['workflow.nodes.tool_id'], ['Select an installed tool; tool availability is separate from scientific readiness']),
    'workflow_reference_type_mismatch': ('The declared tool output type does not match the receiving input.', ['workflow.nodes.inputs'], ['Choose an output and input with compatible types']),
    'workflow_required_input_argument_missing': ('The selected tool requires an input that is not bound.', ['workflow.nodes.inputs'], ['Bind the required input before saving this workflow']),
    'workflow_unknown_input_argument': ('This input is not declared by the selected tool.', ['workflow.nodes.inputs'], ['Review the tool input contract rather than reusing incompatible bindings']),
    'workflow_input_value_or_project_binding_invalid': ('An input value or project binding does not match the tool contract.', ['workflow.nodes.inputs'], ['Check the selected object, field type and required values']),
    'workflow_map_requires_list': ('Fan-out requires a collection, not a single object.', ['workflow.nodes.map'], ['Select a collection of compatible objects']),
    'workflow_map_item_type_mismatch': ('One or more fan-out items do not match the receiving tool input.', ['workflow.nodes.map'], ['Review the collection and the tool input type']),
    'workflow_output_field_not_declared': ('The selected field is not in the upstream output contract.', ['workflow.nodes.inputs'], ['Select a declared upstream output field']),
    'workflow_document_revision_conflict': ('This workflow was edited in another operation.', [], ['Reload the saved workflow and review the latest revision']),
    'workflow_project_revision_changed': ('Project inputs changed while this workflow was being edited.', [], ['Reload the project and recheck the input bindings']),
    'formal_stage_requires_registered_upstream_result': ('This scientific stage needs the registered result from its required upstream stage.', ['workflow.nodes.inputs'], ['Keep the original scientific dependency and its result binding']),
    'formal_stage_predecessor_mismatch': ('This connection does not match the scientific method dependency.', ['workflow.nodes.inputs'], ['Keep the method-required upstream stage; do not substitute an unrelated result']),
    "jpred_requires_recoverable_native_route": ("JPred is configured to submit only, not retrieve a prediction.", [], ["Configure the backend native JPred runner with the installed jpredapi client", "Keep existing job records; do not submit the same job again"]),
    "remote_submission_reconciliation_required": ("The service may have accepted this job, but its acknowledgement is unknown.", [], ["Reconcile the original submission log or service job identity", "Do not resubmit until the original job is accounted for"]),
    "remote_retrieval_failed": ("The known remote job is retained; its result could not yet be retrieved.", [], ["Retry retrieval of the same job", "Check the service and the backend diagnostic"]),
    "annotation_requires_json": ("Choose an imported annotation JSON file.", ["files"], ["Import and save the source file first"]),
    "annotation_binding_conflict": ("An existing source binding contradicts the selected file; nothing was rebound.", ["files"], ["Check the selected files and the original annotation source"]),
    "structure_annotations_already_linked": ("This structure already has a different linked annotation source.", ["files"], ["Preserve the existing source; use a new project for a changed annotation set"]),
    "disclosure_quarantined": ("This original is quarantined by a credential or private-value rule; it has not been exported.", [], ["Review the original locally", "Import a separate scientific file without credentials"]),
    "invalid_image_source": ("The image could not be decoded in its declared format.", ["files"], ["Check or re-export the original image"]),
    "image_media_type_mismatch": ("Image bytes do not match the filename format.", ["files"], ["Use the correct PNG or JPEG filename"]),
    "image_decode_budget_exceeded": ("Image exceeds the pixel budget or has multiple frames.", ["files"], ["Import a single-frame image within the display budget"]),
    "display_source_missing": ("The registered original is missing.", ["files"], ["Restore or reimport the original"]),
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


def diagnostic_code(error, fallback):
    """Recover typed graph failures wrapped by Pydantic/FastAPI, not text matches."""
    if isinstance(error, WorkflowError):
        return error.code
    errors = getattr(error, 'errors', None)
    if callable(errors):
        for issue in errors():
            wrapped = issue.get('ctx', {}).get('error')
            if isinstance(wrapped, WorkflowError):
                return wrapped.code
    return fallback

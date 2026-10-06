"""Non-solving hints from the existing typed input/parameter contracts.

No stage invocation, parameter approval, topology inference or scientific claim.
Final stages remain authoritative for candidate-specific/evidence gates.
"""
from hashlib import sha256

from igem_drylab.parameters import ParameterRegistry, resolve_requirement
from igem_drylab.parameters.requirements import requirements_for_stage
from .models import Contract, Project
from .scientific_project import ScientificProject
from .store import canonical


class KnownMissingInput(Contract):
    stage: str
    code: str
    field_path: str
    construct_id: str | None
    condition_id: str | None
    reason_codes: list[str]
    source_kind: str


class ScientificPrecheckView(Contract):
    project_id: str
    project_revision: int
    input_sha256: str
    missing: list[KnownMissingInput]
    scope: str = "declared_inputs_and_parameter_contracts_only"
    final_stage_gates_required: bool = True
    scientific_approval_granted: bool = False
    limitations: list[str]


def precheck(project: Project) -> ScientificPrecheckView:
    missing=[]
    def absent(stage,code,field,source):
        missing.append(KnownMissingInput(stage=stage,code=code,field_path="scientific_project.config."+field,
            construct_id=None,condition_id=None,reason_codes=["not_declared"],source_kind=source))
    if project.scientific_project is None:
        missing.append(KnownMissingInput(stage="m1",code="typed_scientific_project",field_path="scientific_project",
            construct_id=None,condition_id=None,reason_codes=["not_declared"],source_kind="typed_configuration_and_original_files"))
    else:
        science=ScientificProject.model_validate(project.scientific_project)
        science.verify()
        config=science.config
        if not (config.inputs.constructs or config.inputs.construct_records):
            absent("m1","explicit_construct_definitions","inputs.constructs","construct_sequence_and_identity")
        if config.execution.mode=="real" and config.stages.m1_llps.require_external_evidence_in_real_mode and config.stages.m1_llps.predictor_evidence_file is None:
            absent("m1","registered_predictor_evidence_file","stages.m1_llps.predictor_evidence_file","predictor_original_outputs_or_reviewed_tool_jobs")
        if config.stages.m2_fusion.structure_metrics_file is None:
            absent("m2","structure_metrics_file","stages.m2_fusion.structure_metrics_file","same_construct_structure_reference_mapping_geometry")
        if config.stages.m5_feedback.wetlab_results_file is None:
            absent("m5","wetlab_results_file","stages.m5_feedback.wetlab_results_file","typed_measurements_units_replicates_qc")
        registry=ParameterRegistry(config.parameters)
        scopes=[(item.id,item.condition_id) for item in config.inputs.designs] or [(item.id,config.stages.m4_reaction.condition_id) for item in config.inputs.constructs] or [(None,config.stages.m4_reaction.condition_id)]
        for stage in ("m3","m4"):
            for construct_id,condition_id in scopes:
                for requirement in requirements_for_stage(config,stage):
                    result=resolve_requirement(registry,requirement,config.experimental_context,
                        allow_assumptions=config.execution.allow_assumptions,construct_id=construct_id,condition_id=condition_id,
                        require_provenance=config.execution.mode=="real" and config.execution.require_provenance)
                    if result.selected_parameter is None:
                        missing.append(KnownMissingInput(stage=stage,code=requirement.name,field_path="scientific_project.config.parameters",
                            construct_id=construct_id,condition_id=condition_id,reason_codes=result.reasons,
                            source_kind="reviewed_condition_compatible_parameter_record"))
    return ScientificPrecheckView(project_id=project.id,project_revision=project.revision,
        input_sha256=sha256(canonical(project.model_dump(mode="json")).encode()).hexdigest(),missing=missing,
        limitations=["仅检查已声明输入与现有参数合同；不是完整候选门控或运行许可。",
            "构建/条件身份未声明时不能判断候选范围；M3 上游上下文可能进一步收紧需求。",
            "未登记预测器文件可能由受审阅真实工具作业生成；预检不会调用这些工具。",
            "未检查完全部科学 gate；空缺项列表也不代表证据充分、实验验证或允许预测。"])

from __future__ import annotations

from typing import Any, Literal
from hashlib import sha256
from pathlib import Path

from pydantic import Field

from igem_drylab.constructs.linker_features import M1FeatureDefinitions, compute_protparam_evidence, compute_sequence_features
from igem_drylab.constructs import linker_features

from .models import AssemblyRecord, Contract, LiteralInput, MapSpec, NodeInput, Project, ProjectInput, SequenceRecord, Workflow, WorkflowNode
from .pathway import Pathway, solve_pathway
from igem_drylab.resources import default_config_path
from .tools import NodeContext, ToolDefinition, WorkflowTools


class SequenceInput(Contract):
    item: SequenceRecord
    feature_definitions: M1FeatureDefinitions


class GatherInput(Contract):
    results: list[dict[str, Any]]


class AssemblyInput(Contract):
    item: AssemblyRecord
    sequence_metrics: list[dict[str, Any]]


class PathwayInput(Contract):
    pathway: Pathway


def sequence_analysis(payload: SequenceInput, context: NodeContext) -> dict[str, Any]:
    definition_hash = sha256(payload.feature_definitions.model_dump_json().encode()).hexdigest()
    features = compute_sequence_features(payload.item.sequence, definitions=payload.feature_definitions, definitions_sha256=definition_hash)
    properties = compute_protparam_evidence(payload.item.sequence, input_sha256=features.sequence_sha256)
    return {"schema_version": "sequence-metrics-v1", "id": payload.item.id, "role": payload.item.role, "features": features.model_dump(mode="json"), "protparam": properties.model_dump(mode="json"), "interpretation": "Sequence composition and physicochemical calculation; LLPS and assembly are not established by these metrics."}


def assembly_inventory(payload: AssemblyInput, context: NodeContext) -> dict[str, Any]:
    metrics = {item["id"]: item for item in payload.sequence_metrics}
    missing = set(payload.item.subunits) - metrics.keys()
    if missing:
        raise ValueError(f"missing_subunit_metrics:{sorted(missing)}")
    return {
        "assembly_id": payload.item.id, "subunits": payload.item.subunits,
        "total_subunits": sum(payload.item.subunits.values()),
        "molecular_weight_da": sum(metrics[name]["protparam"]["molecular_weight_da"] * count for name, count in payload.item.subunits.items()),
        "interpretation": "Declared stoichiometry inventory. Structural feasibility requires structure/interface evidence.",
    }


def gather(payload: GatherInput, context: NodeContext) -> dict[str, Any]:
    return {"count": len(payload.results), "results": payload.results}


def pathway_analysis(payload: PathwayInput, context: NodeContext) -> dict[str, Any]:
    return solve_pathway(payload.pathway)


def builtin_tools() -> WorkflowTools:
    tools = WorkflowTools()
    from .custom_formula import custom_formula_tool
    tools.register(custom_formula_tool())
    from .synthetic_ps import SyntheticPSInput,run_ps_tool
    tools.register(ToolDefinition('synthetic.ps_v3','PS-v3 synthetic demonstration','Recompute canonical synthetic inputs with the original M3 and amount-model kernels. Not formal prediction or validation.',
        '1',SyntheticPSInput,run_ps_tool,'synthetic_demonstration',implementation_files=(Path(__file__).with_name('synthetic_ps.py'),
        Path(__file__).parents[1]/'m3_equilibrium.py',Path(__file__).parents[1]/'m4_compartments.py')))
    for tool in (
        ToolDefinition("fusion.sequence_metrics", "Fusion sequence statistics", "Compute recorded sequence composition/features and ProtParam statistics.", "2", SequenceInput, sequence_analysis, "sequence_analysis", implementation_files=(Path(linker_features.__file__),)),
        ToolDefinition("assembly.inventory", "Assembly inventory", "Check declared subunit references and inventory molecular weights.", "1", AssemblyInput, assembly_inventory, "assembly_inventory"),
        ToolDefinition("workflow.gather", "Gather batch results", "Gather construct results in original input order.", "1", GatherInput, gather, "gather"),
        ToolDefinition("pathway.steady_state", "Custom pathway two-phase steady state", "Explicit stoichiometry and two-phase competitive MM; all kinetics are user-provided.", "1", PathwayInput, pathway_analysis, "pathway_simulation", implementation_files=(Path(__file__).with_name("pathway.py"),)),
    ):
        tools.register(tool)
    from .scientific_project import stage_tools
    for tool in stage_tools():
        tools.register(tool)
    from .sequence_predictions import sequence_prediction_tools
    for tool in sequence_prediction_tools():
        tools.register(tool)
    from .m1_checks import m1_check_tools
    for tool in m1_check_tools():
        tools.register(tool)
    from .mpipi import original_mpipi_tool
    tools.register(original_mpipi_tool())
    return tools


Goal = Literal["fusion_screen", "assembly_review", "pathway_simulation", "scientific_pipeline", "m1_sequence_checks"]


def recommend(project: Project, goal: Goal) -> Workflow:
    if goal == "m1_sequence_checks":
        if not project.sequences:
            raise ValueError("upload_and_confirm_sequences_first")
        from .m1_checks import m1_workflow
        constructs=[]
        if project.scientific_project:
            from .scientific_project import ScientificProject
            constructs=ScientificProject.model_validate(project.scientific_project).config.inputs.constructs
        return m1_workflow(sequence_count=len(project.sequences),
            constructs=constructs,
            aggregation_exclusion_reference=project.conditions.get('m1_aggregation_exclusion_reference'))
    if goal == "scientific_pipeline":
        from .scientific_project import ScientificProject
        if project.scientific_project is None:
            raise ValueError("load_and_confirm_typed_scientific_project_first")
        science = ScientificProject.model_validate(project.scientific_project)
        science.verify()
        nodes = []
        for index, stage in enumerate(("m1", "m2", "m3", "m4", "m5")):
            if index >= int(science.config.prepared_through[1:]):
                break
            inputs = {"project": ProjectInput(path=["scientific_project"])}
            if index:
                inputs["upstream_result"] = NodeInput(node_id=nodes[-1].id, path=["result_identity"])
            nodes.append(WorkflowNode(id=stage, label=stage.upper() + " original-formula pipeline and evidence gates", tool_id="project." + stage, inputs=inputs))
        return Workflow(id="scientific-project", name="M1–M5 scientific pipeline", description="Configuration/evidence bound; stages persist independently and missing evidence remains blocked. Human parameter approval is separate from numerical completion.", nodes=nodes)
    if goal == "pathway_simulation":
        if project.pathway is None:
            raise ValueError("upload_and_confirm_a_pathway_first")
        Pathway.model_validate(project.pathway)
        return Workflow(id="custom-pathway", name="User pathway two-phase steady state", description="Use the confirmed pathway; verify rate laws, units and stoichiometry, then solve steady residuals.", nodes=[WorkflowNode(id="pathway", label="Solve pathway steady state", tool_id="pathway.steady_state", inputs={"pathway": ProjectInput(path=["pathway"])})])
    if not project.sequences:
        raise ValueError("upload_and_confirm_sequences_first")
    definitions, _ = M1FeatureDefinitions.from_yaml(default_config_path("m1_feature_definitions.yaml"))
    nodes = [
        WorkflowNode(id="sequences", label="Analyze fusion sequences", tool_id="fusion.sequence_metrics", inputs={"feature_definitions": LiteralInput(value=definitions.model_dump(mode="json"))}, map=MapSpec(items=ProjectInput(path=["sequences"]))),
        WorkflowNode(id="summary", label="Gather construct statistics", tool_id="workflow.gather", inputs={"results": NodeInput(node_id="sequences", path=["items"])}),
    ]
    if goal == "assembly_review":
        if not project.assemblies:
            raise ValueError("declare_assembly_subunits_first")
        nodes.extend([
            WorkflowNode(id="assemblies", label="Check assembly subunits", tool_id="assembly.inventory", inputs={"sequence_metrics": NodeInput(node_id="summary", path=["results"])}, map=MapSpec(items=ProjectInput(path=["assemblies"]))),
            WorkflowNode(id="assembly_summary", label="Gather assembly inventory", tool_id="workflow.gather", inputs={"results": NodeInput(node_id="assemblies", path=["items"])}),
        ])
    return Workflow(id=goal, name="Fusion sequence statistics" if goal == "fusion_screen" else "融合蛋白Assembly inventory", description="Batch by construct; structure/interface tools require explicit evidence.", nodes=nodes)

from __future__ import annotations

from typing import Any, Literal
from hashlib import sha256
from pathlib import Path

from pydantic import Field

from igem_drylab.constructs.linker_features import M1FeatureDefinitions, compute_protparam_evidence, compute_sequence_features
from igem_drylab.constructs import linker_features

from .models import AssemblyRecord, Contract, LiteralInput, MapSpec, NodeInput, Project, ProjectInput, SequenceRecord, Workflow, WorkflowNode
from .pathway import Pathway, solve_pathway
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
    return {"id": payload.item.id, "role": payload.item.role, "features": features.model_dump(mode="json"), "protparam": properties.model_dump(mode="json"), "interpretation": "Sequence composition and physicochemical calculation; LLPS and assembly are not established by these metrics."}


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
    for tool in (
        ToolDefinition("fusion.sequence_metrics", "融合蛋白序列与理化性质", "计算逐条序列的组成、精确特征和 ProtParam。", "1", SequenceInput, sequence_analysis, "sequence_analysis", implementation_files=(Path(linker_features.__file__),)),
        ToolDefinition("assembly.inventory", "自组装组成核验", "按用户声明的亚基数汇总分子量，检查亚基引用。", "1", AssemblyInput, assembly_inventory, "assembly_inventory"),
        ToolDefinition("workflow.gather", "汇总批处理结果", "保留输入顺序并汇总多个构建的结果。", "1", GatherInput, gather, "gather"),
        ToolDefinition("pathway.steady_state", "自定义通路两相稳态", "显式化学计量与两相竞争 MM；用户提供全部动力学参数。", "1", PathwayInput, pathway_analysis, "pathway_simulation", implementation_files=(Path(__file__).with_name("pathway.py"),)),
    ):
        tools.register(tool)
    return tools


Goal = Literal["fusion_screen", "assembly_review", "pathway_simulation"]


def recommend(project: Project, goal: Goal) -> Workflow:
    if goal == "pathway_simulation":
        if project.pathway is None:
            raise ValueError("upload_and_confirm_a_pathway_first")
        Pathway.model_validate(project.pathway)
        return Workflow(id="custom-pathway", name="用户通路两相稳态分析", description="读取已确认通路，检查速率律、单位与化学计量，求解稳态残差。", nodes=[WorkflowNode(id="pathway", label="计算通路稳态", tool_id="pathway.steady_state", inputs={"pathway": ProjectInput(path=["pathway"])})])
    if not project.sequences:
        raise ValueError("upload_and_confirm_sequences_first")
    definitions, _ = M1FeatureDefinitions.from_yaml(Path(__file__).resolve().parents[3] / "configs" / "m1_feature_definitions.yaml")
    nodes = [
        WorkflowNode(id="sequences", label="逐条分析融合蛋白", tool_id="fusion.sequence_metrics", inputs={"feature_definitions": LiteralInput(value=definitions.model_dump(mode="json"))}, map=MapSpec(items=ProjectInput(path=["sequences"]))),
        WorkflowNode(id="summary", label="汇总并比较构建", tool_id="workflow.gather", inputs={"results": NodeInput(node_id="sequences", path=["items"])}),
    ]
    if goal == "assembly_review":
        if not project.assemblies:
            raise ValueError("declare_assembly_subunits_first")
        nodes.extend([
            WorkflowNode(id="assemblies", label="核验自组装亚基组成", tool_id="assembly.inventory", inputs={"sequence_metrics": NodeInput(node_id="summary", path=["results"])}, map=MapSpec(items=ProjectInput(path=["assemblies"]))),
            WorkflowNode(id="assembly_summary", label="汇总自组装组成", tool_id="workflow.gather", inputs={"results": NodeInput(node_id="assemblies", path=["items"])}),
        ])
    return Workflow(id=goal, name="融合蛋白序列筛查" if goal == "fusion_screen" else "融合蛋白自组装组成核验", description="按构建批处理，可扩展结构与界面工具。", nodes=nodes)

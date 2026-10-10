"""Typed, evidence-bound adapters over the existing deterministic stages.

No new scientific defaults, equations, parameter approval or inferred evidence.
"""
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from igem_drylab.pipeline.config import ProjectConfig, load_config
from igem_drylab.pipeline.models import M1Candidate, M2FusionAssessment, M3ConcentrationAssessment, M4ReactionPrediction
from igem_drylab.scoring.m2_structure import load_m2_structure_metrics
from .models import Contract
from .models import NodeInput, ProjectInput, WorkflowError
from .store import canonical
from .tools import NodeContext, ToolDefinition


class EvidenceFile(Contract):
    path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    def verify(self):
        if not self.path.is_file() or sha256(self.path.read_bytes()).hexdigest() != self.sha256:
            raise ValueError("scientific_input_artifact_hash_mismatch:" + str(self.path))


def input_paths(config: ProjectConfig, allowed_roots: tuple[Path, ...] | None = None) -> set[Path]:
    """Configured data/rule files plus typed M2 artifact dependencies.

    Executable deployment directories are tool infrastructure, not scientific
    input files. Remote references remain declared provenance, not local bytes.
    """
    paths: set[Path] = set()
    def walk(value):
        if isinstance(value, Path):
            paths.add(value.resolve())
        elif isinstance(value, BaseModel):
            for key in type(value).model_fields:
                walk(getattr(value, key))
        elif isinstance(value, dict):
            for item in value.values(): walk(item)
        elif isinstance(value, (list, tuple)):
            for item in value: walk(item)
    walk(config.inputs)
    walk(config.stages)
    def authorize(path):
        if allowed_roots is not None and not any(path.resolve().is_relative_to(root.resolve()) for root in allowed_roots):
            raise WorkflowError("scientific_file_outside_authorized_workspace")
    for path in paths:
        authorize(path)
    predictor_file=config.stages.m1_llps.predictor_evidence_file
    if predictor_file and predictor_file.is_file():
        from igem_drylab.constructs.predictor_artifacts import load_predictor_artifacts
        previous=set(paths)
        walk(load_predictor_artifacts(predictor_file))
        for dependency in paths-previous:
            authorize(dependency)
    region_file = config.stages.m2_fusion.region_assessments_file
    if region_file and region_file.is_file():
        from igem_drylab.region_assessment import load_region_requests
        from igem_drylab.parsers.structure_prediction import parse_structure_prediction_output
        for request in load_region_requests(region_file):
            authorize(request.confidence_file)
            prediction = parse_structure_prediction_output(request.confidence_file, candidate_id=request.tool_input_id or request.candidate_id)
            authorize(prediction.model_file)
            paths.update((request.confidence_file, prediction.model_file))
    metrics_file = config.stages.m2_fusion.structure_metrics_file
    calculation_file = config.stages.m2_fusion.calculation_requests_file
    if calculation_file and calculation_file.is_file():
        from igem_drylab.structural_workflow import load_calculation_requests
        for _, _, request, _ in load_calculation_requests(calculation_file):
            previous = set(paths)
            walk(request)
            for dependency in paths-previous:
                authorize(dependency)
    if metrics_file and metrics_file.is_file():
        for row in load_m2_structure_metrics(metrics_file).values():
            for field in ("artifact_path", "reference_artifact_path", "geometry_input_path", "sasa_configuration_path"):
                raw = getattr(row, field)
                if raw:
                    path = Path(raw)
                    path = (path if path.is_absolute() else metrics_file.parent / path).resolve()
                    authorize(path)
                    paths.add(path)
    return paths


class ScientificProject(Contract):
    config: ProjectConfig
    evidence_files: list[EvidenceFile]
    dependency_scope: str = "configured_data_rules_and_typed_M2_artifacts; remote_sources_are_declared_provenance"

    def verify(self):
        bound = {item.path.resolve(): item for item in self.evidence_files}
        if not input_paths(self.config) <= bound.keys():
            raise ValueError("scientific_project_has_unbound_input_files")
        for item in bound.values():
            item.verify()


def load_scientific_project(path: Path, *, allowed_roots: tuple[Path, ...] | None = None) -> ScientificProject:
    source = path.resolve()
    config = load_config(source)
    files = input_paths(config, allowed_roots) | {source}
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        logical = tuple(sorted(Path(item).relative_to(allowed_roots[0]).as_posix() for item in missing
            if allowed_roots and Path(item).is_relative_to(allowed_roots[0])))
        raise WorkflowError("scientific_project_missing_local_dependencies", logical_files=logical,
            private_detail="Missing scientific dependencies: " + ",".join(sorted(missing)))
    return ScientificProject(config=config, evidence_files=[EvidenceFile(path=path, sha256=sha256(path.read_bytes()).hexdigest())
        for path in sorted(files)])


class StageInput(Contract):
    project: ScientificProject
    upstream_records: list[dict[str, Any]] = Field(default_factory=list)
    upstream_artifacts: list[EvidenceFile] = Field(default_factory=list)
    upstream_result: dict[str, str] | None = None


def validate_stage_bindings(workflow) -> None:
    nodes = {node.id: node for node in workflow.nodes}
    preceding = {"project.m2":"project.m1","project.m3":"project.m2","project.m4":"project.m3","project.m5":"project.m4"}
    for node in workflow.nodes:
        if node.tool_id not in {"project.m1",*preceding}: continue
        project = node.inputs.get("project")
        if not isinstance(project,ProjectInput) or project.path != ["scientific_project"] or node.map is not None:
            raise WorkflowError("formal_stage_requires_bound_project")
        if node.tool_id == "project.m1":
            if set(node.inputs) != {"project"}: raise WorkflowError("unexpected_formal_stage_input")
            continue
        source = node.inputs.get("upstream_result")
        if set(node.inputs) != {"project","upstream_result"} or not isinstance(source,NodeInput) or source.path != ["result_identity"]:
            raise WorkflowError("formal_stage_requires_registered_upstream_result")
        if nodes[source.node_id].tool_id != preceding[node.tool_id] or node.dependencies() != {source.node_id}:
            raise WorkflowError("formal_stage_predecessor_mismatch")


def bound_predecessor(payload: StageInput, context: NodeContext, stage: str) -> list[dict[str, Any]]:
    if not context.scientific_project_sha256 or sha256(canonical(payload.project.model_dump(mode="json")).encode()).hexdigest() != context.scientific_project_sha256:
        raise WorkflowError("scientific_snapshot_identity_mismatch")
    if stage == "m1": return []
    previous = {"m2":"m1","m3":"m2","m4":"m3","m5":"m4"}[stage]
    if len(context.upstream_results) != 1 or payload.upstream_result is None:
        raise WorkflowError("formal_stage_requires_registered_upstream_result")
    parent = context.upstream_results[0]
    if payload.upstream_result != {"artifact_id":parent["artifact_id"],"sha256":parent["sha256"]} or parent["run_id"] != context.run_id or parent["project_id"] != context.project_id or parent["snapshot_hash"] != context.snapshot_sha256:
        raise WorkflowError("upstream_result_identity_mismatch")
    output = parent["output"]
    if output.get("schema_version") not in {"scientific-stage-v1","scientific-stage-v2"} or output.get("module") != previous:
        raise WorkflowError("upstream_schema_or_stage_mismatch")
    rows = output.get("records")
    if not isinstance(rows,list): raise WorkflowError("invalid_registered_upstream_records")
    if payload.upstream_records and canonical(payload.upstream_records) != canonical(rows):
        raise WorkflowError("client_records_not_registered_result")
    for item in output.get("resource_artifacts",[]): EvidenceFile.model_validate(item).verify()
    return rows


def stage_tools():
    source_root = Path(__file__).resolve().parents[1]
    implementation = tuple(sorted(source_root.rglob("*.py")))
    definitions = []
    for stage, predecessor in (("m1", None), ("m2", M1Candidate), ("m3", M2FusionAssessment),
                               ("m4", M3ConcentrationAssessment), ("m5", M4ReactionPrediction)):
        def handler(payload: StageInput, context: NodeContext, *, stage=stage, predecessor=predecessor):
            if int(stage[1:]) > int(payload.project.config.prepared_through[1:]):
                raise WorkflowError("stage_configuration_not_prepared:" + stage)
            from igem_drylab.pipeline import stages
            upstream = bound_predecessor(payload,context,stage)
            payload.project.verify()
            for item in payload.upstream_artifacts:
                item.verify()
            config = payload.project.config.model_copy(deep=True)
            if context.runtime_tools:
                from igem_drylab.pipeline.config import ToolConfig
                config.tools = {key: ToolConfig.model_validate(item) for key, item in context.runtime_tools.items()}
            # Output placement is orchestration only; no scientific inputs changed.
            config.run.id, config.run.output_dir = context.run_id, context.work_dir
            runner = getattr(stages, "run_" + stage)
            args = [config, context.work_dir]
            if predecessor is not None:
                args.append([predecessor.model_validate(row) for row in upstream])
            records, output = runner(*args)
            serialized = [row.model_dump(mode="json") for row in records]
            trajectory_refs = {}
            artifacts = {output.json_file, output.csv_file}
            if stage == "m2":
                region_output = output.directory / "region_observations.json"
                if region_output.is_file():
                    artifacts.add(region_output)
                artifacts.update(output.directory.glob("calculation-*.json"))
            if stage == "m4":
                for row in records:
                    if row.trajectory_artifact and row.trajectory_artifact.is_file():
                        artifacts.add(row.trajectory_artifact)
                        trajectory_refs[row.candidate_id] = EvidenceFile(path=row.trajectory_artifact,sha256=sha256(row.trajectory_artifact.read_bytes()).hexdigest()).model_dump(mode="json")
            return {"schema_version": "scientific-stage-v2", "module": stage,
                "execution_mode": config.execution.mode, "records": serialized,
                "resource_artifacts": [EvidenceFile(path=path,sha256=sha256(path.read_bytes()).hexdigest()).model_dump(mode="json") for path in sorted(artifacts)],
                "trajectory_refs": trajectory_refs, "output": output.model_dump(mode="json"),
                "claim_scope": "original_stage_contracts_not_automatic_experimental_validation"}
        definitions.append(ToolDefinition("project." + stage, stage.upper() + " original-formula scientific stage", "Read bound scientific inputs/evidence through the deterministic stage.",
            "2", StageInput, handler, "scientific_project", implementation_files=implementation))
    return definitions

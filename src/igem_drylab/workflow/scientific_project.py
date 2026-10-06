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
from igem_drylab.pipeline import stages
from igem_drylab.scoring.m2_structure import load_m2_structure_metrics
from .models import Contract
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
            raise ValueError("scientific_file_outside_authorized_workspace")
    for path in paths:
        authorize(path)
    metrics_file = config.stages.m2_fusion.structure_metrics_file
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
        raise ValueError("scientific_project_missing_local_dependencies:" + ",".join(sorted(missing)))
    return ScientificProject(config=config, evidence_files=[EvidenceFile(path=path, sha256=sha256(path.read_bytes()).hexdigest())
        for path in sorted(files)])


class StageInput(Contract):
    project: ScientificProject
    upstream_records: list[dict[str, Any]] = Field(default_factory=list)
    upstream_artifacts: list[EvidenceFile] = Field(default_factory=list)


def stage_tools():
    source_root = Path(stages.__file__).resolve().parents[1]
    implementation = tuple(sorted(source_root.rglob("*.py")))
    definitions = []
    for stage, predecessor in (("m1", None), ("m2", M1Candidate), ("m3", M2FusionAssessment),
                               ("m4", M3ConcentrationAssessment), ("m5", M4ReactionPrediction)):
        def handler(payload: StageInput, context: NodeContext, *, stage=stage, predecessor=predecessor):
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
                args.append([predecessor.model_validate(row) for row in payload.upstream_records])
            records, output = runner(*args)
            serialized = [row.model_dump(mode="json") for row in records]
            trajectories = {}
            artifacts = {output.json_file, output.csv_file}
            if stage == "m4":
                for row in records:
                    if row.trajectory_artifact and row.trajectory_artifact.is_file():
                        artifacts.add(row.trajectory_artifact)
                        trajectories[row.candidate_id] = json.loads(row.trajectory_artifact.read_text(encoding="utf-8"))
            return {"schema_version": "scientific-stage-v1", "module": stage,
                "execution_mode": config.execution.mode, "records": serialized,
                "resource_artifacts": [EvidenceFile(path=path,sha256=sha256(path.read_bytes()).hexdigest()).model_dump(mode="json") for path in sorted(artifacts)],
                "trajectories": trajectories, "output": output.model_dump(mode="json"),
                "claim_scope": "original_stage_contracts_not_automatic_experimental_validation"}
        definitions.append(ToolDefinition("project." + stage, stage.upper() + " 原式项目管线", "读取已绑定科学配置和证据，复用确定性 stage。",
            "1", StageInput, handler, "scientific_project", implementation_files=implementation))
    return definitions

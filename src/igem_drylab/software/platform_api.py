"""HTTP transport for local projects, immutable runs, workflows and plugins."""
from __future__ import annotations

from hashlib import sha256
from io import StringIO
import csv
import json
from pathlib import Path
from threading import Thread
from typing import Any, Literal
from uuid import uuid4

from Bio import SeqIO
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import Field

from igem_drylab.workflow.builtins import Goal, builtin_tools, recommend
from igem_drylab.workflow.engine import WorkflowEngine
from igem_drylab.workflow.mcp_bridge import register_scientific_mcp
from igem_drylab.workflow.models import Contract, PlanBinding, Project, SequenceRecord, Workflow, WorkflowError
from igem_drylab.workflow.pathway import Pathway
from igem_drylab.workflow.plugins import PluginManager
from igem_drylab.workflow.store import WorkflowStore, plan_binding


class SaveProject(Contract):
    project: Project
    expected_revision: int | None = None


class ImportRequest(Contract):
    filename: str
    content: str = Field(max_length=10_000_000)
    input_kind: Literal["auto", "pathway", "wetlab"] = "auto"


class ScientificImportRequest(Contract):
    config_path: Path


class PlanRequest(Contract):
    project_id: str
    goal: Goal
    objective: str = ""


class RunRequest(Contract):
    project_id: str
    workflow: Workflow
    confirmation: PlanBinding


class CustomPlanRequest(Contract):
    project_id: str
    workflow: Workflow


class ControlRequest(Contract):
    action: Literal["pause", "cancel", "resume", "retry"]


class PluginRequest(Contract):
    source_path: Path
    trusted: bool = False
    expected_hash: str | None = None


class GithubPluginRequest(Contract):
    repository_url: str
    commit: str


def platform_router(data_dir: Path) -> APIRouter:
    data_dir = data_dir.resolve()
    store = WorkflowStore(data_dir / "platform.sqlite3")
    tools = builtin_tools()
    register_scientific_mcp(tools)
    plugins = PluginManager(data_dir / "plugins", store, tools)
    plugins.load_installed()
    engine = WorkflowEngine(store, tools, data_dir / "artifacts")
    router = APIRouter(prefix="/api/platform")

    def launch(run_id: str, retry: bool = False) -> None:
        def execute() -> None:
            try:
                engine.run(run_id, retry_failed=retry)
            except Exception as exc:
                store.event(run_id, "dispatch_error", {"type": type(exc).__name__, "message": str(exc)})
        Thread(target=execute, daemon=True).start()

    @router.get("/info")
    def info() -> dict[str, Any]:
        return {"name": "FusionLab", "data_dir": str(data_dir), "storage": "SQLite WAL", "max_workers": engine.max_workers, "plugin_sandbox": False, "agent_backend": "validated_workflow_templates", "supported_rate_laws": ["two_phase_competitive_mm_v1"]}

    @router.get("/projects")
    def projects() -> list[dict[str, Any]]:
        return store.projects()

    @router.post("/projects")
    def save_project(request: SaveProject) -> Project:
        if request.project.scientific_project is not None:
            from igem_drylab.workflow.scientific_project import ScientificProject
            ScientificProject.model_validate(request.project.scientific_project).verify()
        if request.project.pathway is not None:
            Pathway.model_validate(request.project.pathway)
        for sequence in request.project.sequences:
            from igem_drylab.constructs.linker_features import normalize_amino_acid_sequence
            sequence.sequence = normalize_amino_acid_sequence(sequence.sequence)
        for file in request.project.files:
            path = Path(file["path"]).resolve()
            if not path.is_relative_to(data_dir / "imports") or not path.is_file() or sha256(path.read_bytes()).hexdigest() != file["sha256"]:
                raise ValueError("invalid_import_artifact")
        return store.save_project(request.project, request.expected_revision)

    @router.post("/scientific-projects/preview")
    def scientific_preview(request: ScientificImportRequest) -> dict[str, Any]:
        from igem_drylab.workflow.scientific_project import load_scientific_project
        project = load_scientific_project(request.config_path)
        return {"scientific_project": project.model_dump(mode="json"), "requires_confirmation": True,
            "dependency_scope": project.dependency_scope}

    @router.post("/imports/preview")
    def import_preview(request: ImportRequest) -> dict[str, Any]:
        extension = Path(request.filename).suffix.lower()
        digest = sha256(request.content.encode()).hexdigest()
        root = data_dir / "imports"
        root.mkdir(parents=True, exist_ok=True)
        source = root / f"{digest}{extension}"
        # Parse before storing. The project itself changes only after confirmation.
        if extension in {".fasta", ".fa", ".faa", ".gb", ".gbk", ".genbank"}:
            format_name = "genbank" if extension in {".gb", ".gbk", ".genbank"} else "fasta"
            records = list(SeqIO.parse(StringIO(request.content), format_name))
            sequences: list[dict[str, Any]] = []
            for record in records:
                if format_name == "fasta":
                    sequences.append(SequenceRecord(id=record.id, sequence=str(record.seq)).model_dump())
                else:
                    for index, feature in enumerate(record.features):
                        if feature.type == "CDS" and "translation" in feature.qualifiers:
                            sequences.append(SequenceRecord(id=feature.qualifiers.get("protein_id", [f"{record.id}_CDS_{index}"])[0], sequence=feature.qualifiers["translation"][0]).model_dump())
            if not sequences:
                raise ValueError("no_protein_sequences; GenBank requires annotated CDS translations")
            from igem_drylab.constructs.linker_features import normalize_amino_acid_sequence
            for item in sequences:
                item["sequence"] = normalize_amino_acid_sequence(item["sequence"])
            Project(id="preview", name="preview", sequences=sequences)
            patch: dict[str, Any] = {"sequences": sequences}
            kind = "sequences"
        elif extension == ".json" and request.input_kind == "wetlab":
            from igem_drylab.wetlab.models import WetLabResult
            raw = json.loads(request.content)
            rows = raw.get("records") if isinstance(raw, dict) else raw
            if not isinstance(rows, list) or not rows:
                raise ValueError("wetlab_requires_nonempty_typed_records")
            records = [WetLabResult.model_validate(row).model_dump(mode="json") for row in rows]
            from igem_drylab.wetlab import quality_control
            qc = quality_control([WetLabResult.model_validate(row) for row in records])
            patch, kind = {"datasets": [{"id": digest, "name": request.filename, "kind": "wetlab",
                "records": records, "qc": [item.model_dump(mode="json") for item in qc]}]}, "wetlab"
        elif extension == ".json":
            pathway = Pathway.model_validate_json(request.content)
            patch, kind = {"pathway": pathway.model_dump(mode="json")}, "pathway"
        elif extension in {".csv", ".tsv"}:
            rows = list(csv.DictReader(StringIO(request.content), delimiter="\t" if extension == ".tsv" else ","))
            if not rows:
                raise ValueError("empty_table")
            patch, kind = {"datasets": [{"id": digest, "name": request.filename, "rows": rows}]}, "dataset"
        else:
            raise ValueError("supported_imports: FASTA, annotated GenBank, pathway JSON, CSV, TSV")
        source.write_bytes(request.content.encode("utf-8"))
        return {"kind": kind, "patch": patch, "file": {"id": digest, "sha256": digest, "path": str(source), "name": Path(request.filename).name}}

    @router.post("/plans")
    def plan(request: PlanRequest) -> dict[str, Any]:
        project = store.project(request.project_id)
        workflow = recommend(project, request.goal)
        if request.objective:
            workflow.description += f" 用户任务说明：{request.objective}"
        return {"workflow": workflow.model_dump(mode="json"), "source": "validated_template", "requires_confirmation": True,
            "confirmation": plan_binding(project, workflow).model_dump(mode="json")}

    @router.post("/plans/custom")
    def custom_plan(request: CustomPlanRequest) -> dict[str, Any]:
        validate_workflow(request.workflow)
        return {"workflow": request.workflow.model_dump(mode="json"), "source": "user_reviewed_workflow", "requires_confirmation": True,
            "confirmation": plan_binding(store.project(request.project_id), request.workflow).model_dump(mode="json")}

    @router.post("/workflows/validate")
    def validate_workflow(workflow: Workflow) -> Workflow:
        for node in workflow.nodes:
            tools.get(node.tool_id)
        return workflow

    @router.post("/runs", status_code=202)
    def run(request: RunRequest) -> dict[str, Any]:
        if request.project_id != request.confirmation.project_id:
            raise WorkflowError("plan_project_mismatch", status_code=409)
        run_id = engine.create_confirmed(request.confirmation, request.workflow)
        result = store.run(run_id)
        launch(run_id)
        return result

    @router.get("/runs")
    def runs(project_id: str | None = None) -> list[dict[str, Any]]:
        return store.runs(project_id)

    @router.get("/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, Any]:
        return store.run(run_id)

    @router.post("/runs/{run_id}/control")
    def control(run_id: str, request: ControlRequest) -> dict[str, Any]:
        run = store.run(run_id)
        if request.action in {"pause", "cancel"}:
            if run["status"] in {"succeeded", "cancelled", "failed"}:
                raise ValueError("terminal_run_cannot_be_paused_or_cancelled")
            store.control(run_id, request.action)
        else:
            if run["status"] in {"succeeded", "cancelled"}:
                raise WorkflowError("run_is_terminal", status_code=409)
            engine.verify_snapshot(run)
            if run["owner"]:
                from datetime import datetime, timedelta, timezone
                if run["heartbeat"] > (datetime.now(timezone.utc) - timedelta(seconds=20)).isoformat():
                    raise WorkflowError("run_has_active_worker", status_code=409)
            launch(run_id, retry=request.action == "retry")
        return store.run(run_id)

    @router.post("/runs/{run_id}/clone", status_code=202)
    def clone(run_id: str) -> dict[str, Any]:
        old = store.run(run_id)["snapshot"]
        new_id = engine.create(Project.model_validate(old["project"]), Workflow.model_validate(old["workflow"]))
        result = store.run(new_id)
        launch(new_id)
        return result

    @router.get("/artifacts/{artifact_id}")
    def artifact(artifact_id: str) -> FileResponse:
        with store.connection() as db:
            row = db.execute("SELECT path,hash FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
        if row is None:
            raise KeyError(artifact_id)
        path = Path(row["path"])
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != row["hash"]:
            raise ValueError("artifact_hash_mismatch")
        return FileResponse(path, media_type="application/json", filename="result.json")

    @router.get("/tools")
    def tool_list() -> list[dict[str, Any]]:
        return tools.list()

    @router.get("/plugins")
    def plugin_list() -> list[dict[str, Any]]:
        return plugins.installed()

    @router.post("/plugins/inspect")
    def inspect_plugin(request: PluginRequest) -> dict[str, Any]:
        return plugins.inspect(request.source_path)

    @router.post("/plugins/github")
    def github_plugin(request: GithubPluginRequest) -> dict[str, Any]:
        return plugins.fetch_github(request.repository_url, request.commit)

    @router.get("/schemas")
    def schemas() -> dict[str, Any]:
        from igem_drylab.workflow.plugins import PluginManifest
        from igem_drylab.workflow.scientific_project import ScientificProject
        from igem_drylab.wetlab.models import WetLabResult
        return {"Project": Project.model_json_schema(), "Workflow": Workflow.model_json_schema(), "Pathway": Pathway.model_json_schema(), "PluginManifest": PluginManifest.model_json_schema(),
            "ScientificProject": ScientificProject.model_json_schema(), "WetLabResult": WetLabResult.model_json_schema()}

    @router.post("/plugins/install")
    def install_plugin(request: PluginRequest) -> dict[str, Any]:
        if not request.expected_hash:
            raise WorkflowError("plugin_changed_since_inspection", status_code=409)
        return plugins.install(request.source_path, trusted=request.trusted, expected_hash=request.expected_hash)

    return router

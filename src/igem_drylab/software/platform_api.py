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
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pydantic import Field

from igem_drylab.workflow.builtins import Goal, builtin_tools, recommend
from igem_drylab.workflow.engine import WorkflowEngine
from igem_drylab.workflow.disclosure import DisclosureBoundary
from igem_drylab.workflow.mcp_bridge import register_scientific_mcp
from igem_drylab.workflow.models import Contract, PlanBinding, Project, SequenceRecord, Workflow, WorkflowError
from igem_drylab.workflow.pathway import Pathway
from igem_drylab.workflow.plugins import PluginManager
from igem_drylab.workflow.store import WorkflowStore, plan_binding
from igem_drylab.workflow.planning import PlanningService, ProposalRequest, ProposalDecision


class SaveProject(Contract):
    project: Project
    expected_revision: int | None = None


class ImportRequest(Contract):
    filename: str
    content: str = Field(max_length=10_000_000)
    input_kind: Literal["auto", "pathway", "wetlab"] = "auto"


class ScientificImportRequest(Contract):
    config_path: Path


class ScientificBundleRequest(Contract):
    config_filename: str
    files: list[ImportRequest] = Field(min_length=1, max_length=256)


class PlanRequest(Contract):
    project_id: str
    goal: Goal
    objective: str = ""


class RunRequest(Contract):
    project_id: str
    workflow: Workflow
    confirmation: PlanBinding
    request_id: str | None = Field(default=None, max_length=128)
    proposal_id: str | None = None
    execution_type: Literal["reviewed_proposal","manual_review"] = "reviewed_proposal"
    manual_review_id: str | None = None


class MeasurementBindingRequest(Contract):
    project_id: str
    expected_revision: int
    file_id: str


class CustomPlanRequest(Contract):
    project_id: str
    workflow: Workflow
    objective: str = ""


class ControlRequest(Contract):
    action: Literal["pause", "cancel", "resume", "retry"]
    node_id: str | None = None


class PluginRequest(Contract):
    source_path: Path
    trusted: bool = False
    expected_hash: str | None = None


class GithubPluginRequest(Contract):
    repository_url: str
    commit: str


def platform_router(data_dir: Path, *, discover_tools: bool = True, planning_backend=None, workflow_tools=None) -> APIRouter:
    data_dir = data_dir.resolve()
    store = WorkflowStore(data_dir / "platform.sqlite3")
    tools = workflow_tools if workflow_tools is not None else builtin_tools()
    engine = WorkflowEngine(store, tools, data_dir / "artifacts")
    from igem_drylab.workflow.scheduler import RunDispatcher
    dispatcher = RunDispatcher(engine)
    boundary = engine.disclosure
    from igem_drylab.workflow.views import PublicReads
    reads = PublicReads(store,boundary)
    planning = PlanningService(store,boundary,planning_backend,engine)
    if planning_backend is not None:
        private_client = getattr(planning_backend,"client",None)
        for field in ("api_key","api_base"):
            boundary.register_private(getattr(private_client,field,None))
    boundary.register_private(str(data_dir))
    plugins = PluginManager(data_dir / "plugins", store, tools, disclosure=boundary)
    plugins.load_installed()
    router = APIRouter(prefix="/api/platform")
    router.store, router.engine, router.disclosure = store, engine, boundary
    capabilities = {"scientific_mcp": "checking" if discover_tools else "unavailable"}

    def discover() -> None:
        try:
            register_scientific_mcp(tools)
            capabilities["scientific_mcp"] = "ready"
        except Exception as exc:
            capabilities["scientific_mcp"] = "unavailable"
            boundary.diagnostic(exc, code="mcp_discovery_failed")

    if discover_tools:
        Thread(target=discover, daemon=True).start()

    def launch(run_id: str, retry: bool = False, node_id: str | None = None) -> None:
        dispatcher.submit(run_id,retry=retry,node_id=node_id)

    @router.get("/info")
    def info() -> dict[str, Any]:
        return {"name": "FusionLab", "protocol_version": "2", "authentication": "session_required", "workspace_id": sha256(str(data_dir).encode()).hexdigest(), "storage": "SQLite WAL", "max_workers": engine.max_workers, "plugin_sandbox": False, "agent_backend": "hybrid_semantic_compiler" if planning_backend else "validated_workflow_templates", "capabilities": capabilities | {"stage_step":"ready","checkpoints":"ready","cancel_dispatch":"ready","hybrid_planning":"ready" if planning_backend else "unavailable","cross_run_reuse":"unavailable"}, "resources":engine.budget.state() | dispatcher.state(), "remote_desktop_authenticated_session": False, "supported_rate_laws": ["two_phase_competitive_mm_v1"]}

    @router.post("/proposals")
    def propose(request: ProposalRequest):
        result = planning.propose(request)
        if result.workflow: validate_workflow(result.workflow)
        return result

    @router.get("/proposals/{proposal_id}")
    def proposal(proposal_id: str):
        result = planning.get(proposal_id)
        boundary.check(result.model_dump(mode="json"))
        return result

    @router.post("/proposals/{proposal_id}/decision")
    def proposal_decision(proposal_id: str,request: ProposalDecision):
        return planning.decide(proposal_id,request.action)

    @router.post("/custom-proposals")
    def custom_proposal(request: CustomPlanRequest):
        validate_workflow(request.workflow)
        return planning.custom(request.project_id,request.workflow,request.objective)

    @router.get("/projects/{project_id}/input-diff")
    def project_diff(project_id:str,run_id:str):
        from igem_drylab.workflow.input_diff import input_diff
        result=input_diff(store,boundary,store.project(project_id),run_id)
        boundary.check(result)
        return result

    @router.get("/projects/{project_id}/precheck")
    def scientific_precheck(project_id:str):
        from igem_drylab.workflow.precheck import precheck
        result=precheck(store.project(project_id)).model_dump(mode="json")
        boundary.check(result)
        return result

    @router.get("/plan-actions")
    def plan_actions(project_id: str,after_seq: int = Query(0,ge=0),limit: int = Query(100,ge=1,le=200)):
        return planning.actions(project_id,after_seq,limit)

    @router.post("/scientific-projects/bind-measurement")
    def bind_measurement(request: MeasurementBindingRequest):
        project = store.project(request.project_id)
        if project.revision != request.expected_revision: raise WorkflowError("project_revision_conflict",status_code=409)
        if project.scientific_project is None: raise WorkflowError("typed_scientific_project_required")
        dataset = next((row for row in project.datasets if row.get("kind") == "wetlab" and row.get("file_id") == request.file_id),None)
        if dataset is None: raise WorkflowError("registered_wetlab_dataset_required")
        path = Path(boundary.resolve_asset(request.file_id,project.id))
        from igem_drylab.wetlab.models import WetLabResult
        raw = json.loads(path.read_bytes())
        rows = raw.get("records") if isinstance(raw,dict) else raw
        if not isinstance(rows,list) or not rows: raise WorkflowError("wetlab_requires_nonempty_typed_records")
        for row in rows: WetLabResult.model_validate(row)
        from igem_drylab.workflow.scientific_project import ScientificProject, EvidenceFile
        science = ScientificProject.model_validate(project.scientific_project)
        science.config.stages.m5_feedback.wetlab_results_file = path
        science.evidence_files = [item for item in science.evidence_files if item.path != path] + [EvidenceFile(path=path,sha256=sha256(path.read_bytes()).hexdigest())]
        science.verify()
        draft = project.model_copy(update={"scientific_project":science.model_dump(mode="json")})
        return {"project":boundary.project(draft),"requires_confirmation":True,"status":"binding_preview_not_parameter_approval"}

    @router.get("/projects")
    def projects() -> list[dict[str, Any]]:
        return [boundary.project(Project.model_validate(item)) for item in store.projects()]

    @router.get("/project-summaries")
    def project_summaries(offset: int = Query(0,ge=0), limit: int = Query(100,ge=1,le=200)):
        return reads.projects(offset,limit)

    @router.get("/projects/{project_id}")
    def get_project(project_id: str) -> dict[str, Any]:
        return boundary.project(store.project(project_id))

    @router.post("/projects")
    def save_project(request: SaveProject) -> dict[str, Any]:
        boundary.check(request.project.model_dump(mode="json"))
        request.project = boundary.private_project(request.project)
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
        return boundary.project(store.save_project(request.project, request.expected_revision))

    @router.post("/scientific-projects/preview")
    def scientific_preview(request: ScientificImportRequest) -> dict[str, Any]:
        from igem_drylab.workflow.scientific_project import load_scientific_project
        path = request.config_path.resolve()
        if not path.is_relative_to(data_dir / "imports"):
            raise WorkflowError("upload_scientific_inputs_instead_of_server_path", status_code=403)
        with store.connection() as db:
            bundles = [Path(row[0]) for row in db.execute("SELECT root FROM scientific_bundles")]
        root = next((root for root in bundles if path.is_relative_to(root)), None)
        if root is None:
            raise WorkflowError("unknown_scientific_bundle", status_code=403)
        from igem_drylab.resources import default_config_path
        project = load_scientific_project(path, allowed_roots=(root, default_config_path("m1_feature_definitions.yaml"), default_config_path("m1_rules_v3.yaml")))
        if project.config.tools:
            raise WorkflowError("runtime_settings_not_scientific_input")
        return {"scientific_project": boundary.scientific(project.model_dump(mode="json")), "requires_confirmation": True,
            "dependency_scope": project.dependency_scope}

    @router.post("/scientific-projects/upload-preview")
    def scientific_upload(request: ScientificBundleRequest) -> dict[str, Any]:
        # Resolve and validate all relative names before writing the owned bundle.
        root = data_dir / "imports" / str(uuid4())
        contents: dict[Path, str] = {}
        for item in request.files:
            target = (root / item.filename).resolve()
            if not target.is_relative_to(root) or ".." in Path(item.filename).parts or target in contents:
                raise WorkflowError("invalid_upload_identity")
            contents[target] = item.content
        if sum(len(item.encode()) for item in contents.values()) > 20_000_000:
            raise WorkflowError("scientific_upload_budget_exceeded")
        source = (root / request.config_filename).resolve()
        if source not in contents:
            raise WorkflowError("missing_uploaded_scientific_config")
        # Reject runtime settings before resolving or reading scientific files.
        import yaml
        raw = yaml.safe_load(contents[source])
        if not isinstance(raw, dict) or raw.get("tools"):
            raise WorkflowError("runtime_settings_not_scientific_input")
        for target, content in contents.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        with store.connection() as db:
            db.execute("INSERT INTO scientific_bundles VALUES(?,?)", (root.name,str(root)))
        return scientific_preview(ScientificImportRequest(config_path=source))

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
        file = boundary.asset(source, fresh=True)
        for dataset in patch.get("datasets", []):
            dataset["file_id"] = file["id"]
        result = {"kind": kind, "patch": patch, "file": file}
        boundary.check(result)
        return result

    @router.post("/plans")
    def plan(request: PlanRequest) -> dict[str, Any]:
        project = store.project(request.project_id)
        workflow = recommend(project, request.goal)
        if request.objective:
            workflow.description += f" 用户任务说明：{request.objective}"
        boundary.check(workflow.model_dump(mode="json"))
        review = planning.custom(project.id,workflow,request.objective,source="manual_compatibility")
        return {"workflow": workflow.model_dump(mode="json"), "source": "validated_template", "requires_confirmation": True,
            "confirmation": review.confirmation.model_dump(mode="json"),"review_id":review.id}

    @router.post("/plans/custom")
    def custom_plan(request: CustomPlanRequest) -> dict[str, Any]:
        validate_workflow(request.workflow)
        review = planning.custom(request.project_id,request.workflow,request.objective,source="manual_compatibility")
        return {"workflow": request.workflow.model_dump(mode="json"), "source": "user_reviewed_workflow", "requires_confirmation": True,
            "confirmation": review.confirmation.model_dump(mode="json"),"review_id":review.id}

    @router.post("/workflows/validate")
    def validate_workflow(workflow: Workflow) -> Workflow:
        boundary.check(workflow.model_dump(mode="json"))
        from igem_drylab.workflow.scientific_project import validate_stage_bindings
        validate_stage_bindings(workflow)
        for node in workflow.nodes:
            tools.get(node.tool_id)
        return workflow

    @router.post("/runs", status_code=202)
    def run(request: RunRequest) -> dict[str, Any]:
        if request.project_id != request.confirmation.project_id:
            raise WorkflowError("plan_project_mismatch", status_code=409)
        request_id = request.request_id or sha256(request.confirmation.model_dump_json().encode()).hexdigest()
        review_id = request.proposal_id if request.execution_type == "reviewed_proposal" else request.manual_review_id
        if not review_id or (request.proposal_id and request.manual_review_id):
            raise WorkflowError("accepted_proposal_binding_required",status_code=409)
        manual = request.execution_type == "manual_review"
        planning.authorize_run(review_id,request.confirmation,request.workflow,manual=manual)
        run_id = engine.create_confirmed(request.confirmation, request.workflow, request_id,
            authorize=lambda db,snapshot: planning.authorize_run(review_id,request.confirmation,request.workflow,db=db,snapshot=snapshot,manual=manual))
        result = store.run(run_id)
        if result["status"] == "queued": launch(run_id)
        planning.started(review_id,run_id)
        return boundary.run(result)

    @router.post("/runs/{run_id}/iteration")
    def iteration(run_id: str):
        from igem_drylab.workflow.iteration import create_iteration
        return create_iteration(store, boundary, engine, run_id, data_dir)

    @router.get("/runs")
    def runs(project_id: str | None = None, offset: int = Query(0,ge=0), limit: int = Query(100,ge=1,le=200)) -> list[dict[str, Any]]:
        result = store.runs(project_id,offset=offset,limit=limit)
        boundary.check(result)
        return result

    @router.get("/runs/{run_id}/summary")
    def run_summary(run_id: str):
        return reads.summary(run_id)

    @router.get("/runs/{run_id}/events")
    def run_events(run_id: str, after_seq: int = Query(0,ge=0), limit: int = Query(100,ge=1,le=500)):
        return reads.events(run_id,after_seq,limit)

    @router.get("/runs/{run_id}/nodes/{node_id}/result")
    def node_result(run_id: str,node_id: str, offset: int = Query(0,ge=0), limit: int = Query(20,ge=1,le=100)):
        return reads.node(run_id,node_id,offset,limit)

    @router.get("/files/{file_id}")
    def science_file(file_id: str,project_id: str):
        with store.connection() as db:
            row = db.execute("SELECT project_id FROM file_assets WHERE id=?",(file_id,)).fetchone()
        if row is None or row[0] != project_id:
            raise WorkflowError("file_project_mismatch",status_code=403)
        path = Path(boundary.resolve_asset(file_id,project_id))
        raw = path.read_bytes()
        boundary.check_bytes(raw)
        if path.suffix.lower() == ".json": boundary.check(json.loads(raw))
        return FileResponse(path,filename=path.name,headers={"X-Content-SHA256":sha256(raw).hexdigest()})

    @router.get("/files/{file_id}/data")
    def scientific_data(file_id: str,project_id: str,offset: int = Query(0,ge=0),limit: int = Query(100,ge=1,le=500)):
        with store.connection() as db:
            row = db.execute("SELECT project_id,hash FROM file_assets WHERE id=?",(file_id,)).fetchone()
        if row is None or row[0] != project_id:
            raise WorkflowError("file_project_mismatch",status_code=403)
        path = Path(boundary.resolve_asset(file_id,project_id))
        data = json.loads(path.read_bytes())
        contract = data.get("prediction_contract") if isinstance(data,dict) else None
        if not isinstance(contract,dict) or not isinstance(contract.get("time"),list) or not isinstance(contract.get("concentrations"),dict):
            raise WorkflowError("unsupported_trajectory_contract")
        time = contract["time"]
        sliced = {**contract,"time":time[offset:offset+limit],"concentrations":{}}
        for compartment,species in contract["concentrations"].items():
            if not isinstance(species,dict): raise WorkflowError("invalid_trajectory_contract")
            sliced["concentrations"][compartment] = {}
            for name,values in species.items():
                if not isinstance(values,list) or len(values) != len(time): raise WorkflowError("invalid_trajectory_contract")
                sliced["concentrations"][compartment][name] = values[offset:offset+limit]
        result = {"file_id":file_id,"sha256":row["hash"],"offset":offset,"total":len(time),"prediction_contract":sliced}
        boundary.check(result)
        return result

    @router.get("/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, Any]:
        return boundary.run(store.run(run_id))

    @router.post("/runs/{run_id}/control")
    def control(run_id: str, request: ControlRequest) -> dict[str, Any]:
        run = store.run(run_id)
        if request.action in {"pause", "cancel"}:
            store.control(run_id, request.action)
        else:
            if run["status"] in {"succeeded", "cancelled"}:
                raise WorkflowError("run_is_terminal", status_code=409)
            engine.verify_snapshot(run)
            if request.node_id and request.node_id not in {node["id"] for node in run["snapshot"]["workflow"]["nodes"]}:
                raise WorkflowError("unknown_retry_node")
            if run["owner"]:
                from datetime import datetime, timedelta, timezone
                if run["heartbeat"] > (datetime.now(timezone.utc) - timedelta(seconds=20)).isoformat():
                    raise WorkflowError("run_has_active_worker", status_code=409)
            store.clear_control(run_id)
            launch(run_id, retry=request.action == "retry", node_id=request.node_id)
        return boundary.run(store.run(run_id))

    @router.post("/runs/{run_id}/clone", status_code=202)
    def clone(run_id: str) -> dict[str, Any]:
        old = store.run(run_id)["snapshot"]
        # A clone is a newly reviewed plan against the current input revision,
        # not permission to reinterpret the immutable old run.
        return planning.custom(old["project"]["id"],Workflow.model_validate(old["workflow"]),
            "从旧运行生成新审阅范围；尚未执行。",source="run_clone",previous_review_identity=engine.snapshot_review_identity(old)).model_dump(mode="json")

    @router.get("/artifacts/{artifact_id}")
    def artifact(artifact_id: str, project_id: str) -> FileResponse:
        with store.connection() as db:
            row = db.execute("SELECT artifacts.path,artifacts.hash,runs.project_id FROM artifacts JOIN runs ON runs.id=artifacts.run_id WHERE artifacts.id=?", (artifact_id,)).fetchone()
        if row is None:
            raise KeyError(artifact_id)
        if row["project_id"] != project_id:
            raise WorkflowError("artifact_project_mismatch", status_code=403)
        path = Path(row["path"])
        if not path.resolve().is_relative_to(data_dir / "artifacts"):
            raise WorkflowError("artifact_workspace_mismatch", status_code=403)
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != row["hash"]:
            raise ValueError("artifact_hash_mismatch")
        boundary.check(json.loads(path.read_text(encoding="utf-8")))
        return FileResponse(path, media_type="application/json", filename="result.json", headers={"X-Content-SHA256": row["hash"]})

    @router.get("/artifacts/{artifact_id}/science-export")
    def science_export(artifact_id: str, project_id: str):
        with store.connection() as db:
            row = db.execute("SELECT artifacts.*,runs.project_id FROM artifacts JOIN runs ON runs.id=artifacts.run_id WHERE artifacts.id=?",(artifact_id,)).fetchone()
        if row is None: raise KeyError(artifact_id)
        if row["project_id"] != project_id: raise WorkflowError("artifact_project_mismatch",status_code=403)
        raw = Path(row["path"]).read_bytes()
        if sha256(raw).hexdigest() != row["hash"]: raise WorkflowError("artifact_hash_mismatch")
        from igem_drylab.workflow.store import canonical
        projected = boundary.tree(json.loads(raw),project_id=project_id)
        boundary.check(projected)
        body = canonical({"export_schema":"scientific-public-export-v1","original_artifact_id":artifact_id,
            "original_sha256":row["hash"],"path_projection":"registered_file_identities_only; not_original_bytes", "result":projected}).encode()
        return Response(body,media_type="application/json",headers={"Content-Disposition":"attachment; filename=scientific-public-export.json","X-Content-SHA256":sha256(body).hexdigest()})

    @router.get("/tools")
    def tool_list() -> list[dict[str, Any]]:
        # The public catalogue is attestation, not private executable schemas.
        # Internal tool schemas may include runtime command/profile definitions.
        result=[{key:item[key] for key in ("id","name","description","version","capability","runtime","plugin_hash","idempotent","resource")} for item in tools.list()]
        boundary.check(result)
        return result

    @router.get("/plugins")
    def plugin_list() -> list[dict[str, Any]]:
        return [public_plugin(item) for item in plugins.installed()]

    def public_plugin(item):
        from igem_drylab.software.public_contracts import PluginInspectionView
        manifest=item["manifest"]
        result=PluginInspectionView(manifest={key:manifest[key] for key in ("id","name","description","version","capability","license","runtime","permissions")},
            hash=item["hash"],sandboxed=item["sandboxed"],trust_required=item["trust_required"],installed=item.get("installed",False),
            source_path="plugin-source:"+Path(item["source_path"]).name if item.get("source_path") else None,
            capability_requests=["permission:"+key for key in manifest.get("permissions",[])]+["secret_env:"+key for key in manifest.get("secret_env",[])]).model_dump(mode="json")
        boundary.check(result)
        return result

    @router.post("/plugins/inspect")
    def inspect_plugin(request: PluginRequest) -> dict[str, Any]:
        if str(request.source_path).startswith("plugin-source:"):
            request.source_path = data_dir / "plugins" / "sources" / str(request.source_path).removeprefix("plugin-source:")
        if not request.source_path.resolve().is_relative_to(data_dir / "plugins" / "sources"):
            raise WorkflowError("plugin_source_outside_owned_workspace", status_code=403)
        return public_plugin(plugins.inspect(request.source_path))

    @router.post("/plugins/github")
    def github_plugin(request: GithubPluginRequest) -> dict[str, Any]:
        result = plugins.fetch_github(request.repository_url, request.commit)
        return public_plugin(result)

    @router.get("/schemas")
    def schemas() -> dict[str, Any]:
        from igem_drylab.software.public_contracts import public_schemas
        from igem_drylab.wetlab.models import WetLabResult
        result=public_schemas() | {"Pathway":Pathway.model_json_schema(),"WetLabResult":WetLabResult.model_json_schema()}
        boundary.check(result)
        return result

    @router.post("/plugins/install")
    def install_plugin(request: PluginRequest) -> dict[str, Any]:
        if not request.expected_hash:
            raise WorkflowError("plugin_changed_since_inspection", status_code=409)
        if str(request.source_path).startswith("plugin-source:"):
            request.source_path = data_dir / "plugins" / "sources" / str(request.source_path).removeprefix("plugin-source:")
        if not request.source_path.resolve().is_relative_to(data_dir / "plugins" / "sources"):
            raise WorkflowError("plugin_source_outside_owned_workspace", status_code=403)
        result = plugins.install(request.source_path, trusted=request.trusted, expected_hash=request.expected_hash)
        return public_plugin(result)

    return router

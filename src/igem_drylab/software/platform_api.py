"""HTTP transport for local projects, immutable runs, workflows and plugins."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from threading import Thread
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import Field

from igem_drylab.workflow.builtins import Goal, recommend
from igem_drylab.workflow.mcp_bridge import register_scientific_mcp
from igem_drylab.workflow.models import Contract, PlanBinding, Project, Workflow, WorkflowError
from igem_drylab.workflow.pathway import Pathway
from igem_drylab.workflow.store import plan_binding
from igem_drylab.workflow.planning import ProposalRequest, ProposalDecision
from igem_drylab.workflow.declared_series import DeclaredColumn, DeclaredSeries, read_columns
from igem_drylab.workflow.scientific_setup import ScientificSetupRequest
from igem_drylab.workflow.annotation_binding import AnnotationBindingRequest, bind_annotation


class SaveProject(Contract):
    project: Project
    expected_revision: int | None = None


class ImportRequest(Contract):
    filename: str
    content: str = Field(max_length=10_000_000)
    input_kind: Literal["auto", "pathway", "wetlab"] = "auto"


class ImportRevisionRequest(Contract):
    options: dict[str,dict[str,Any]] = Field(default_factory=dict)
    expected_revision: int | None = None


class ImportCommitRequest(Contract):
    choices: dict[str,Literal['reuse','replace','new_version']] = Field(default_factory=dict)


class SeriesMappingRequest(Contract):
    project_id: str
    expected_revision: int
    file_id: str
    source_reference: str = Field(min_length=1)
    time_key: str = Field(min_length=1)
    time_unit: str = Field(min_length=1)
    columns: list[DeclaredColumn] = Field(min_length=1, max_length=128)


class ScientificRecordRequest(Contract):
    kind: Literal["construct", "parameter"]
    value: dict[str, Any]


class ScientificImportRequest(Contract):
    config_path: Path


class ScientificBundleRequest(Contract):
    config_filename: str
    files: list[ImportRequest] = Field(min_length=1, max_length=256)


class PlanRequest(Contract):
    project_id: str
    goal: Goal
    objective: str = ""


class MethodPlanRequest(Contract):
    project_id: str
    method: Literal['sequence-properties','galatea-m1-m2','ps-v3-demo']


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


def platform_router(data_dir: Path, *, discover_tools: bool = True, planning_backend=None, workflow_tools=None, runtime_tools=None) -> APIRouter:
    data_dir = data_dir.resolve()
    from .application import ApplicationService
    application=ApplicationService(data_dir,workflow_tools=workflow_tools,planning_backend=planning_backend,runtime_tools=runtime_tools)
    store,tools,engine=application.store,application.tools,application.engine
    dispatcher,boundary=application.dispatcher,application.boundary
    from igem_drylab.workflow.views import PublicReads
    reads = PublicReads(store,boundary)
    from igem_drylab.workflow.display_resources import DisplayResources
    resources = DisplayResources(store, boundary)
    from igem_drylab.workflow.lineage_compare import LineageComparison
    comparisons = LineageComparison(store, boundary)
    planning,plugins=application.planning,application.plugins
    router = APIRouter(prefix="/api/platform")
    router.store, router.engine, router.disclosure = store, engine, boundary
    router.application=application
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
        return {"name": "FusionLab", "protocol_version": "2", "authentication": "session_required", "workspace_id": sha256(str(data_dir).encode()).hexdigest(), "storage": "SQLite WAL", "max_workers": engine.max_workers, "plugin_sandbox": False, "agent_backend": "hybrid_semantic_compiler" if planning_backend else "validated_workflow_templates", "capabilities": capabilities | {"stage_step":"ready","checkpoints":"ready","cancel_dispatch":"ready","hybrid_planning":"ready" if planning_backend else "unavailable","cross_run_reuse":"unavailable"}, "resources":engine.budget.state() | dispatcher.state(), "remote_desktop_authenticated_session": True, "supported_rate_laws": ["two_phase_competitive_mm_v1"]}

    @router.post("/proposals")
    def propose(request: ProposalRequest):
        return application.propose(request)

    @router.post('/method-plans')
    def method_plan(request: MethodPlanRequest):
        return application.plan(request.project_id,request.method)

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
    def scientific_precheck(project_id:str, through: Literal["m1", "m2", "m3", "m4", "m5"] | None = None):
        return application.check_inputs(project_id,through)

    @router.get("/projects/{project_id}/scientific-observation")
    def scientific_observation(project_id:str):
        from igem_drylab.agent.scientific_environment import ScientificEnvironment
        from igem_drylab.workflow.models import ExecutionPolicy
        observation=ScientificEnvironment(store,tools).observe(store.project(project_id),ExecutionPolicy())
        result=observation.model_dump(mode="json")
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

    @router.get("/projects/{project_id}/sequences")
    def project_sequence_choices(project_id: str, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)):
        from igem_drylab.workflow.sequence_index import sequence_page
        result = sequence_page(store.project(project_id), boundary, offset, limit).model_dump(mode="json")
        boundary.check(result)
        return result

    @router.post("/projects")
    def save_project(request: SaveProject) -> dict[str, Any]:
        return application.save_project(request.project,request.expected_revision)

    @router.get("/scientific-projects/form-schema")
    def scientific_form_schema(prepared_through: Literal["m1", "m2", "m3", "m4", "m5"] = "m5"):
        from igem_drylab.workflow.scientific_setup import form_schema
        result = form_schema(prepared_through)
        boundary.check(result)
        return result

    @router.post("/scientific-projects/create-preview")
    def scientific_create_preview(request: ScientificSetupRequest):
        from igem_drylab.workflow.scientific_setup import preview_setup
        return preview_setup(request, store, boundary)

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
            from igem_drylab.workflow.disclosure import check_import_content
            check_import_content(target.name, content.encode())
            boundary.check_bytes(content.encode())
        for target, content in contents.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        with store.connection() as db:
            db.execute("INSERT INTO scientific_bundles VALUES(?,?)", (root.name,str(root)))
        return scientific_preview(ScientificImportRequest(config_path=source))

    @router.post("/scientific-projects/upload-binary")
    async def scientific_binary(request: Request, config_filename: str):
        from igem_drylab.workflow.binary_import import receive_bundle
        def publish(root, filename, hashes):
            # Validate every extra before granting it any public identity. Failed
            # originals remain private in the owned quarantine, never masked.
            try:
                for name in hashes:
                    boundary.check_original(root / name)
            except WorkflowError as error:
                if str(error) == "disclosure_quarantined":
                    quarantine = data_dir / "quarantine"
                    quarantine.mkdir(exist_ok=True)
                    root.rename(quarantine / root.name)
                raise
            from igem_drylab.workflow.scientific_project import load_scientific_project
            from igem_drylab.resources import default_config_path
            science = load_scientific_project(root / filename, allowed_roots=(root, default_config_path("m1_feature_definitions.yaml"), default_config_path("m1_rules_v3.yaml")))
            from igem_drylab.workflow.scientific_project import EvidenceFile
            bound = {item.path for item in science.evidence_files}
            science.evidence_files.extend(EvidenceFile(path=root / name, sha256=digest) for name, digest in hashes.items() if root / name not in bound)
            science.verify()
            with store.connection() as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute("INSERT INTO scientific_bundles VALUES(?,?)", (root.name, str(root)))
                result = boundary.scientific(science.model_dump(mode="json"), db=db)
                # Register extra uploaded display assets without inventing scientific bindings.
                for logical_name in hashes:
                    boundary.asset(root / logical_name, logical_name=logical_name, db=db)
            return {"scientific_project": result, "requires_confirmation": True, "dependency_scope": science.dependency_scope}
        return await receive_bundle(request, data_dir / "imports", config_filename, publish)

    @router.get("/projects/{project_id}/resources")
    def project_resources(project_id: str, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                          kind: Literal["image", "structure", "series", "scan", "m5", "table"] | None = None):
        return resources.catalog(project_id, offset, limit, kind=kind)

    @router.get("/runs/{run_id}/resources")
    def run_resources(run_id: str, project_id: str, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                      kind: Literal["image", "structure", "series", "scan", "m5", "table"] | None = None):
        return resources.catalog(project_id, offset, limit, run_id, kind=kind)

    @router.get("/projects/{project_id}/lineage")
    def project_lineage(project_id: str, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
        return comparisons.lineage(project_id, offset, limit)

    @router.get("/projects/{project_id}/compare")
    def compare_runs(project_id: str, left_run_id: str, right_run_id: str, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50), objective: Literal["yield_abs", "productivity"] = "yield_abs"):
        return comparisons.compare(project_id, left_run_id, right_run_id, offset, limit, objective)

    @router.get("/files/{file_id}/series")
    def display_series(file_id: str, project_id: str, offset: int = Query(0, ge=0), limit: int = Query(500, ge=1, le=100_000), series_id: list[str] | None = Query(None)):
        return resources.series(project_id, file_id, offset, limit, series_id)

    @router.get('/files/{file_id}/series.csv')
    def export_series(file_id: str,project_id: str):
        from igem_drylab.workflow.series_export import series_csv
        resources.series(project_id,file_id,0,1)  # Verify identity/format before sending headers.
        return StreamingResponse(series_csv(resources,project_id,file_id),media_type='text/csv',
            headers={'Content-Disposition':'attachment; filename="recorded-series.csv"','Cache-Control':'no-store'})

    @router.get("/files/{file_id}/table")
    def display_table(file_id: str, project_id: str, offset: int = Query(0, ge=0), limit: int = Query(500, ge=1, le=1000)):
        from igem_drylab.workflow.table_display import table_page
        return table_page(resources, project_id, file_id, offset, limit)

    @router.get("/files/{file_id}/resource")
    def resource_item(file_id: str, project_id: str, run_id: str | None = None):
        resources.source(project_id, file_id)
        result = resources.catalog(project_id, run_id=run_id, file_id=file_id)
        if not result["items"]:
            raise WorkflowError("resource_not_in_selected_run", status_code=404)
        return result

    @router.post("/imports/series-mapping")
    def series_mapping(request: SeriesMappingRequest):
        project = store.project(request.project_id)
        if project.revision != request.expected_revision:
            raise WorkflowError("project_revision_changed", status_code=409)
        path, identity, name = resources.source(project.id, request.file_id)
        boundary.check_original(path)
        if path.suffix.lower() not in {".csv", ".tsv"}:
            raise WorkflowError("mapping_requires_delimited_table")
        declaration = DeclaredSeries(schema_version="display-series-source-v1",
            target_sha256=identity.source_sha256, source_reference=request.source_reference,
            format=path.suffix.lower()[1:], time_key=request.time_key, time_unit=request.time_unit,
            missing_token="", columns=request.columns)
        read_columns(path, declaration)  # Validate all original values before publishing a declaration.
        raw = declaration.model_dump_json().encode()
        boundary.check(declaration.model_dump(mode="json"))
        root = data_dir / "imports"
        root.mkdir(parents=True, exist_ok=True)
        source = root / (sha256(raw).hexdigest() + ".json")
        source.write_bytes(raw)
        file = boundary.asset(source, project_id=project.id, fresh=True, logical_name=name + ".series.json")
        return {"kind": "series", "patch": {}, "file": file}

    @router.post("/scientific-records/preview")
    def scientific_record(request: ScientificRecordRequest):
        from igem_drylab.software.public_contracts import ScientificRecordView
        from igem_drylab.pipeline.config import ConstructDefinition
        from igem_drylab.parameters import ParameterRecord
        boundary.check(request.value)
        if request.kind == "construct":
            result = ScientificRecordView(kind="construct", construct_record=ConstructDefinition.model_validate(request.value))
        else:
            if request.value.get("review_status", "extracted") != "extracted" or request.value.get("approved_by") is not None:
                raise WorkflowError("record_preview_cannot_approve")
            result = ScientificRecordView(kind="parameter", parameter=ParameterRecord.model_validate(request.value))
        value = result.model_dump(mode="json")
        boundary.check(value)
        return value

    @router.post("/imports/display-file")
    async def display_import(request: Request, filename: str):
        extension = Path(filename).suffix.lower()
        if extension not in {".png", ".jpg", ".jpeg", ".pdb", ".cif", ".mmcif", ".bcif", ".zip"}:
            raise WorkflowError("unsupported_display_import")
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > 20_000_000:
                raise WorkflowError("display_source_budget_exceeded", status_code=413)
            raw.extend(chunk)
        if extension=='.zip':
            from igem_drylab.workflow.synthetic_ps import preview_ps_archive
            return preview_ps_archive(application,filename,bytes(raw))
        from igem_drylab.workflow.disclosure import check_import_content
        check_import_content(filename, bytes(raw))
        boundary.check_bytes(bytes(raw))
        root = data_dir / "imports"
        root.mkdir(parents=True, exist_ok=True)
        source = root / (sha256(raw).hexdigest() + extension)
        source.write_bytes(raw)
        file = boundary.asset(source, fresh=True, logical_name=filename)
        return {"kind": "display_only", "patch": {}, "file": file}

    @router.post("/imports/structure-annotations")
    def annotation_binding(request: AnnotationBindingRequest):
        return bind_annotation(request, resources, data_dir)

    @router.get("/files/{file_id}/scan")
    def display_scan(file_id: str, project_id: str, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=10000)):
        from igem_drylab.workflow.scan_display import scan_page
        return scan_page(resources, project_id, file_id, offset, limit)

    @router.get('/files/{file_id}/m5-comparison')
    def display_m5(file_id: str, project_id: str):
        return resources.m5(project_id, file_id)

    @router.get("/files/{file_id}/image-preview")
    def display_image(file_id: str, project_id: str):
        raw = resources.image(project_id, file_id)
        return Response(raw, media_type="image/png", headers={"X-Preview-SHA256": sha256(raw).hexdigest(), "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

    @router.get("/files/{file_id}/structure-metadata")
    def structure_metadata(file_id: str, project_id: str, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)):
        return resources.structure(project_id, file_id, offset, limit)[0]

    @router.get("/files/{file_id}/structure-annotations")
    def structure_annotations(file_id: str, project_id: str):
        return resources.structure(project_id, file_id, limit=0, full_annotations=True)[0]

    @router.get("/files/{file_id}/structure-preview")
    def structure_preview(file_id: str, project_id: str):
        _, raw = resources.structure(project_id, file_id, annotations=False)
        return Response(raw, media_type="text/plain", headers={"X-Preview-SHA256": sha256(raw).hexdigest(), "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

    @router.post("/imports/preview")
    def import_preview(request: ImportRequest) -> dict[str, Any]:
        return application.preview_import(request.filename,request.content,request.input_kind)

    async def uploaded_files(request):
        # Multipart streams file/folder contents into the same parser service.
        # Filename paths are checked before any filesystem publication.
        from starlette.datastructures import UploadFile
        files=[];received=0
        async with request.form(max_files=256,max_fields=1,max_part_size=20_000_000) as form:
            for _,value in form.multi_items():
                if not isinstance(value,UploadFile): raise WorkflowError('import_requires_files')
                chunks=[]
                while chunk:=await value.read(65536):
                    received+=len(chunk)
                    if received>20_000_000: raise WorkflowError('scientific_upload_budget_exceeded',status_code=413)
                    chunks.append(chunk)
                files.append((value.filename or '',b''.join(chunks)))
        return files

    @router.post('/projects/{project_id}/imports')
    async def transaction_preview(project_id: str,request: Request):
        return application.imports.preview(project_id,await uploaded_files(request)).model_dump(mode='json')

    @router.get('/projects/{project_id}/imports')
    def transaction_pending(project_id: str):
        return {'transaction_ids':application.imports.pending(project_id)}

    @router.post('/projects/{project_id}/imports/{transaction_id}/files')
    async def transaction_append(project_id: str,transaction_id: str,request: Request):
        return application.imports.append(project_id,transaction_id,await uploaded_files(request)).model_dump(mode='json')

    @router.get('/projects/{project_id}/imports/{transaction_id}')
    def transaction_inspect(project_id: str,transaction_id: str):
        return application.imports.inspect(project_id,transaction_id).model_dump(mode='json')

    @router.patch('/projects/{project_id}/imports/{transaction_id}')
    def transaction_revise(project_id: str,transaction_id: str,request: ImportRevisionRequest):
        return application.imports.revise(project_id,transaction_id,request.options,request.expected_revision).model_dump(mode='json')

    @router.post('/projects/{project_id}/imports/{transaction_id}/commit')
    def transaction_commit(project_id: str,transaction_id: str,request: ImportCommitRequest):
        return application.imports.commit(project_id,transaction_id,request.choices)

    @router.post('/projects/{project_id}/imports/{transaction_id}/discard')
    def transaction_discard(project_id: str,transaction_id: str):
        return application.imports.discard(project_id,transaction_id).model_dump(mode='json')

    @router.get('/projects/{project_id}/designs/{design_id}')
    def genbank_design(project_id: str, design_id: str, record_index: int = Query(0, ge=0),
                       feature_offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                       nucleotide_offset: int = Query(0, ge=0)):
        from igem_drylab.workflow.genbank_design import GenBankDesign, design_page
        project = store.project(project_id)
        row = next((item for item in project.datasets if item.get('kind') == 'genbank_design' and item.get('id') == design_id), None)
        if row is None:
            raise WorkflowError('genbank_design_not_found', status_code=404)
        design = GenBankDesign.model_validate(row)
        if design.file_id not in {item.get('id') for item in project.files}:
            raise WorkflowError('genbank_design_file_not_attached', status_code=403)
        source = Path(boundary.resolve_asset(design.file_id, project_id))
        result = design_page(source.read_text(encoding='utf-8'), design, project.sequences,
            record_index, feature_offset, limit, nucleotide_offset).model_dump(mode='json')
        boundary.check(result)
        return result

    @router.post("/plans")
    def plan(request: PlanRequest) -> dict[str, Any]:
        project = store.project(request.project_id)
        workflow = recommend(project, request.goal)
        if request.objective:
            workflow.description += f" Original user objective: {request.objective}"
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
        return application.validate_workflow(workflow)

    @router.post("/runs", status_code=202)
    def run(request: RunRequest) -> dict[str, Any]:
        return application.start_run(**request.model_dump(exclude={'workflow','confirmation'}),
            workflow=request.workflow,confirmation=request.confirmation)

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
            row = db.execute("SELECT project_id,name FROM file_assets WHERE id=?",(file_id,)).fetchone()
        if row is None or row[0] != project_id:
            raise WorkflowError("file_project_mismatch",status_code=403)
        path = Path(boundary.resolve_asset(file_id,project_id))
        raw = path.read_bytes()
        boundary.check_original(path)
        return FileResponse(path,filename=row["name"],headers={"X-Content-SHA256":sha256(raw).hexdigest()})

    @router.get("/files/{file_id}/data")
    def scientific_data(file_id: str,project_id: str,offset: int = Query(0,ge=0),limit: int = Query(100,ge=1,le=500)):
        with store.connection() as db:
            row = db.execute("SELECT project_id,hash FROM file_assets WHERE id=?",(file_id,)).fetchone()
        if row is None or row[0] != project_id:
            raise WorkflowError("file_project_mismatch",status_code=403)
        path = Path(boundary.resolve_asset(file_id,project_id))
        page = resources.series(project_id, file_id, offset, limit)
        if page['result_schema_version']=='m4-compartment-amount-v1':
            return page  # Typed units per column; never flatten amounts into cytosol concentration.
        concentrations = {}
        for descriptor in page["series"]:
            concentrations.setdefault(descriptor["compartment"], {})[descriptor["species"]] = page["values"][descriptor["id"]]
        result = {"file_id": file_id, "sha256": row["hash"], "offset": offset, "total": page["total"], "prediction_contract": {
            "schema_version": page["result_schema_version"], "model_kind": page["model_kind"], "formula_version": page["formula_version"],
            "time_unit": page["time_unit"], "concentration_unit": page["series"][0]["unit"] if page["series"] else None,
            "time": page["time"], "concentrations": concentrations}}
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
            "Review a new scope from a frozen run; not executed.",source="run_clone",previous_review_identity=engine.snapshot_review_identity(old)).model_dump(mode="json")

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
        result=[{key:getattr(item,key) for key in ("id","name","description","version","capability","runtime","plugin_hash","idempotent","resource")} for item in tools.definitions()]
        boundary.check(result)
        return result

    @router.get("/projects/{project_id}/prediction-tools")
    def prediction_tool_list(project_id: str):
        from igem_drylab.software.public_contracts import PredictionToolView
        from igem_drylab.workflow.runtime_profiles import RuntimeProfiles
        from igem_drylab.pipeline.adapters import create_tool_adapter
        from igem_drylab.pipeline.config import ToolConfig
        from igem_drylab.external_tools import tool_spec
        project = store.project(project_id)
        profile, private = RuntimeProfiles(store).get(project.runtime_profile_ref) if project.runtime_profile_ref else (None, {})
        with store.connection() as db:
            last = db.execute("""SELECT n.output,r.updated_at FROM nodes n JOIN runs r ON n.run_id=r.id
                WHERE r.project_id=? AND json_extract(n.output,'$.schema_version')='sequence-prediction-v1'
                AND json_extract(r.snapshot,'$.runtime_profile.hash')=? ORDER BY r.updated_at DESC""",
                (project_id, profile["hash"] if profile else None)).fetchall()
        rows = []
        for name in ("iupred2a", "seg", "colabfold", "pscore", "jpred"):
            config = ToolConfig.model_validate(private.get(name, {}))
            adapter = create_tool_adapter(name, config)
            executed = next(((json.loads(row["output"]), row["updated_at"]) for row in last if json.loads(row["output"]).get("tool") == name), None)
            from igem_drylab.workflow.sequence_predictions import uses_native_jpred_route
            complete_route = name!="jpred" or uses_native_jpred_route(config)
            status = "configured_unverified" if complete_route and adapter.is_available() else "not_configured"
            latest_file, checked = None, None
            if executed:
                output, checked = executed
                if complete_route and output["tool_status"] == "succeeded" and output["parse_status"] == "succeeded":
                    status = "available"
                elif output["tool_status"] not in {"succeeded", "not_configured", "not_eligible"}:
                    status = "failed"
                paths = list(output.get("outputs", {}).values())
                if paths:
                    with store.connection() as db:
                        asset = db.execute("SELECT id FROM file_assets WHERE project_id=? AND path=?", (project_id, paths[0])).fetchone()
                    latest_file = asset[0] if asset else None
            rows.append(PredictionToolView(id="prediction." + name, name=tools.get("prediction." + name).name,
                status=status, version=config.verified_version, last_real_check=checked,
                latest_file_id=latest_file, source_reference=tool_spec(name).official_url).model_dump(mode="json"))
        boundary.check(rows)
        return rows

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

"""FastAPI transport for the Dashboard; scientific execution stays in MCP tools."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock, Thread
from typing import Literal, TYPE_CHECKING
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from igem_drylab.mcp import ToolRegistry

RunStatus = Literal["queued", "running", "succeeded", "failed", "unavailable"]


class DashboardModule(BaseModel):
    id: str
    name: str
    description: str
    inputs: list[str]
    outputs: list[str]
    run_available: bool
    unavailable_reason: str | None = None


class DashboardRunRequest(BaseModel):
    module_id: str
    config_path: Path
    output_dir: Path | None = None


class DashboardLog(BaseModel):
    step: str
    status: RunStatus
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DashboardRun(BaseModel):
    run_id: str
    module_id: str
    status: RunStatus
    logs: list[DashboardLog] = Field(default_factory=list)
    result: dict[str, object] | None = None
    error: dict[str, str] | None = None


_MODULES = [
    DashboardModule(id="m0", name="M0 · Data validation", description="Validate the project configuration and declared inputs.", inputs=["project YAML"], outputs=["normalized input summary"], run_available=True),
    DashboardModule(id="m1", name="M1 · Sequence screen", description="Sequence-level construct feasibility screen.", inputs=["construct definitions", "linker sequences"], outputs=["M1 candidate records"], run_available=False, unavailable_reason="No standalone M1 tool contract exists; use the deterministic full pipeline."),
    DashboardModule(id="m2", name="M2 · Structural screen", description="Structural accessibility negative screen from supplied metrics.", inputs=["M1 candidates", "parsed structure metrics"], outputs=["M2 assessments"], run_available=False, unavailable_reason="No standalone M2 tool contract exists; use the deterministic full pipeline."),
    DashboardModule(id="m3", name="M3 · Phase partitioning", description="Mass-conserving dense/dilute enzyme distribution.", inputs=["M2 candidates", "reviewed partition parameters"], outputs=["candidate-specific M4 context"], run_available=False, unavailable_reason="No standalone M3 tool contract exists; use the deterministic full pipeline."),
    DashboardModule(id="m4", name="M4 · Kinetic simulation", description="Run production M4 with its deterministic M1–M3 prerequisites.", inputs=["project YAML", "reviewed M3/M4 parameters"], outputs=["M4 predictions and trajectory artifacts"], run_available=True),
    DashboardModule(id="m5", name="M5 · Wet-lab feedback", description="QC and bounded fitting of structured wet-lab measurements.", inputs=["M4 predictions", "wet-lab measurements"], outputs=["feedback assessment"], run_available=False, unavailable_reason="No standalone M5 tool contract exists; use the deterministic full pipeline."),
]
_BY_ID = {module.id: module for module in _MODULES}


class DashboardRuns:
    """Small in-memory run ledger required by the polling API."""

    def __init__(self) -> None:
        self._runs: dict[str, DashboardRun] = {}
        self._lock = Lock()

    def create(self, module_id: str) -> DashboardRun:
        run = DashboardRun(run_id=str(uuid4()), module_id=module_id, status="queued")
        run.logs.append(DashboardLog(step=module_id, status="queued", message="Run accepted."))
        with self._lock:
            self._runs[run.run_id] = run
        return run

    def get(self, run_id: str) -> DashboardRun | None:
        with self._lock:
            run = self._runs.get(run_id)
            return run.model_copy(deep=True) if run is not None else None

    def append(self, run_id: str, status: RunStatus, message: str) -> None:
        def apply(run: DashboardRun) -> None:
            run.status = status
            run.logs.append(DashboardLog(step=run.module_id, status=status, message=message))
        self._update(run_id, apply)

    def complete(self, run_id: str, result: dict[str, object]) -> None:
        def apply(run: DashboardRun) -> None:
            run.status = "succeeded"
            run.result = result
            run.logs.append(DashboardLog(step=run.module_id, status="succeeded", message="Runtime tool completed."))
        self._update(run_id, apply)

    def fail(self, run_id: str, error: dict[str, str]) -> None:
        def apply(run: DashboardRun) -> None:
            run.status = "failed"
            run.error = error
            run.logs.append(DashboardLog(step=run.module_id, status="failed", message=error["message"]))
        self._update(run_id, apply)

    def _update(self, run_id: str, update: Callable[[DashboardRun], None]) -> None:
        with self._lock:
            if run_id in self._runs:
                update(self._runs[run_id])


def create_app(registry: ToolRegistry | None = None, *, data_dir: Path | None = None, session_token: str | None = None,
               deployment_mode: Literal["authenticated", "development"] = "authenticated", discover_tools: bool = True, planning_backend=None, workflow_tools=None, runtime_tools=None,
               frontend_dir: Path | None = None,local_web_origin: str | None = None) -> FastAPI:
    """Build the durable platform API and retain deprecated legacy routes."""
    if deployment_mode == "authenticated" and not session_token:
        raise ValueError("authenticated_deployment_requires_private_session_token")
    # Production workbench never executes the deprecated in-memory runner.
    # Loading its complete science/research registry must not block basic API
    # readiness. Explicit development callers initialize it only when used.
    tool_registry = registry
    registry_lock = Lock()
    runs = DashboardRuns()
    app = FastAPI(title="iGEM Dry-Lab Dashboard API", version="0.1.0")
    from .platform_api import platform_router
    router = platform_router(data_dir or Path("outputs/platform"), discover_tools=discover_tools,planning_backend=planning_backend,workflow_tools=workflow_tools,runtime_tools=runtime_tools)
    app.include_router(router)
    app.state.platform_store, app.state.workflow_engine, app.state.disclosure = router.store, router.engine, router.disclosure
    app.state.application=router.application
    router.application.assistant_settings.configure_deployment(local_workspace=bool(local_web_origin))
    if session_token:
        router.disclosure.register_private(session_token)

    if deployment_mode == "development" and not session_token:
        @app.middleware("http")
        async def local_development_only(request: Request, call_next):
            if request.client and request.client.host not in {"127.0.0.1", "::1", "testclient"}:
                return JSONResponse(status_code=403, content={"detail": {"code": "development_requires_loopback"}})
            return await call_next(request)

    from igem_drylab.workflow.models import WorkflowError
    from igem_drylab.workflow.tools import ToolFailure

    @app.exception_handler(WorkflowError)
    def workflow_failure(request: Request, exc: WorkflowError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": router.disclosure.diagnostic(exc, code=exc.code)})

    @app.exception_handler(ToolFailure)
    def tool_failure(request: Request, exc: ToolFailure) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": router.disclosure.diagnostic(exc, code=exc.code)})

    @app.exception_handler(ValueError)
    def invalid_input(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": router.disclosure.diagnostic(exc, code="invalid_input")})

    @app.exception_handler(KeyError)
    def missing_record(request: Request, exc: KeyError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": router.disclosure.diagnostic(exc, code="not_found")})

    @app.exception_handler(RequestValidationError)
    def invalid_contract(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": router.disclosure.diagnostic(exc, code="invalid_contract")})
    from .session import configure_session
    configure_session(app, session_token,local_web_origin=local_web_origin)

    @app.get("/api/dashboard/dag", response_model=list[DashboardModule], deprecated=True)
    def get_dag() -> list[DashboardModule]:
        return _MODULES

    @app.post("/api/dashboard/runs", response_model=DashboardRun, status_code=202, deprecated=True)
    def start_run(request: DashboardRunRequest) -> DashboardRun:
        nonlocal tool_registry
        if deployment_mode != "development":
            raise HTTPException(status_code=410, detail={"code": "legacy_execution_requires_durable_reviewed_plan"})
        module = _BY_ID.get(request.module_id)
        if module is None:
            raise HTTPException(status_code=404, detail={"code": "unknown_module", "message": f"Unknown module: {request.module_id}"})
        run = runs.create(module.id)
        if not module.run_available:
            runs.append(run.run_id, "unavailable", module.unavailable_reason or "This module cannot run independently.")
            return runs.get(run.run_id)  # type: ignore[return-value]
        with registry_lock:
            if tool_registry is None:
                from igem_drylab.mcp import create_default_registry
                tool_registry = create_default_registry()
        Thread(target=_execute, args=(runs, tool_registry, run.run_id, request), daemon=True).start()
        return run

    @app.get("/api/dashboard/runs/{run_id}", response_model=DashboardRun, deprecated=True)
    def get_run(run_id: str) -> DashboardRun:
        run = runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail={"code": "unknown_run", "message": f"Unknown run: {run_id}"})
        return run

    if frontend_dir is not None:
        from .web import mount_frontend
        mount_frontend(app,frontend_dir)
    return app


def _execute(runs: DashboardRuns, registry: ToolRegistry, run_id: str, request: DashboardRunRequest) -> None:
    runs.append(run_id, "running", "Dispatching existing local runtime tool.")
    tool_name, arguments = _tool_request(request)
    result = registry.call(tool_name, arguments)
    payload = result.structured_content
    if result.is_error:
        error = payload.get("error", {})
        runs.fail(run_id, {"code": str(error.get("type", "runtime_error")), "message": str(error.get("message", "Runtime tool failed."))})
        return
    runs.complete(run_id, payload)


def _tool_request(request: DashboardRunRequest) -> tuple[str, dict[str, object]]:
    if request.module_id == "m0":
        return "igem.pipeline.validate", {"config_path": str(request.config_path)}
    if request.module_id == "m4":
        arguments: dict[str, object] = {"config_path": str(request.config_path), "stage": "m4"}
        if request.output_dir is not None:
            arguments["output_dir"] = str(request.output_dir)
        return "igem.pipeline.run_stage", arguments
    raise ValueError(f"Module {request.module_id} has no standalone runtime tool.")


def serve(*, host: str, port: int, data_dir: Path | None = None, development: bool = False, token_env: str = "FUSIONLAB_API_TOKEN") -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("Dashboard requires the optional dependency group: pip install -e '.[software]'") from exc
    import os
    if not development and not os.environ.get(token_env) and host in {'127.0.0.1','localhost'}:
        from .web import serve_local
        serve_local(data_dir=data_dir,port=port)
        return
    if development and host not in {"127.0.0.1", "::1"}:
        raise ValueError("anonymous_development_must_bind_loopback")
    token = None if development else os.environ.get(token_env)
    uvicorn.run(create_app(data_dir=data_dir, session_token=token, deployment_mode="development" if development else "authenticated"), host=host, port=port)

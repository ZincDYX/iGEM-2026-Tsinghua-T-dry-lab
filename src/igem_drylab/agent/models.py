from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


StepStatus = Literal["pending", "ready", "running", "waiting_approval", "succeeded", "failed", "skipped", "blocked"]
ResourceLabel = Literal["cpu", "gpu", "network", "external_api"]


class AgentTask(BaseModel):
    """A reproducible request to the dry-lab agent.

    ``inputs`` deliberately contains paths/identifiers, not secrets.  For
    example, a task may provide ``config_path`` and an existing ColabFold output
    directory.  API keys always remain in environment variables.
    """

    task_id: str
    objective: str
    constraints: list[str] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    artifacts_dir: str = "outputs/agent_runs"
    require_human_approval: bool = True
    max_replans: int = Field(default=2, ge=0, le=5)


class ResultCondition(BaseModel):
    """Permit a step only when a prior tool result has an accepted value."""

    source_step_id: str
    source_path: list[str]
    allowed_values: list[Any]


class ResultBinding(BaseModel):
    """Copy a JSON value from one successful tool result into a later step."""

    target_step_id: str
    target_argument: str
    source_path: list[str]


class PlanStep(BaseModel):
    step_id: str
    objective: str
    tool_name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    required_artifact_ids: list[str] = Field(default_factory=list)
    produces: list[str] = Field(default_factory=list)
    run_conditions: list[ResultCondition] = Field(default_factory=list)
    result_bindings: list[ResultBinding] = Field(default_factory=list)
    resources: list[ResourceLabel] = Field(default_factory=lambda: ["cpu"])
    priority: int = Field(default=50, ge=0, le=100)
    estimated_gpu_minutes: float = Field(default=0.0, ge=0)
    estimated_api_calls: int = Field(default=0, ge=0)
    retry_limit: int = Field(default=1, ge=0, le=5)
    attempts: int = Field(default=0, ge=0)
    status: StepStatus = "pending"
    rationale: str = ""


class Plan(BaseModel):
    task_id: str
    steps: list[PlanStep]
    plan_id: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("plan-%Y%m%dT%H%M%S%f"))
    previous_plan_id: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class ToolCallRecord(BaseModel):
    step_id: str
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    status: Literal["succeeded", "failed"]
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentTrace(BaseModel):
    task: AgentTask
    plan: Plan
    calls: list[ToolCallRecord] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    context_summary: dict[str, Any] = Field(default_factory=dict)
    replan_count: int = 0
    replan_reasons: list[str] = Field(default_factory=list)
    final_status: Literal["completed", "waiting_for_human", "blocked", "failed"] = "completed"

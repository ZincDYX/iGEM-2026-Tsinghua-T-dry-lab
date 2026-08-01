from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


StepStatus = Literal["pending", "ready", "running", "succeeded", "failed", "skipped"]


class AgentTask(BaseModel):
    task_id: str
    objective: str
    constraints: list[str] = Field(default_factory=list)
    artifacts_dir: str = "outputs/agent_runs"


class PlanStep(BaseModel):
    step_id: str
    objective: str
    tool_name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    status: StepStatus = "pending"
    rationale: str = ""


class Plan(BaseModel):
    task_id: str
    steps: list[PlanStep]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ToolCallRecord(BaseModel):
    step_id: str
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    status: Literal["succeeded", "failed"]


class AgentTrace(BaseModel):
    task: AgentTask
    plan: Plan
    calls: list[ToolCallRecord] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

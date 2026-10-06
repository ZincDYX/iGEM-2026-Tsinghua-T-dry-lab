from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class WorkflowError(ValueError):
    """Machine-readable failure at an API/persistence boundary."""

    def __init__(self, code: str, *, status_code: int = 422, logical_files: tuple[str, ...] = (), private_detail: str | None = None) -> None:
        super().__init__(code)
        self.code, self.status_code = code, status_code
        self.logical_files, self.private_detail = logical_files, private_detail


class PlanBinding(Contract):
    project_id: str
    project_revision: int = Field(ge=1)
    project_input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    workflow_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    paused = "paused"
    interrupted = "interrupted"
    cancelled = "cancelled"


class NodeStatus(str, Enum):
    pending = "pending"
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    interrupted = "interrupted"
    blocked = "blocked"


class LiteralInput(Contract):
    kind: Literal["literal"] = "literal"
    value: Any


class ProjectInput(Contract):
    kind: Literal["project"] = "project"
    path: list[str | int] = Field(default_factory=list)


class NodeInput(Contract):
    kind: Literal["node"] = "node"
    node_id: str
    path: list[str | int] = Field(default_factory=list)


InputValue = Annotated[LiteralInput | ProjectInput | NodeInput, Field(discriminator="kind")]


class MapSpec(Contract):
    items: InputValue
    item_argument: str = "item"


class WorkflowNode(Contract):
    id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_.-]+$")
    label: str
    tool_id: str
    inputs: dict[str, InputValue] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    map: MapSpec | None = None

    def dependencies(self) -> set[str]:
        values = list(self.inputs.values())
        if self.map:
            values.append(self.map.items)
        return set(self.depends_on) | {value.node_id for value in values if isinstance(value, NodeInput)}


class ExecutionPolicy(Contract):
    target_node_id: str | None = None
    max_completed_stages: int | None = Field(default=None, ge=1)
    checkpoints_before: list[str] = Field(default_factory=list)
    checkpoints_after: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    max_tool_calls: int = Field(default=1000, ge=1)
    stop_after_seconds: float | None = Field(default=None, gt=0)
    memory_limit_mb: int | None = Field(default=None, ge=1)


class Workflow(Contract):
    id: str
    name: str
    description: str = ""
    version: str = "1"
    nodes: list[WorkflowNode] = Field(min_length=1)
    execution_policy: ExecutionPolicy = Field(default_factory=ExecutionPolicy)

    @model_validator(mode="after")
    def validate_graph(self) -> "Workflow":
        ids = [node.id for node in self.nodes]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate_node_id")
        policy = self.execution_policy
        selected = set(policy.checkpoints_before + policy.checkpoints_after)
        if policy.target_node_id: selected.add(policy.target_node_id)
        if selected - set(ids): raise ValueError("unknown_policy_node")
        if policy.memory_limit_mb is not None: raise ValueError("memory_limit_not_supported_by_process_backend")
        if not policy.allowed_tools: policy.allowed_tools = sorted({node.tool_id for node in self.nodes})
        if {node.tool_id for node in self.nodes} - set(policy.allowed_tools): raise ValueError("tool_not_in_execution_authorization")
        remaining = {node.id: node.dependencies() for node in self.nodes}
        if any(dependencies - set(ids) for dependencies in remaining.values()):
            raise ValueError("unknown_dependency")
        while remaining:
            ready = {key for key, dependencies in remaining.items() if not dependencies}
            if not ready:
                raise ValueError("workflow_cycle")
            remaining = {key: dependencies - ready for key, dependencies in remaining.items() if key not in ready}
        return self


class SequenceRecord(Contract):
    id: str
    sequence: str = Field(min_length=1)
    role: str = "fusion_protein"


class AssemblyRecord(Contract):
    id: str
    subunits: dict[str, int]
    description: str = ""

    @model_validator(mode="after")
    def positive_stoichiometry(self) -> "AssemblyRecord":
        if not self.subunits or any(count < 1 for count in self.subunits.values()):
            raise ValueError("assembly_requires_positive_subunit_counts")
        return self


class Project(Contract):
    id: str
    name: str = Field(min_length=1)
    revision: int = Field(default=1, ge=1)
    description: str = ""
    sequences: list[SequenceRecord] = Field(default_factory=list)
    assemblies: list[AssemblyRecord] = Field(default_factory=list)
    conditions: dict[str, Any] = Field(default_factory=dict)
    pathway: dict[str, Any] | None = None
    files: list[dict[str, str]] = Field(default_factory=list)
    datasets: list[dict[str, Any]] = Field(default_factory=list)
    # Validated as ScientificProject at API/execution boundaries, avoiding a
    # dependency cycle between the generic ledger and scientific stage adapter.
    scientific_project: dict[str, Any] | None = None
    runtime_profile_ref: str | None = None
    parent_run_id: str | None = None
    parent_snapshot_sha256: str | None = None

    @model_validator(mode="after")
    def unique_sequences(self) -> "Project":
        ids = [sequence.id for sequence in self.sequences]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate_sequence_id")
        if len({assembly.id for assembly in self.assemblies}) != len(self.assemblies):
            raise ValueError("duplicate_assembly_id")
        for assembly in self.assemblies:
            if set(assembly.subunits) - set(ids):
                raise ValueError("assembly_references_unknown_sequence")
        return self


def read_path(value: Any, path: list[str | int]) -> Any:
    for key in path:
        value = value[key]
    return value

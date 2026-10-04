from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class WorkflowError(ValueError):
    """Machine-readable failure at an API/persistence boundary."""

    def __init__(self, code: str, *, status_code: int = 422) -> None:
        super().__init__(code)
        self.code, self.status_code = code, status_code


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


class Workflow(Contract):
    id: str
    name: str
    description: str = ""
    version: str = "1"
    nodes: list[WorkflowNode] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_graph(self) -> "Workflow":
        ids = [node.id for node in self.nodes]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate_node_id")
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

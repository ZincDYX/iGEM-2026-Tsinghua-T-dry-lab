"""Single Pydantic source for public protocol types and browser validation."""
from copy import deepcopy
from pathlib import PureWindowsPath, PurePosixPath
from typing import Any, Literal

from pydantic import Field, create_model

from igem_drylab.pipeline.config import ProjectConfig
from igem_drylab.workflow.models import Contract, Project, Workflow, PlanBinding
from igem_drylab.workflow.disclosure import NodeResultView
from igem_drylab.workflow.views import ProjectSummaryView, RunSummaryView
from igem_drylab.workflow.planning import ProposalView
from igem_drylab.agent.scientific_environment import ScientificObservation
from igem_drylab.workflow.public_errors import PublicError
from igem_drylab.workflow.precheck import ScientificPrecheckView
from igem_drylab.workflow.sequence_index import SequenceIndexView, SequencePage
from igem_drylab.workflow.sequence_results import SequenceMapView
from igem_drylab.workflow.display_resources import ResourcePage, SeriesPage, StructurePage
from igem_drylab.workflow.lineage_compare import LineagePage, ComparePage
from igem_drylab.wetlab.comparison import M5ComparisonSeries
from igem_drylab.workflow.scan_display import ScanPage
from igem_drylab.workflow.table_display import TablePage
from igem_drylab.pipeline.config import ConstructDefinition
from igem_drylab.parameters import ParameterRecord
from igem_drylab.workflow.genbank_design import GenBankDesign, GenBankPage
from .import_service import ImportTransactionPreview


class AssetIdentity(Contract):
    id: str
    file_id: str
    path: str
    sha256: str
    name: str


class PublicRunInput(Contract):
    id: str


ScientificConfig = create_model("ScientificConfig",__base__=Contract,
    **{name:(field.annotation,deepcopy(field)) for name,field in ProjectConfig.model_fields.items() if name not in {"run","tools"}},
    run=(PublicRunInput,...))


class ScientificInputsView(Contract):
    config: ScientificConfig
    evidence_files: list[AssetIdentity]
    dependency_scope: str
    sequence_index: SequenceIndexView


ProjectView = create_model("ProjectView",__base__=Contract,
    **{name:(field.annotation,deepcopy(field)) for name,field in Project.model_fields.items() if name not in {"files","scientific_project"}},
    files=(list[AssetIdentity],Field(default_factory=list)),scientific_project=(ScientificInputsView | None,None))


class RuntimeInfoView(Contract):
    name: str
    protocol_version: Literal["2"]
    authentication: str
    workspace_id: str
    storage: str
    max_workers: int
    plugin_sandbox: bool
    agent_backend: str
    capabilities: dict[str,str]
    resources: dict[str,int | bool]
    remote_desktop_authenticated_session: bool
    supported_rate_laws: list[str]


class PublicEvent(Contract):
    seq: int
    node_id: str | None
    event: str
    timestamp: str
    payload: dict[str,Any]


class EventPage(Contract):
    items: list[PublicEvent]
    cursor: int
    has_more: bool


class NodePage(Contract):
    node: NodeResultView
    offset: int
    limit: int
    total_records: int
    artifact: dict[str,str] | None
    sequence_map: SequenceMapView | None


class PlanView(Contract):
    workflow: Workflow
    confirmation: PlanBinding
    source: str
    requires_confirmation: bool
    review_id: str


class ScientificPreviewView(Contract):
    scientific_project: ScientificInputsView
    requires_confirmation: bool
    dependency_scope: str


class BindingPreviewView(Contract):
    project: ProjectView
    requires_confirmation: bool
    status: str


class IterationView(Contract):
    project: ProjectView
    parent_run_id: str
    parent_snapshot_sha256: str
    reuse_supported: bool
    explanation: str


class ImportView(Contract):
    kind: str
    patch: dict[str,Any]
    file: AssetIdentity


class ScientificRecordView(Contract):
    kind: Literal["construct", "parameter"]
    construct_record: ConstructDefinition | None = None
    parameter: ParameterRecord | None = None


class ActionView(Contract):
    seq: int
    proposal_id: str | None
    run_id: str | None
    action: str
    actor: str
    timestamp: str


class RunListView(Contract):
    id: str
    project_id: str
    status: str
    snapshot_hash: str
    created_at: str
    updated_at: str
    name: str
    project_revision: int


class InputDiffView(Contract):
    baseline_run_id: str
    baseline_snapshot_sha256: str
    project_id: str
    project_revision: int
    changed_fields: list[str]
    total_changed_fields: int
    affected_nodes: list[str]
    reuse_supported: bool
    explanation: str


class PluginMetadataView(Contract):
    id: str
    name: str
    description: str
    version: str
    capability: str
    license: str
    runtime: str
    permissions: list[str]


class PluginInspectionView(Contract):
    manifest: PluginMetadataView
    hash: str
    sandboxed: bool
    trust_required: bool
    installed: bool
    source_path: str | None
    capability_requests: list[str]


class PredictionToolView(Contract):
    id: str
    name: str
    status: Literal["not_configured", "configured_unverified", "available", "failed"]
    version: str | None
    last_real_check: str | None
    latest_file_id: str | None
    source_reference: str
    location: Literal["connected_backend"] = "connected_backend"


PUBLIC_MODELS = {model.__name__:model for model in (ScientificRecordView, TablePage, ScanPage, M5ComparisonSeries, LineagePage, ComparePage, ResourcePage, SeriesPage, StructurePage, ScientificPrecheckView,PublicError,ProjectView,ProjectSummaryView,RunSummaryView,RuntimeInfoView,EventPage,
    NodePage,PlanView,ProposalView,ScientificPreviewView,BindingPreviewView,IterationView,ImportView,ActionView,RunListView,InputDiffView,PluginInspectionView,PredictionToolView,SequencePage,Workflow)}


PUBLIC_MODELS["ScientificObservation"] = ScientificObservation
PUBLIC_MODELS['GenBankDesign'] = GenBankDesign
PUBLIC_MODELS['GenBankPage'] = GenBankPage
PUBLIC_MODELS['ImportTransactionPreview'] = ImportTransactionPreview


def public_schemas():
    def clean(value):
        if isinstance(value,dict):
            # Public responses are model_dump(), not partial request objects.
            # Defaults must already be serialized by the server; the browser
            # never fills them or coerces scientific values.
            if value.get("type") == "object" and "properties" in value:
                value["required"] = list(value["properties"])
            default = value.get("default")
            if isinstance(default,str) and (PureWindowsPath(default).is_absolute() or PurePosixPath(default).is_absolute()):
                value.pop("default")
            for item in value.values(): clean(item)
        elif isinstance(value,list):
            for item in value: clean(item)
    result = {name:model.model_json_schema() for name,model in PUBLIC_MODELS.items()}
    for schema in result.values(): clean(schema)
    return result

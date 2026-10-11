"""Persisted workflow editor state, separate from executable approval/snapshots.

This is not another DAG or scheduler. The embedded Workflow is the engine's
existing contract; positions and selection never enter its scientific binding.
"""
import json
from typing import Literal

from pydantic import Field, TypeAdapter, ValidationError, model_validator
from jsonschema import Draft202012Validator, ValidationError as SchemaValidationError

from .models import Contract, LiteralInput, NodeInput, ProjectInput, Workflow, WorkflowError, read_path
from .store import canonical, now
from .tools import ToolFailure


class NodePosition(Contract):
    x: float = Field(ge=0, le=100_000)
    y: float = Field(ge=0, le=100_000)


class WorkflowDocumentInput(Contract):
    workflow: Workflow | None = None
    layout: dict[str, NodePosition] = Field(default_factory=dict)
    selected_node_id: str | None = None
    view: Literal['graph', 'list'] = 'graph'
    expected_revision: int | None = Field(default=None, ge=1)
    expected_project_revision: int = Field(ge=1)

    @model_validator(mode='after')
    def existing_nodes_only(self):
        if self.workflow is None:
            return self
        ids = {node.id for node in self.workflow.nodes}
        if set(self.layout) - ids or self.selected_node_id is not None and self.selected_node_id not in ids:
            raise WorkflowError('workflow_layout_references_missing_node')
        return self


class WorkflowDocument(Contract):
    id: str
    project_id: str
    project_revision: int
    revision: int
    semantic_revision: int
    layout_revision: int
    workflow: Workflow
    layout: dict[str, NodePosition]
    selected_node_id: str | None
    view: Literal['graph', 'list']


def _schema_at(schema, path):
    """Only inspect declared types; an open output schema is not proof of a type."""
    definitions = schema.get('$defs', {})
    for key in [*path, None]:
        while '$ref' in schema and schema['$ref'].startswith('#/$defs/'):
            schema = definitions[schema['$ref'].split('/')[-1]]
        if key is None:
            return schema
        if isinstance(key, int):
            schema = schema.get('items', {})
        else:
            properties = schema.get('properties', {})
            if key not in properties and schema.get('additionalProperties') is False:
                raise WorkflowError('workflow_output_field_not_declared')
            schema = properties.get(key, {})
    return schema


def validate_editor_inputs(workflow, tools, project=None):
    """Validate known static values and declared typed references, never run tools.

Dynamic/unspecified output schemas still undergo native input validation at
dispatch. No scientific readiness is inferred from this editor validation.
"""
    nodes = {node.id: node for node in workflow.nodes}
    for node in workflow.nodes:
        try:
            definition = tools.get(node.tool_id)
        except ToolFailure as error:
            raise WorkflowError('unknown_tool') from error
        fields = definition.input_model.model_fields
        schema = definition.input_schema if definition.input_schema is not None else definition.input_model.model_json_schema()
        properties = schema.get('properties', {})
        supplied = set(node.inputs) | ({node.map.item_argument} if node.map else set())
        if schema.get('additionalProperties') is False and supplied - properties.keys():
            raise WorkflowError('workflow_unknown_input_argument')
        if set(schema.get('required', [])) - supplied:
            raise WorkflowError('workflow_required_input_argument_missing')
        for name, value in node.inputs.items():
            adapter = TypeAdapter(fields[name].rebuild_annotation()) if name in fields and definition.input_schema is None else None
            target = {'$defs': schema.get('$defs', {}), **properties.get(name, {})}
            validate = adapter.validate_python if adapter else Draft202012Validator(target).validate
            try:
                if isinstance(value, LiteralInput):
                    validate(value.value)
                elif isinstance(value, ProjectInput) and project is not None:
                    validate(read_path(project.model_dump(mode='python'), value.path))
                elif isinstance(value, NodeInput):
                    parent = nodes[value.node_id]
                    source = tools.get(parent.tool_id).output_schema
                    if parent.map:
                        source = {'type': 'object', '$defs': source.get('$defs', {}), 'properties': {'items': {'type': 'array', 'items': source}}, 'additionalProperties': False}
                    source = _schema_at(source, value.path)
                    target = _schema_at(target, [])
                    source_type, target_type = source.get('type'), target.get('type')
                    if source_type and target_type and source_type != target_type and not (source_type == 'integer' and target_type == 'number'):
                        raise WorkflowError('workflow_reference_type_mismatch')
            except (ValidationError, SchemaValidationError, KeyError, IndexError, TypeError) as error:
                raise WorkflowError('workflow_input_value_or_project_binding_invalid') from error
        if node.map and isinstance(node.map.items, ProjectInput) and project is not None:
            try:
                items = read_path(project.model_dump(mode='python'), node.map.items.path)
                if not isinstance(items, list):
                    raise WorkflowError('workflow_map_requires_list')
                name = node.map.item_argument
                adapter = TypeAdapter(fields[name].rebuild_annotation()) if name in fields and definition.input_schema is None else None
                validate = adapter.validate_python if adapter else Draft202012Validator({'$defs': schema.get('$defs', {}), **properties.get(name, {})}).validate
                for item in items:
                    validate(item)
            except (ValidationError, SchemaValidationError, KeyError, IndexError, TypeError) as error:
                raise WorkflowError('workflow_map_item_type_mismatch') from error


class WorkflowDocuments:
    def __init__(self, application):
        self.application, self.store = application, application.store
        with self.store.connection() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS workflow_definitions(
                project_id TEXT NOT NULL REFERENCES projects(id), id TEXT NOT NULL,
                semantic_revision INTEGER NOT NULL, workflow TEXT NOT NULL,
                PRIMARY KEY(project_id,id,semantic_revision));
                CREATE TABLE IF NOT EXISTS workflow_documents(
                project_id TEXT NOT NULL REFERENCES projects(id), id TEXT NOT NULL,
                revision INTEGER NOT NULL, semantic_revision INTEGER NOT NULL,
                project_revision INTEGER NOT NULL, layout_revision INTEGER NOT NULL,
                state TEXT NOT NULL, updated_at TEXT NOT NULL,
                PRIMARY KEY(project_id,id))''')

    @staticmethod
    def _decode(row):
        if row is None:
            return None
        return WorkflowDocument.model_validate({
            **{key: row[key] for key in ('project_id','id','revision','semantic_revision','project_revision','layout_revision')},
            'workflow': json.loads(row['workflow']), **json.loads(row['state'])})

    _select = '''SELECT d.*,f.workflow FROM workflow_documents d JOIN workflow_definitions f
        ON f.project_id=d.project_id AND f.id=d.id AND f.semantic_revision=d.semantic_revision'''

    def get(self, project_id, document_id):
        self.store.project(project_id)
        with self.store.connection() as db:
            row = db.execute(self._select + ' WHERE d.project_id=? AND d.id=?', (project_id, document_id)).fetchone()
        if row is None:
            raise KeyError(document_id)
        return self._decode(row)

    def list(self, project_id):
        self.store.project(project_id)
        with self.store.connection() as db:
            rows = db.execute(self._select + ' WHERE d.project_id=? ORDER BY d.updated_at DESC', (project_id,))
            return [self._decode(row) for row in rows]

    def save(self, project_id, document_id, request: WorkflowDocumentInput):
        project = self.store.project(project_id)
        with self.store.connection() as db:
            previous = self._decode(db.execute(self._select + ' WHERE d.project_id=? AND d.id=?', (project_id, document_id)).fetchone())
        if request.expected_revision != (previous.revision if previous else None):
            raise WorkflowError('workflow_document_revision_conflict', status_code=409)
        workflow = request.workflow or (previous.workflow if previous else None)
        if workflow is None:
            raise WorkflowError('workflow_definition_required')
        semantic_changed = previous is None or canonical(previous.workflow.model_dump(mode='json')) != canonical(workflow.model_dump(mode='json'))
        if semantic_changed or previous.project_revision != project.revision:
            self.application.validate_workflow(workflow, project)
        ids = {node.id for node in workflow.nodes}
        if set(request.layout) - ids or request.selected_node_id is not None and request.selected_node_id not in ids:
            raise WorkflowError('workflow_layout_references_missing_node')
        with self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            current = db.execute('SELECT revision FROM projects WHERE id=?', (project_id,)).fetchone()
            if current['revision'] != request.expected_project_revision:
                raise WorkflowError('workflow_project_revision_changed', status_code=409)
            row = db.execute('SELECT revision FROM workflow_documents WHERE project_id=? AND id=?', (project_id, document_id)).fetchone()
            if request.expected_revision != (row['revision'] if row else None):
                raise WorkflowError('workflow_document_revision_conflict', status_code=409)
            layout_changed = previous is None or (previous.layout, previous.selected_node_id, previous.view) != (request.layout, request.selected_node_id, request.view)
            if not semantic_changed and not layout_changed and previous.project_revision == current['revision']:
                return previous
            document = WorkflowDocument(id=document_id, project_id=project_id, project_revision=current['revision'],
                revision=previous.revision + 1 if previous else 1,
                semantic_revision=(previous.semantic_revision + int(semantic_changed)) if previous else 1,
                layout_revision=(previous.layout_revision + int(layout_changed)) if previous else 1,
                workflow=workflow, layout=request.layout, selected_node_id=request.selected_node_id, view=request.view)
            self.application.boundary.check(document.model_dump(mode='json'))
            if semantic_changed:
                db.execute('INSERT INTO workflow_definitions VALUES(?,?,?,?)', (project_id, document_id, document.semantic_revision, workflow.model_dump_json()))
            state = canonical({'layout': {key: value.model_dump() for key,value in request.layout.items()}, 'selected_node_id': request.selected_node_id, 'view': request.view})
            db.execute('''INSERT INTO workflow_documents VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(project_id,id)
                DO UPDATE SET revision=excluded.revision,semantic_revision=excluded.semantic_revision,project_revision=excluded.project_revision,
                layout_revision=excluded.layout_revision,state=excluded.state,updated_at=excluded.updated_at''',
                (project_id, document_id, document.revision, document.semantic_revision, document.project_revision, document.layout_revision, state, now()))
            return document

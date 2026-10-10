"""Create a bound scientific draft from explicit form values and registered files.

No scientific stage, new formula, parameter approval or inferred input values.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from igem_drylab.pipeline.config import ProjectConfig
from igem_drylab.resources import default_config_path
from .models import Contract, WorkflowError
from .scientific_project import ScientificProject, EvidenceFile, input_paths

EXPLICIT_M3 = ('recruitment_bias_oc_vs_dmt', 'phi_source', 'binding_model', 'recruitment_mode', 'ptr_pt_phase_handling')
EXPLICIT_M4 = ('network_mode', 'scenario_mode', 'unit_mode', 'target_product', 't_end',
    'max_side_product_fraction_13', 'min_13_reduction', 'min_15_improvement', 'min_productivity', 'activity_mode')


class ScientificSetupRequest(Contract):
    project_id: str
    expected_revision: int
    config: dict


def form_schema(prepared_through="m5"):
    # Schema is the existing Pydantic contract; defaults are intentionally not
    # used to populate new scientific inputs or expose installation paths.
    schema = ProjectConfig.model_json_schema()
    def strip(value):
        if isinstance(value, dict):
            value.pop('default', None)
            for item in value.values(): strip(item)
        elif isinstance(value, list):
            for item in value: strip(item)
    strip(schema)
    schema['properties'].pop('tools')
    schema['properties'].pop('run')
    schema['$defs'].pop('ToolConfig', None)
    schema['$defs'].pop('RunConfig', None)
    schema['required'] = ['inputs', 'execution', 'prepared_through']
    schema['$defs']['StagesConfig']['required'] = ([] if prepared_through in {'m1','m2'} else
        ['m3_concentration'] if prepared_through == 'm3' else ['m3_concentration', 'm4_reaction'])
    schema['$defs']['M3Config']['required'] = list(EXPLICIT_M3)
    schema['$defs']['M4Config']['required'] = list(EXPLICIT_M4)
    schema['$defs']['ExecutionConfig']['required'] = ['mode', 'allow_assumptions']
    # Existing approvals are records, not editable form decisions. Their
    # dedicated review workflow remains the only UI operation that approves.
    for definition in schema['$defs'].values():
        for name, field in definition.get('properties', {}).items():
            if name in {'review_status', 'approved_by', 'm1_review', 'parameter_version', 'validation_flags'}:
                field['readOnly'] = True
    return schema


def preview_setup(request, store, boundary):
    saved = store.project(request.project_id)
    if saved.revision != request.expected_revision:
        raise WorkflowError('project_revision_conflict', status_code=409)
    if saved.scientific_project is not None:
        raise WorkflowError('scientific_project_already_attached')
    raw = deepcopy(request.config)
    boundary.check(raw)
    if 'tools' in raw or 'run' in raw:
        raise WorkflowError('runtime_settings_not_scientific_input')
    # Validate the existing nested contract before traversing untrusted form
    # values. This supplies no form values and does not materialize file paths.
    ProjectConfig.model_validate({**raw, 'run': {'id': saved.id}})
    if raw.get('execution', {}).get('mode') != 'real' or raw['execution'].get('allow_assumptions') is not False:
        raise WorkflowError('setup_requires_explicit_real_execution_without_assumptions')
    # Decision controls and modelling assumptions must be explicit. Do not let
    # the pipeline's historical demo/config defaults silently fill this form.
    m3 = raw.get('stages', {}).get('m3_concentration', {})
    m4 = raw.get('stages', {}).get('m4_reaction', {})
    target = raw.get('prepared_through', 'm5')  # legacy full-project requests remain strict
    if ((target in {'m3','m4','m5'} and any(k not in m3 for k in EXPLICIT_M3))
            or (target in {'m4','m5'} and any(k not in m4 for k in EXPLICIT_M4))):
        raise WorkflowError('setup_requires_explicit_model_and_decision_controls')
    if any(p.get('review_status', 'extracted') != 'extracted' or p.get('approved_by') for p in raw.get('parameters', [])):
        raise WorkflowError('preview_cannot_approve_scientific_records')
    if any(c.get('m1_review') for c in raw.get('inputs', {}).get('constructs', [])):
        raise WorkflowError('preview_cannot_approve_scientific_records')
    if any(c.get('review_status') == 'approved' for c in raw.get('inputs', {}).get('construct_records', [])):
        raise WorkflowError('preview_cannot_approve_scientific_records')
    # All user-chosen file references must be existing asset identities.
    def paths(value, schema):
        if '$ref' in schema:
            schema = form_schema_cache['$defs'][schema['$ref'].rsplit('/', 1)[-1]]
        if schema.get('format') == 'path' and value is not None and not str(value).startswith('asset:'):
            raise WorkflowError('use_registered_file_identity', status_code=403)
        if isinstance(value, dict):
            for k, v in value.items():
                paths(v, schema.get('properties', {}).get(k, {}))
        elif isinstance(value, list):
            for v in value: paths(v, schema.get('items', {}))
        for branch in schema.get('anyOf', []):
            if branch.get('type') != 'null': paths(value, branch)
    form_schema_cache = form_schema(target)
    paths(raw, form_schema_cache)
    config = ProjectConfig.model_validate({**boundary.materialize(raw, saved.id), 'run': {'id': saved.id}})
    rules = {default_config_path('m1_feature_definitions.yaml').resolve(), default_config_path('m1_rules_v3.yaml').resolve()}
    with store.connection() as db:
        granted = {Path(row[0]).resolve() for row in db.execute('SELECT path FROM file_assets WHERE project_id=?', (saved.id,))}
    dependencies = input_paths(config, allowed_roots=tuple(granted | rules))
    if config.inputs.protein_fasta.resolve() not in granted:
        raise WorkflowError('file_project_mismatch', status_code=403)
    from Bio import SeqIO
    from igem_drylab.constructs.linker_features import normalize_amino_acid_sequence
    ids = set()
    for record in SeqIO.parse(config.inputs.protein_fasta, 'fasta'):
        if record.id in ids: raise WorkflowError('duplicate_sequence_id')
        normalize_amino_acid_sequence(str(record.seq))
        ids.add(record.id)
    if not ids: raise WorkflowError('empty_protein_fasta')
    # Reuse the existing relative-file/reference validation, without writing a
    # user-authored YAML or creating a second import/config implementation.
    from igem_drylab.pipeline.config import _resolve_relative_paths
    config = _resolve_relative_paths(config, config.inputs.protein_fasta.parent)
    science = ScientificProject(config=config, evidence_files=[EvidenceFile(path=p, sha256=sha256(p.read_bytes()).hexdigest()) for p in sorted(dependencies)])
    science.verify()
    result = boundary.scientific(science.model_dump(mode='json'), project_id=saved.id)
    return {'scientific_project': result, 'requires_confirmation': True, 'dependency_scope': science.dependency_scope}

"""Shared local application operations for HTTP, desktop and CLI.

One durable store, approval service and scientific engine; no HTTP loopback
client, second scheduler or client-supplied scientific approval.
"""
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from igem_drylab.workflow.models import Project, Workflow, WorkflowError
from igem_drylab.workflow.store import WorkflowStore
from igem_drylab.workflow.engine import WorkflowEngine
from igem_drylab.workflow.builtins import builtin_tools, recommend
from igem_drylab.workflow.planning import PlanningService


class ApplicationService:
    def __init__(self,data_dir: Path,*,workflow_tools=None,planning_backend=None,runtime_tools=None):
        self.data_dir = data_dir.resolve()
        self.store = WorkflowStore(self.data_dir/'platform.sqlite3')
        self.tools = workflow_tools if workflow_tools is not None else builtin_tools()
        self.engine = WorkflowEngine(self.store,self.tools,self.data_dir/'artifacts')
        from igem_drylab.workflow.scheduler import RunDispatcher
        self.dispatcher = RunDispatcher(self.engine)
        self.boundary = self.engine.disclosure
        self.backend_profile = None
        if runtime_tools is not None:
            from igem_drylab.workflow.runtime_profiles import RuntimeProfiles
            self.backend_profile = RuntimeProfiles(self.store).install('backend-configured-tools',runtime_tools)
            self.boundary.register_runtime(runtime_tools)
        self.planning = PlanningService(self.store,self.boundary,planning_backend,self.engine)
        if planning_backend is not None:
            client = getattr(planning_backend,'client',None)
            for field in ('api_key','api_base'): self.boundary.register_private(getattr(client,field,None))
        self.boundary.register_private(str(self.data_dir))
        from igem_drylab.workflow.plugins import PluginManager
        self.plugins = PluginManager(self.data_dir/'plugins',self.store,self.tools,disclosure=self.boundary)
        self.plugins.load_installed()
        from .import_service import ImportService
        self.imports=ImportService(self)
        from igem_drylab.workflow.documents import WorkflowDocuments
        self.workflow_documents = WorkflowDocuments(self)

    def create_project(self,name):
        return self.save_project(Project(id=str(uuid4()),name=name))

    def save_project(self,project: Project,expected_revision=None):
        boundary = self.boundary
        boundary.check(project.model_dump(mode='json'))
        project = boundary.private_project(project)
        if self.backend_profile is not None:
            try: self.store.project(project.id)
            except KeyError: project.runtime_profile_ref=self.backend_profile['id']
        if project.scientific_project is not None:
            from igem_drylab.workflow.scientific_project import ScientificProject
            ScientificProject.model_validate(project.scientific_project).verify()
        if project.pathway is not None:
            from igem_drylab.workflow.pathway import Pathway
            Pathway.model_validate(project.pathway)
        from igem_drylab.constructs.linker_features import normalize_amino_acid_sequence
        for sequence in project.sequences: sequence.sequence=normalize_amino_acid_sequence(sequence.sequence)
        for file in project.files:
            path=Path(file['path']).resolve()
            if (not path.is_relative_to(self.data_dir/'imports') or not path.is_file()
                or sha256(path.read_bytes()).hexdigest()!=file['sha256']):
                raise ValueError('invalid_import_artifact')
        return boundary.project(self.store.save_project(project,expected_revision))

    def check_inputs(self,project_id,through=None):
        from igem_drylab.workflow.precheck import precheck
        result=precheck(self.store.project(project_id),through).model_dump(mode='json')
        self.boundary.check(result)
        return result

    def preview_import(self,filename,content,input_kind='auto'):
        from .imports import preview_import
        return preview_import(self.data_dir,self.boundary,filename,content,input_kind)

    def import_files(self,project_id,paths,input_kind='auto'):
        preview=self.preview_files(project_id,paths,input_kind)
        return self.imports.commit(project_id,preview.id)

    def preview_files(self,project_id,paths,input_kind='auto',transaction_id=None):
        paths=[Path(path).resolve() for path in paths]
        root=Path(__import__('os').path.commonpath([str(path.parent) for path in paths])) if paths else self.data_dir
        files=[(path.relative_to(root).as_posix(),path.read_bytes()) for path in paths]
        options={name:{'role':input_kind} for name,_ in files} if input_kind!='auto' else None
        if transaction_id is not None:
            return self.imports.append(project_id,transaction_id,files)
        return self.imports.preview(project_id,files,options)

    def validate_workflow(self,workflow: Workflow,project=None):
        self.boundary.check(workflow.model_dump(mode='json'))
        from igem_drylab.workflow.scientific_project import validate_stage_bindings
        validate_stage_bindings(workflow)
        from igem_drylab.workflow.documents import validate_editor_inputs
        validate_editor_inputs(workflow, self.tools, project)
        return workflow

    def propose(self,request):
        result=self.planning.propose(request)
        if result.workflow: self.validate_workflow(result.workflow)
        return result

    def plan(self,project_id,method):
        project=self.store.project(project_id)
        if method=='ps-v3-demo':
            from igem_drylab.workflow.models import WorkflowNode,ProjectInput
            packages=[(index,file) for index,file in enumerate(project.files) if any(d.get('kind')=='synthetic_ps_v3' and d.get('file_id')==file['id'] for d in project.datasets)]
            if len(packages)!=1: raise WorkflowError('select_one_synthetic_ps_package')
            workflow=Workflow(id=str(uuid4()),name='PS-v3 synthetic demonstration',
                description='Four closed reference scenarios; ideal unverified sites, no fermentation or ER advantage. E3 remains blocked.',
                nodes=[WorkflowNode(id='synthetic-demo',label='Synthetic M3/M4 reference scenarios',tool_id='synthetic.ps_v3',
                    inputs={'package_file':ProjectInput(path=['files',packages[0][0],'path'])})])
        elif method=='sequence-properties': workflow=recommend(project,'fusion_screen')
        elif method=='galatea-m1-m2':
            workflow=recommend(project,'scientific_pipeline')
            selected={'m1','m2'}
            workflow.nodes=[node for node in workflow.nodes if node.id in selected]
            workflow.execution_policy.allowed_tools=sorted({node.tool_id for node in workflow.nodes})
            workflow=Workflow.model_validate(workflow.model_dump(mode='json'))
        else: raise WorkflowError('unknown_analysis_method')
        self.validate_workflow(workflow)
        return self.planning.custom(project_id,workflow,'Review '+method+'; not executed.')

    def start_run(self,*,project_id,workflow,confirmation,proposal_id=None,manual_review_id=None,
                  execution_type='reviewed_proposal',request_id=None,background=True):
        if project_id != confirmation.project_id: raise WorkflowError('plan_project_mismatch',status_code=409)
        request_id=request_id or sha256(confirmation.model_dump_json().encode()).hexdigest()
        review_id=proposal_id if execution_type=='reviewed_proposal' else manual_review_id
        if not review_id or (proposal_id and manual_review_id): raise WorkflowError('accepted_proposal_binding_required',status_code=409)
        manual=execution_type=='manual_review'
        self.planning.authorize_run(review_id,confirmation,workflow,manual=manual)
        run_id=self.engine.create_confirmed(confirmation,workflow,request_id,
            authorize=lambda db,snapshot:self.planning.authorize_run(review_id,confirmation,workflow,db=db,snapshot=snapshot,manual=manual))
        result=self.store.run(run_id)
        if result['status']=='queued':
            if background: self.dispatcher.submit(run_id)
            else: self.engine.run(run_id)
        self.planning.started(review_id,run_id)
        return self.boundary.run(self.store.run(run_id))

    def run_approved(self,proposal_id):
        proposal=self.planning.get(proposal_id)
        if proposal.status!='accepted' or proposal.workflow is None or proposal.confirmation is None:
            raise WorkflowError('accepted_proposal_binding_required',status_code=409)
        return self.start_run(project_id=proposal.project_id,workflow=proposal.workflow,
            confirmation=proposal.confirmation,proposal_id=proposal_id,background=False)

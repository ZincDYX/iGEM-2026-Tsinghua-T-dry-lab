"""One persisted import transaction for files, directories and ZIPs.

The preview owns immutable bytes and parser choices. Commit checks the saved
project revision and publishes all selected objects atomically. Uploaded code
is never executed; relative configuration references stay in this transaction.
"""
from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path,PurePosixPath
from typing import Any,Literal
from uuid import uuid4
from zipfile import ZipFile,ZipInfo,BadZipFile

from pydantic import Field
from igem_drylab.workflow.models import Contract,Project,WorkflowError
from igem_drylab.workflow.store import canonical,now,file_sha256
from igem_drylab.workflow.binary_import import validate_archive_members,MAX_BYTES,MAX_FILES
from .parsers import ParserRegistry,ParsedInput,ImportIssue


class ImportedItem(ParsedInput):
    filename: str
    file: dict[str,str]
    duplicate_file_id: str | None = None


class ImportTransactionPreview(Contract):
    id: str
    project_id: str
    expected_revision: int
    state: Literal['preview','committed','discarded']
    items: list[ImportedItem]
    issues: list[ImportIssue] = Field(default_factory=list)
    proposed_links: list[dict[str,Any]] = Field(default_factory=list)
    requires_confirmation: bool = True


class ImportService:
    def __init__(self,application):
        self.application=application
        self.store=application.store
        self.boundary=application.boundary
        self.registry=ParserRegistry()
        with self.store.connection() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS import_transactions(
                id TEXT PRIMARY KEY,project_id TEXT NOT NULL,revision INTEGER NOT NULL,
                state TEXT NOT NULL,payload TEXT NOT NULL,root TEXT NOT NULL,
                result_revision INTEGER,created_at TEXT NOT NULL)''')

    def _expand(self,files):
        files=list(files)
        if not files or len(files)>MAX_FILES or sum(len(raw) for _,raw in files)>MAX_BYTES:
            raise WorkflowError('scientific_upload_budget_exceeded')
        expanded=[]
        for name,raw in files:
            if Path(name).suffix.lower()=='.zip':
                try:
                    with ZipFile(BytesIO(raw)) as archive:
                        validate_archive_members(archive.infolist())
                        # A corrected PS package is one independently scoped
                        # dataset, not a mixture of formal/synthetic imports.
                        from igem_drylab.workflow.synthetic_ps import SET_ID
                        canonical_members=[i for i in archive.infolist() if i.filename.endswith('canonical_parameters.json')]
                        def is_ps(member):
                            try: value=json.loads(archive.read(member))
                            except (ValueError,UnicodeError): return False
                            return isinstance(value,dict) and value.get('parameter_set_id')==SET_ID
                        if any(is_ps(i) for i in canonical_members):
                            expanded.append((name,raw));continue
                        expanded.extend((i.filename,archive.read(i)) for i in archive.infolist() if not i.is_dir())
                except BadZipFile as error: raise WorkflowError('invalid_scientific_archive') from error
            else: expanded.append((name,raw))
        if sum(len(raw) for _,raw in expanded)>MAX_BYTES: raise WorkflowError('scientific_upload_budget_exceeded')
        validate_archive_members([ZipInfo(name) for name,_ in expanded])
        return expanded

    def _write_entries(self,project_id,root,files,options=None):
        entries=[]
        from igem_drylab.workflow.disclosure import check_import_content
        for name,raw in files:
            check_import_content(name,raw)
            self.boundary.check_bytes(raw)
            path=root.joinpath(*PurePosixPath(name).parts)
            path.parent.mkdir(parents=True,exist_ok=True)
            try:
                with path.open('xb') as stream: stream.write(raw)
            except FileExistsError as error:
                raise WorkflowError('import_filename_already_present') from error
            asset=self.boundary.asset(path,fresh=True,project_id=project_id,logical_name=name)
            entries.append({'filename':name,'file':asset,'options':(options or {}).get(name,{})})
        return entries

    def preview(self,project_id,files,options=None):
        project=self.store.project(project_id)
        expanded=self._expand(files)
        from .input_collection import collection_options
        inferred=collection_options(expanded)
        for name, explicit in (options or {}).items():
            inferred[name]={**inferred.get(name,{}),**explicit}
        transaction_id=str(uuid4())
        root=self.application.data_dir/'imports'/transaction_id
        root.mkdir(parents=True)
        entries=self._write_entries(project_id,root,expanded,inferred)
        payload={'entries':entries}
        view=self._parse(transaction_id,project,root,payload)
        payload['view']=view.model_dump(mode='json')
        self.boundary.check(payload['view'])
        with self.store.connection() as db:
            db.execute('INSERT INTO import_transactions VALUES(?,?,?,?,?,?,NULL,?)',
                (transaction_id,project_id,project.revision,'preview',canonical(payload),str(root),now()))
        return view

    def _parse(self,transaction_id,project,root,payload):
        items=[]
        for entry in payload['entries']:
            path=root.joinpath(*PurePosixPath(entry['filename']).parts)
            if file_sha256(path)!=entry['file']['sha256']: raise WorkflowError('file_identity_changed')
            if entry.get('parsed_options')==entry['options'] and 'parsed' in entry:
                parsed=ParsedInput.model_validate(entry['parsed'])
            elif path.suffix.lower()=='.zip':
                from igem_drylab.workflow.synthetic_ps import read_ps_archive,SET_ID
                values,_=read_ps_archive(path.read_bytes())
                parsed=ParsedInput(detected_format='ZIP',semantic_type='SyntheticDemonstration',records=[values],
                    supported_scope='PS-v3 synthetic closed reference only; not formal prediction, M2 evidence or ER advantage.',
                    input_roles=['synthetic_ps_v3'],patch={'datasets':[{'id':entry['file']['id'],'file_id':entry['file']['id'],
                        'name':entry['filename'],'kind':'synthetic_ps_v3','parameter_set_id':SET_ID,'source_type':'synthetic',
                        'formal_prediction_allowed':False,'canonical_parameters':values}]})
            else: parsed=self.registry.parse(path,entry['options'])
            entry['parsed']=parsed.model_dump(mode='json')
            entry['parsed_options']=deepcopy(entry['options'])
            duplicate=next((f['id'] for f in project.files if f['sha256']==entry['file']['sha256']),None)
            item=ImportedItem(**parsed.model_dump(mode='json'),filename=entry['filename'],file=entry['file'],duplicate_file_id=duplicate)
            if parsed.semantic_type=='DesignRecord':
                from igem_drylab.workflow.genbank_design import GenBankDesign
                record=parsed.records[0]
                item.patch['datasets']=[GenBankDesign(id=entry['file']['id'],file_id=entry['file']['id'],name=entry['filename'],
                    records=record['records'],cds_proteins=record['cds_proteins']).model_dump(mode='json')]
            elif not item.patch.get('datasets'):
                # One compact descriptor per source, not a copy of the full
                # table/coordinate array in every project and run snapshot.
                descriptor_records=parsed.records
                if parsed.semantic_type=='SequenceCollection':
                    descriptor_records=[{key:value for key,value in record.items() if key!='sequence'} for record in parsed.records]
                item.patch['datasets']=[{'id':entry['file']['id'],'file_id':entry['file']['id'],'name':entry['filename'],
                    'kind':parsed.semantic_type,'supported_scope':parsed.supported_scope,'input_roles':parsed.input_roles,
                    'parser_options':entry['options'],'records':descriptor_records if parsed.semantic_type not in {'UnclassifiedConfiguration','ProjectConfig'} else [],
                    'has_unresolved_inputs':bool(parsed.issues)}]
            items.append(item)
        links=[]
        protein_records=[(item,record) for item in items if item.semantic_type=='SequenceCollection'
            for record in item.records if record['molecule_type']=='protein']
        for structure in (i for i in items if i.semantic_type=='StructureRecord'):
            for chain in structure.records[0]['chains']:
                for sequence,record in protein_records:
                    # Exact observed sequence is a proposal only. Truncations,
                    # gaps and pocket mappings are never assigned by filename.
                    if chain['coordinate_sequence']==record['sequence']:
                        links.append({'kind':'exact_observed_sequence_match','structure_file_id':structure.file['id'],
                            'sequence_file_id':sequence.file['id'],'sequence_id':record['id'],'model':chain['model'],
                            'auth_chain':chain['auth_chain'],'label_chain':chain['label_chain'],'status':'proposed_not_scientific_approval'})
        view=ImportTransactionPreview(id=transaction_id,project_id=project.id,expected_revision=project.revision,
            state='preview',items=items,proposed_links=links)
        configurations=[item for item in items if item.semantic_type=='ProjectConfig']
        if len(configurations)>1:
            for item in configurations:
                item.input_roles=['project_config','evidence_attachment']
                item.issues.append(ImportIssue(code='multiple_project_configurations',severity='confirmation',field='role',
                    message='Choose one project configuration. Keep the others as evidence attachments; configurations are not merged or applied in file order.'))
        names={entry['filename'] for entry in payload['entries']}
        for item in items:
            if item.semantic_type!='ProjectConfig': continue
            config=item.records[0]
            # Follow only fields typed as paths in the original Pydantic
            # scientific config. All names resolve inside this transaction.
            from igem_drylab.pipeline.config import ProjectConfig
            schema=ProjectConfig.model_json_schema()
            bound=deepcopy(config)
            # Runtime/output bookkeeping is not an imported scientific input.
            bound.pop('run',None)
            bound.pop('tools',None)
            def check(value,node,field):
                if '$ref' in node: node=schema['$defs'][node['$ref'].rsplit('/',1)[-1]]
                if node.get('format')=='path' and value is not None:
                    name=str(value)
                    parent=PurePosixPath(item.filename).parent
                    target=(root/parent/name).resolve()
                    if not target.is_relative_to(root) or Path(name).is_absolute() or '\\' in name or ':' in name:
                        raise WorkflowError('scientific_file_outside_authorized_workspace')
                    relative=target.relative_to(root).as_posix()
                    if relative not in names:
                        item.issues.append(ImportIssue(code='missing_transaction_dependency',message='Add the referenced file to this import: '+relative,
                            severity='confirmation',field=field,expected_filename=relative))
                    else:
                        target_item=next(i for i in items if i.filename==relative)
                        item.proposed_links.append({'kind':'configuration_file_reference','field':field,
                            'file_id':target_item.file['id'],'status':'proposed'})
                        if field=='config.inputs.protein_fasta' and (target_item.semantic_type!='SequenceCollection'
                            or any(record['molecule_type']!='protein' for record in target_item.records)):
                            item.issues.append(ImportIssue(code='protein_fasta_confirmation_required',
                                message='Confirm that the referenced FASTA contains protein sequences; DNA/RNA is not translated or screened as protein.',
                                severity='confirmation',field=field))
                    return next((i.file['path'] for i in items if i.filename==relative),value)
                if isinstance(value,dict):
                    value={key:check(child,node.get('properties',{}).get(key,node.get('additionalProperties',{}) if isinstance(node.get('additionalProperties'),dict) else {}),field+'.'+key) for key,child in value.items()}
                elif isinstance(value,list):
                    value=[check(child,node.get('items',{}),field+'.'+str(index)) for index,child in enumerate(value)]
                for branch in node.get('anyOf',[]):
                    if branch.get('type')!='null': value=check(value,branch,field)
                return value
            bound=check(bound,schema,'config')
            if not item.issues and not any(i.issues for i in items if i.semantic_type=='SequenceCollection'):
                from igem_drylab.workflow.scientific_setup import preview_setup,ScientificSetupRequest
                # Reuse the original explicit-value and review-status gates.
                # Relative paths become registered IDs; no user SHA entry.
                try:
                    preview=preview_setup(ScientificSetupRequest(project_id=project.id,
                        expected_revision=project.revision,config=bound),self.store,self.boundary)
                    item.patch['scientific_project']=preview['scientific_project']
                except (ValueError,WorkflowError) as error:
                    from pydantic import ValidationError
                    if isinstance(error,ValidationError):
                        for detail in error.errors(include_input=False,include_url=False)[:10]:
                            field='config.'+'.'.join(str(part) for part in detail['loc'])
                            item.issues.append(ImportIssue(code='configuration_field_required' if detail['type']=='missing' else 'configuration_field_invalid',
                                message='Required input is missing.' if detail['type']=='missing' else 'This value does not meet the scientific input contract.',
                                severity='confirmation',field=field))
                        continue
                    code=error.code if isinstance(error,WorkflowError) else 'scientific_configuration_validation_required'
                    item.issues.append(ImportIssue(code=code,message='Scientific configuration needs correction or source review. Use the original contract fields; no biological defaults or approvals were supplied.',severity='confirmation',field='config'))
        view.proposed_links.extend(link for item in items for link in item.proposed_links)
        return view

    def _load(self,project_id,transaction_id):
        with self.store.connection() as db:
            row=db.execute('SELECT * FROM import_transactions WHERE id=? AND project_id=?',(transaction_id,project_id)).fetchone()
        if row is None: raise WorkflowError('import_transaction_not_found',status_code=404)
        return dict(row),json.loads(row['payload'])

    def inspect(self,project_id,transaction_id):
        row,payload=self._load(project_id,transaction_id)
        return ImportTransactionPreview.model_validate({**payload['view'],'state':row['state']})

    def pending(self,project_id):
        self.store.project(project_id)
        with self.store.connection() as db:
            rows=db.execute("SELECT id FROM import_transactions WHERE project_id=? AND state='preview' ORDER BY created_at DESC",(project_id,)).fetchall()
        return [row['id'] for row in rows]

    def append(self,project_id,transaction_id,files):
        row,payload=self._load(project_id,transaction_id)
        if row['state']!='preview': raise WorkflowError('import_transaction_already_decided',status_code=409)
        project=self.store.project(project_id)
        if project.revision!=row['revision']: raise WorkflowError('project_revision_conflict',status_code=409)
        expanded=self._expand(files)
        names={entry['filename'] for entry in payload['entries']}
        if any(name in names for name,_ in expanded): raise WorkflowError('import_filename_already_present')
        root=Path(row['root'])
        existing_size=sum(root.joinpath(*PurePosixPath(name).parts).stat().st_size for name in names)
        if len(names)+len(expanded)>MAX_FILES or existing_size+sum(len(raw) for _,raw in expanded)>MAX_BYTES:
            raise WorkflowError('scientific_upload_budget_exceeded')
        payload['entries'].extend(self._write_entries(project_id,root,expanded))
        return self._save_preview(row,payload,project)

    def revise(self,project_id,transaction_id,options,expected_revision=None):
        row,payload=self._load(project_id,transaction_id)
        if row['state']!='preview': raise WorkflowError('import_transaction_already_decided',status_code=409)
        if any(name not in {e['filename'] for e in payload['entries']} for name in options): raise WorkflowError('unknown_import_file')
        for entry in payload['entries']:
            if entry['filename'] in options: entry['options']=options[entry['filename']]
        project=self.store.project(project_id)
        if project.revision!=(expected_revision if expected_revision is not None else row['revision']):
            raise WorkflowError('project_revision_conflict',status_code=409)
        return self._save_preview(row,payload,project)

    def _save_preview(self,row,payload,project):
        view=self._parse(row['id'],project,Path(row['root']),payload)
        payload['view']=view.model_dump(mode='json')
        self.boundary.check(payload['view'])
        with self.store.connection() as db:
            cursor=db.execute("UPDATE import_transactions SET payload=?,revision=? WHERE id=? AND state='preview' AND revision=? AND payload=?",
                (canonical(payload),project.revision,row['id'],row['revision'],row['payload']))
            if cursor.rowcount!=1: raise WorkflowError('import_transaction_already_decided',status_code=409)
        return view

    def commit(self,project_id,transaction_id,choices=None):
        row,payload=self._load(project_id,transaction_id)
        if row['state']=='committed': return self.boundary.project(self.store.project(project_id))
        if row['state']!='preview': raise WorkflowError('import_transaction_already_decided',status_code=409)
        project=self.store.project(project_id)
        if project.revision!=row['revision']: raise WorkflowError('project_revision_conflict',status_code=409)
        view=ImportTransactionPreview.model_validate(payload['view'])
        choices=choices or {}
        for item in view.items:
            path=Path(row['root']).joinpath(*PurePosixPath(item.filename).parts)
            if file_sha256(path)!=item.file['sha256']: raise WorkflowError('file_identity_changed')
            if any(i.severity in {'error','confirmation'} for i in item.issues):
                raise WorkflowError('import_confirmation_required',logical_files=(item.filename,))
            if item.duplicate_file_id:
                choice=choices.get(item.filename)
                if choice not in {'reuse','replace','new_version'}: raise WorkflowError('duplicate_import_choice_required')
                if choice=='reuse': continue
                if choice=='replace':
                    project.files=[f for f in project.files if f['id']!=item.duplicate_file_id]
                    project.datasets=[d for d in project.datasets if d.get('file_id')!=item.duplicate_file_id]
            private_file={**item.file,'path':str(path)}
            project.files.append(private_file)
            for sequence in item.patch.get('sequences',[]):
                old=next((r for r in project.sequences if r.id==sequence['id']),None)
                if old and (old.sequence!=sequence['sequence'] or old.localization_context!=sequence.get('localization_context','cytosolic')):
                    raise WorkflowError('sequence_conflict_requires_explicit_revision')
                if old is None:
                    from igem_drylab.workflow.models import SequenceRecord
                    project.sequences.append(SequenceRecord.model_validate(sequence))
            project.datasets.extend(deepcopy(item.patch.get('datasets',[])))
            if 'pathway' in item.patch: project.pathway=item.patch['pathway']
            if 'scientific_project' in item.patch:
                public=self.boundary.project(project)
                public['scientific_project']=item.patch['scientific_project']
                project=self.boundary.private_project(Project.model_validate(public))
                from igem_drylab.workflow.scientific_project import ScientificProject
                ScientificProject.model_validate(project.scientific_project).verify()
        # A compact source binding is preserved; proposed links are not
        # automatic M2 acceptance, parameter approval or workflow authorization.
        if view.proposed_links:
            project.datasets.append({'id':transaction_id,'kind':'proposed_input_links','name':'Imported binding proposals','records':view.proposed_links})
        self.boundary.check(self.boundary.project(project))
        with self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            state=db.execute('SELECT state FROM import_transactions WHERE id=?',(transaction_id,)).fetchone()[0]
            if state!='preview': raise WorkflowError('import_transaction_already_decided',status_code=409)
            updated=self.store.save_project(project,row['revision'],db=db)
            db.execute("UPDATE import_transactions SET state='committed',result_revision=? WHERE id=?",(updated.revision,transaction_id))
        return self.boundary.project(updated)

    def discard(self,project_id,transaction_id):
        row,_=self._load(project_id,transaction_id)
        if row['state']=='committed': raise WorkflowError('import_transaction_already_decided',status_code=409)
        with self.store.connection() as db:
            db.execute("UPDATE import_transactions SET state='discarded' WHERE id=?",(transaction_id,))
        return self.inspect(project_id,transaction_id)

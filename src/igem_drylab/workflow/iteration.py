"""Byte-preserving dependency closure and atomic project/grant publication."""
from hashlib import sha256
import json
from pathlib import Path
import os
import shutil
from tempfile import TemporaryDirectory
from uuid import uuid4

from igem_drylab.resources import default_config_path
from .models import Project, WorkflowError
from .scientific_project import ScientificProject


def rebind_paths(value, replacements):
    if isinstance(value, str) and Path(value).is_absolute():
        return str(replacements.get(Path(value).resolve(), value))
    if isinstance(value, dict):
        return {key: rebind_paths(item, replacements) for key, item in value.items()}
    if isinstance(value, list):
        return [rebind_paths(item, replacements) for item in value]
    return value


def create_iteration(store, boundary, engine, run_id, data_dir):
    frozen = store.run(run_id)
    project = Project.model_validate(frozen["snapshot"]["project"])
    sources = {Path(item["path"]).resolve(): item["sha256"] for item in project.files}
    if project.scientific_project:
        science = ScientificProject.model_validate(project.scientific_project)
        sources.update({item.path.resolve(): item.sha256 for item in science.evidence_files})
    with store.connection() as db:
        bundles = [(row["id"], Path(row["root"]).resolve()) for row in db.execute("SELECT * FROM scientific_bundles")]
    trusted = {default_config_path(name).resolve() for name in ("m1_feature_definitions.yaml", "m1_rules_v3.yaml")}
    unbundled = [source for source in sources if source not in trusted and not any(source.is_relative_to(root) for _, root in bundles)]
    common = Path(os.path.commonpath([str(source.parent) for source in unbundled])) if unbundled else None
    logical = {}
    for source in sources:
        owners = [(identifier, root) for identifier, root in bundles if source.is_relative_to(root)]
        if owners:
            identifier, root = max(owners, key=lambda item: len(item[1].parts))
            logical[source] = Path("bundles") / identifier / source.relative_to(root)
        elif source in trusted:
            logical[source] = Path("trusted-rules") / source.name
        else:
            logical[source] = Path("inputs") / source.relative_to(common)
    identity = str(uuid4())
    imports = (data_dir / "imports").resolve()
    imports.mkdir(parents=True, exist_ok=True)
    published = imports / identity
    committed = False
    try:
        engine.verify_snapshot(frozen, execution_identity=False)
        with TemporaryDirectory(prefix=".iteration-", dir=imports) as directory:
            staging = Path(directory)
            for source, relative in logical.items():
                raw = source.read_bytes()
                if sha256(raw).hexdigest() != sources[source]:
                    raise WorkflowError("iteration_dependency_graph_invalid", logical_files=(relative.as_posix(),))
                target = staging / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            original = project.model_dump(mode="json")
            original.update(id=identity, name=project.name + " · iteration", revision=1,
                            parent_run_id=run_id, parent_snapshot_sha256=frozen["snapshot_hash"])
            draft = Project.model_validate(rebind_paths(original, {source: staging / relative for source, relative in logical.items()}))
            if draft.scientific_project:
                ScientificProject.model_validate(draft.scientific_project).verify()
            # The copied closure is private until the project and all grants commit.
            staging.rename(published)
            draft = Project.model_validate(rebind_paths(draft.model_dump(mode="json"),
                                                       {staging / relative: published / relative for relative in logical.values()}))
            if draft.scientific_project:
                ScientificProject.model_validate(draft.scientific_project).verify()
            with store.connection() as db:
                db.execute("BEGIN IMMEDIATE")
                # References follow this exact copied source closure, not the
                # current project's newer datasets or another project's grant.
                grants={}
                for row in db.execute('SELECT id,path FROM file_assets WHERE project_id=?',(project.id,)).fetchall():
                    source=Path(row['path']).resolve()
                    if source in logical:
                        grants[row['id']]=boundary.asset(published/logical[source],project_id=draft.id,db=db)['id']
                for dataset in draft.datasets:
                    old=dataset.get('file_id')
                    if old in grants:
                        dataset['file_id']=grants[old]
                        if dataset.get('id')==old: dataset['id']=grants[old]
                from .models import Workflow,LiteralInput,SequenceRef
                workflow=Workflow.model_validate(rebind_paths(frozen['snapshot']['workflow'],{source:published/relative for source,relative in logical.items()}))
                for node in workflow.nodes:
                    for name,value in node.inputs.items():
                        if isinstance(value,SequenceRef):
                            value.construct_version=draft.revision
                            if value.file_id in grants: value.file_id=grants[value.file_id]
                        elif node.tool_id=='synthetic.ps_v3' and name=='package_file_id' and isinstance(value,LiteralInput):
                            if value.value in grants: value.value=grants[value.value]
                    if node.tool_id=='workflow.custom_formula' and all(isinstance(value,LiteralInput) for value in node.inputs.values()):
                        from .methods import MethodDraftView
                        from .custom_formula import FormulaExecution,expression_latex
                        execution=FormulaExecution.model_validate({name:value.value for name,value in node.inputs.items()})
                        row=db.execute('SELECT payload FROM method_drafts WHERE id=? AND project_id=?',(execution.method_id,project.id)).fetchone()
                        if row is None: raise WorkflowError('iteration_owned_method_missing')
                        if row:
                            original_method=MethodDraftView.model_validate_json(row['payload'])
                            method=original_method.model_copy(update={'id':str(uuid4()),'project_id':draft.id,'project_revision':draft.revision,'previous_id':None,
                                'version':execution.method_version,'title':execution.title,'execution_spec':execution.spec,'latex':expression_latex(execution.spec.expression)})
                            db.execute('INSERT INTO method_drafts VALUES(?,?,?)',(method.id,draft.id,method.model_dump_json()))
                            node.inputs['method_id']=LiteralInput(value=method.id)
                updated = store.save_project(draft, db=db)
                public = boundary.project(updated, db=db)
                public_workflow=boundary.tree(workflow.model_dump(mode='json'),project_id=draft.id,db=db)
                boundary.check(public_workflow)
                db.execute("INSERT INTO scientific_bundles VALUES(?,?)", (identity, str(published)))
            committed = True
            return {"project": public, "workflow":public_workflow,"parent_run_id": run_id, "parent_snapshot_sha256": frozen["snapshot_hash"],
                    "reuse_supported": False,
                    "explanation": "Independent byte-preserving iteration from the frozen snapshot. Review a new plan; cross-run computation reuse is not supported."}
    except (OSError, ValueError) as error:
        if isinstance(error, WorkflowError):
            raise
        raise WorkflowError("iteration_dependency_graph_invalid", logical_files=tuple(sorted(path.as_posix() for path in logical.values())),
                            private_detail=str(error)) from error
    finally:
        if not committed and published.is_dir() and published.parent == imports:
            # Only this invocation's newly created copy; never original evidence.
            shutil.rmtree(published)

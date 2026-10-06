"""Describe saved input changes using actual DAG bindings, never guessed stages."""
from __future__ import annotations

from .models import Project, ProjectInput, Workflow, WorkflowError


def input_diff(store,boundary,project:Project,run_id:str):
    run=store.run(run_id)
    if run["project_id"] != project.id and (project.parent_run_id != run_id or project.parent_snapshot_sha256 != run["snapshot_hash"]):
        raise WorkflowError("diff_project_mismatch",status_code=403)
    before=boundary.project(Project.model_validate(run["snapshot"]["project"]))
    after=boundary.project(project)
    # Derived display index/grant identity is not a scientific input binding.
    for public in (before, after):
        if public.get("scientific_project"):
            public["scientific_project"].pop("sequence_index", None)
    with store.connection() as db:
        hashes={"asset:"+row["id"]:row["hash"] for row in db.execute("SELECT id,hash FROM file_assets")}
    def semantic(value):
        if isinstance(value,str):return "sha256:"+hashes[value] if value in hashes else value
        if isinstance(value,dict):
            if {"file_id","sha256","path"} <= value.keys():return {"content_sha256":value["sha256"]}
            return {key:semantic(item) for key,item in value.items()}
        if isinstance(value,list):return [semantic(item) for item in value]
        return value
    before,after=semantic(before),semantic(after)
    changed=[]
    def compare(a,b,path):
        if isinstance(a,dict) and isinstance(b,dict):
            for key in sorted(a.keys()|b.keys()):compare(a.get(key),b.get(key),path+[key])
        elif isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
            for i,(old,new) in enumerate(zip(a,b)):compare(old,new,path+[str(i)])
        elif a!=b:changed.append(path)
    compare(before,after,[])
    workflow=Workflow.model_validate(run["snapshot"]["workflow"])
    affected=set()
    for node in workflow.nodes:
        bindings=[*node.inputs.values(),*([node.map.items] if node.map else [])]
        for binding in bindings:
            if isinstance(binding,ProjectInput):
                prefix=[str(key) for key in binding.path]
                if any(path[:len(prefix)]==prefix or prefix[:len(path)]==path for path in changed):affected.add(node.id)
    while True:
        expanded=affected|{node.id for node in workflow.nodes if node.dependencies()&affected}
        if expanded==affected:break
        affected=expanded
    return {"baseline_run_id":run_id,"baseline_snapshot_sha256":run["snapshot_hash"],"project_id":project.id,"project_revision":project.revision,
        "changed_fields":[".".join(path) for path in changed[:200]],"total_changed_fields":len(changed),
        "affected_nodes":[node.id for node in workflow.nodes if node.id in affected],"reuse_supported":False,
        "explanation":"按真实 ProjectInput 及下游依赖保守判定；整份科学配置绑定影响该绑定的所有阶段。不推断未经核验的细粒度依赖，不自动复用。文件换项目逻辑 ID 但字节相同不当成数值变更。"}

"""Adapt the existing semantic/compiler planner into the single durable engine.

This module proposes; it never executes, approves parameters or reads credentials.
"""
from __future__ import annotations

from typing import Literal
from pydantic import Field
from uuid import uuid4

from .builtins import Goal, recommend
from .models import Contract, ExecutionPolicy, PlanBinding, Workflow, WorkflowError
from .store import now, plan_binding


class ProposalRequest(Contract):
    project_id: str
    goal: Goal
    objective: str = ""
    mode: Literal["template","hybrid"] = "template"
    external_planning_approved: bool = False
    policy: ExecutionPolicy = Field(default_factory=ExecutionPolicy)


class ProposalView(Contract):
    id: str
    task_id: str
    project_id: str
    source: str
    status: Literal["proposed","accepted","rejected","blocked","stale"]
    objective: str
    rationale: str
    change_types: list[str] = Field(default_factory=list)
    evidence: list[str]
    requested_stages: list[str]
    execution_stages: list[str]
    reused_artifacts: list[str]
    missing_inputs: list[str]
    limitations: list[str]
    workflow: Workflow | None
    confirmation: PlanBinding | None
    created_at: str
    review_identity: dict | None = None
    previous_review_identity: dict | None = None


class ProposalDecision(Contract):
    action: Literal["accept","reject"]


class PlanningService:
    def __init__(self,store,boundary,backend=None,engine=None):
        self.store,self.boundary,self.backend = store,boundary,backend
        self.engine = engine
        with store.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY,project_id TEXT NOT NULL,payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS plan_actions(seq INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT NOT NULL,proposal_id TEXT,run_id TEXT,action TEXT NOT NULL,actor TEXT NOT NULL,timestamp TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS actions_project_seq ON plan_actions(project_id,seq);
            """)

    def propose(self,request: ProposalRequest) -> ProposalView:
        project = self.store.project(request.project_id)
        self.boundary.check({"objective":request.objective})
        identity = str(uuid4())
        result = ProposalView(id=identity,task_id=identity,project_id=project.id,source="validated_template",status="proposed",
            objective=request.objective,rationale="确定性模板编译；没有调用语言模型。",evidence=[],requested_stages=[],execution_stages=[],
            reused_artifacts=[],missing_inputs=[],limitations=["提案接受不是参数审批，也不启动计算。","未核验跨运行阶段依赖身份，不自动复用旧科学产物。"],workflow=None,confirmation=None,created_at=now())
        workflow = None
        if request.mode == "hybrid":
            result.source = "hybrid_semantic_compiler"
            if self.backend is None or not request.external_planning_approved:
                result.status = "blocked"
                result.rationale = "未配置私有规划提供者，或尚未同意向该提供者发送目标与公开证据摘要。"
                result.missing_inputs = ["private_planning_provider_or_explicit_data_permission"]
            else:
                from igem_drylab.agent.models import AgentTask
                from igem_drylab.agent.context import ContextBundle
                task = AgentTask(task_id=identity,objective=request.objective,artifacts_dir="logical-agent-workspace",
                    inputs={"project_revision":project.revision,"scientific_project_available":project.scientific_project is not None},
                    constraints=["do_not_invent_parameters","human_approval_before_execution"])
                context = ContextBundle(task=task,constraints=task.constraints,
                    artifact_summaries=[{"file_id":item["file_id"],"sha256":item["sha256"],"name":item["name"]} for item in self.boundary.project(project)["files"]])
                # Call the existing semantic interpreter + deterministic compiler,
                # not AgentRuntime or a second executor.
                compiled = self.backend.create_plan(task,context,{"igem.pipeline.plan_stage"})
                semantic = compiled.diagnostics.get("semantic_decision",{})
                result.rationale = semantic.get("rationale") or "确定性编译器要求补充输入或证据。"
                result.change_types = list(semantic.get("change_types",[]))
                result.missing_inputs = list(semantic.get("missing_inputs",[]))
                result.evidence = [item["sha256"] for item in context.artifact_summaries]
                requested = [step.arguments["stage"] for step in compiled.steps if step.action_type == "dispatch_stage"]
                result.requested_stages = requested
                if not requested or any(step.status == "blocked" for step in compiled.steps):
                    result.status = "blocked"
                    result.limitations.extend(step.rationale for step in compiled.steps)
                elif not project.scientific_project:
                    result.status = "blocked"
                    result.missing_inputs.append("typed_scientific_project")
                else:
                    workflow = recommend(project,"scientific_pipeline")
                    target = max(requested,key=lambda item:["m1","m2","m3","m4","m5"].index(item))
                    selected = {target}
                    definitions = {node.id:node for node in workflow.nodes}
                    while True:
                        expanded = selected | set().union(*(definitions[key].dependencies() for key in selected))
                        if expanded == selected: break
                        selected = expanded
                    workflow.nodes = [node for node in workflow.nodes if node.id in selected]
                    workflow.execution_policy.allowed_tools = sorted({node.tool_id for node in workflow.nodes})
                    expanded_stages = [node.id for node in workflow.nodes if node.id not in requested]
                    if expanded_stages:
                        result.limitations.append("缺少经过核验的可复用前序产物，因此显式补全前置阶段："+", ".join(expanded_stages))
                        constraints = semantic.get("scientific_constraints",[])
                        if "do_not_rerun_unaffected_structural_stages" in constraints:
                            result.status = "blocked"
                            result.missing_inputs.append("verified_reusable_prerequisites")
                            workflow = None
        else:
            workflow = recommend(project,request.goal)
            result.requested_stages = [node.id for node in workflow.nodes]
        if workflow is not None:
            workflow.execution_policy = request.policy.model_copy(deep=True)
            workflow = Workflow.model_validate(workflow.model_dump(mode="json"))
            result.execution_stages = [node.id for node in workflow.nodes]
            result.workflow = workflow
            result.confirmation = plan_binding(project,workflow)
            result.review_identity = self.engine.review_identity(project,workflow) if self.engine else None
        self.boundary.check(result.model_dump(mode="json"))
        with self.store.connection() as db:
            db.execute("INSERT INTO proposals VALUES(?,?,?)",(identity,project.id,result.model_dump_json()))
            self._action(db,result,"proposed","planner")
        return result

    def custom(self,project_id:str,workflow:Workflow,objective:str,*,source="user_reviewed_workflow",previous_review_identity=None):
        project=self.store.project(project_id)
        identity=str(uuid4())
        result=ProposalView(id=identity,task_id=identity,project_id=project_id,source=source,status="proposed",
            objective=objective,rationale="用户提交的 DAG；已校验图、工具与正式前序来源绑定，尚未接受或执行。",evidence=[],requested_stages=[node.id for node in workflow.nodes],
            execution_stages=[node.id for node in workflow.nodes],reused_artifacts=[],missing_inputs=[],limitations=["用户 DAG 不自动批准科学参数；同一 durable 执行器仍核验来源与审批。"],
            workflow=workflow,confirmation=plan_binding(project,workflow),created_at=now(),
            review_identity=self.engine.review_identity(project,workflow) if self.engine else None,previous_review_identity=previous_review_identity)
        self.boundary.check(result.model_dump(mode="json"))
        with self.store.connection() as db:
            db.execute("INSERT INTO proposals VALUES(?,?,?)",(identity,project_id,result.model_dump_json()))
            self._action(db,result,"proposed","user")
        return result

    def get(self,proposal_id: str):
        with self.store.connection() as db:
            row = db.execute("SELECT payload FROM proposals WHERE id=?",(proposal_id,)).fetchone()
        if row is None: raise KeyError(proposal_id)
        return ProposalView.model_validate_json(row[0])

    def decide(self,proposal_id: str,action: str):
        prepared = self.get(proposal_id)
        current = self.engine.review_identity(self.store.project(prepared.project_id),prepared.workflow) if self.engine and prepared.workflow else None
        with self.store.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload FROM proposals WHERE id=?",(proposal_id,)).fetchone()
            if row is None: raise KeyError(proposal_id)
            result = ProposalView.model_validate_json(row[0])
            if result.status not in {"proposed","accepted"}: raise WorkflowError("proposal_not_actionable",status_code=409)
            project = db.execute("SELECT payload FROM projects WHERE id=?",(result.project_id,)).fetchone()
            from .models import Project
            if not project or result.workflow is None or result.confirmation != plan_binding(Project.model_validate_json(project[0]),result.workflow):
                raise WorkflowError("proposal_stale_regenerate",status_code=409)
            if action == "accept" and result.review_identity != current:
                raise WorkflowError("reviewed_tool_or_profile_changed",status_code=409)
            result.status = "accepted" if action == "accept" else "rejected"
            db.execute("UPDATE proposals SET payload=? WHERE id=?",(result.model_dump_json(),proposal_id))
            self._action(db,result,action,"user")
            if action == "accept" and result.source == "manual_compatibility":
                self._action(db,result,"manual_plan_confirmed","user")
        return result

    def authorize_run(self,proposal_id: str,confirmation: PlanBinding,workflow: Workflow,*,db=None,snapshot=None,manual=False):
        if db is None: proposal = self.get(proposal_id)
        else:
            row = db.execute("SELECT payload FROM proposals WHERE id=?",(proposal_id,)).fetchone()
            if row is None: raise KeyError(proposal_id)
            proposal = ProposalView.model_validate_json(row[0])
        if proposal.status != "accepted" or proposal.confirmation != confirmation or proposal.workflow != workflow:
            raise WorkflowError("accepted_proposal_binding_required",status_code=409)
        if manual != (proposal.source == "manual_compatibility"):
            raise WorkflowError("explicit_review_execution_type_required",status_code=409)
        actual = self.engine.snapshot_review_identity(snapshot) if snapshot is not None else self.engine.review_identity(self.store.project(proposal.project_id),workflow)
        if proposal.review_identity is None or proposal.review_identity != actual:
            raise WorkflowError("reviewed_tool_or_profile_changed",status_code=409)
        if db is not None and snapshot.get("runtime_profile"):
            profile=snapshot["runtime_profile"]
            row=db.execute("SELECT revision,hash FROM runtime_profiles WHERE id=?",(profile["id"],)).fetchone()
            if row is None or (row["revision"],row["hash"]) != (profile["revision"],profile["hash"]):
                raise WorkflowError("reviewed_tool_or_profile_changed",status_code=409)

    def actions(self,project_id: str,after: int,limit: int):
        with self.store.connection() as db:
            rows = db.execute("SELECT seq,proposal_id,run_id,action,actor,timestamp FROM plan_actions WHERE project_id=? AND seq>? ORDER BY seq LIMIT ?",(project_id,after,limit))
            return [dict(row) for row in rows]

    @staticmethod
    def _action(db,proposal,action,actor,run_id=None):
        db.execute("INSERT INTO plan_actions(project_id,proposal_id,run_id,action,actor,timestamp) VALUES(?,?,?,?,?,?)",(proposal.project_id,proposal.id,run_id,action,actor,now()))

    def started(self,proposal_id,run_id):
        with self.store.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM plan_actions WHERE proposal_id=? AND run_id=? AND action='execution_requested'",(proposal_id,run_id)).fetchone(): return
            self._action(db,self.get(proposal_id),"execution_requested","user",run_id)
        self.store.event(run_id,"agent_plan_execution_requested",{"proposal_id":proposal_id,"actor":"user"})

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
from igem_drylab.agent.scientific_environment import ScientificEnvironment,ScientificObservation
from igem_drylab.agent.decision import ScientificAction,InspectProjectAction,PrepareNodeAction,WaitAction,SemanticDecision


class ProposalRequest(Contract):
    project_id: str
    goal: Goal
    objective: str = ""
    mode: Literal["template","hybrid"] = "template"
    external_planning_approved: bool = False
    policy: ExecutionPolicy = Field(default_factory=ExecutionPolicy)


class ProposalView(Contract):
    observation: ScientificObservation | None = None
    scientific_actions: list[ScientificAction] = Field(default_factory=list)
    reviewed_tool_labels: list[str] = Field(default_factory=list)
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
            objective=request.objective,rationale="Template planner; no language model was called.",evidence=[],requested_stages=[],execution_stages=[],
            reused_artifacts=[],missing_inputs=[],limitations=["Accepting a proposal does not approve parameters or start execution.","Cross-run dependency reuse is not verified; original scientific outputs are not automatically reused."],workflow=None,confirmation=None,created_at=now())
        workflow = None
        environment = ScientificEnvironment(self.store,self.engine.tools) if self.engine else None
        if environment:
            result.observation = environment.observe(project,request.policy)
            self.boundary.check(result.observation.model_dump(mode="json"))
            result.scientific_actions = [InspectProjectAction(kind="inspect_project",reason="Read actual declared gaps, registry applicability, capabilities and recorded stage outcomes.")]
        if request.mode == "hybrid":
            result.source = "hybrid_semantic_compiler"
            if self.backend is None or not request.external_planning_approved:
                result.status = "blocked"
                result.rationale = "Private planner unavailable or external disclosure consent not granted."
                result.missing_inputs = ["private_planning_provider_or_explicit_data_permission"]
            else:
                from igem_drylab.agent.models import AgentTask
                from igem_drylab.agent.context import ContextBundle
                task = AgentTask(task_id=identity,objective=request.objective,artifacts_dir="logical-agent-workspace",
                    inputs={"project_revision":project.revision,"scientific_project_available":project.scientific_project is not None},
                    constraints=["do_not_invent_parameters","human_approval_before_execution"])
                context = ContextBundle(task=task,constraints=task.constraints,
                    scientific_observation=result.observation,
                    artifact_summaries=[{"file_id":item["file_id"],"sha256":item["sha256"],"name":item["name"]} for item in self.boundary.project(project)["files"]])
                # Call the existing semantic interpreter + deterministic compiler,
                # not AgentRuntime or a second executor.
                compiled = self.backend.create_plan(task,context,{"igem.pipeline.plan_stage"})
                semantic = compiled.diagnostics.get("semantic_decision",{})
                if semantic.get("scientific_actions") and environment:
                    typed = SemanticDecision.model_validate(semantic).scientific_actions
                    try:
                        result.scientific_actions += environment.validate_actions(typed,result.observation)
                    except WorkflowError as error:
                        result.status = "blocked"
                        result.missing_inputs = [error.code]
                result.rationale = semantic.get("rationale") or "The deterministic compiler requires additional inputs or evidence."
                result.change_types = list(semantic.get("change_types",[]))
                result.missing_inputs.extend(semantic.get("missing_inputs",[]))
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
                    if target not in definitions:
                        result.status = "blocked"
                        result.missing_inputs.append("stage_configuration_not_prepared:"+target)
                        workflow = None
                        selected = set()
                    while True:
                        if workflow is None: break
                        expanded = selected | set().union(*(definitions[key].dependencies() for key in selected))
                        if expanded == selected: break
                        selected = expanded
                    if workflow is not None:
                        workflow.nodes = [node for node in workflow.nodes if node.id in selected]
                        workflow.execution_policy.allowed_tools = sorted({node.tool_id for node in workflow.nodes})
                    expanded_stages = [node.id for node in workflow.nodes if node.id not in requested] if workflow else []
                    if expanded_stages:
                        result.limitations.append("No verified reusable predecessor artifacts; dependencies explicitly added: "+", ".join(expanded_stages))
                        constraints = semantic.get("scientific_constraints",[])
                        if "do_not_rerun_unaffected_structural_stages" in constraints:
                            result.status = "blocked"
                            result.missing_inputs.append("verified_reusable_prerequisites")
                            workflow = None
        else:
            workflow = recommend(project,request.goal)
            result.requested_stages = [node.id for node in workflow.nodes]
        if workflow is not None:
            if result.status == "blocked":
                workflow = None
        if workflow is not None:
            workflow.execution_policy = request.policy.model_copy(deep=True)
            workflow = Workflow.model_validate(workflow.model_dump(mode="json"))
            result.execution_stages = [node.id for node in workflow.nodes]
            result.workflow = workflow
            result.confirmation = plan_binding(project,workflow)
            result.review_identity = self.engine.review_identity(project,workflow) if self.engine else None
            result.reviewed_tool_labels = self._tool_labels(result.review_identity)
            if environment:
                first = workflow.nodes[0]
                actions=[PrepareNodeAction(kind="prepare_node",tool_id=first.tool_id,input_refs=["project:"+project.id],reason="Prepare the reviewed execution entry point; no tool runs or approvals are performed by proposing.")]
                if result.observation.gaps:
                    actions.append(WaitAction(kind="wait",pending_refs=sorted({gap.code for gap in result.observation.gaps}),reason="Later quantitative work still requires the recorded sources or approvals; already prepared stages remain usable."))
                # An unconfigured external route is recorded as a gap, not a fabricated capability.
                try:
                    result.scientific_actions += environment.validate_actions(actions,result.observation)
                except WorkflowError as error:
                    result.limitations.append(error.code)
        self.boundary.check(result.model_dump(mode="json"))
        with self.store.connection() as db:
            db.execute("INSERT INTO proposals VALUES(?,?,?)",(identity,project.id,result.model_dump_json()))
            self._action(db,result,"proposed","planner")
        return result

    def custom(self,project_id:str,workflow:Workflow,objective:str,*,source="user_reviewed_workflow",previous_review_identity=None):
        project=self.store.project(project_id)
        identity=str(uuid4())
        result=ProposalView(id=identity,task_id=identity,project_id=project_id,source=source,status="proposed",
            objective=objective,rationale="User DAG validated for graph, tools and formal predecessor bindings; not accepted or executed.",evidence=[],requested_stages=[node.id for node in workflow.nodes],
            execution_stages=[node.id for node in workflow.nodes],reused_artifacts=[],missing_inputs=[],limitations=["User DAGs do not approve scientific parameters; the durable executor verifies provenance and approvals."],
            workflow=workflow,confirmation=plan_binding(project,workflow),created_at=now(),
            review_identity=self.engine.review_identity(project,workflow) if self.engine else None,previous_review_identity=previous_review_identity)
        result.reviewed_tool_labels = self._tool_labels(result.review_identity)
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
    def _tool_labels(identity):
        return [tool+" · "+str(values["version"])+" · "+str(values["runtime"])
            for tool,values in (identity or {}).get("tools",{}).items()]

    @staticmethod
    def _action(db,proposal,action,actor,run_id=None):
        db.execute("INSERT INTO plan_actions(project_id,proposal_id,run_id,action,actor,timestamp) VALUES(?,?,?,?,?,?)",(proposal.project_id,proposal.id,run_id,action,actor,now()))

    def started(self,proposal_id,run_id):
        with self.store.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM plan_actions WHERE proposal_id=? AND run_id=? AND action='execution_requested'",(proposal_id,run_id)).fetchone(): return
            self._action(db,self.get(proposal_id),"execution_requested","user",run_id)
        self.store.event(run_id,"agent_plan_execution_requested",{"proposal_id":proposal_id,"actor":"user"})

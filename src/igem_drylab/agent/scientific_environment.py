"""Read-only domain observations for the existing workbench planner.

No independent executor, registry, model inference, parameter approval or file
registration. The durable engine still verifies scientific inputs/results and
authorization at execution boundaries. Recorded observations are not proof
that an unverified historical artifact is reusable.
"""
from hashlib import sha256
import json
from pydantic import BaseModel,ConfigDict,Field
from typing import Literal

from .decision import ScientificAction


class ObservationContract(BaseModel):
    model_config=ConfigDict(extra="forbid")


class ScientificGap(ObservationContract):
    stage: str
    code: str
    construct_id: str | None
    condition_id: str | None
    reasons: list[str]


class DomainCapability(ObservationContract):
    tool_id: str
    version: str
    resource: str
    route_state: Literal["local_method", "configured_not_verified", "unconfigured"]
    execution_allowed_by_policy: bool


class RecordedStageResult(ObservationContract):
    run_id: str
    node_id: str
    stage: str
    node_status: str
    attempt: int
    result_ref: str | None
    current_project_revision: bool
    scientific_status_counts: dict[str,int]
    numerically_solved_count: int | None
    evidence_ready_count: int | None
    claim_scopes: list[str]


class RecordedJob(ObservationContract):
    run_id: str
    node_id: str
    tool_id: str
    node_status: str
    attempt: int
    tool_status: str | None
    parse_status: str | None
    remote_status: str | None = None
    remote_poll_count: int | None = None
    remote_cancellation_confirmed: Literal[False] = False


class ReviewedParameterSummary(ObservationContract):
    parameter_id: str
    parameter_type: str
    construct_id: str | None
    condition_id: str | None
    review_status: str
    source_type: str
    unit: str | None
    entity_basis: str | None
    model_version: str | None
    value: float | str
    parameter_version: int
    conditions: dict[str,str | float]


class ScientificObservation(ObservationContract):
    project_id: str
    project_revision: int
    observation_identity: str
    scientific_input_identity: str | None
    prepared_through: str | None
    scenarios: dict[str,str]
    available_input_refs: list[str]
    gaps: list[ScientificGap]
    omitted_gap_count: int
    parameter_summaries: list[ReviewedParameterSummary]
    omitted_parameter_count: int
    capabilities: list[DomainCapability]
    recorded_results: list[RecordedStageResult]
    recorded_jobs: list[RecordedJob]
    accepted_proposal_refs: list[str]
    budget: dict[str,int | float | None]
    limitations: list[str]


class ScientificEnvironment:
    def __init__(self,store,tools):
        self.store,self.tools=store,tools

    def observe(self,project,policy):
        from igem_drylab.workflow.precheck import precheck
        from igem_drylab.workflow.scientific_project import ScientificProject
        from igem_drylab.workflow.runtime_profiles import RuntimeProfiles
        from igem_drylab.compartments import scenario_for_construct
        config=ScientificProject.model_validate(project.scientific_project).config if project.scientific_project else None
        check=precheck(project)
        gaps=[ScientificGap(stage=g.stage,code=g.code,construct_id=g.construct_id,condition_id=g.condition_id,reasons=g.reason_codes) for g in check.missing[:64]]
        scenarios={}
        if config:
            for row in [*config.inputs.constructs,*config.inputs.designs]:
                scenarios[row.id]=scenario_for_construct(config,row.id)
            for row in config.inputs.construct_records:
                scenarios[row.construct_id]=scenario_for_construct(config,row.construct_id)
        runtime={}
        if project.runtime_profile_ref:
            _,runtime=RuntimeProfiles(self.store).get(project.runtime_profile_ref)
        if config:
            runtime={**{key:value.model_dump() for key,value in config.tools.items()},**runtime}
        capabilities=[]
        for definition in self.tools.definitions():
            tool_id=definition.id
            if tool_id.startswith("prediction."):
                route=runtime.get(tool_id.partition(".")[2],{})
                state="configured_not_verified" if route.get("enabled") and route.get("mode")=="external" else "unconfigured"
                if tool_id=="prediction.jpred" and state!="unconfigured":
                    from igem_drylab.pipeline.config import ToolConfig
                    from igem_drylab.workflow.sequence_predictions import uses_native_jpred_route
                    if not uses_native_jpred_route(ToolConfig.model_validate(route)):
                        state="unconfigured"
            else:
                state="local_method" if definition.runtime=="builtin" else "configured_not_verified"
            capabilities.append(DomainCapability(tool_id=tool_id,version=definition.version,resource=definition.resource,
                route_state=state,execution_allowed_by_policy=not policy.allowed_tools or tool_id in policy.allowed_tools))
        results=[]
        jobs=[]
        accepted=[]
        with self.store.connection() as db:
            # Bounded summaries, never load all histories or large result payloads.
            rows=db.execute("""SELECT runs.id AS run_id,nodes.id AS node_id,nodes.status,nodes.attempts,
                json_extract(runs.snapshot,'$.project.revision') AS revision,
                (SELECT json_extract(value,'$.tool_id') FROM json_each(runs.snapshot,'$.workflow.nodes')
                    WHERE json_extract(value,'$.id')=COALESCE(nodes.parent_id,nodes.id)) AS tool_id,
                artifacts.id AS artifact_id,
                (SELECT json_group_object(status,quantity) FROM
                    (SELECT COALESCE(json_extract(value,'$.status'),'unknown') AS status,COUNT(*) AS quantity
                     FROM json_each(nodes.output,'$.records') GROUP BY status)) AS status_counts,
                (SELECT CASE WHEN COUNT(*)=0 THEN 0 WHEN COUNT(*)=SUM(json_type(value,'$.numerically_solved') IN ('true','false'))
                    THEN SUM(json_extract(value,'$.numerically_solved') IS 1) END FROM json_each(nodes.output,'$.records')) AS solved_count,
                (SELECT CASE WHEN COUNT(*)=0 THEN 0 WHEN COUNT(*)=SUM(json_type(value,'$.evidence_ready') IN ('true','false'))
                    THEN SUM(json_extract(value,'$.evidence_ready') IS 1) END FROM json_each(nodes.output,'$.records')) AS evidence_count,
                (SELECT json_group_array(DISTINCT COALESCE(json_extract(value,'$.claim_scope'),'unknown'))
                    FROM json_each(nodes.output,'$.records')) AS claim_scopes,
                json_extract(nodes.output,'$.tool_status') AS tool_status,
                json_extract(nodes.output,'$.parse_status') AS parse_status,
                json_extract(nodes.remote_job,'$.status') AS remote_status,
                json_extract(nodes.remote_job,'$.poll_count') AS remote_poll_count
                FROM runs JOIN nodes ON nodes.run_id=runs.id
                LEFT JOIN artifacts ON artifacts.run_id=nodes.run_id AND artifacts.node_id=nodes.id
                    AND json_extract(artifacts.metadata,'$.attempt')=nodes.attempts
                WHERE runs.project_id=?
                ORDER BY runs.created_at DESC,nodes.rowid DESC LIMIT 20""",(project.id,)).fetchall()
            for row in rows:
                tool_id=row["tool_id"] or ""
                jobs.append(RecordedJob(run_id=row["run_id"],node_id=row["node_id"],tool_id=tool_id,node_status=row["status"],
                    attempt=row["attempts"],tool_status=row["tool_status"],parse_status=row["parse_status"],
                    remote_status=row["remote_status"],remote_poll_count=row["remote_poll_count"]))
                if not tool_id.startswith("project."):continue
                committed=row["status"]=="succeeded" and row["artifact_id"] is not None
                counts=json.loads(row["status_counts"] or "{}") if committed else {}
                results.append(RecordedStageResult(run_id=row["run_id"],node_id=row["node_id"],stage=tool_id.partition(".")[2],
                    node_status=row["status"],attempt=row["attempts"],result_ref=row["artifact_id"],current_project_revision=row["revision"]==project.revision,
                    scientific_status_counts=counts,numerically_solved_count=row["solved_count"] if committed else None,
                    evidence_ready_count=row["evidence_count"] if committed else None,
                    claim_scopes=sorted(json.loads(row["claim_scopes"] or "[]")) if committed else []))
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='proposals'").fetchone():
                accepted=[row[0] for row in db.execute("""SELECT id FROM proposals WHERE project_id=? AND
                    json_extract(payload,'$.status')='accepted' AND json_extract(payload,'$.confirmation.project_revision')=? LIMIT 20""",(project.id,project.revision))]
        parameters=config.parameters if config else []
        summaries=[ReviewedParameterSummary(parameter_id=r.parameter_id,parameter_type=r.parameter_type,construct_id=r.construct_id,
            condition_id=r.condition_id,review_status=r.review_status,source_type=r.source_type,unit=r.unit,
            entity_basis=r.conditions.get("entity_basis"),model_version=r.model_version,value=r.value,parameter_version=r.parameter_version,
            conditions={key:value for key,value in r.conditions.items() if key in {"host","strain","temperature_c","pH","assay_system","binding_pair","entity_basis"}}) for r in parameters[:64]]
        input_identity=sha256(json.dumps(config.model_dump(mode="json",exclude={"run","tools"}),sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest() if config else None
        observation=ScientificObservation(project_id=project.id,project_revision=project.revision,observation_identity="",
            scientific_input_identity=input_identity,
            prepared_through=config.prepared_through if config else None,scenarios=scenarios,available_input_refs=["project:"+project.id],gaps=gaps,omitted_gap_count=max(0,len(check.missing)-64),
            parameter_summaries=summaries,omitted_parameter_count=max(0,len(parameters)-64),capabilities=capabilities,recorded_results=results,recorded_jobs=jobs,
            accepted_proposal_refs=accepted,budget={"max_tool_calls":policy.max_tool_calls,"dispatch_deadline_seconds":policy.stop_after_seconds,"memory_limit_mb":policy.memory_limit_mb},
            limitations=["Declared gaps/recorded results only: no parameter approval, numerical calculation or verified cross-run reuse.",
                "Configured route is not proof of successful execution or valid authorization.",
                "Context bounded to 64 gaps, 64 parameter summaries and 20 recent node observations; omitted counts explicit.",
                "Historical different-revision results cannot authorize execution; metadata-only reuse still requires verified dependency read sets."])
        observation.observation_identity=sha256(json.dumps(observation.model_dump(),sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
        return observation

    @staticmethod
    def validate_actions(actions:list[ScientificAction],observation):
        from igem_drylab.workflow.models import WorkflowError
        tools={c.tool_id:c for c in observation.capabilities}
        results={r.result_ref for r in observation.recorded_results if r.result_ref and r.node_status=="succeeded" and r.current_project_revision}
        runs={r.run_id for r in observation.recorded_jobs}
        gaps={g.code for g in observation.gaps}
        evidence=results | {p.parameter_id for p in observation.parameter_summaries}
        for action in actions:
            if set(action.evidence_refs)-evidence:
                raise WorkflowError("scientific_action_unobserved_evidence")
            if action.kind=="prepare_node":
                capability=tools.get(action.tool_id)
                if capability is None or not capability.execution_allowed_by_policy or capability.route_state=="unconfigured":
                    raise WorkflowError("scientific_action_tool_unavailable_or_not_allowed")
                if set(action.input_refs)-(evidence | set(observation.available_input_refs)):
                    raise WorkflowError("scientific_action_unobserved_inputs")
            elif action.kind=="submit_job" and action.reviewed_proposal_id not in observation.accepted_proposal_refs:
                raise WorkflowError("scientific_action_requires_existing_human_accepted_proposal")
            elif action.kind=="inspect_job" and action.run_id not in runs:
                raise WorkflowError("scientific_action_unobserved_run")
            elif action.kind=="evaluate_result" and action.result_ref not in results:
                raise WorkflowError("scientific_action_requires_current_successful_result")
            elif action.kind=="wait" and set(action.pending_refs)-(runs | gaps):
                raise WorkflowError("scientific_action_unobserved_wait_condition")
        return actions

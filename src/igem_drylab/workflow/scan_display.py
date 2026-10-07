"""Read-only finite-scaffold-scan-v2 adapter. No solver, ranking or approval."""
import json
import math
from typing import Literal
from .models import Contract, WorkflowError
from .display_resources import ResourceIdentity


class ScanPoint(Contract):
    ordinal: int
    candidate_id: str
    site_ratio: float | None
    dense_oc_dmt_ratio: float | None
    status: str
    feasible: bool | None
    metric_value: float | None
    reason_codes: list[str]


class ScanPage(Contract):
    schema_version: Literal["display-finite-scan-v1"] = "display-finite-scan-v1"
    identity: ResourceIdentity
    offset: int
    total: int
    has_more: bool
    decision_id: str
    decision_scope: str
    objective: str
    metric_definition: str | None
    metric_unit: str | None
    comparison_contract: dict | None
    points: list[ScanPoint]
    ranking_performed: Literal[False] = False
    claim_scope: Literal["source_reported_scan_not_execution_or_parameter_approval"] = "source_reported_scan_not_execution_or_parameter_approval"


def scan_page(resources, project_id, file_id, offset, limit):
    path, identity, _ = resources.source(project_id, file_id)
    raw = json.loads(path.read_bytes())
    if not isinstance(raw,dict) or raw.get("schema_version") != "finite-scaffold-scan-v2":
        raise WorkflowError("unsupported_scan_display_contract")
    rows, decision = raw.get("scaffold_scan"), raw.get("design_decision")
    if not isinstance(rows,list) or len(rows)>100_000 or not isinstance(decision,dict):
        raise WorkflowError("invalid_scan_display_contract")
    objective = decision.get("objective")
    if objective not in {"yield_abs","productivity"}:
        raise WorkflowError("invalid_scan_display_contract")
    formal = decision.get("decision_scope") == "formal_conditional_mechanism"
    expected = decision.get("comparison_contract")
    from igem_drylab.design_analysis import DesignComparisonContract
    try:
        expected = DesignComparisonContract.model_validate(expected).model_dump(mode="json") if expected else None
    except ValueError as error:
        raise WorkflowError("invalid_scan_comparison_contract") from error
    points=[]
    def finite(value):
        return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
    for i,row in enumerate(rows[offset:offset+limit],offset):
        if not isinstance(row,dict) or not isinstance(row.get("candidate"),dict):
            raise WorkflowError("invalid_scan_display_contract")
        candidate=row["candidate"]
        reasons=[]
        status=row.get("status")
        if status!="valid": reasons.append("source_row_not_valid")
        if not formal: reasons.append("source_scope_not_formal")
        grades=row.get("evidence_grades") or {}
        if not (grades.get("evidence_ready") is True and grades.get("context_evidence_ready") is True and
                grades.get("data_quality") in {"measured","fitted","literature","mixed"} and
                grades.get("claim_scope")==grades.get("context_claim_scope")=="conditional_mechanism"):
            reasons.append("source_evidence_not_formally_eligible")
        actual=row.get("comparison_contract")
        try:
            actual=DesignComparisonContract.model_validate(actual).model_dump(mode="json")
        except (ValueError,TypeError):
            actual=None
        if expected is None or actual is None:
            reasons.append("comparison_contract_missing")
        elif any(actual[k]!=expected[k] for k in expected if k!="steady_state_observation_reference"):
            reasons.append("comparison_contract_differs")
        context=row.get("context") or {}
        counts=context.get("nominal_site_counts") or {}
        ratio=candidate.get("site_ratio")
        if not finite(ratio) or ratio not in {1,2,3,4,6} or not finite(counts.get("PDZ")) or counts["PDZ"]<=0 or not finite(counts.get("SH3")) or counts["SH3"]/counts["PDZ"]!=ratio:
            reasons.append("declared_site_ratio_not_bound_to_context")
        if candidate.get("candidate_id")!=context.get("candidate_id"):
            reasons.append("candidate_context_identity_mismatch")
        metric=(row.get("metrics") or {}).get(objective)
        if not finite(metric): reasons.append("metric_not_recorded")
        dense=row.get("dense_oc_dmt_ratio")
        points.append(ScanPoint(ordinal=i,candidate_id=str(candidate.get("candidate_id","")),
            site_ratio=ratio if finite(ratio) else None,dense_oc_dmt_ratio=dense if finite(dense) else None,
            status=str(status),feasible=row.get("feasible") if isinstance(row.get("feasible"),bool) else None,
            metric_value=metric if not reasons else None,reason_codes=reasons))
    result=ScanPage(identity=identity,offset=offset,total=len(rows),has_more=offset+limit<len(rows),
        decision_id=decision.get("decision_id",""),decision_scope=decision.get("decision_scope",""),objective=objective,
        metric_definition=expected["metric_definition"] if expected else None,metric_unit=expected["metric_unit"] if expected else None,
        comparison_contract=expected,points=points).model_dump(mode="json")
    resources.boundary.check(result)
    return result

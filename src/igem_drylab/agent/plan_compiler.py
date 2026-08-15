"""Deterministic compiler from semantic decisions to validated Agent DAGs."""
from __future__ import annotations

from .decision import ChangeType, EvidenceAction, PlanningDecision, RequestedOutcome, Stage
from .models import AgentTask, Plan, PlanStep


_ORDER = (Stage.m1, Stage.m2, Stage.m3, Stage.m4)
_ROUTES = {
    ChangeType.parameter_update: (Stage.m3, Stage.m4),
    ChangeType.scaffold_capacity_update: (Stage.m3, Stage.m4),
    ChangeType.construct_sequence_update: _ORDER,
    ChangeType.fusion_architecture_update: _ORDER,
    ChangeType.new_design_request: _ORDER,
}


class DeterministicPlanCompiler:
    """Apply project routing and guardrails; never calls an LLM or equations."""
    def compile(self, task: AgentTask, decision: PlanningDecision) -> Plan:
        blocked = self._guardrail_block(task)
        if blocked:
            return Plan(task_id=task.task_id, steps=[PlanStep(step_id="collect_missing_inputs", objective="Request valid inputs or human-reviewed evidence.", action_type="request_input", status="blocked", rationale=blocked)])
        if task.inputs.get("missing_parameter") or task.inputs.get("conflicting_evidence"):
            return self._evidence_route(task, decision)
        if decision.missing_inputs:
            return Plan(task_id=task.task_id, steps=[PlanStep(step_id="collect_missing_inputs", objective="Request declared missing inputs.", action_type="request_input", status="blocked", rationale="Missing inputs: " + ", ".join(decision.missing_inputs))])
        if ChangeType.interpretation_only in decision.change_types or decision.requested_outcome == RequestedOutcome.interpret:
            if task.inputs.get("all_artifacts_validated"):
                return Plan(task_id=task.task_id, steps=[PlanStep(step_id="reuse_validated_artifacts", objective="Reuse validated artifacts without scientific recomputation.", action_type="reuse_artifact", status="succeeded", rationale="Interpretation-only request with validated artifacts.")])
        stages = self._stages(decision, task)
        steps: list[PlanStep] = []
        previous: str | None = None
        for stage in stages:
            step = PlanStep(step_id=f"dispatch_{stage.value}", objective=f"Dispatch deterministic {stage.value.upper()} stage.", tool_name="igem.pipeline.plan_stage", action_type="dispatch_stage", arguments={"stage": stage.value}, depends_on=[previous] if previous else [], priority=90 - len(steps) * 5, rationale="Compiled from typed semantic decision; deterministic stage owns all scientific calculations.")
            if stage == Stage.m2 and decision.requires_new_compute:
                step.resources, step.estimated_gpu_minutes = ["gpu"], 60
            steps.append(step); previous = step.step_id
        return Plan(task_id=task.task_id, steps=steps or [PlanStep(step_id="collect_missing_inputs", objective="Request a concrete project-state change or input.", action_type="request_input", status="blocked", rationale="Decision does not support safe scientific execution.")])

    @staticmethod
    def _stages(decision: PlanningDecision, task: AgentTask) -> list[Stage]:
        selected: set[Stage] = set()
        for change in decision.change_types: selected.update(_ROUTES.get(change, ()))
        if ChangeType.timecourse_update in decision.change_types: selected.add(Stage.m5)
        if ChangeType.artifact_update in decision.change_types:
            selected.update((Stage.m2, Stage.m3, Stage.m4) if task.inputs.get("artifact_stale") else (Stage.m2,))
        ordered = [stage for stage in _ORDER if stage in selected]
        return ([Stage.m5] if Stage.m5 in selected else []) + ordered

    @staticmethod
    def _evidence_route(task: AgentTask, decision: PlanningDecision) -> Plan:
        available = bool(task.inputs.get("evidence_database_path") or task.inputs.get("evidence_available") or task.inputs.get("conflicting_evidence"))
        if not available and decision.evidence_action not in {EvidenceAction.search_local_evidence, EvidenceAction.human_review}:
            return Plan(task_id=task.task_id, steps=[PlanStep(step_id="request_measurement", objective="Request a compatible measurement or local evidence source.", action_type="request_measurement", status="blocked", rationale="Missing parameter has no declared evidence route.")])
        resolve = PlanStep(step_id="resolve_missing_parameter", objective="Resolve compatible local evidence without inventing a parameter.", action_type="resolve_evidence", tool_name="igem.literature.qa" if task.inputs.get("evidence_database_path") else None, arguments={"evidence_path": task.inputs.get("evidence_database_path")} if task.inputs.get("evidence_database_path") else {}, rationale="Evidence creates only a review candidate; it cannot enter M3/M4 automatically.")
        review = PlanStep(step_id="review_missing_parameter", objective="Human review of evidence/parameter candidate is required before downstream numerical execution.", action_type="human_review", depends_on=[resolve.step_id], status="blocked", rationale="Unresolved or conflicting evidence requires human approval.")
        return Plan(task_id=task.task_id, steps=[resolve, review])

    @staticmethod
    def _guardrail_block(task: AgentTask) -> str | None:
        text = task.objective.lower(); inputs = task.inputs
        if inputs.get("artifact_checksum_invalid"): return "Invalid artifact checksum/provenance: reuse is prohibited."
        if inputs.get("author_native_sensitivity") and any(word in text for word in ("absolute", "micromolar", "titer")): return "Author-native sensitivity cannot support physical titer/productivity."
        if "docking score" in text and any(word in text for word in ("kcat", "km", "kinetic")): return "Docking is not a kinetic modifier."
        if "sh3:pdz" in text and "oc:dmt" in text and any(word in text for word in ("treat", "equate", "measured")): return "Capacity ratio is not measured enzyme abundance."
        if inputs.get("robustness_summary_available"): return "Sensitivity prioritizes measurement; it does not establish causality or optimality."
        return None


def _is_timecourse(task: AgentTask) -> bool:
    return bool(task.inputs.get("wetlab_time_course_available")) or "time-course" in task.objective.lower()

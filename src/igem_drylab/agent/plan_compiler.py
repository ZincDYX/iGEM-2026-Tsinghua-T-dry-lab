"""Deterministic compiler from semantic decisions to validated Agent DAGs."""
from __future__ import annotations

from .decision import ChangeType, PlanningDecision, Stage
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
            return Plan(task_id=task.task_id, steps=[PlanStep(step_id="collect_missing_inputs", objective="Request valid inputs or human-reviewed evidence.", status="blocked", rationale=blocked)])
        if decision.missing_inputs:
            return Plan(task_id=task.task_id, steps=[PlanStep(step_id="collect_missing_inputs", objective="Request declared missing inputs.", status="blocked", rationale="Missing inputs: " + ", ".join(decision.missing_inputs))])
        if ChangeType.interpretation_only in decision.change_types and task.inputs.get("all_artifacts_validated"):
            return Plan(task_id=task.task_id, steps=[PlanStep(step_id="reuse_validated_artifacts", objective="Reuse validated artifacts without scientific recomputation.", status="succeeded", rationale="Interpretation-only request with validated artifacts.")])
        stages = self._stages(decision)
        if ChangeType.wetlab_measurement_update in decision.change_types and _is_timecourse(task):
            stages = [Stage.m5, *[stage for stage in stages if stage != Stage.m5]]
        if not stages and decision.evidence_action in {"search_local_evidence", "human_review", "request_measurement"}:
            return Plan(task_id=task.task_id, steps=[PlanStep(step_id="review_missing_parameters", objective="Review evidence or request a measurement before model execution.", status="blocked", rationale="Evidence action requires human review; no parameter is fabricated.")])
        steps: list[PlanStep] = []
        previous: str | None = None
        for stage in stages:
            step = PlanStep(step_id=f"dispatch_{stage.value}", objective=f"Dispatch deterministic {stage.value.upper()} stage.", tool_name="igem.pipeline.plan_stage", arguments={"stage": stage.value}, depends_on=[previous] if previous else [], priority=90 - len(steps) * 5, rationale="Compiled from typed semantic decision; deterministic stage owns all scientific calculations.")
            if stage == Stage.m2 and decision.requires_new_compute:
                step.resources, step.estimated_gpu_minutes = ["gpu"], 60
            steps.append(step); previous = step.step_id
        return Plan(task_id=task.task_id, steps=steps or [PlanStep(step_id="collect_missing_inputs", objective="Request a concrete project-state change or input.", status="blocked", rationale="Decision does not support safe scientific execution.")])

    @staticmethod
    def _stages(decision: PlanningDecision) -> list[Stage]:
        selected: set[Stage] = set(decision.affected_stages)
        for change in decision.change_types: selected.update(_ROUTES.get(change, ()))
        if ChangeType.wetlab_measurement_update in decision.change_types: selected.add(Stage.m5)
        ordered = [stage for stage in _ORDER if stage in selected]
        return ([Stage.m5] if Stage.m5 in selected else []) + ordered

    @staticmethod
    def _guardrail_block(task: AgentTask) -> str | None:
        text = task.objective.lower(); inputs = task.inputs
        if inputs.get("artifact_checksum_invalid"): return "Invalid artifact checksum/provenance: reuse is prohibited."
        if inputs.get("missing_parameter"): return "Required parameter is missing; resolve evidence or request measurement."
        if inputs.get("author_native_sensitivity") and any(word in text for word in ("absolute", "micromolar", "titer")): return "Author-native sensitivity cannot support physical titer/productivity."
        if "docking score" in text and any(word in text for word in ("kcat", "km", "kinetic")): return "Docking is not a kinetic modifier."
        if "sh3:pdz" in text and "oc:dmt" in text and any(word in text for word in ("treat", "equate", "measured")): return "Capacity ratio is not measured enzyme abundance."
        if inputs.get("robustness_summary_available"): return "Sensitivity prioritizes measurement; it does not establish causality or optimality."
        return None


def _is_timecourse(task: AgentTask) -> bool:
    return bool(task.inputs.get("wetlab_time_course_available")) or "time-course" in task.objective.lower()

from __future__ import annotations

from typing import Protocol

from igem_drylab.mcp import ToolRegistry

from .context import ContextBundle
from .models import AgentTask, Plan, PlanStep


class PlanningBackend(Protocol):
    def create_plan(self, task: AgentTask, context: ContextBundle, available_tools: set[str]) -> Plan: ...


class RuleBasedDryLabPlanner:
    """Conservative project-specific planner used when no LLM planner is configured.

    It prefers existing artifacts and cheap checks. It never schedules a heavy
    prediction merely because an objective mentions protein structure.
    """

    def create_plan(self, task: AgentTask, context: ContextBundle, available_tools: set[str]) -> Plan:
        steps: list[PlanStep] = []
        config_path = task.inputs.get("config_path")
        structure_path = task.inputs.get("structure_output_path")
        vina_reference = task.inputs.get("reference_vina_output")
        vina_fusion = task.inputs.get("fusion_vina_output")
        objective = task.objective.lower()

        if isinstance(config_path, str) and "igem.pipeline.validate" in available_tools:
            steps.append(PlanStep(step_id="validate_config", objective="Validate the project configuration before scientific work.", tool_name="igem.pipeline.validate", arguments={"config_path": config_path}, priority=100, rationale="Invalid configuration invalidates later results."))

        if isinstance(structure_path, str) and "igem.parsers.structure_prediction" in available_tools:
            steps.append(PlanStep(step_id="parse_structure", objective="Parse existing ColabFold/structure confidence artifacts.", tool_name="igem.parsers.structure_prediction", arguments={"path": structure_path}, depends_on=_dependencies(steps), priority=90, rationale="Reuse existing structure output before scheduling new GPU work."))

        if isinstance(vina_reference, str) and isinstance(vina_fusion, str) and "igem.scoring.docking_penalty" in available_tools:
            steps.append(PlanStep(step_id="score_docking", objective="Compare wild-type and fusion docking outputs.", tool_name="igem.scoring.docking_penalty", arguments={"candidate_id": task.inputs.get("candidate_id", task.task_id), "reference_vina_output": vina_reference, "fusion_vina_output": vina_fusion}, depends_on=_dependencies(steps), priority=80, rationale="Use existing Vina results before proposing new docking."))

        if any(token in objective for token in ("ode", "timing", "oc", "dmt", "glabridin")) and "igem.scoring.m4_piecewise_ode" in available_tools:
            steps.append(PlanStep(step_id="simulate_timing", objective="Run OC-first/DMT-later piecewise ODE using explicit assumptions.", tool_name="igem.scoring.m4_piecewise_ode", arguments={"candidate_id": task.inputs.get("candidate_id", task.task_id), "params": task.inputs.get("ode_params", {}), "oc_gate": task.inputs.get("oc_gate", {}), "dmt_gate": task.inputs.get("dmt_gate", {})}, depends_on=_dependencies(steps), priority=60, rationale="The ODE is cheap and provides a testable timing hypothesis, not an absolute yield claim."))

        if not steps:
            steps.append(PlanStep(step_id="collect_missing_inputs", objective="Identify missing construct, structure, kinetic, and wet-lab inputs.", rationale="No executable artifact paths were supplied; agent must not invent data.", status="blocked"))
        return Plan(task_id=task.task_id, steps=steps)


class Planner:
    """Task-to-DAG compiler with deterministic default and pluggable LLM backend."""

    def __init__(self, registry: ToolRegistry | None = None, backend: PlanningBackend | None = None) -> None:
        self.registry = registry
        self.backend = backend or RuleBasedDryLabPlanner()

    def create_plan(self, task: AgentTask, context: ContextBundle | None = None) -> Plan:
        context = context or ContextBundle(task=task, constraints=list(task.constraints))
        tools = set(self.registry.names()) if self.registry else set()
        plan = self.backend.create_plan(task, context, tools)
        self._validate(plan, tools)
        return plan

    @staticmethod
    def _validate(plan: Plan, available_tools: set[str]) -> None:
        ids = [step.step_id for step in plan.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("Planner produced duplicate step IDs")
        for step in plan.steps:
            if step.tool_name and step.tool_name not in available_tools:
                raise ValueError(f"Planner selected unavailable tool: {step.tool_name}")
            unknown = set(step.depends_on) - set(ids)
            if unknown:
                raise ValueError(f"Step '{step.step_id}' has unknown dependencies: {sorted(unknown)}")
        _assert_acyclic(plan)


def _dependencies(steps: list[PlanStep]) -> list[str]:
    return [steps[-1].step_id] if steps else []


def _assert_acyclic(plan: Plan) -> None:
    dependencies = {step.step_id: set(step.depends_on) for step in plan.steps}
    resolved: set[str] = set()
    while dependencies:
        ready = [step_id for step_id, parents in dependencies.items() if parents <= resolved]
        if not ready:
            raise ValueError("Planner produced a cyclic dependency graph")
        for step_id in ready:
            resolved.add(step_id)
            dependencies.pop(step_id)

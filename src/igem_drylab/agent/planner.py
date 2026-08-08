from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from igem_drylab.mcp import ToolRegistry
from igem_drylab.pipeline import load_config
from igem_drylab.parameters import ParameterRegistry, m4_requirements

from .context import ContextBundle
from .models import AgentTask, Plan, PlanStep, ResultBinding, ResultCondition


class PlanningBackend(Protocol):
    def create_plan(self, task: AgentTask, context: ContextBundle, available_tools: set[str]) -> Plan: ...


class RuleBasedDryLabPlanner:
    """Conservative project-specific planner used when no LLM planner is configured.

    It prefers existing artifacts and cheap checks. It never schedules a heavy
    prediction merely because an objective mentions protein structure.
    """

    def create_plan(self, task: AgentTask, context: ContextBundle, available_tools: set[str]) -> Plan:
        """Choose a bounded next-step DAG from explicit inputs.

        This is intentionally a *selector*, not a free-form scientific author.
        It reuses files first, only schedules new compute after an explicit
        request, and binds numerical outputs between compatible local tools.
        """
        steps: list[PlanStep] = []
        inputs = task.inputs
        candidate_id = _string_or(inputs.get("candidate_id"), task.task_id)
        config_path = inputs.get("config_path")
        config = _load_config_if_present(config_path)
        validate_dependencies: list[str] = []
        if isinstance(config_path, str) and "igem.pipeline.validate" in available_tools:
            steps.append(
                PlanStep(
                    step_id="validate_config",
                    objective="Validate the project configuration before scientific work.",
                    tool_name="igem.pipeline.validate",
                    arguments={"config_path": config_path},
                    priority=100,
                    rationale="Invalid configuration invalidates later results.",
                )
            )
            validate_dependencies = ["validate_config"]

        self._select_literature_qa(inputs, available_tools, validate_dependencies, steps)
        self._select_missing_parameter_evidence(task, config, available_tools, validate_dependencies, steps)

        structure_step = self._select_structure_step(task, available_tools, config, candidate_id, validate_dependencies, steps)
        fth1_step = self._select_fth1_expansion(inputs, available_tools, structure_step, steps)
        sasa_step = self._select_pocket_sasa(inputs, available_tools, structure_step, steps)
        m2_step = self._select_m2_score(inputs, available_tools, candidate_id, sasa_step, structure_step, steps)
        docking_step = self._select_docking(task, available_tools, config, candidate_id, m2_step, validate_dependencies, steps)
        self._select_ode(task, available_tools, candidate_id, m2_step, docking_step, steps)

        if not steps:
            steps.append(
                PlanStep(
                    step_id="collect_missing_inputs",
                    objective="Identify missing construct, structure, kinetic, and wet-lab inputs.",
                    rationale="No executable artifact paths were supplied; agent must not invent data.",
                    status="blocked",
                )
            )
        return Plan(task_id=task.task_id, steps=steps)

    @staticmethod
    def _select_missing_parameter_evidence(task: AgentTask, config: Any, available_tools: set[str], dependencies: list[str], steps: list[PlanStep]) -> None:
        """Route missing declared M4 inputs to registry/evidence, never invent values."""
        objective = task.objective.lower()
        requested = task.inputs.get("target_stage") == "m4" or any(token in objective for token in ("dmt", "glabridin", "timing", "kinetic"))
        if config is None or not requested or "igem.parameters.resolve" not in available_tools:
            return
        registry = ParameterRegistry(config.parameters)
        missing = [item.name for item in m4_requirements() if registry.resolve(item, allow_assumptions=config.execution.allow_assumptions).status != "resolved"]
        max_queries = int(task.inputs.get("max_literature_queries", 3))
        evidence_path = task.inputs.get("evidence_database_path")
        for index, name in enumerate(missing[:max_queries]):
            resolve_id = f"resolve_{name}"
            steps.append(PlanStep(step_id=resolve_id, objective=f"Resolve approved parameter '{name}' from the registry.", tool_name="igem.parameters.resolve", arguments={"config_path": task.inputs.get("config_path"), "stage": "m4", "requirement_name": name}, depends_on=dependencies, priority=96, rationale="Only approved, identity-compatible registry records can enter real M4."))
            if isinstance(evidence_path, str) and "igem.literature.qa" in available_tools:
                steps.append(PlanStep(step_id=f"find_evidence_{name}", objective=f"Retrieve local evidence relevant to missing parameter '{name}'.", tool_name="igem.literature.qa", arguments={"question": f"Find evidence for parameter {name}; preserve enzyme/substrate/condition identity and DOI.", "evidence_path": evidence_path, "top_k": 5}, depends_on=[resolve_id], run_conditions=[ResultCondition(source_step_id=resolve_id, source_path=["structuredContent", "resolution", "status"], allowed_values=["missing", "conflict", "needs_review"])], priority=90, rationale="Evidence retrieval creates a review candidate, never an automatic parameter update."))
        if missing:
            steps.append(PlanStep(step_id="review_missing_parameters", objective="Review compatible evidence or request wet-lab measurement for unresolved M4 parameters.", depends_on=[step.step_id for step in steps if step.step_id.startswith("find_evidence_")], priority=85, status="blocked", rationale="Human approval is required before literature evidence becomes an approved model parameter."))

    @staticmethod
    def _select_literature_qa(
        inputs: dict[str, Any], available_tools: set[str], validate_dependencies: list[str], steps: list[PlanStep]
    ) -> None:
        """Retrieve only from an explicit local evidence file; no implicit LLM call."""
        evidence_path = inputs.get("evidence_database_path")
        question = inputs.get("literature_question")
        if not isinstance(evidence_path, str) or not isinstance(question, str) or not question.strip():
            return
        if "igem.literature.qa" not in available_tools:
            return
        steps.append(PlanStep(
            step_id="query_literature_evidence",
            objective="Retrieve DOI-linked local evidence for the stated literature question.",
            tool_name="igem.literature.qa",
            arguments={"question": question, "evidence_path": evidence_path, "top_k": int(inputs.get("literature_top_k", 5))},
            depends_on=validate_dependencies,
            priority=95,
            rationale="Retrieval returns quoted evidence and provenance; it does not validate a kinetic parameter.",
        ))

    @staticmethod
    def _select_structure_step(
        task: AgentTask, available_tools: set[str], config: Any, candidate_id: str, validate_dependencies: list[str], steps: list[PlanStep]
    ) -> str | None:
        existing = task.inputs.get("structure_output_path")
        if isinstance(existing, str) and "igem.parsers.structure_prediction" in available_tools:
            steps.append(PlanStep(
                step_id="parse_structure", objective="Parse existing ColabFold confidence artifacts.",
                tool_name="igem.parsers.structure_prediction", arguments={"path": existing, "candidate_id": candidate_id},
                depends_on=validate_dependencies, priority=90,
                rationale="Reuse existing structure output before scheduling new GPU work.",
            ))
            return "parse_structure"

        input_file = task.inputs.get("structure_input_file")
        if not isinstance(input_file, str) or not task.inputs.get("allow_new_compute", False):
            return None
        if "igem.compute.run_tool" not in available_tools or not _tool_enabled(config, "colabfold"):
            steps.append(PlanStep(
                step_id="configure_colabfold", objective="Configure ColabFold before requesting a new structure prediction.",
                rationale="A new prediction was explicitly requested but ColabFold is not enabled in the YAML configuration.", status="blocked",
            ))
            return None
        output_dir = str(Path(task.artifacts_dir) / candidate_id / "colabfold")
        steps.append(PlanStep(
            step_id="run_colabfold", objective="Run one local ColabFold prediction for the supplied construct.",
            tool_name="igem.compute.run_tool",
            arguments={"config_path": task.inputs.get("config_path"), "tool_name": "colabfold", "output_dir": output_dir,
                       "context": {"input_file": input_file}, "justification": "No reusable structure output was supplied."},
            depends_on=validate_dependencies, resources=["gpu"], estimated_gpu_minutes=60, priority=85,
            rationale="GPU prediction is limited to an explicit construct and requires human approval.",
        ))
        if "igem.parsers.structure_prediction" in available_tools:
            steps.append(PlanStep(
                step_id="parse_structure", objective="Parse the newly generated ColabFold confidence artifacts.",
                tool_name="igem.parsers.structure_prediction", arguments={"path": output_dir, "candidate_id": candidate_id},
                depends_on=["run_colabfold"], priority=80,
                rationale="Only parse a prediction after its run succeeds.",
            ))
            return "parse_structure"
        return "run_colabfold"

    @staticmethod
    def _select_fth1_expansion(inputs: dict[str, Any], available_tools: set[str], structure_step: str | None, steps: list[PlanStep]) -> str | None:
        request = inputs.get("fth1_expansion")
        if not isinstance(request, dict) or "igem.multichain.expand_fth1_arms" not in available_tools:
            return None
        arguments = dict(request)
        arguments.setdefault("output_pdb", str(Path(inputs.get("artifacts_dir", "outputs/agent_runs")) / "fth1_expanded.pdb"))
        steps.append(PlanStep(
            step_id="expand_fth1_arms", objective="Map a local fusion arm onto the FTH1 24-mer template and screen geometric clashes.",
            tool_name="igem.multichain.expand_fth1_arms", arguments=arguments,
            depends_on=[structure_step] if structure_step else [], priority=75,
            rationale="This is a geometric crowding screen, not a claim that the condensate forms.",
        ))
        return "expand_fth1_arms"

    @staticmethod
    def _select_pocket_sasa(inputs: dict[str, Any], available_tools: set[str], structure_step: str | None, steps: list[PlanStep]) -> str | None:
        request = inputs.get("pocket_sasa")
        if not isinstance(request, dict) or "igem.scoring.pocket_sasa" not in available_tools:
            return None
        if not isinstance(request.get("chain"), str) or not isinstance(request.get("residues"), list):
            return None
        steps.append(PlanStep(
            step_id="score_pocket_sasa", objective="Calculate active-pocket SASA retention for the supplied fusion and reference structures.",
            tool_name="igem.scoring.pocket_sasa", arguments=dict(request),
            depends_on=[structure_step] if structure_step else [], priority=70,
            rationale="A pocket-accessibility screen is cheaper than docking and should run first.",
        ))
        return "score_pocket_sasa"

    @staticmethod
    def _select_m2_score(inputs: dict[str, Any], available_tools: set[str], candidate_id: str, sasa_step: str | None, structure_step: str | None, steps: list[PlanStep]) -> str | None:
        metrics = inputs.get("m2_metrics")
        if not isinstance(metrics, dict) or "igem.scoring.m2_structure" not in available_tools:
            return None
        arguments = {"candidate_id": candidate_id, **metrics}
        bindings = []
        dependencies = [item for item in (structure_step, sasa_step) if item]
        if sasa_step:
            bindings.append(ResultBinding(target_step_id="score_m2", target_argument="sasa_retention", source_path=["structuredContent", "result", "sasa_retention"]))
        steps.append(PlanStep(
            step_id="score_m2", objective="Apply the transparent M2 fusion-compatibility screen.",
            tool_name="igem.scoring.m2_structure", arguments=arguments, depends_on=dependencies,
            priority=65, rationale="Only candidates passing activity, clash, and confidence checks proceed to docking.",
        ))
        if bindings:
            next(step for step in steps if step.step_id == sasa_step).result_bindings.extend(bindings)
        return "score_m2"

    @staticmethod
    def _select_docking(
        task: AgentTask, available_tools: set[str], config: Any, candidate_id: str, m2_step: str | None,
        validate_dependencies: list[str], steps: list[PlanStep]
    ) -> str | None:
        conditions = _m2_conditions(m2_step)
        reference = task.inputs.get("reference_vina_output")
        fusion = task.inputs.get("fusion_vina_output")
        if isinstance(reference, str) and isinstance(fusion, str) and "igem.scoring.docking_penalty" in available_tools:
            steps.append(PlanStep(
                step_id="score_docking", objective="Compare existing wild-type and fusion Vina results.",
                tool_name="igem.scoring.docking_penalty",
                arguments={"candidate_id": candidate_id, "reference_vina_output": reference, "fusion_vina_output": fusion},
                depends_on=[item for item in (*validate_dependencies, m2_step) if item], run_conditions=conditions,
                priority=60, rationale="Dock only candidates that pass the M2 negative screen.",
            ))
            return "score_docking"

        request = task.inputs.get("docking_request")
        if not isinstance(request, dict) or not _tool_enabled(config, "autodock_vina") or "igem.compute.run_tool" not in available_tools:
            return None
        reference_config = request.get("reference_config_file")
        fusion_config = request.get("fusion_config_file")
        if not isinstance(reference_config, str) or not isinstance(fusion_config, str):
            return None
        root = Path(task.artifacts_dir) / candidate_id / "vina"
        run_steps: list[str] = []
        for label, config_file in (("reference", reference_config), ("fusion", fusion_config)):
            step_id = f"run_vina_{label}"
            run_steps.append(step_id)
            steps.append(PlanStep(
                step_id=step_id, objective=f"Run local AutoDock Vina for the {label} enzyme model.",
                tool_name="igem.compute.run_tool",
                arguments={"config_path": task.inputs.get("config_path"), "tool_name": "autodock_vina", "output_dir": str(root / label),
                           "context": {"config_file": config_file}, "justification": "No reusable Vina output was supplied."},
                depends_on=[item for item in (*validate_dependencies, m2_step) if item], run_conditions=conditions,
                priority=55, rationale="Vina is run only after M2 passes and only for the requested pair.",
            ))
        if "igem.scoring.docking_penalty" in available_tools:
            steps.append(PlanStep(
                step_id="score_docking", objective="Compare the two newly generated Vina pose tables.",
                tool_name="igem.scoring.docking_penalty",
                arguments={"candidate_id": candidate_id, "reference_vina_output": str(root / "reference" / "vina_stdout.txt"),
                           "fusion_vina_output": str(root / "fusion" / "vina_stdout.txt")},
                depends_on=run_steps, priority=50, rationale="Use captured Vina stdout only after both docking jobs succeed.",
            ))
            return "score_docking"
        return None

    @staticmethod
    def _select_ode(task: AgentTask, available_tools: set[str], candidate_id: str, m2_step: str | None, docking_step: str | None, steps: list[PlanStep]) -> None:
        objective = task.objective.lower()
        if not any(token in objective for token in ("ode", "timing", "simulate", "simulation", "时序", "动力学")):
            return
        if "igem.pipeline.run_stage" not in available_tools or not isinstance(task.inputs.get("config_path"), str):
            return
        steps.append(PlanStep(step_id="run_production_m4", objective="Run the production five-state glabridin M4 from reviewed project configuration.", tool_name="igem.pipeline.run_stage", arguments={"config_path": task.inputs["config_path"], "stage": "m4", "output_dir": str(Path(task.artifacts_dir) / candidate_id / "production_m4")}, priority=45, rationale="Agent reuses pipeline PT 9→10, OC 10→11, DMT 9→13/11→15 implementation; it does not use the generic four-state ODE."))


def _load_config_if_present(config_path: object) -> Any | None:
    if not isinstance(config_path, str) or not Path(config_path).is_file():
        return None
    return load_config(Path(config_path))


def _tool_enabled(config: Any, tool_name: str) -> bool:
    tool = config.tools.get(tool_name) if config is not None else None
    return bool(tool and tool.enabled and tool.command)


def _string_or(value: object, fallback: str) -> str:
    return value if isinstance(value, str) and value else fallback


def _m2_conditions(m2_step: str | None) -> list[ResultCondition]:
    if not m2_step:
        return []
    return [ResultCondition(source_step_id=m2_step, source_path=["structuredContent", "result", "recommended_for_m3"], allowed_values=[True])]


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

"""LLM semantic-decision backend followed by deterministic plan compilation."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

from igem_drylab.literature.llm import ChatClient

from .context import ContextBundle
from .decision import PlanningDecision
from .env import load_local_env
from .models import AgentTask, Plan
from .plan_compiler import DeterministicPlanCompiler


@dataclass(frozen=True)
class HybridLLMPlanningBackend:
    """LLM understands semantic changes; compiler exclusively owns tool DAGs."""
    client: ChatClient
    compiler: DeterministicPlanCompiler = DeterministicPlanCompiler()

    @classmethod
    def from_environment(cls, *, api_base: str, model: str, api_key_env: str) -> "HybridLLMPlanningBackend":
        load_local_env(); key = os.getenv(api_key_env)
        if not key: raise ValueError(f"Environment variable '{api_key_env}' is not set")
        return cls(ChatClient(api_key=key, api_base=api_base, model=model, temperature=0.0, timeout_seconds=45, retries=1))

    def create_plan(self, task: AgentTask, context: ContextBundle, available_tools: set[str]) -> Plan:
        schema = PlanningDecision.model_json_schema()
        prompt = {
            "system": "You are the semantic decision layer of a conservative dry-lab agent. Return JSON only. You classify what changed; you never choose tools, commands, dependencies, resources, numeric values, paths, sequences, or scientific results.",
            "task": task.model_dump(mode="json"),
            "context": {"constraints": context.constraints, "artifacts": context.artifact_summaries, "conflicts": context.conflicts},
            "rules": ["Use only enums in the supplied schema.", "Do not invent parameters, evidence, sequences, paths, residues, concentrations, rates, or wet-lab results.", "Docking/structure evidence never modifies kinetics.", "Invalid artifacts are never reusable.", "Author-native sensitivity is not physical titer.", "Gold labels are not available."],
            "planning_decision_schema": schema,
        }
        telemetry: dict[str, object] = {"architecture": "hybrid", "api_call_succeeded": False, "json_parse_succeeded": False, "schema_valid_first_attempt": False, "schema_valid_after_repair": False, "repair_attempted": False, "schema_error": None, "response_format": "json_object", "structured_output_method": "OpenAI-compatible JSON Output"}
        payload = self._call(prompt); telemetry["api_call_succeeded"] = telemetry["json_parse_succeeded"] = True
        try:
            decision = PlanningDecision.model_validate(payload); telemetry["schema_valid_first_attempt"] = True
        except Exception as error:
            telemetry["schema_error"] = str(error); telemetry["repair_attempted"] = True
            repair = {"system": "Repair this JSON once. Return only a PlanningDecision matching the schema; do not add facts.", "invalid_json": payload, "validation_error": str(error), "planning_decision_schema": schema}
            repaired = self._call(repair)
            try: decision = PlanningDecision.model_validate(repaired); telemetry["schema_valid_after_repair"] = True
            except Exception as repair_error: raise ValueError(f"Hybrid PlanningDecision rejected after one repair: {repair_error}") from repair_error
        plan = self.compiler.compile(task, decision)
        diagnostics = {**telemetry, "planning_decision": decision.model_dump(mode="json")}
        return plan.model_copy(update={"diagnostics": diagnostics})

    def _call(self, prompt: dict[str, object]) -> dict[str, object]:
        try: return self.client.complete_json(json.dumps(prompt, ensure_ascii=False), response_format={"type": "json_object"})
        except TypeError: return self.client.complete_json(json.dumps(prompt, ensure_ascii=False))

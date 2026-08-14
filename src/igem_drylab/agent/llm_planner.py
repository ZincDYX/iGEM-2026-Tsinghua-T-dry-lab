from __future__ import annotations

import json
import os
from dataclasses import dataclass

from igem_drylab.literature.llm import ChatClient

from .context import ContextBundle
from .env import load_local_env
from .models import AgentTask, Plan, PlanStep


@dataclass(frozen=True)
class OpenAICompatiblePlanningBackend:
    """Optional LLM planner with a strict JSON contract.

    This backend is optional because a language model can propose a plan but
    cannot be trusted to bypass planner validation, budget rules, approval, or
    deterministic scientific checks.
    """

    client: ChatClient

    @classmethod
    def from_environment(cls, *, api_base: str, model: str, api_key_env: str = "DEEPSEEK_API_KEY") -> "OpenAICompatiblePlanningBackend":
        load_local_env()
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"Environment variable '{api_key_env}' is not set")
        # A planning response is compact; fail promptly instead of allowing one
        # unhealthy provider request to stall an entire benchmark suite.
        return cls(ChatClient(api_key=api_key, api_base=api_base, model=model, temperature=0.0, timeout_seconds=45, retries=1))

    def create_plan(self, task: AgentTask, context: ContextBundle, available_tools: set[str]) -> Plan:
        # Use the generated *actual* step schema, wrapped in the small Plan
        # envelope needed by this endpoint.  Sending the complete recursive
        # Pydantic document made Flash requests needlessly slow in v2 trials.
        schema = {"type": "object", "required": ["task_id", "steps"], "properties": {"task_id": {"type": "string"}, "steps": {"type": "array", "items": PlanStep.model_json_schema()}}}
        example = {
            "task_id": task.task_id,
            "steps": [{"step_id": "collect_missing_inputs", "objective": "Request a missing FASTA path.", "tool_name": None, "arguments": {}, "depends_on": [], "required_artifact_ids": [], "produces": [], "run_conditions": [], "result_bindings": [], "resources": ["cpu"], "priority": 50, "estimated_gpu_minutes": 0.0, "estimated_api_calls": 0, "retry_limit": 1, "attempts": 0, "status": "blocked", "rationale": "A required input is absent."}],
        }
        prompt = {
            "role": "You are a conservative dry-lab planning component.",
            "task": task.model_dump(mode="json"),
            "available_tools": sorted(available_tools),
            "context": {
                "constraints": context.constraints,
                "memory": context.retrieved_memory,
                "artifacts": context.artifact_summaries,
                "conflicts": context.conflicts,
            },
            "rules": [
                "Return one JSON object that validates against the supplied schema.",
                "DO NOT use 'id'; use 'step_id'. DO NOT use 'tool'; use 'tool_name'.",
                "Arrays must be [] rather than null; resources must be an array.",
                "Prefer parsing existing artifacts over scheduling new compute.",
                "Do not invent paths, kinetic parameters, residues, or wet-lab measurements.",
                "Mark external API or expensive GPU steps with appropriate resources and estimates.",
                "Do not claim absolute yield or LLPS proof.",
            ],
            "json_schema": schema,
            "minimal_valid_example": example,
        }
        telemetry: dict[str, object] = {"api_call_succeeded": False, "json_parse_succeeded": False, "schema_valid_first_attempt": False, "schema_error": None, "repair_attempted": False, "schema_valid_after_repair": False, "response_format": "json_object", "structured_output_method": "OpenAI-compatible JSON Output"}
        try:
            payload = self.client.complete_json(json.dumps(prompt, ensure_ascii=False), response_format={"type": "json_object"})
            telemetry["api_call_succeeded"] = telemetry["json_parse_succeeded"] = True
        except TypeError:  # Minimal test doubles predating the optional argument.
            payload = self.client.complete_json(json.dumps(prompt, ensure_ascii=False))
            telemetry["api_call_succeeded"] = telemetry["json_parse_succeeded"] = True
        try:
            plan = Plan.model_validate({"task_id": task.task_id, "steps": payload.get("steps")})
            telemetry["schema_valid_first_attempt"] = True
            return plan.model_copy(update={"diagnostics": telemetry})
        except Exception as exc:
            telemetry["schema_error"] = str(exc)
        telemetry["repair_attempted"] = True
        repair = {"role": "Repair invalid plan JSON once. Return JSON only.", "invalid_json": payload, "validation_error": telemetry["schema_error"], "json_schema": schema, "rules": ["Use exact field names.", "Do not add facts, paths, parameter values, or benchmark expectations."]}
        try:
            repaired = self.client.complete_json(json.dumps(repair, ensure_ascii=False), response_format={"type": "json_object"})
        except TypeError:
            repaired = self.client.complete_json(json.dumps(repair, ensure_ascii=False))
        telemetry["api_call_succeeded"] = telemetry["json_parse_succeeded"] = True
        try:
            plan = Plan.model_validate({"task_id": task.task_id, "steps": repaired.get("steps")})
        except Exception as exc:
            telemetry["schema_error"] = str(exc)
            raise ValueError(f"LLM plan schema rejected after one repair: {exc}") from exc
        telemetry["schema_valid_after_repair"] = True
        return plan.model_copy(update={"diagnostics": telemetry})

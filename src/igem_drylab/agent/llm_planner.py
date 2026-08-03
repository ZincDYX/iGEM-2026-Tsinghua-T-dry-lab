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
        return cls(ChatClient(api_key=api_key, api_base=api_base, model=model))

    def create_plan(self, task: AgentTask, context: ContextBundle, available_tools: set[str]) -> Plan:
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
                "Return JSON only: {steps:[PlanStep-compatible objects]}.",
                "Prefer parsing existing artifacts over scheduling new compute.",
                "Do not invent paths, kinetic parameters, residues, or wet-lab measurements.",
                "Mark external API or expensive GPU steps with appropriate resources and estimates.",
                "Do not claim absolute yield or LLPS proof.",
            ],
        }
        payload = self.client.complete_json(json.dumps(prompt, ensure_ascii=False))
        raw_steps = payload.get("steps")
        if not isinstance(raw_steps, list) or not raw_steps:
            raise ValueError("LLM planner response requires a non-empty 'steps' list")
        return Plan(task_id=task.task_id, steps=[PlanStep.model_validate(item) for item in raw_steps])

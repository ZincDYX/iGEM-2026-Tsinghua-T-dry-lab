from __future__ import annotations

import json
from typing import Any

from .icl import IclExample, select_icl_examples
from .llm import ChatClient
from .schema import ExtractionSchema


def build_prompt(
    *,
    text: str,
    schema: ExtractionSchema,
    examples: list[IclExample],
    icl_top_k: int = 3,
) -> str:
    selected = select_icl_examples(
        examples,
        text,
        schema.metrics,
        domain=schema.domain,
        k=icl_top_k,
    )
    parts = [
        "You are an information extraction assistant.",
        "Extract experimental records, not just article-level summaries.",
        "A record corresponds to one enzyme or mutant, one substrate, one reaction system, one set of reaction conditions, and one set of results.",
        "Split records when enzyme, mutant, substrate, temperature, pH, time, LLPS state, or reaction system differs.",
        "Requested metrics: " + ", ".join(schema.metrics),
    ]
    if schema.instructions:
        parts.append("Schema instructions:\n" + "\n".join(f"- {item}" for item in schema.instructions))
    if selected:
        parts.append("Examples:")
        for example in selected:
            if example.instruction:
                parts.append("Instruction:\n" + example.instruction)
            parts.append("Context:\n" + example.context)
            parts.append("Expected JSON:\n" + json.dumps({"records": [example.output]}, ensure_ascii=False))
    parts.append("Text:\n" + text)
    parts.append(
        'Return JSON only as {"records": [<record>, ...]}. '
        "Each record must use keys exactly matching requested metric names. "
        'Each metric value is an object: {"value": <string_or_number|null>, "unit": <string|null>, "evidence": <string|null>}. '
        'If the article contains no extractable experimental record, return {"records": []}.'
    )
    return "\n\n".join(parts)


def extract_records_from_text(
    *,
    text: str,
    schema: ExtractionSchema,
    examples: list[IclExample],
    client: ChatClient,
    icl_top_k: int = 3,
) -> list[dict[str, Any]]:
    prompt = build_prompt(text=text, schema=schema, examples=examples, icl_top_k=icl_top_k)
    payload = client.complete_json(prompt)
    records = payload.get("records", [])
    if not isinstance(records, list):
        raise ValueError("LLM JSON must contain a list field named records")
    return [record for record in records if isinstance(record, dict)]

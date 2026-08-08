"""Bounded, provenance-preserving extraction for long literature texts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Protocol

from .extractor import extract_records_from_text
from .icl import IclExample
from .schema import ExtractionSchema


class JsonCompletionClient(Protocol):
    def complete_json(self, prompt: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ExtractedRecord:
    """One model-extracted record and the text span needed to audit it."""

    record_id: str
    record: dict[str, Any]
    source_id: str
    chunk_index: int
    text_hash: str
    validation_status: str
    validation_errors: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "record": self.record,
            "source_id": self.source_id,
            "chunk_index": self.chunk_index,
            "text_hash": self.text_hash,
            "validation_status": self.validation_status,
            "validation_errors": list(self.validation_errors),
        }


def chunk_text(text: str, *, max_characters: int = 12_000, overlap_characters: int = 800) -> list[str]:
    """Split near paragraph boundaries with a deterministic overlap."""
    if max_characters < 200:
        raise ValueError("max_characters must be at least 200")
    if overlap_characters < 0:
        raise ValueError("overlap_characters must be >= 0")
    # A caller may lower max_characters while retaining the public default 800.
    # Clamp only this geometrically impossible overlap rather than failing a run.
    overlap_characters = min(overlap_characters, max_characters // 4)
    cleaned = text.strip()
    if not cleaned:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + max_characters)
        if end < len(cleaned):
            boundary = max(cleaned.rfind("\n\n", start + max_characters // 2, end), cleaned.rfind(". ", start + max_characters // 2, end))
            if boundary > start:
                end = boundary + 1
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned):
            break
        start = max(end - overlap_characters, start + 1)
    return chunks


def validate_record(record: dict[str, Any], schema: ExtractionSchema) -> tuple[str, tuple[str, ...]]:
    """Validate the public metric contract without silently changing model output."""
    errors: list[str] = []
    unexpected = sorted(set(record) - set(schema.metrics))
    if unexpected:
        errors.append("unexpected keys: " + ", ".join(unexpected))
    for metric in schema.metrics:
        value = record.get(metric)
        if value is None:
            continue
        if not isinstance(value, dict):
            errors.append(f"{metric}: expected an object with value/unit/evidence")
            continue
        missing = {"value", "unit", "evidence"} - set(value)
        if missing:
            errors.append(f"{metric}: missing " + ", ".join(sorted(missing)))
    return ("valid" if not errors else "needs_review", tuple(errors))


def extract_records_chunked(
    *,
    text: str,
    schema: ExtractionSchema,
    examples: list[IclExample],
    client: JsonCompletionClient,
    source_id: str = "",
    max_characters: int = 12_000,
    overlap_characters: int = 800,
    icl_top_k: int = 3,
    repair_invalid: bool = False,
) -> list[ExtractedRecord]:
    """Extract records per chunk and remove exact duplicate model outputs.

    This function deliberately labels malformed outputs ``needs_review`` rather
    than inventing units, values, or evidence text.  It is therefore suitable
    for making a review queue, not for treating an LLM output as a database.
    """
    results: list[ExtractedRecord] = []
    seen: set[str] = set()
    for index, chunk in enumerate(chunk_text(text, max_characters=max_characters, overlap_characters=overlap_characters)):
        records = extract_records_from_text(text=chunk, schema=schema, examples=examples, client=client, icl_top_k=icl_top_k)
        for record in records:
            status, errors = validate_record(record, schema)
            if status != "valid" and repair_invalid:
                repaired = _repair_record(record, schema, client)
                if repaired is not None:
                    record = repaired
                    status, errors = validate_record(record, schema)
            canonical = _canonical(record)
            if canonical in seen:
                continue
            seen.add(canonical)
            digest = hashlib.sha256(f"{source_id}|{index}|{canonical}".encode("utf-8")).hexdigest()[:16]
            results.append(ExtractedRecord(
                record_id=f"llm-{digest}", record=record, source_id=source_id,
                chunk_index=index, text_hash=hashlib.sha256(chunk.encode("utf-8")).hexdigest(),
                validation_status=status, validation_errors=errors,
            ))
    return results


def _repair_record(record: dict[str, Any], schema: ExtractionSchema, client: JsonCompletionClient) -> dict[str, Any] | None:
    """Ask once for syntactic repair only; no missing scientific value may be inferred."""
    import json

    prompt = (
        "Return JSON only. Repair this extraction record to the requested metric keys. "
        "Do not infer missing values, units, or evidence; use null instead. Each present metric must be "
        '{"value": ..., "unit": ..., "evidence": ...}.\nRequested metrics: '
        + ", ".join(schema.metrics)
        + "\nRecord:\n"
        + json.dumps(record, ensure_ascii=False)
    )
    payload = client.complete_json(prompt)
    candidate = payload.get("record", payload)
    return candidate if isinstance(candidate, dict) else None


def _canonical(record: dict[str, Any]) -> str:
    import json

    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

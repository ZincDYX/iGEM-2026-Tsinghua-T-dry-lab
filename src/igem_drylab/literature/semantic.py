"""Optional OpenAI-compatible embedding backend for literature QA.

The deterministic QA path never imports a local model or requires this module's
environment variables. Embeddings are cached beside the evidence file so a
query sends only its own text after the initial cache build.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import requests


class SemanticBackendError(RuntimeError):
    """Raised when an optional embedding service cannot be used."""


@dataclass(frozen=True)
class EmbeddingApiBackend:
    """Small client for an OpenAI-compatible embeddings endpoint."""

    api_base: str
    api_key: str
    model: str
    timeout_seconds: int = 30

    @property
    def cache_identity(self) -> str:
        return self.model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = requests.post(
                self.api_base,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "input": list(texts)},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            rows = response.json().get("data", [])
        except (requests.RequestException, ValueError, AttributeError) as exc:
            raise SemanticBackendError(f"embedding request failed: {exc}") from exc
        vectors = [row.get("embedding") for row in sorted(rows, key=lambda row: row.get("index", 0))]
        if len(vectors) != len(texts) or any(not _valid_vector(vector) for vector in vectors):
            raise SemanticBackendError("embedding response did not contain one numeric vector per input")
        return [[float(value) for value in vector] for vector in vectors]


def backend_from_environment() -> EmbeddingApiBackend | None:
    """Return a backend only when all explicit QA embedding variables exist."""
    api_base = os.getenv("QA_EMBEDDING_API_BASE")
    api_key = os.getenv("QA_EMBEDDING_API_KEY")
    model = os.getenv("QA_EMBEDDING_MODEL")
    if not all((api_base, api_key, model)):
        return None
    return EmbeddingApiBackend(api_base=api_base, api_key=api_key, model=model)


def evidence_fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cache_path_for(evidence_path: Path) -> Path:
    return evidence_path.with_suffix(evidence_path.suffix + ".qa_embeddings.json")


def embedding_cache_key(record_id: str, model: str, index_text: str) -> str:
    digest = hashlib.sha256(index_text.encode("utf-8")).hexdigest()
    return f"{model}:{record_id}:{digest}"


def load_incremental_embedding_cache(evidence_path: Path) -> dict[str, list[float]]:
    """Read record-scoped vectors; invalid entries are ignored independently."""
    path = cache_path_for(evidence_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries = payload.get("record_vectors", {})
    except (OSError, ValueError, AttributeError):
        return {}
    return {key: [float(item) for item in value] for key, value in entries.items() if isinstance(key, str) and _valid_vector(value)}


def write_incremental_embedding_cache(evidence_path: Path, entries: dict[str, list[float]]) -> None:
    """Atomically persist only successfully obtained record-scoped vectors."""
    path = cache_path_for(evidence_path)
    previous = load_incremental_embedding_cache(evidence_path)
    previous.update(entries)
    payload = {"metadata": {"source_path": str(evidence_path.resolve()), "format": "record_scoped_v1"}, "record_vectors": previous}
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload), encoding="utf-8")
    temporary.replace(path)


def load_embedding_cache(evidence_path: Path, *, fingerprint: str, model: str, record_ids: list[str]) -> list[list[float]] | None:
    path = cache_path_for(evidence_path)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        metadata = payload["metadata"]
        vectors = payload["vectors"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if (
        metadata.get("source_path") != str(evidence_path.resolve())
        or metadata.get("source_fingerprint") != fingerprint
        or metadata.get("model") != model
        or metadata.get("record_ids") != record_ids
        or not isinstance(vectors, list)
        or not vectors
        or any(not _valid_vector(vector) for vector in vectors)
    ):
        return None
    dimension = metadata.get("dimensions")
    if not isinstance(dimension, int) or any(len(vector) != dimension for vector in vectors):
        return None
    return [[float(value) for value in vector] for vector in vectors]


def write_embedding_cache(evidence_path: Path, *, fingerprint: str, model: str, record_ids: list[str], vectors: list[list[float]]) -> None:
    if not vectors or any(not _valid_vector(vector) for vector in vectors):
        raise SemanticBackendError("cannot cache invalid embedding vectors")
    payload = {
        "metadata": {
            "source_path": str(evidence_path.resolve()),
            "source_fingerprint": fingerprint,
            "model": model,
            "dimensions": len(vectors[0]),
            "record_ids": record_ids,
        },
        "vectors": vectors,
    }
    cache_path_for(evidence_path).write_text(json.dumps(payload), encoding="utf-8")


def _valid_vector(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, (int, float)) for item in value)

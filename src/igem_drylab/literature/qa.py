"""Hybrid, provenance-preserving retrieval for local literature evidence.

This module intentionally keeps retrieval separate from parameter approval.
BM25 and metadata conditioning always work offline. Semantic retrieval and LLM
synthesis are optional enhancements that fail closed to the deterministic path.
"""

from __future__ import annotations

import csv
import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence

from .llm import ChatClient, LlmError
from .semantic import (
    EmbeddingApiBackend,
    SemanticBackendError,
    backend_from_environment,
    evidence_fingerprint,
    embedding_cache_key,
    load_incremental_embedding_cache,
    load_embedding_cache,
    write_embedding_cache,
    write_incremental_embedding_cache,
)

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_+\-'.]*")
BM25_K1 = 1.5
BM25_B = 0.75
RRF_K = 60
METADATA_BONUS_PER_MATCH = 0.01
MMR_LAMBDA = 0.7
DEFAULT_EMBEDDING_BATCH_SIZE = 64
DEFAULT_CANDIDATE_POOL_SIZE = 200
STAGE_ONE_BM25_QUOTA = 80
STAGE_ONE_ENTITY_QUOTA = 60
STAGE_ONE_MECHANISM_QUOTA = 50
STAGE_ONE_TRANSFER_QUOTA = 50

FIELD_ALIASES = {
    "enzyme": ("enzyme", "enzyme_name", "best_enzyme_name_value", "enzyme_name_value"),
    "substrate": ("substrate", "substrate_name", "best_substrate_name_value", "substrate_name_value"),
    "product": ("product", "product_name", "main_product_name", "best_main_product_name_value", "main_product_name_value", "best_canonical_product", "canonical_product"),
    "parameter_type": ("parameter_type", "metric", "parameter", "measurement_type", "primary_result_metric", "structured_metric"),
    "host": ("host", "host_species", "organism", "assay_host", "best_canonical_host", "best_expression_host_value", "expression_host_value", "best_host_group"),
    "condition": ("condition", "assay_condition", "experimental_condition", "condition_prior_scope"),
}
INDEX_FIELD_NAMES = tuple({name for names in FIELD_ALIASES.values() for name in names})
QUERY_ALIASES = {
    "enzyme": {"dmt": "DMT", "ggdmt1": "DMT", "oc": "OC", "ggoc1": "OC", "pt": "PT", "ggpt1": "PT"},
    "parameter_type": {
        "kcat": "kcat", "km": "Km", "kp": "Kp", "partition coefficient": "partition coefficient",
        "abundance": "abundance", "activity": "activity", "phi": "phi",
    },
    "host": {"yeast": "yeast", "saccharomyces cerevisiae": "yeast"},
}
EXPLICIT_RELAXATION_PRIORITY = ("host", "condition", "product", "substrate", "parameter_type", "enzyme")


class EvidenceDatabaseUnavailable(FileNotFoundError):
    pass


class EmbeddingBackend(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


@dataclass(frozen=True)
class EvidenceDocument:
    record_id: str
    title: str
    doi: str
    evidence: str
    source_file: str = ""
    fields: dict[str, Any] | None = None

    def as_dict(self, *, score: float | None = None, retrieval: dict[str, Any] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "record_id": self.record_id,
            "title": self.title,
            "doi": self.doi,
            "evidence": self.evidence,
            "source_file": self.source_file,
            "fields": self.fields or {},
        }
        if score is not None:
            payload["score"] = round(score, 6)
        if retrieval is not None:
            payload["retrieval"] = retrieval
        return payload


@dataclass(frozen=True)
class RankedEvidence:
    index: int
    lexical_score: float = 0.0
    semantic_score: float | None = None
    lexical_rank: int | None = None
    semantic_rank: int | None = None
    rrf_score: float = 0.0
    matched_metadata: tuple[str, ...] = ()


def load_evidence_documents(path: Path) -> list[EvidenceDocument]:
    if not path.is_file():
        raise EvidenceDatabaseUnavailable(f"Evidence database not found: {path}")
    if path.suffix.lower() == ".jsonl":
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    elif path.suffix.lower() == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
        rows = raw.get("records", raw) if isinstance(raw, dict) else raw
    elif path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    else:
        raise ValueError("Evidence database must be .jsonl, .json, or .csv")
    if not isinstance(rows, list):
        raise ValueError("Evidence database must contain a list of records")
    documents: list[EvidenceDocument] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        record = row.get("record") if isinstance(row.get("record"), dict) else row
        fields = _compatibility_fields(record)
        evidence = (
            _first_text(row, "evidence", "evidence_text", "primary_result_evidence", "data_source_type_evidence", "best_llps_trigger_evidence", "best_llps_component_evidence", "best_llps_state_evidence")
            or _first_text(record, "evidence", "evidence_text", "primary_result_evidence", "data_source_type_evidence", "best_llps_trigger_evidence", "best_llps_component_evidence", "best_llps_state_evidence")
            or _find_metric_evidence(record)
        )
        if not evidence:
            continue
        documents.append(EvidenceDocument(
            record_id=_first_text(row, "record_id", "evidence_id", "aggregate_record_id", "article_id") or _first_text(record, "record_id", "evidence_id", "aggregate_record_id", "article_id") or f"row-{index}",
            title=_first_text(row, "title", "title_clean") or _first_text(record, "title", "title_clean") or "Untitled source",
            doi=_first_text(row, "doi") or _first_text(record, "doi"),
            evidence=evidence,
            source_file=_first_text(row, "source_file", "text_file") or _first_text(record, "source_file", "text_file"),
            fields=fields,
        ))
    return documents


def extract_query_constraints(question: str, documents: Sequence[EvidenceDocument] | None = None) -> dict[str, str]:
    """Normalize explicit entity/metadata mentions without scientific inference."""
    del documents  # Kept in the public signature for future schema-aware callers.
    normalized = " ".join(_tokens(question))
    constraints: dict[str, str] = {}
    for key, aliases in QUERY_ALIASES.items():
        for alias, canonical in aliases.items():
            if _contains_alias(normalized, alias):
                constraints[key] = canonical
                break
    compound = re.search(r"\b(?:compound|intermediate|substrate)\s*(9|10|11|13|15)\b", normalized)
    if compound:
        constraints["substrate"] = compound.group(1)
    if "glabridin" in normalized:
        constraints.setdefault("product", "glabridin")
    return constraints


def parse_query_intent(question: str) -> dict[str, Any]:
    """Transparent multi-entity query routing; it does not assert biology."""
    normalized = " ".join(_tokens(question))
    enzymes = [canonical for alias, canonical in QUERY_ALIASES["enzyme"].items() if _contains_alias(normalized, alias)]
    outcomes = [canonical for alias, canonical in QUERY_ALIASES["parameter_type"].items() if _contains_alias(normalized, alias)]
    context = [term for term in ("llps", "condensate", "phase separation") if _contains_alias(normalized, term)]
    return {"enzymes": list(dict.fromkeys(enzymes)), "outcomes": list(dict.fromkeys(outcomes)), "context": context, "constraints": extract_query_constraints(question)}


def bm25_search(
    question: str,
    documents: Sequence[EvidenceDocument],
    *,
    constraints: dict[str, str] | None = None,
    candidate_indices: Sequence[int] | None = None,
) -> list[RankedEvidence]:
    """Rank evidence with a compact BM25 implementation and bounded metadata boost."""
    query_terms = _tokens(question)
    indices = _candidate_indices(documents, candidate_indices)
    if not query_terms or not indices:
        return []
    corpus = [Counter(_tokens(_index_text(documents[index]))) for index in indices]
    average_length = sum(sum(vector.values()) for vector in corpus) / len(corpus)
    document_frequency = Counter(term for vector in corpus for term in vector)
    scored: list[tuple[int, float, tuple[str, ...]]] = []
    for local_index, vector in enumerate(corpus):
        index = indices[local_index]
        length = sum(vector.values())
        score = 0.0
        for term in query_terms:
            frequency = vector.get(term, 0)
            if not frequency:
                continue
            inverse_frequency = math.log(1 + (len(corpus) - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
            denominator = frequency + BM25_K1 * (1 - BM25_B + BM25_B * length / max(average_length, 1.0))
            score += inverse_frequency * frequency * (BM25_K1 + 1) / denominator
        matches = _metadata_matches(documents[index], constraints or {})
        project_matches = _project_metadata_matches(documents[index])
        all_matches = tuple((*matches, *project_matches))
        if score > 0:
            score += min(METADATA_BONUS_PER_MATCH * len(all_matches), 0.05)
            scored.append((index, score, all_matches))
    ranked = sorted(scored, key=lambda item: (-item[1], documents[item[0]].record_id))
    return [RankedEvidence(index=index, lexical_score=score, lexical_rank=rank, matched_metadata=matches) for rank, (index, score, matches) in enumerate(ranked, start=1)]


def semantic_search(
    question: str,
    documents: Sequence[EvidenceDocument],
    *,
    backend: EmbeddingBackend,
    evidence_path: Path | None = None,
    candidate_indices: Sequence[int] | None = None,
) -> tuple[list[RankedEvidence], dict[int, list[float]]]:
    """Rank by embedding cosine similarity, reusing a valid local document cache."""
    indices = _candidate_indices(documents, candidate_indices)
    document_vectors = _document_embeddings([documents[index] for index in indices], backend=backend, evidence_path=evidence_path)
    query_vectors = backend.embed([question])
    if len(query_vectors) != 1:
        raise SemanticBackendError("embedding backend did not return one query vector")
    scores = [(index, _cosine(query_vectors[0], document_vectors[local])) for local, index in enumerate(indices)]
    ranked = sorted(((index, score) for index, score in scores if score > 0), key=lambda item: (-item[1], documents[item[0]].record_id))
    return [RankedEvidence(index=index, semantic_score=score, semantic_rank=rank) for rank, (index, score) in enumerate(ranked, start=1)], dict(zip(indices, document_vectors))


def rrf_fuse(lexical: Sequence[RankedEvidence], semantic: Sequence[RankedEvidence]) -> list[RankedEvidence]:
    """Fuse ranked routes without mixing incomparable BM25 and cosine scores."""
    merged: dict[int, RankedEvidence] = {}
    for hit in lexical:
        merged[hit.index] = RankedEvidence(
            index=hit.index,
            lexical_score=hit.lexical_score,
            lexical_rank=hit.lexical_rank,
            rrf_score=1 / (RRF_K + (hit.lexical_rank or 1)),
            matched_metadata=hit.matched_metadata,
        )
    for hit in semantic:
        previous = merged.get(hit.index, RankedEvidence(index=hit.index))
        merged[hit.index] = RankedEvidence(
            index=hit.index,
            lexical_score=previous.lexical_score,
            semantic_score=hit.semantic_score,
            lexical_rank=previous.lexical_rank,
            semantic_rank=hit.semantic_rank,
            rrf_score=previous.rrf_score + 1 / (RRF_K + (hit.semantic_rank or 1)),
            matched_metadata=previous.matched_metadata,
        )
    return sorted(merged.values(), key=lambda hit: (-hit.rrf_score, hit.index))


def deduplicate_sources(candidates: Sequence[RankedEvidence], documents: Sequence[EvidenceDocument], *, max_per_doi: int = 1) -> list[RankedEvidence]:
    """Remove duplicate records/text and enforce source diversity before MMR."""
    accepted: list[RankedEvidence] = []
    record_ids: set[str] = set()
    source_counts: Counter[str] = Counter()
    evidence_tokens: list[set[str]] = []
    for candidate in candidates:
        document = documents[candidate.index]
        source = _source_identity(document)
        tokens = set(_tokens(document.evidence))
        if document.record_id in record_ids or source_counts[source] >= max_per_doi:
            continue
        if any(_jaccard(tokens, seen) >= 0.92 for seen in evidence_tokens):
            continue
        accepted.append(candidate)
        record_ids.add(document.record_id)
        source_counts[source] += 1
        evidence_tokens.append(tokens)
    return accepted


def mmr_select(
    candidates: Sequence[RankedEvidence],
    documents: Sequence[EvidenceDocument],
    *,
    top_k: int,
    semantic_vectors: dict[int, list[float]] | None = None,
) -> list[RankedEvidence]:
    """Select relevant, non-redundant sources.

    MMR is a retrieval diversity heuristic, not evidence strength.
    """
    remaining = list(candidates)
    selected: list[RankedEvidence] = []
    if top_k < 1:
        return selected
    max_relevance = max((candidate.rrf_score for candidate in remaining), default=1.0)
    while remaining and len(selected) < top_k:
        def mmr_score(candidate: RankedEvidence) -> float:
            relevance = candidate.rrf_score / max_relevance
            redundancy = max((_candidate_similarity(candidate, chosen, documents, semantic_vectors) for chosen in selected), default=0.0)
            return MMR_LAMBDA * relevance - (1 - MMR_LAMBDA) * redundancy
        chosen = max(remaining, key=lambda candidate: (mmr_score(candidate), candidate.rrf_score, -candidate.index))
        selected.append(chosen)
        remaining.remove(chosen)
    return selected


def retrieve_evidence(
    question: str,
    documents: Sequence[EvidenceDocument],
    *,
    top_k: int = 5,
    constraints: dict[str, str] | None = None,
    semantic_enabled: bool = False,
    semantic_backend: EmbeddingBackend | None = None,
    evidence_path: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """Execute BM25, optional semantic retrieval, RRF, deduplication, and MMR."""
    intent = parse_query_intent(question)
    inferred_constraints = intent["constraints"]
    explicit_constraints = _validated_constraints(constraints)
    scoped_indices, active_constraints, relaxed_constraints = _select_candidate_indices(documents, explicit_constraints)
    candidate_indices = _stage_one_candidates(question, documents, scoped_indices, intent)
    lexical = bm25_search(question, documents, constraints=inferred_constraints, candidate_indices=candidate_indices)
    semantic: list[RankedEvidence] = []
    semantic_vectors: dict[int, list[float]] | None = None
    semantic_status = "disabled"
    if semantic_enabled:
        backend = semantic_backend or backend_from_environment()
        if backend is None:
            semantic_status = "unavailable"
        else:
            try:
                semantic, semantic_vectors = semantic_search(
                    question, documents, backend=backend, evidence_path=evidence_path, candidate_indices=candidate_indices,
                )
                semantic_status = "used"
            except Exception:  # Optional backends must never break deterministic retrieval.
                semantic_status = "unavailable"
    fused = rrf_fuse(lexical, semantic)
    relevant = _relevant_candidates(fused, documents, intent)
    direct = [candidate for candidate in relevant if _evidence_tier(documents[candidate.index], intent) == "direct"]
    transferable = [candidate for candidate in relevant if _evidence_tier(documents[candidate.index], intent) == "transferable"]
    if direct:
        evidence_mode = "direct"
        selected = mmr_select(
            deduplicate_sources(direct, documents), documents, top_k=top_k, semantic_vectors=semantic_vectors,
        )
    elif transferable:
        evidence_mode = "transferable_fallback"
        selected = mmr_select(
            deduplicate_sources(transferable, documents), documents, top_k=top_k, semantic_vectors=semantic_vectors,
        )
    else:
        evidence_mode = "no_match"
        selected = []
    max_score = max((hit.rrf_score for hit in selected), default=1.0)
    sources = [
        documents[hit.index].as_dict(
            score=hit.rrf_score / max_score,
            retrieval={
                "lexical_rank": hit.lexical_rank,
                "semantic_rank": hit.semantic_rank,
                "rrf_score": round(hit.rrf_score, 8),
                "matched_metadata": list(hit.matched_metadata),
                "tier": _evidence_tier(documents[hit.index], intent),
            },
        )
        for hit in selected
    ]
    legacy_constraints = {**inferred_constraints, **active_constraints}
    query_analysis = {
        "constraints": legacy_constraints, "intent": intent,
        "inferred_constraints": inferred_constraints,
        "explicit_constraints": explicit_constraints,
        "active_constraints": active_constraints,
        "relaxed_constraints": relaxed_constraints,
    }
    retrieval = {
        "lexical": "bm25",
        "semantic": semantic_status,
        "fusion": "rrf" if semantic_status == "used" else "lexical_fallback",
        "diversity": "doi_dedup+mmr",
        "candidate_count": len(candidate_indices),
        "final_count": len(sources),
        "evidence_mode": evidence_mode,
    }
    return sources, query_analysis, retrieval


def _stage_one_candidates(question: str, documents: Sequence[EvidenceDocument], scoped_indices: Sequence[int], intent: dict[str, Any]) -> list[int]:
    """High-recall local union before any semantic API call."""
    lexical = bm25_search(question, documents, candidate_indices=scoped_indices)
    lexical_order = [hit.index for hit in lexical]
    lexical_rank = {index: rank for rank, index in enumerate(lexical_order)}

    def ordered(indices: Sequence[int]) -> list[int]:
        return sorted(indices, key=lambda index: (lexical_rank.get(index, len(documents)), documents[index].record_id))

    entity_indices: list[int] = []
    mechanism_indices: list[int] = []
    transfer_indices: list[int] = []
    for index in scoped_indices:
        document = documents[index]
        text = _index_text(document).lower()
        metadata = _metadata(document)
        mechanism = _has_llps_context(text)
        catalytic = _has_catalytic_evidence(text)
        transfer = bool(_project_metadata_matches(document)) or str(metadata.get("llps_transferability_class", "")).lower() in {"high", "medium"}
        entity = bool(intent["enzymes"]) and _entity_matches(metadata, intent)
        if entity:
            entity_indices.append(index)
        if mechanism and catalytic:
            mechanism_indices.append(index)
        if transfer:
            transfer_indices.append(index)

    routes = (
        lexical_order[:STAGE_ONE_BM25_QUOTA],
        ordered(entity_indices)[:STAGE_ONE_ENTITY_QUOTA],
        ordered(mechanism_indices)[:STAGE_ONE_MECHANISM_QUOTA],
        ordered(transfer_indices)[:STAGE_ONE_TRANSFER_QUOTA],
    )
    selected: list[int] = []
    for route in routes:
        for index in route:
            if index not in selected:
                selected.append(index)
            if len(selected) == DEFAULT_CANDIDATE_POOL_SIZE:
                return selected
    return selected


def _evidence_tier(document: EvidenceDocument, intent: dict[str, Any]) -> str:
    metadata = _metadata(document)
    text = _index_text(document).lower()
    has_requested_dimension = bool(intent["enzymes"] or intent["context"] or intent["outcomes"] or intent["constraints"])
    if has_requested_dimension and _entity_matches(metadata, intent, text=text) and _context_matches(text, intent) and _outcome_matches(text, intent):
        return "direct"
    if _has_llps_context(text) and _has_catalytic_evidence(text):
        return "transferable"
    return "background"


def _relevant_candidates(candidates: Sequence[RankedEvidence], documents: Sequence[EvidenceDocument], intent: dict[str, Any]) -> list[RankedEvidence]:
    """Reject zero-signal background before DOI diversity/MMR can promote it."""
    return [
        candidate
        for candidate in candidates
        if _evidence_tier(documents[candidate.index], intent) in {"direct", "transferable"}
    ]


def _entity_matches(metadata: dict[str, Any], intent: dict[str, Any], *, text: str = "") -> bool:
    if not intent["enzymes"]:
        return True
    enzyme = _canonical_value("enzyme", _canonical_metadata_value(metadata, "enzyme") or "")
    requested = {item.lower() for item in intent["enzymes"]}
    return enzyme in requested or (not enzyme and any(_contains_alias(text, item) for item in requested))


def _context_matches(text: str, intent: dict[str, Any]) -> bool:
    return not intent["context"] or _has_llps_context(text)


def _outcome_matches(text: str, intent: dict[str, Any]) -> bool:
    if not intent["outcomes"]:
        return True
    outcome_terms = {
        "activity": ("activity", "catalytic", "enzyme activity"),
        "kcat": ("kcat", "turnover"),
        "Km": ("km", "michaelis"),
        "Kp": ("kp", "partition coefficient"),
        "partition coefficient": ("partition coefficient", "partitioning"),
        "abundance": ("abundance", "concentration", "expression"),
        "phi": ("phi", "volume fraction"),
    }
    return any(term in text for outcome in intent["outcomes"] for term in outcome_terms.get(outcome, (outcome.lower(),)))


def _has_llps_context(text: str) -> bool:
    return any(term in text for term in ("llps", "condensate", "phase separation"))


def _has_catalytic_evidence(text: str) -> bool:
    return any(term in text for term in ("activity", "catalytic", "enzyme", "kcat", "km", "kinetic"))


def search_evidence(question: str, documents: Sequence[EvidenceDocument], *, top_k: int = 5) -> list[dict[str, Any]]:
    """Backward-compatible deterministic evidence search used by existing callers."""
    sources, _analysis, _retrieval = retrieve_evidence(question, documents, top_k=top_k)
    return sources


def answer_question(
    question: str,
    evidence_path: Path,
    *,
    top_k: int = 5,
    mode: str = "retrieve_only",
    constraints: dict[str, str] | None = None,
    semantic_enabled: bool = False,
    semantic_backend: EmbeddingBackend | None = None,
    chat_client: ChatClient | Any | None = None,
) -> dict[str, Any]:
    """Return provenance-bearing evidence, optionally followed by one grounded LLM call."""
    if mode not in {"retrieve_only", "synthesize"}:
        raise ValueError("mode must be 'retrieve_only' or 'synthesize'")
    try:
        documents = load_evidence_documents(evidence_path)
    except EvidenceDatabaseUnavailable as exc:
        return _base_response(False, "database_unavailable", str(exc), [], mode=mode)
    sources, query_analysis, retrieval = retrieve_evidence(
        question,
        documents,
        top_k=top_k,
        constraints=constraints,
        semantic_enabled=semantic_enabled,
        semantic_backend=semantic_backend,
        evidence_path=evidence_path,
    )
    if not sources:
        response = _base_response(True, "no_match", "No sufficiently relevant evidence was found in the local database.", [], mode=mode)
        response.update(query_analysis=query_analysis, retrieval=retrieval)
        return response
    retrieval_answer = _retrieval_summary(sources)
    response = _base_response(True, "retrieved", retrieval_answer, sources, mode=mode)
    response.update(query_analysis=query_analysis, retrieval=retrieval)
    if mode == "retrieve_only":
        return response
    client = chat_client or _synthesis_client_from_environment()
    if client is None:
        response.update(
            status="synthesis_error",
            answer="AI synthesis unavailable. Retrieved evidence is shown below.",
            limitations=["No QA synthesis API is configured; retrieval results remain available."],
        )
        return response
    try:
        synthesis = synthesize_answer(
            question, query_analysis["constraints"], sources,
            evidence_mode=retrieval["evidence_mode"], client=client,
        )
    except (LlmError, ValueError, TypeError, KeyError) as exc:
        response.update(
            status="synthesis_error",
            answer="AI synthesis unavailable. Retrieved evidence is shown below.",
            limitations=[f"Synthesis response was unavailable: {exc}"],
        )
        return response
    response.update(answer=synthesis["answer"], claims=synthesis["claims"], limitations=synthesis["limitations"], suggested_next_steps=synthesis["suggested_next_steps"], selected_evidence_ids=synthesis["selected_evidence_ids"])
    return response


def synthesize_answer(
    question: str,
    constraints: dict[str, str],
    sources: Sequence[dict[str, Any]],
    *,
    evidence_mode: str = "direct",
    client: Any,
) -> dict[str, Any]:
    """Make exactly one grounded synthesis request from already-selected evidence."""
    evidence = [
        {
            "evidence_id": source["record_id"],
            "title": source["title"],
            "doi": source["doi"],
            "quoted_evidence": source["evidence"],
            "metadata": _important_fields(source.get("fields", {})),
        }
        for source in sources
    ]
    prompt = (
        "Answer only from the supplied evidence. Do not use outside knowledge or invent DOI, values, mechanisms, or results. "
        "Every factual claim must cite evidence_ids. Distinguish direct_report from interpretation. If evidence is insufficient, say so. "
        "Retrieved evidence is not a validated model parameter. "
        + (
            "No direct project-specific evidence was retrieved. The selected sources are transferable evidence from related "
            "LLPS-enzyme systems; do not present them as facts about the queried enzymes, and state that experimental validation is required. "
            if evidence_mode == "transferable_fallback" else ""
        )
        + "Return one JSON object with answer, claims, limitations, "
        "suggested_next_steps, and selected_evidence_ids.\n\n"
        f"Question: {question}\nConstraints: {json.dumps(constraints)}\nEvidence: {json.dumps(evidence, ensure_ascii=False)}"
    )
    parsed = client.complete_json(prompt)
    answer = parsed.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("synthesis JSON must contain a non-empty answer")
    known_ids = {source["record_id"] for source in sources}
    claims = []
    for claim in parsed.get("claims", []):
        if not isinstance(claim, dict) or not isinstance(claim.get("claim"), str):
            continue
        evidence_ids = [item for item in claim.get("evidence_ids", []) if isinstance(item, str) and item in known_ids]
        claim_type = claim.get("type") if claim.get("type") in {"direct_report", "interpretation"} else "interpretation"
        claims.append({"claim": claim["claim"], "evidence_ids": evidence_ids, "type": claim_type})
    return {
        "answer": answer.strip(),
        "claims": claims,
        "limitations": _string_list(parsed.get("limitations")),
        "suggested_next_steps": _string_list(parsed.get("suggested_next_steps")),
        "selected_evidence_ids": [item for item in _string_list(parsed.get("selected_evidence_ids")) if item in known_ids],
    }


def _document_embeddings(documents: Sequence[EvidenceDocument], *, backend: EmbeddingBackend, evidence_path: Path | None) -> list[list[float]]:
    texts = [_index_text(document) for document in documents]
    if not isinstance(backend, EmbeddingApiBackend) or evidence_path is None or not evidence_path.is_file():
        return _embed_in_batches(backend, texts)
    keys = [embedding_cache_key(document.record_id, backend.cache_identity, text) for document, text in zip(documents, texts)]
    cached = load_incremental_embedding_cache(evidence_path)
    missing = [index for index, key in enumerate(keys) if key not in cached]
    if missing:
        new_vectors = _embed_in_batches(backend, [texts[index] for index in missing])
        additions = {keys[index]: vector for index, vector in zip(missing, new_vectors)}
        write_incremental_embedding_cache(evidence_path, additions)
        cached.update(additions)
    vectors = [cached[key] for key in keys]
    if vectors and any(len(vector) != len(vectors[0]) for vector in vectors):
        raise SemanticBackendError("embedding cache contains incompatible dimensions")
    return vectors


def _embed_in_batches(
    backend: EmbeddingBackend,
    texts: Sequence[str],
    *,
    batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
) -> list[list[float]]:
    """Embed a corpus sequentially; never expose an API to an unbounded batch."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = backend.embed(texts[start : start + batch_size])
        if len(batch) != len(texts[start : start + batch_size]) or any(not _valid_embedding(vector) for vector in batch):
            raise SemanticBackendError("embedding backend did not return one numeric vector per input")
        vectors.extend([[float(value) for value in vector] for vector in batch])
    if len(vectors) != len(texts):
        raise SemanticBackendError("embedding vector count does not match corpus")
    if vectors and any(len(vector) != len(vectors[0]) for vector in vectors):
        raise SemanticBackendError("embedding vectors have inconsistent dimensions")
    return vectors


def _valid_embedding(vector: object) -> bool:
    return isinstance(vector, Sequence) and bool(vector) and all(isinstance(value, (int, float)) for value in vector)


def _candidate_indices(documents: Sequence[EvidenceDocument], candidate_indices: Sequence[int] | None) -> list[int]:
    if candidate_indices is None:
        return list(range(len(documents)))
    return [index for index in candidate_indices if 0 <= index < len(documents)]


def _select_candidate_indices(
    documents: Sequence[EvidenceDocument], explicit_constraints: dict[str, str],
) -> tuple[list[int], dict[str, str], list[str]]:
    """Apply caller constraints first, relaxing in a documented deterministic order."""
    active = dict(explicit_constraints)
    relaxed: list[str] = []
    while active:
        indices = [index for index, document in enumerate(documents) if _matches_all_constraints(document, active)]
        if indices:
            return indices, active, relaxed
        key = next((item for item in EXPLICIT_RELAXATION_PRIORITY if item in active), next(iter(active)))
        relaxed.append(f"{key}={active.pop(key)}")
    return list(range(len(documents))), active, relaxed


def _matches_all_constraints(document: EvidenceDocument, constraints: dict[str, str]) -> bool:
    return len(_metadata_matches(document, constraints)) == len(constraints)


def _metadata(document: EvidenceDocument) -> dict[str, Any]:
    fields = document.fields or {}
    metadata = dict(fields)
    nested = fields.get("fields")
    if isinstance(nested, dict):
        metadata.update(nested)
    return metadata


def _canonical_metadata_value(metadata: dict[str, Any], key: str) -> Any | None:
    """Resolve canonical metadata first, using aliases only when it is absent."""
    value = _field_value(metadata, key)
    if value is not None:
        return value
    for alias in FIELD_ALIASES.get(key, (key,)):
        value = _field_value(metadata, alias)
        if value is not None:
            return value
    return None


def _compatibility_fields(record: dict[str, Any]) -> dict[str, Any]:
    """Preserve raw evidence fields while filling only missing canonical aliases."""
    fields = dict(record)
    nested = fields.get("fields")
    nested_fields = nested if isinstance(nested, dict) else {}
    for canonical, aliases in FIELD_ALIASES.items():
        if _field_value(fields, canonical) is not None or _field_value(nested_fields, canonical) is not None:
            continue
        for alias in aliases:
            value = _field_value(fields, alias)
            if value is None:
                value = _field_value(nested_fields, alias)
            if value is not None:
                fields[canonical] = value
                break
    return fields


def _field_value(fields: dict[str, Any], key: str) -> Any | None:
    value = fields.get(key)
    return value if value is not None and str(value).strip() else None


def _metadata_matches(document: EvidenceDocument, constraints: dict[str, str]) -> tuple[str, ...]:
    metadata = _metadata(document)
    matches = []
    for key, expected in constraints.items():
        value = _canonical_metadata_value(metadata, key)
        if value is not None and _canonical_value(key, value) == _canonical_value(key, expected):
            matches.append(key)
    return tuple(matches)


def _project_metadata_matches(document: EvidenceDocument) -> tuple[str, ...]:
    metadata = _metadata(document)
    matches = []
    for key in ("is_project_glabridin_direct", "is_project_llps_related", "is_project_yeast", "high_transferability", "is_project_high_transfer_llps"):
        if metadata.get(key) is True or str(metadata.get(key, "")).lower() == "true":
            matches.append(f"project:{key}")
    return tuple(matches)


def _index_text(document: EvidenceDocument) -> str:
    metadata = _metadata(document)
    field_text = " ".join(
        str(value)
        for key in FIELD_ALIASES
        if (value := _canonical_metadata_value(metadata, key)) is not None
    )
    return f"{document.title} {document.evidence} {field_text}"


def _validated_constraints(constraints: dict[str, str] | None) -> dict[str, str]:
    if not constraints:
        return {}
    return {str(key): str(value) for key, value in constraints.items() if isinstance(value, (str, int, float)) and str(value).strip()}


def _canonical_value(key: str, value: object) -> str:
    text = " ".join(_tokens(str(value)))
    if key == "enzyme":
        for alias, canonical in QUERY_ALIASES["enzyme"].items():
            if _contains_alias(text, alias):
                return canonical.lower()
    if key == "parameter_type":
        for alias, canonical in QUERY_ALIASES["parameter_type"].items():
            if _contains_alias(text, alias):
                return canonical.lower()
    if key == "host" and (_contains_alias(text, "yeast") or _contains_alias(text, "saccharomyces cerevisiae")):
        return "yeast"
    if key in {"substrate", "product"}:
        compound = re.search(r"\b(9|10|11|13|15)\b", text)
        if compound:
            return compound.group(1)
    return text


def _source_identity(document: EvidenceDocument) -> str:
    if document.doi.strip():
        return f"doi:{document.doi.strip().lower()}"
    return f"fallback:{' '.join(_tokens(document.title))}|{' '.join(_tokens(document.source_file))}"


def _candidate_similarity(left: RankedEvidence, right: RankedEvidence, documents: Sequence[EvidenceDocument], semantic_vectors: dict[int, list[float]] | None) -> float:
    if semantic_vectors and left.index in semantic_vectors and right.index in semantic_vectors:
        return _cosine(semantic_vectors[left.index], semantic_vectors[right.index])
    return _jaccard(set(_tokens(_index_text(documents[left.index]))), set(_tokens(_index_text(documents[right.index]))))


def _important_fields(fields: object) -> dict[str, Any]:
    if not isinstance(fields, dict):
        return {}
    metadata = dict(fields)
    if isinstance(fields.get("fields"), dict):
        metadata.update(fields["fields"])
    return {key: metadata[key] for key in (*INDEX_FIELD_NAMES, "condition", "project_tier") if key in metadata}


def _synthesis_client_from_environment() -> ChatClient | None:
    api_key = os.getenv("QA_SYNTHESIS_API_KEY")
    api_base = os.getenv("QA_SYNTHESIS_API_BASE")
    model = os.getenv("QA_SYNTHESIS_MODEL")
    if not all((api_key, api_base, model)):
        return None
    return ChatClient(api_key=api_key, api_base=api_base, model=model, retries=1)


def _base_response(ok: bool, status: str, answer: str, sources: list[dict[str, Any]], *, mode: str) -> dict[str, Any]:
    return {"ok": ok, "status": status, "answer": answer, "sources": sources, "mode": mode, "claims": [], "limitations": [], "suggested_next_steps": [], "selected_evidence_ids": []}


def _retrieval_summary(sources: Sequence[dict[str, Any]]) -> str:
    citations = "; ".join(filter(None, (f"{source['title']} ({source['doi']})" for source in sources)))
    return f"Retrieved {len(sources)} local evidence record(s); inspect their quoted evidence before using a parameter. {citations}"


def _contains_alias(text: str, alias: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", text) is not None


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left or right else 0.0


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        raise SemanticBackendError("embedding vectors have incompatible dimensions")
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


def _string_list(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _first_text(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _find_metric_evidence(record: dict[str, Any]) -> str:
    for value in record.values():
        if isinstance(value, dict) and isinstance(value.get("evidence"), str) and value["evidence"].strip():
            return value["evidence"].strip()
    return ""

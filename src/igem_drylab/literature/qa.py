"""Small, local evidence retrieval with explicit provenance.

The retrieval score is lexical TF-IDF cosine similarity.  It is useful for a
transparent offline review page, but is not a substitute for semantic evidence
assessment by a human reader.
"""

from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_+\-'.]*")


class EvidenceDatabaseUnavailable(FileNotFoundError):
    pass


@dataclass(frozen=True)
class EvidenceDocument:
    record_id: str
    title: str
    doi: str
    evidence: str
    source_file: str = ""
    fields: dict[str, Any] | None = None

    def as_dict(self, *, score: float | None = None) -> dict[str, Any]:
        payload = {"record_id": self.record_id, "title": self.title, "doi": self.doi, "evidence": self.evidence,
                   "source_file": self.source_file, "fields": self.fields or {}}
        if score is not None:
            payload["score"] = round(score, 6)
        return payload


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
        evidence = _first_text(row, "evidence", "evidence_text", "data_source_type_evidence") or _find_metric_evidence(record)
        if not evidence:
            continue
        documents.append(EvidenceDocument(
            record_id=_first_text(row, "record_id", "evidence_id", "article_id") or f"row-{index}",
            title=_first_text(row, "title") or "Untitled source", doi=_first_text(row, "doi"), evidence=evidence,
            source_file=_first_text(row, "source_file", "text_file"), fields=record,
        ))
    return documents


def search_evidence(question: str, documents: list[EvidenceDocument], *, top_k: int = 5) -> list[dict[str, Any]]:
    if not question.strip() or top_k < 1:
        return []
    query = Counter(_tokens(question))
    if not query:
        return []
    corpus = [Counter(_tokens(f"{item.title} {item.evidence}")) for item in documents]
    document_frequency = Counter(token for vector in corpus for token in vector)
    n = len(corpus)
    query_weighted = _tfidf(query, document_frequency, n)
    scored = []
    for document, vector in zip(documents, corpus):
        score = _cosine(query_weighted, _tfidf(vector, document_frequency, n))
        if score > 0:
            scored.append(document.as_dict(score=score))
    return sorted(scored, key=lambda item: (-float(item["score"]), item["record_id"]))[:top_k]


def answer_question(question: str, evidence_path: Path, *, top_k: int = 5) -> dict[str, Any]:
    """Return retrieval results; never fabricates a scientific conclusion."""
    try:
        documents = load_evidence_documents(evidence_path)
    except EvidenceDatabaseUnavailable as exc:
        return {"ok": False, "status": "database_unavailable", "answer": str(exc), "sources": []}
    sources = search_evidence(question, documents, top_k=top_k)
    if not sources:
        return {"ok": True, "status": "no_match", "answer": "No lexical match was found in the local evidence database.", "sources": []}
    citations = "; ".join(filter(None, (f"{source['title']} ({source['doi']})" for source in sources)))
    return {"ok": True, "status": "retrieved", "answer": f"Retrieved {len(sources)} local evidence record(s); inspect their quoted evidence before using a parameter. {citations}", "sources": sources}


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _tfidf(vector: Counter[str], document_frequency: Counter[str], n: int) -> dict[str, float]:
    return {token: (1 + math.log(count)) * (math.log((1 + n) / (1 + document_frequency[token])) + 1) for token, count in vector.items()}


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    numerator = sum(value * right.get(token, 0.0) for token, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


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

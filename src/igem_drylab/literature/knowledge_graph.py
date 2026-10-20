"""Deterministic, provenance-bearing knowledge graph for evidence retrieval.

The graph is deliberately derived only from fields already present in an
evidence record.  It does not use an LLM to invent entities or biological
relations, and it never promotes extracted evidence into an approved model
parameter.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence


GRAPH_SCHEMA_VERSION = "igem-evidence-graph-v1"
GRAPH_RRF_K = 60

GRAPH_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "enzyme": ("enzyme", "enzyme_name", "best_enzyme_name_value", "enzyme_name_value"),
    "mutant": ("mutant", "mutation", "variant", "enzyme_variant"),
    "substrate": ("substrate", "substrate_name", "best_substrate_name_value", "substrate_name_value"),
    "product": ("product", "product_name", "main_product_name", "best_main_product_name_value", "best_canonical_product", "canonical_product"),
    "product_family": ("product_family", "best_product_family", "canonical_product_family"),
    "host": ("host", "host_species", "organism", "assay_host", "best_canonical_host", "best_expression_host_value", "best_host_group"),
    "construct": ("construct", "construct_id", "fusion_construct", "protein_construct"),
    "scaffold": ("scaffold", "scaffold_name", "llps_scaffold"),
    "llps_component": ("llps_component", "best_llps_component_value", "condensate_component"),
    "llps_trigger": ("llps_trigger", "best_llps_trigger_value", "trigger", "trigger_type"),
    "llps_state": ("llps_state", "best_llps_state_value", "phase_state"),
    "reaction_system": ("reaction_system", "reaction_system_type", "assay_system", "system_type"),
    "metric": ("parameter_type", "metric", "parameter", "measurement_type", "primary_result_metric", "structured_metric"),
    "temperature": ("reaction_temperature", "temperature", "temperature_c"),
    "ph": ("reaction_ph", "ph", "pH"),
    "time": ("reaction_time", "time", "duration"),
    "condition": ("condition", "assay_condition", "experimental_condition", "condition_prior_scope"),
}

RELATIONS = {
    "enzyme": "USES_ENZYME",
    "mutant": "USES_VARIANT",
    "substrate": "USES_SUBSTRATE",
    "product": "PRODUCES",
    "product_family": "HAS_PRODUCT_FAMILY",
    "host": "PERFORMED_IN",
    "construct": "USES_CONSTRUCT",
    "scaffold": "USES_SCAFFOLD",
    "llps_component": "USES_LLPS_COMPONENT",
    "llps_trigger": "USES_LLPS_TRIGGER",
    "llps_state": "HAS_LLPS_STATE",
    "reaction_system": "USES_REACTION_SYSTEM",
    "metric": "REPORTS_METRIC",
    "temperature": "AT_TEMPERATURE",
    "ph": "AT_PH",
    "time": "FOR_DURATION",
    "condition": "UNDER_CONDITION",
}

UNKNOWN_VALUES = {"", "unknown", "unidentified", "not reported", "not available", "n/a", "na", "none", "null", "-"}
QUERY_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in", "is", "of", "on", "or", "that", "the", "to", "was", "were", "what", "which", "with",
    "evidence", "report", "reported", "study", "studies", "show", "shows",
}


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    kind: str
    label: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    source: str
    relation: str
    target: str
    record_id: str
    doi: str = ""
    evidence: str = ""
    provenance_status: str = "extracted"


@dataclass(frozen=True)
class GraphHit:
    index: int
    score: float
    graph_rank: int
    matched_entities: tuple[str, ...]
    paths: tuple[str, ...]


@dataclass
class EvidenceKnowledgeGraph:
    nodes: dict[str, GraphNode]
    edges: list[GraphEdge]
    evidence_fingerprint: str
    schema_version: str = GRAPH_SCHEMA_VERSION
    _adjacency: dict[str, list[tuple[str, GraphEdge]]] = field(default_factory=dict, repr=False)
    _record_nodes: dict[str, str] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if not self._adjacency:
            adjacency: dict[str, list[tuple[str, GraphEdge]]] = defaultdict(list)
            for edge in self.edges:
                adjacency[edge.source].append((edge.target, edge))
                adjacency[edge.target].append((edge.source, edge))
            self._adjacency = dict(adjacency)
        if not self._record_nodes:
            self._record_nodes = {
                str(node.properties.get("record_id")): node_id
                for node_id, node in self.nodes.items()
                if node.kind == "experiment" and node.properties.get("record_id")
            }

    @property
    def stats(self) -> dict[str, Any]:
        kinds: dict[str, int] = defaultdict(int)
        for node in self.nodes.values():
            kinds[node.kind] += 1
        relations: dict[str, int] = defaultdict(int)
        for edge in self.edges:
            relations[edge.relation] += 1
        return {
            "schema_version": self.schema_version,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "node_kinds": dict(sorted(kinds.items())),
            "relations": dict(sorted(relations.items())),
            "evidence_fingerprint": self.evidence_fingerprint,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.stats,
            "nodes": [asdict(node) for node in sorted(self.nodes.values(), key=lambda item: item.node_id)],
            "edges": [asdict(edge) for edge in self.edges],
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "EvidenceKnowledgeGraph":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != GRAPH_SCHEMA_VERSION:
            raise ValueError(f"Unsupported knowledge-graph schema: {payload.get('schema_version')}")
        nodes = {item["node_id"]: GraphNode(**item) for item in payload.get("nodes", [])}
        edges = [GraphEdge(**item) for item in payload.get("edges", [])]
        return cls(nodes=nodes, edges=edges, evidence_fingerprint=str(payload.get("evidence_fingerprint", "")))

    def search(
        self,
        question: str,
        documents: Sequence[Any],
        *,
        intent: dict[str, Any] | None = None,
        allowed_indices: Sequence[int] | None = None,
        top_n: int = 100,
        max_hops: int = 3,
    ) -> list[GraphHit]:
        """Traverse entity-to-experiment paths and return explainable graph hits."""
        record_index = {str(document.record_id): index for index, document in enumerate(documents)}
        allowed = set(allowed_indices) if allowed_indices is not None else set(record_index.values())
        query_terms = _query_terms(question)
        concepts = _intent_concepts(intent or {})
        starts: list[tuple[str, float, str]] = []
        for node_id, node in self.nodes.items():
            if node.kind in {"paper", "experiment", "evidence"}:
                continue
            normalized = _normalize(node.label)
            concept_exact = any(_concept_matches(node.kind, normalized, kind, value) for kind, value in concepts)
            overlap = len(query_terms & _tokens(node.label))
            if concept_exact:
                starts.append((node_id, 6.0, f"{node.kind}={node.label}"))
            elif overlap:
                starts.append((node_id, min(3.0, 0.75 * overlap), f"{node.kind}~{node.label}"))

        scores: dict[int, float] = defaultdict(float)
        matches: dict[int, set[str]] = defaultdict(set)
        paths: dict[int, list[str]] = defaultdict(list)
        for start_id, start_score, matched_entity in starts:
            queue: deque[tuple[str, int, tuple[str, ...]]] = deque([(start_id, 0, (self.nodes[start_id].label,))])
            visited = {start_id}
            while queue:
                node_id, distance, labels = queue.popleft()
                node = self.nodes[node_id]
                if node.kind == "experiment" and distance > 0:
                    record_id = str(node.properties.get("record_id", ""))
                    index = record_index.get(record_id)
                    if index is not None and index in allowed:
                        distance_weight = 1.0 if distance == 1 else 0.35 / max(1, distance - 1)
                        scores[index] += start_score * distance_weight
                        matches[index].add(matched_entity)
                        if len(paths[index]) < 6:
                            paths[index].append(" -> ".join(labels))
                if distance >= max_hops:
                    continue
                for neighbor, _edge in self._adjacency.get(node_id, []):
                    if neighbor in visited:
                        continue
                    visited.add(neighbor)
                    queue.append((neighbor, distance + 1, (*labels, self.nodes[neighbor].label)))

        # Reward records that cover several independent query concepts.  This
        # is relation coverage, not an assertion of evidence quality.
        for index in list(scores):
            scores[index] += 1.5 * max(0, len(matches[index]) - 1)
        ranked = sorted(scores, key=lambda index: (-scores[index], documents[index].record_id))[:top_n]
        return [
            GraphHit(
                index=index,
                score=scores[index],
                graph_rank=rank,
                matched_entities=tuple(sorted(matches[index])),
                paths=tuple(paths[index]),
            )
            for rank, index in enumerate(ranked, start=1)
        ]


def build_knowledge_graph(documents: Sequence[Any]) -> EvidenceKnowledgeGraph:
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []
    edge_keys: set[tuple[str, str, str, str]] = set()

    def add_node(node: GraphNode) -> None:
        nodes.setdefault(node.node_id, node)

    def add_edge(edge: GraphEdge) -> None:
        key = (edge.source, edge.relation, edge.target, edge.record_id)
        if key not in edge_keys:
            edge_keys.add(key)
            edges.append(edge)

    for document in documents:
        record_id = str(document.record_id)
        experiment_id = _node_id("experiment", record_id)
        source_identity = document.doi or document.title or record_id
        paper_id = _node_id("paper", source_identity)
        evidence_id = _node_id("evidence", f"{record_id}|{document.evidence}")
        add_node(GraphNode(paper_id, "paper", document.title or document.doi or record_id, {"doi": document.doi, "title": document.title}))
        add_node(GraphNode(experiment_id, "experiment", record_id, {"record_id": record_id, "doi": document.doi, "title": document.title}))
        add_node(GraphNode(evidence_id, "evidence", f"Evidence for {record_id}", {"record_id": record_id, "quote": document.evidence, "source_file": document.source_file}))
        base = {"record_id": record_id, "doi": document.doi, "evidence": document.evidence}
        add_edge(GraphEdge(paper_id, "CONTAINS", experiment_id, **base))
        add_edge(GraphEdge(experiment_id, "SUPPORTED_BY", evidence_id, **base))

        metadata = _flatten_fields(document.fields or {})
        for kind, aliases in GRAPH_FIELD_ALIASES.items():
            for value in _field_values(metadata, aliases):
                entity_id = _node_id(kind, value)
                add_node(GraphNode(entity_id, kind, value, {"normalized": _normalize(value)}))
                add_edge(GraphEdge(experiment_id, RELATIONS[kind], entity_id, **base))
    return EvidenceKnowledgeGraph(nodes=nodes, edges=edges, evidence_fingerprint=graph_fingerprint(documents))


def load_or_build_knowledge_graph(documents: Sequence[Any], graph_path: Path | None = None) -> tuple[EvidenceKnowledgeGraph, str]:
    fingerprint = graph_fingerprint(documents)
    if graph_path is not None and graph_path.is_file():
        try:
            graph = EvidenceKnowledgeGraph.load(graph_path)
            if graph.evidence_fingerprint == fingerprint:
                return graph, "loaded"
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            pass
    return build_knowledge_graph(documents), "built_in_memory"


def graph_fingerprint(documents: Sequence[Any]) -> str:
    digest = hashlib.sha256()
    for document in documents:
        digest.update(str(document.record_id).encode("utf-8", errors="ignore"))
        digest.update(b"\0")
        digest.update(str(document.doi).encode("utf-8", errors="ignore"))
        digest.update(b"\0")
        digest.update(json.dumps(document.fields or {}, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8", errors="ignore"))
        digest.update(b"\n")
    return digest.hexdigest()


def _flatten_fields(fields: dict[str, Any]) -> dict[str, Any]:
    merged = dict(fields)
    nested = fields.get("fields")
    if isinstance(nested, dict):
        for key, value in nested.items():
            merged.setdefault(str(key), value)
    return merged


def _field_values(metadata: dict[str, Any], aliases: Iterable[str]) -> list[str]:
    lowered = {str(key).lower(): value for key, value in metadata.items()}
    values: list[str] = []
    for alias in aliases:
        value = lowered.get(alias.lower())
        if isinstance(value, dict):
            value = value.get("value")
        candidates = value if isinstance(value, list) else [value]
        for candidate in candidates:
            text = str(candidate).strip() if candidate is not None else ""
            if _normalize(text) not in UNKNOWN_VALUES and text not in values:
                values.append(text[:240])
        if values:
            break
    return values


def _intent_concepts(intent: dict[str, Any]) -> list[tuple[str, str]]:
    concepts: list[tuple[str, str]] = []
    for value in intent.get("enzymes", []):
        concepts.append(("enzyme", str(value)))
    for value in intent.get("outcomes", []):
        concepts.append(("metric", str(value)))
    for value in intent.get("context", []):
        concepts.append(("llps", str(value)))
    for key, value in (intent.get("constraints") or {}).items():
        concepts.append(("metric" if key == "parameter_type" else str(key), str(value)))
    return concepts


def _concept_matches(node_kind: str, node_value: str, concept_kind: str, concept_value: str) -> bool:
    value = _normalize(concept_value)
    if concept_kind == "llps":
        return node_kind in {"llps_component", "llps_trigger", "llps_state", "reaction_system"} and any(term in node_value for term in ("llps", "condensate", "phase separation", "droplet"))
    compatible = node_kind == concept_kind or (concept_kind == "condition" and node_kind in {"condition", "temperature", "ph", "time"})
    if not compatible:
        return False
    if concept_kind == "enzyme":
        aliases = {"dmt": ("dmt", "ggdmt1"), "oc": ("oc", "ggoc1"), "pt": ("pt", "ggpt1")}
        return any(alias in node_value for alias in aliases.get(value, (value,)))
    return value == node_value or value in node_value


def _node_id(kind: str, value: str) -> str:
    digest = hashlib.sha1(f"{kind}|{_normalize(value)}".encode("utf-8", errors="ignore")).hexdigest()[:20]
    return f"{kind}:{digest}"


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9_+\-'.]*", value.lower()) if token not in QUERY_STOPWORDS}


def _query_terms(question: str) -> set[str]:
    return _tokens(question)

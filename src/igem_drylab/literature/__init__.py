"""Minimal schema-first literature extraction utilities."""

from .extractor import build_prompt, extract_records_from_text
from .icl import IclExample, select_icl_examples
from .llm import ChatClient, parse_json_object
from .schema import ExtractionSchema, load_schema
from .database import build_database_from_manifest, mine_numeric_evidence, read_manifest
from .sources import LiteratureSearchQuery, LiteratureSearchResult, search_literature, write_search_manifest

__all__ = [
    "ChatClient",
    "ExtractionSchema",
    "IclExample",
    "LiteratureSearchQuery",
    "LiteratureSearchResult",
    "build_prompt",
    "build_database_from_manifest",
    "extract_records_from_text",
    "load_schema",
    "mine_numeric_evidence",
    "parse_json_object",
    "read_manifest",
    "select_icl_examples",
    "search_literature",
    "write_search_manifest",
]

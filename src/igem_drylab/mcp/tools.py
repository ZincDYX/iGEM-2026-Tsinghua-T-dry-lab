from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from igem_drylab.literature import build_prompt, extract_records_from_text, load_schema
from igem_drylab.literature.elsevier import extract_text_from_xml, fetch_article_xml, search_scopus
from igem_drylab.literature.icl import load_icl_examples
from igem_drylab.literature.llm import ChatClient
from igem_drylab.pipeline.adapters import create_tool_adapter
from igem_drylab.pipeline import load_config, run_pipeline

from .types import JsonObject, McpTool, McpToolResult, ToolHandler


def _schema(
    properties: JsonObject,
    required: list[str] | None = None,
    *,
    additional_properties: bool = False,
) -> JsonObject:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": additional_properties,
    }


def _require_str(arguments: JsonObject, key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Argument '{key}' must be a non-empty string")
    return value


def _optional_int(arguments: JsonObject, key: str, default: int, *, minimum: int | None = None) -> int:
    value = arguments.get(key, default)
    if not isinstance(value, int):
        raise ValueError(f"Argument '{key}' must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"Argument '{key}' must be >= {minimum}")
    return value


def _optional_path(arguments: JsonObject, key: str) -> Path | None:
    value = arguments.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"Argument '{key}' must be a non-empty string path")
    return Path(value)


def _read_text_file(arguments: JsonObject, path_key: str, inline_key: str) -> str:
    inline = arguments.get(inline_key)
    path = arguments.get(path_key)
    if isinstance(inline, str) and inline:
        return inline
    if isinstance(path, str) and path:
        return Path(path).read_text(encoding="utf-8")
    raise ValueError(f"Provide either '{inline_key}' or '{path_key}'")


def _secret_from_env(arguments: JsonObject, env_key: str, default_env_name: str) -> str:
    env_name = arguments.get(env_key, default_env_name)
    if not isinstance(env_name, str) or not env_name:
        raise ValueError(f"Argument '{env_key}' must be a non-empty environment variable name")
    value = os.getenv(env_name)
    if not value:
        raise ValueError(f"Environment variable '{env_name}' is not set")
    return value


def pipeline_validate(arguments: JsonObject) -> McpToolResult:
    config_path = Path(_require_str(arguments, "config_path"))
    config = load_config(config_path)
    return McpToolResult.ok(
        {
            "ok": True,
            "config_path": str(config_path),
            "run_id": config.run.id,
            "enzymes": [enzyme.id for enzyme in config.inputs.enzymes],
            "scaffolds": [scaffold.id for scaffold in config.inputs.scaffolds],
            "linkers": [linker.id for linker in config.inputs.linkers],
        }
    )


def pipeline_run(arguments: JsonObject) -> McpToolResult:
    config_path = Path(_require_str(arguments, "config_path"))
    output_dir = _optional_path(arguments, "output_dir")
    config = load_config(config_path)
    if output_dir is not None:
        config.run.output_dir = output_dir
    manifest = run_pipeline(config)
    return McpToolResult.ok(
        {
            "ok": True,
            "run_id": manifest.run_id,
            "run_dir": str(manifest.run_dir),
            "stages": [
                {
                    "stage": stage.stage,
                    "json_file": str(stage.json_file),
                    "csv_file": str(stage.csv_file),
                    "record_count": stage.record_count,
                }
                for stage in manifest.stages
            ],
        }
    )


def compute_check_tool(arguments: JsonObject) -> McpToolResult:
    config = load_config(Path(_require_str(arguments, "config_path")))
    tool_name = _require_str(arguments, "tool_name")
    adapter = create_tool_adapter(tool_name, config.tools.get(tool_name))
    description = adapter.describe()
    return McpToolResult.ok(
        {
            "ok": True,
            "tool_name": tool_name,
            "enabled": adapter.config.enabled,
            "mode": adapter.config.mode,
            "command": adapter.config.command,
            "repo_path": str(adapter.config.repo_path) if adapter.config.repo_path is not None else None,
            "available": adapter.is_available(),
            "description": description.model_dump(mode="json"),
        }
    )


def compute_run_tool(arguments: JsonObject) -> McpToolResult:
    config = load_config(Path(_require_str(arguments, "config_path")))
    tool_name = _require_str(arguments, "tool_name")
    output_dir = Path(_require_str(arguments, "output_dir"))
    context = arguments.get("context", {})
    if not isinstance(context, dict):
        raise ValueError("Argument 'context' must be an object")
    dry_run = bool(arguments.get("dry_run", False))
    timeout_seconds = _optional_int(arguments, "timeout_seconds", 3600, minimum=1)
    adapter = create_tool_adapter(tool_name, config.tools.get(tool_name))
    result = adapter.run(output_dir=output_dir, dry_run=dry_run, timeout_seconds=timeout_seconds, **context)
    return McpToolResult.ok({"ok": result.status not in {"failed", "missing_executable"}, "run": result.model_dump(mode="json")})


def literature_build_prompt(arguments: JsonObject) -> McpToolResult:
    text = _read_text_file(arguments, "text_file", "text")
    schema = load_schema(Path(_require_str(arguments, "schema_path")))
    examples = load_icl_examples(_optional_path(arguments, "icl_bank"))
    top_k = _optional_int(arguments, "top_k", 3, minimum=0)
    prompt = build_prompt(text=text, schema=schema, examples=examples, icl_top_k=top_k)
    out_path = _optional_path(arguments, "output_path")
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(prompt, encoding="utf-8")
    return McpToolResult.ok(
        {
            "ok": True,
            "prompt": prompt if out_path is None else None,
            "output_path": str(out_path) if out_path is not None else None,
            "example_count": len(examples),
            "top_k": top_k,
        }
    )


def literature_extract_records(arguments: JsonObject) -> McpToolResult:
    text = _read_text_file(arguments, "text_file", "text")
    schema = load_schema(Path(_require_str(arguments, "schema_path")))
    examples = load_icl_examples(_optional_path(arguments, "icl_bank"))
    top_k = _optional_int(arguments, "top_k", 3, minimum=0)
    client = ChatClient(
        api_key=_secret_from_env(arguments, "api_key_env", "DEEPSEEK_API_KEY"),
        api_base=_require_str(arguments, "api_base"),
        model=_require_str(arguments, "model"),
        temperature=float(arguments.get("temperature", 0.2)),
        timeout_seconds=_optional_int(arguments, "timeout_seconds", 180, minimum=1),
        retries=_optional_int(arguments, "retries", 3, minimum=1),
    )
    records = extract_records_from_text(text=text, schema=schema, examples=examples, client=client, icl_top_k=top_k)
    output_path = _optional_path(arguments, "output_path")
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps({"records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    return McpToolResult.ok(
        {
            "ok": True,
            "records": records,
            "record_count": len(records),
            "output_path": str(output_path) if output_path is not None else None,
        }
    )


def elsevier_search(arguments: JsonObject) -> McpToolResult:
    query = _require_str(arguments, "query")
    count = _optional_int(arguments, "count", 10, minimum=1)
    api_key = _secret_from_env(arguments, "api_key_env", "ELSEVIER_API_KEY")
    entries = search_scopus(api_key=api_key, query=query, count=count)
    return McpToolResult.ok({"ok": True, "query": query, "count": len(entries), "entries": entries})


def elsevier_fetch_article_text(arguments: JsonObject) -> McpToolResult:
    api_key = _secret_from_env(arguments, "api_key_env", "ELSEVIER_API_KEY")
    pii = arguments.get("pii")
    doi = arguments.get("doi")
    if pii is not None and not isinstance(pii, str):
        raise ValueError("Argument 'pii' must be a string when provided")
    if doi is not None and not isinstance(doi, str):
        raise ValueError("Argument 'doi' must be a string when provided")
    xml = fetch_article_xml(api_key=api_key, pii=pii, doi=doi)
    if xml is None:
        raise ValueError("Provide either 'pii' or 'doi'")
    text = extract_text_from_xml(xml)
    return McpToolResult.ok({"ok": True, "text": text, "character_count": len(text)})


PIPELINE_VALIDATE_TOOL = McpTool(
    name="igem.pipeline.validate",
    title="Validate M1-M4 pipeline config",
    description="Validate a YAML config and return the normalized run inputs.",
    input_schema=_schema({"config_path": {"type": "string", "description": "Path to project YAML config."}}, ["config_path"]),
    output_schema=_schema(
        {"ok": {"type": "boolean"}, "run_id": {"type": "string"}},
        additional_properties=True,
    ),
)

PIPELINE_RUN_TOOL = McpTool(
    name="igem.pipeline.run",
    title="Run M1-M4 pipeline",
    description="Run the local M1-M4 dry-lab pipeline and write JSON/CSV outputs.",
    input_schema=_schema(
        {
            "config_path": {"type": "string"},
            "output_dir": {"type": "string", "description": "Optional output directory override."},
        },
        ["config_path"],
    ),
    output_schema=_schema(
        {"ok": {"type": "boolean"}, "run_dir": {"type": "string"}, "stages": {"type": "array"}},
        additional_properties=True,
    ),
)

COMPUTE_CHECK_TOOL = McpTool(
    name="igem.compute.check_tool",
    title="Check configured compute tool",
    description="Inspect command template, mode, and executable availability for a scientific compute tool.",
    input_schema=_schema(
        {
            "config_path": {"type": "string"},
            "tool_name": {
                "type": "string",
                "description": "Tool key from YAML, e.g. abcfold, calvados, freesasa, autodock_vina.",
            },
        },
        ["config_path", "tool_name"],
    ),
    output_schema=_schema(
        {"ok": {"type": "boolean"}, "tool_name": {"type": "string"}, "available": {"type": "boolean"}},
        additional_properties=True,
    ),
)

COMPUTE_RUN_TOOL = McpTool(
    name="igem.compute.run_tool",
    title="Run configured compute tool",
    description="Render and optionally execute a scientific command-line tool from the YAML config.",
    input_schema=_schema(
        {
            "config_path": {"type": "string"},
            "tool_name": {"type": "string"},
            "output_dir": {"type": "string"},
            "context": {
                "type": "object",
                "description": "Template values used by the command, e.g. input_file, config_file, pdb_file.",
            },
            "dry_run": {"type": "boolean"},
            "timeout_seconds": {"type": "integer", "minimum": 1},
        },
        ["config_path", "tool_name", "output_dir"],
    ),
    output_schema=_schema({"ok": {"type": "boolean"}, "run": {"type": "object"}}, additional_properties=True),
)

LITERATURE_BUILD_PROMPT_TOOL = McpTool(
    name="igem.literature.build_prompt",
    title="Build literature extraction prompt",
    description="Build a schema-first extraction prompt with optional ICL examples.",
    input_schema=_schema(
        {
            "text": {"type": "string"},
            "text_file": {"type": "string"},
            "schema_path": {"type": "string"},
            "icl_bank": {"type": "string"},
            "top_k": {"type": "integer", "minimum": 0},
            "output_path": {"type": "string"},
        },
        ["schema_path"],
    ),
    output_schema=_schema(
        {"ok": {"type": "boolean"}, "prompt": {"type": ["string", "null"]}},
        additional_properties=True,
    ),
)

LITERATURE_EXTRACT_RECORDS_TOOL = McpTool(
    name="igem.literature.extract_records",
    title="Extract literature records",
    description="Call an OpenAI-compatible chat endpoint and parse JSON experimental records.",
    input_schema=_schema(
        {
            "text": {"type": "string"},
            "text_file": {"type": "string"},
            "schema_path": {"type": "string"},
            "icl_bank": {"type": "string"},
            "top_k": {"type": "integer", "minimum": 0},
            "api_key_env": {"type": "string", "default": "DEEPSEEK_API_KEY"},
            "api_base": {"type": "string"},
            "model": {"type": "string"},
            "temperature": {"type": "number"},
            "timeout_seconds": {"type": "integer", "minimum": 1},
            "retries": {"type": "integer", "minimum": 1},
            "output_path": {"type": "string"},
        },
        ["schema_path", "api_base", "model"],
    ),
    output_schema=_schema(
        {"ok": {"type": "boolean"}, "records": {"type": "array"}, "record_count": {"type": "integer"}},
        additional_properties=True,
    ),
)

ELSEVIER_SEARCH_TOOL = McpTool(
    name="igem.elsevier.search_scopus",
    title="Search Elsevier Scopus",
    description="Search Scopus through Elsevier API using an API key from an environment variable.",
    input_schema=_schema(
        {
            "query": {"type": "string"},
            "count": {"type": "integer", "minimum": 1},
            "api_key_env": {"type": "string", "default": "ELSEVIER_API_KEY"},
        },
        ["query"],
    ),
    output_schema=_schema(
        {"ok": {"type": "boolean"}, "entries": {"type": "array"}, "count": {"type": "integer"}},
        additional_properties=True,
    ),
)

ELSEVIER_FETCH_ARTICLE_TEXT_TOOL = McpTool(
    name="igem.elsevier.fetch_article_text",
    title="Fetch Elsevier article text",
    description="Fetch article XML by DOI or PII through Elsevier API and extract plain text.",
    input_schema=_schema(
        {
            "doi": {"type": "string"},
            "pii": {"type": "string"},
            "api_key_env": {"type": "string", "default": "ELSEVIER_API_KEY"},
        }
    ),
    output_schema=_schema(
        {"ok": {"type": "boolean"}, "text": {"type": "string"}, "character_count": {"type": "integer"}},
        additional_properties=True,
    ),
)

TOOL_BINDINGS: list[tuple[McpTool, ToolHandler]] = [
    (PIPELINE_VALIDATE_TOOL, pipeline_validate),
    (PIPELINE_RUN_TOOL, pipeline_run),
    (COMPUTE_CHECK_TOOL, compute_check_tool),
    (COMPUTE_RUN_TOOL, compute_run_tool),
    (LITERATURE_BUILD_PROMPT_TOOL, literature_build_prompt),
    (LITERATURE_EXTRACT_RECORDS_TOOL, literature_extract_records),
    (ELSEVIER_SEARCH_TOOL, elsevier_search),
    (ELSEVIER_FETCH_ARTICLE_TEXT_TOOL, elsevier_fetch_article_text),
]

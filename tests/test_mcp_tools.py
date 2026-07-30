from __future__ import annotations

import json
from pathlib import Path

from igem_drylab.mcp import create_default_registry


def test_registry_lists_mcp_style_tool_definitions():
    tools = create_default_registry().list_tools()
    names = {tool["name"] for tool in tools}

    assert "igem.pipeline.validate" in names
    assert "igem.pipeline.run" in names
    assert "igem.literature.build_prompt" in names
    assert all("inputSchema" in tool for tool in tools)


def test_pipeline_validate_tool_returns_structured_content():
    result = create_default_registry().call(
        "igem.pipeline.validate",
        {"config_path": "configs/m1_m4_example.yaml"},
    )

    payload = result.as_protocol_dict()
    assert result.is_error is False
    assert payload["structuredContent"]["ok"] is True
    assert payload["structuredContent"]["run_id"] == "m1-m4-demo"
    assert json.loads(payload["content"][0]["text"]) == payload["structuredContent"]


def test_pipeline_run_tool_writes_outputs(tmp_path):
    result = create_default_registry().call(
        "igem.pipeline.run",
        {"config_path": "configs/m1_m4_example.yaml", "output_dir": str(tmp_path)},
    )

    structured = result.as_protocol_dict()["structuredContent"]
    assert structured["ok"] is True
    assert Path(structured["run_dir"]).exists()
    assert len(structured["stages"]) == 4


def test_literature_build_prompt_tool_can_write_prompt(tmp_path):
    output_path = tmp_path / "prompt.txt"
    result = create_default_registry().call(
        "igem.literature.build_prompt",
        {
            "text_file": "examples/literature/glabridin_excerpt.txt",
            "schema_path": "data/schemas/glabridin_enzyme_catalysis.schema.json",
            "icl_bank": "data/icl/glabridin_examples.minimal.jsonl",
            "output_path": str(output_path),
        },
    )

    structured = result.as_protocol_dict()["structuredContent"]
    assert result.is_error is False
    assert structured["ok"] is True
    assert structured["prompt"] is None
    assert "Return JSON only" in output_path.read_text(encoding="utf-8")


def test_unknown_tool_returns_mcp_error_result():
    result = create_default_registry().call("missing.tool", {})
    structured = result.as_protocol_dict()["structuredContent"]

    assert result.is_error is True
    assert structured["ok"] is False
    assert structured["error"]["type"] == "unknown_tool"

"""Real stdio MCP transport for the existing scientific tool contracts."""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
from typing import Any

import jsonschema
from mcp import Client
from mcp.client.stdio import StdioServerParameters
from pydantic import BaseModel, ConfigDict

from .tools import NodeContext, ToolDefinition, ToolFailure, WorkflowTools


class McpArguments(BaseModel):
    model_config = ConfigDict(extra="allow")


# Explicit catalog, not substring dispatch. Human-only parameter mutations and
# configuration-path pipeline execution stay outside this generic tool catalog.
SCIENTIFIC_TOOLS = {
    "igem.m1.compute_features", "igem.m1.compute_protparam",
    "igem.m1.validate_construct_sequence", "igem.m1.screen_sequence",
    "igem.m1.parse_seg", "igem.m1.parse_iupred2a", "igem.m1.parse_secondary_structure",
    "igem.m2.pocket_sasa", "igem.m2.calculate_geometry", "igem.m2.screen_structure",
    "igem.m2.site_cooccupancy", "igem.m2.parse_structure_prediction", "igem.m2.compare_docking",
    "igem.m3.solve_equilibrium", "igem.m4.solve_steady_state", "igem.m4.analyze_steady_state",
}


def register_scientific_mcp(tools: WorkflowTools) -> None:
    package = Path(__file__).resolve().parents[1]
    implementations = tuple(sorted(package.rglob("*.py")))

    async def discover() -> list[dict[str, Any]]:
        parameters = StdioServerParameters(command=sys.executable, args=["-m", "igem_drylab.mcp.server"], cwd=package.parents[1])
        async with Client(parameters, read_timeout_seconds=30) as client:
            listed = await client.list_tools()
            return [tool.model_dump(mode="json", by_alias=True) for tool in listed.tools]

    # The server's actual names and schemas, not the in-process registry's
    # legacy aliases, are the authoritative transport contract.
    # App factories may themselves be called by an ASGI event loop. Bootstrap
    # discovery owns its short-lived loop in a worker, not the caller's loop.
    with ThreadPoolExecutor(max_workers=1) as bootstrap:
        metadata_list = bootstrap.submit(lambda: asyncio.run(discover())).result()
    for metadata in metadata_list:
        if metadata["name"] not in SCIENTIFIC_TOOLS:
            continue

        def make_handler(contract: dict[str, Any]):
            def invoke(payload: McpArguments, context: NodeContext) -> dict[str, Any]:
                arguments = payload.model_dump(mode="json")
                jsonschema.Draft202012Validator(contract["inputSchema"]).validate(arguments)

                async def call() -> dict[str, Any]:
                    parameters = StdioServerParameters(command=sys.executable, args=["-m", "igem_drylab.mcp.server"], cwd=package.parents[1])
                    async with Client(parameters, read_timeout_seconds=300) as client:
                        result = await client.call_tool(contract["name"], arguments)
                        if result.is_error:
                            raise ToolFailure("mcp_tool_failed", str(result.content))
                        if not isinstance(result.structured_content, dict):
                            raise ToolFailure("invalid_mcp_output", "Scientific tool returned no structured object")
                        return result.structured_content

                return asyncio.run(call())
            return invoke

        tools.register(ToolDefinition(
            metadata["name"], metadata.get("title") or metadata["name"], metadata.get("description") or "",
            "1", McpArguments, make_handler(metadata), "scientific_mcp", runtime="mcp_stdio",
            input_schema=metadata["inputSchema"], output_schema=metadata.get("outputSchema") or {"type": "object"},
            implementation_files=implementations,
        ))

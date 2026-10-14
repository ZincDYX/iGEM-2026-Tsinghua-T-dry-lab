"""Real stdio MCP transport for the existing scientific tool contracts."""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
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
    "igem.m2.site_cooccupancy", "igem.m2.parse_structure_prediction", "igem.m2.compare_docking", "igem.m2.assess_regions",
    "igem.m2.compare_enzyme", "igem.m2.expand_fusion", "igem.m2.place_recruitment", "igem.m2.recruitment_ensemble",
    "igem.m2.prepare_assembly", "igem.m2.assembly_accessibility", "igem.m2.secondary_context", "igem.m2.prepare_pocket",
    "igem.m1.import_fusion_results", "igem.m1.import_llps_results", "igem.m1.prioritize", "igem.m1.parse_mpipi",
    "igem.m1.analyse_phase_profile",
    "igem.m1.nominal_descriptors",
    "igem.m2.compare_core",
    "igem.m2.structure_volume",
    "igem.m3.solve_equilibrium", "igem.m3.ensemble", "igem.m4.solve_steady_state", "igem.m4.analyze_steady_state", "igem.m4.report",
    "igem.m2.membrane_geometry", "igem.m3.er_recruitment", "igem.m4.compartment_amounts", "igem.m4.compare_compartments",
}


def server_parameters(package: Path) -> StdioServerParameters:
    # MCP intentionally filters environment inheritance. Pass only numeric
    # runtime controls, never the desktop session token or unrelated secrets.
    runtime_env = {key: os.environ[key] for key in (
        "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "PYTHONUTF8"
    ) if key in os.environ}
    # Launch the exact source snapshot that discovered the contract, not an
    # unrelated globally installed checkout selected by the child interpreter.
    runtime_env["PYTHONPATH"] = str(package.parent)
    return StdioServerParameters(command=sys.executable, args=["-B", "-m", "igem_drylab.mcp.server"],
        cwd=package.parents[1], env=runtime_env)


def register_scientific_mcp(tools: WorkflowTools) -> None:
    package = Path(__file__).resolve().parents[1]
    implementations = tuple(sorted(package.rglob("*.py")))

    async def discover() -> list[dict[str, Any]]:
        parameters = server_parameters(package)
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
                    parameters = server_parameters(package)
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

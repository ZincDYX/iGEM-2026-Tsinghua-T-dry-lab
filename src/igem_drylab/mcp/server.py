"""Transport-level Model Context Protocol server for the dry-lab tools."""

from __future__ import annotations

from typing import Any, Literal

from mcp.server import MCPServer

from .registry import create_default_registry

server = MCPServer(
    name="igem-drylab-2026",
    title="iGEM 2026 Tsinghua-T dry-lab scientific tools",
    description="Auditable M1--M4 calculations and explicitly configured scientific tool execution.",
    version="0.1.0",
    instructions=(
        "Formal calculations require provenance-bearing real inputs. Missing scientific evidence must "
        "be returned as blocked or insufficient_data and must never be replaced by guessed values."
    ),
)


def _call_local(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    result = create_default_registry().call(name, arguments)
    if result.is_error:
        error = result.structured_content.get("error", {})
        raise ValueError(str(error.get("message", "local tool failed")))
    return result.structured_content


@server.tool(
    name="igem.m1.compute_features",
    title="Compute audited M1 V3 sequence features",
    description=(
        "Compute the exact M1 V3 sequence feature equations with a versioned definition file. "
        "The output is not an LLPS probability or functional score."
    ),
    structured_output=True,
)
def m1_compute_features(
    sequence: str,
    feature_definitions_file: str | None = None,
    forbidden_amino_acid_motifs: list[str] | None = None,
) -> dict[str, Any]:
    arguments: dict[str, Any] = {
        "sequence": sequence,
        "forbidden_amino_acid_motifs": forbidden_amino_acid_motifs or [],
    }
    if feature_definitions_file is not None:
        arguments["feature_definitions_file"] = feature_definitions_file
    return _call_local("igem.m1.compute_features", arguments)


@server.tool(
    name="igem.m1.screen_sequence",
    title="Apply M1 V3 negative-screen rules",
    description=(
        "Apply the exact M1 V3 negative-screen policy. Formal mode blocks on missing external "
        "IUPred2A, secondary-structure, and full-fusion evidence rather than imputing it."
    ),
    structured_output=True,
)
def m1_screen_sequence(
    sequence: str,
    sequence_kind: Literal["idr", "enzyme_ligand_linker", "scaffold_linker", "rigid_linker"],
    localization_context: Literal["cytosolic", "er_anchored"] = "cytosolic",
    feature_definitions_file: str | None = None,
    rules_file: str | None = None,
    forbidden_amino_acid_motifs: list[str] | None = None,
    disorder_evidence: dict[str, Any] | None = None,
    secondary_structure_evidence: dict[str, Any] | None = None,
    fusion_evidence: dict[str, Any] | None = None,
    require_external_evidence: bool = True,
) -> dict[str, Any]:
    arguments: dict[str, Any] = {
        "sequence": sequence,
        "sequence_kind": sequence_kind,
        "localization_context": localization_context,
        "forbidden_amino_acid_motifs": forbidden_amino_acid_motifs or [],
        "disorder_evidence": disorder_evidence,
        "secondary_structure_evidence": secondary_structure_evidence,
        "fusion_evidence": fusion_evidence,
        "require_external_evidence": require_external_evidence,
    }
    if feature_definitions_file is not None:
        arguments["feature_definitions_file"] = feature_definitions_file
    if rules_file is not None:
        arguments["rules_file"] = rules_file
    return _call_local("igem.m1.screen_sequence", arguments)


@server.tool(
    name="igem.m1.parse_iupred2a",
    title="Parse real IUPred2A output",
    description="Parse a versioned IUPred2A per-residue score file for the declared input sequence hash.",
    structured_output=True,
)
def m1_parse_iupred2a(
    path: str,
    tool_version: str,
    input_sha256: str,
    score_boundary: float = 0.5,
) -> dict[str, Any]:
    return _call_local(
        "igem.m1.parse_iupred2a",
        {
            "path": path,
            "tool_version": tool_version,
            "input_sha256": input_sha256,
            "score_boundary": score_boundary,
        },
    )


@server.tool(
    name="igem.m1.parse_secondary_structure",
    title="Parse real PSIPRED/JPred output",
    description="Parse a versioned PSIPRED SS2 or JPred state file for the declared input sequence hash.",
    structured_output=True,
)
def m1_parse_secondary_structure(
    path: str,
    tool_name: Literal["PSIPRED", "JPred"],
    tool_version: str,
    input_sha256: str,
) -> dict[str, Any]:
    return _call_local(
        "igem.m1.parse_secondary_structure",
        {
            "path": path,
            "tool_name": tool_name,
            "tool_version": tool_version,
            "input_sha256": input_sha256,
        },
    )


@server.tool(
    name="igem.compute.check_tool",
    title="Check an explicitly configured scientific executable",
    description="Resolve the configured command and report whether its real executable is available.",
    structured_output=True,
)
def check_external_tool(config_path: str, tool_name: str) -> dict[str, Any]:
    return _call_local("igem.compute.check_tool", {"config_path": config_path, "tool_name": tool_name})


@server.tool(
    name="igem.compute.run_tool",
    title="Run an explicitly configured scientific executable",
    description=(
        "Execute the configured external command without a shell, persist its manifest, and return "
        "missing_executable/failed rather than substituting mock scientific output."
    ),
    structured_output=True,
)
def run_external_tool(
    config_path: str,
    tool_name: str,
    output_dir: str,
    context: dict[str, Any],
    timeout_seconds: int = 3600,
    dry_run: bool = False,
) -> dict[str, Any]:
    return _call_local(
        "igem.compute.run_tool",
        {
            "config_path": config_path,
            "tool_name": tool_name,
            "output_dir": output_dir,
            "context": context,
            "timeout_seconds": timeout_seconds,
            "dry_run": dry_run,
        },
    )


def main() -> None:
    """Run the production MCP server over stdio."""

    server.run(transport="stdio")


if __name__ == "__main__":
    main()

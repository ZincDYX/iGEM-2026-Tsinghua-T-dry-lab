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
    name="igem.m2.calculate_geometry",
    title="Calculate M2 V2 C-alpha geometry",
    description=(
        "Kabsch-align declared core C-alpha atoms and calculate core/pocket C-alpha RMSD, optional "
        "tail distance, and explicit inter-module heavy-atom clashes."
    ),
    structured_output=True,
)
def m2_calculate_geometry(
    reference_pdb: str,
    model_pdb: str,
    reference_chain: str,
    model_chain: str,
    core_residues: list[int],
    pocket_residues: list[int],
    core_residue_mapping: list[dict[str, int]] | None = None,
    pocket_residue_mapping: list[dict[str, int]] | None = None,
    tail_residues: list[int] | None = None,
    first_module_chain: str | None = None,
    first_module_residues: list[int] | None = None,
    second_module_chain: str | None = None,
    second_module_residues: list[int] | None = None,
    clash_cutoff_angstrom: float | None = None,
) -> dict[str, Any]:
    arguments: dict[str, Any] = {
        "reference_pdb": reference_pdb,
        "model_pdb": model_pdb,
        "reference_chain": reference_chain,
        "model_chain": model_chain,
        "core_residues": core_residues,
        "pocket_residues": pocket_residues,
    }
    optional = {
        "tail_residues": tail_residues,
        "core_residue_mapping": core_residue_mapping,
        "pocket_residue_mapping": pocket_residue_mapping,
        "first_module_chain": first_module_chain,
        "first_module_residues": first_module_residues,
        "second_module_chain": second_module_chain,
        "second_module_residues": second_module_residues,
        "clash_cutoff_angstrom": clash_cutoff_angstrom,
    }
    arguments.update({key: value for key, value in optional.items() if value is not None})
    return _call_local("igem.m2.calculate_geometry", arguments)


@server.tool(
    name="igem.m2.screen_structure",
    title="Apply M2 V2 confidence-gated negative screen",
    description=(
        "Apply the explicit 0.70 pocket-SASA and 4 A core-C-alpha-RMSD rules after pLDDT gating. "
        "No composite structure score is generated."
    ),
    structured_output=True,
)
def m2_screen_structure(metrics: dict[str, Any]) -> dict[str, Any]:
    return _call_local("igem.scoring.m2_structure", metrics)


@server.tool(
    name="igem.m2.site_cooccupancy",
    title="Solve species-specific M2 co-occupancy",
    description=(
        "Solve an explicit OC/DMT clash graph and return species-specific feasible ranges and Pareto "
        "combinations without inventing one shared eta."
    ),
    structured_output=True,
)
def m2_site_cooccupancy(graph: dict[str, Any]) -> dict[str, Any]:
    return _call_local("igem.m2.site_cooccupancy", graph)


@server.tool(
    name="igem.m2.pocket_sasa",
    title="Calculate same-residue FreeSASA retention",
    description="Compare declared pocket residues and apply the M2 V2 0.70 retention boundary.",
    structured_output=True,
)
def m2_pocket_sasa(
    chain: str,
    residues: list[int],
    model_json: str | None = None,
    reference_json: str | None = None,
    model_pdb: str | None = None,
    reference_pdb: str | None = None,
    threshold_loss_fraction: float = 0.30,
    model_configuration_hash: str | None = None,
    reference_configuration_hash: str | None = None,
) -> dict[str, Any]:
    arguments: dict[str, Any] = {
        "chain": chain,
        "residues": residues,
        "threshold_loss_fraction": threshold_loss_fraction,
        "model_configuration_hash": model_configuration_hash,
        "reference_configuration_hash": reference_configuration_hash,
    }
    optional = {
        "model_json": model_json,
        "reference_json": reference_json,
        "model_pdb": model_pdb,
        "reference_pdb": reference_pdb,
    }
    arguments.update({key: value for key, value in optional.items() if value is not None})
    return _call_local("igem.scoring.pocket_sasa", arguments)


@server.tool(
    name="igem.m2.parse_structure_prediction",
    title="Parse real structure-prediction artifacts",
    description="Parse version-specific ColabFold/AF3/ABCFold/Boltz/Chai confidence artifacts without inventing missing metrics.",
    structured_output=True,
)
def m2_parse_structure_prediction(path: str, candidate_id: str | None = None) -> dict[str, Any]:
    arguments: dict[str, Any] = {"path": path}
    if candidate_id is not None:
        arguments["candidate_id"] = candidate_id
    return _call_local("igem.parsers.structure_prediction", arguments)


@server.tool(
    name="igem.m2.compare_docking",
    title="Compare same-ligand M2 docking runs",
    description=(
        "Calculate fusion minus reference Vina score only when configuration and ligand hashes match. "
        "The result is not Kd, kcat, activity, an activity multiplier, or a standalone reject rule."
    ),
    structured_output=True,
)
def m2_compare_docking(
    candidate_id: str,
    reference_vina_output: str,
    fusion_vina_output: str,
    reference_configuration_hash: str,
    fusion_configuration_hash: str,
    reference_ligand_hash: str,
    fusion_ligand_hash: str,
) -> dict[str, Any]:
    return _call_local(
        "igem.scoring.docking_penalty",
        {
            "candidate_id": candidate_id,
            "reference_vina_output": reference_vina_output,
            "fusion_vina_output": fusion_vina_output,
            "reference_configuration_hash": reference_configuration_hash,
            "fusion_configuration_hash": fusion_configuration_hash,
            "reference_ligand_hash": reference_ligand_hash,
            "fusion_ligand_hash": fusion_ligand_hash,
        },
    )


@server.tool(
    name="igem.m3.solve_equilibrium",
    title="Solve M3 S1-S5 and E1-E10 equilibrium",
    description=(
        "Solve the documented two-phase OC/DMT free-plus-bound mass balances. Capacity conflicts are "
        "reported without the non-conserving proportional rescaling from the draft."
    ),
    structured_output=True,
)
def m3_solve_equilibrium(inputs: dict[str, Any]) -> dict[str, Any]:
    return _call_local("igem.m3.solve_equilibrium", inputs)


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

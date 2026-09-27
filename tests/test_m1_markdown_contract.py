from __future__ import annotations

import asyncio
from hashlib import sha256
from pathlib import Path
import sys

import pytest
import yaml

from igem_drylab.constructs import (
    FusionToolEvidence,
    M1FeatureDefinitions,
    M1V3Rules,
    SecondaryStructureEvidence,
    compute_sequence_features,
    parse_iupred2a_output,
    screen_sequence_v3,
)


ROOT = Path(__file__).resolve().parents[1]


def _definitions():
    return M1FeatureDefinitions.from_yaml(ROOT / "configs" / "m1_feature_definitions.yaml")


def _rules() -> M1V3Rules:
    return M1V3Rules.model_validate(
        yaml.safe_load((ROOT / "configs" / "m1_rules_v3.yaml").read_text(encoding="utf-8"))
    )


def test_m1_feature_equations_match_markdown_definitions() -> None:
    definitions, digest = _definitions()
    result = compute_sequence_features("GSAKRDEFWY", definitions=definitions, definitions_sha256=digest)

    assert result.length == 10
    assert result.gs_fraction == pytest.approx(0.2)
    assert result.aromatic_fraction == pytest.approx(0.3)
    assert result.hydrophobic_fraction == pytest.approx(0.4)
    assert result.net_charge_proxy == pytest.approx(0.0)
    assert result.shannon_entropy == pytest.approx(3.321928094887362)
    assert result.top2_fraction == pytest.approx(0.2)
    assert result.max_hydrophobic_run == 3
    assert result.feature_definitions_sha256 == digest
    assert result.charge_blockiness is None
    assert result.multivalency_density is None


def test_iupred_parser_calculates_mean_fraction_and_runs(tmp_path: Path) -> None:
    output = tmp_path / "iupred.txt"
    output.write_text("1 A 0.8\n2 A 0.7\n3 A 0.2\n4 A 0.1\n", encoding="utf-8")
    evidence = parse_iupred2a_output(output, tool_version="2A", input_sha256="abc")

    assert evidence.disorder_mean == pytest.approx(0.45)
    assert evidence.disorder_fraction == pytest.approx(0.5)
    assert evidence.longest_disordered_run == 2
    assert evidence.longest_folded_run == 2


def test_v3_screen_passes_only_with_matching_external_evidence(tmp_path: Path) -> None:
    sequence = "GGGGSGGGGS"
    sequence_hash = sha256(sequence.encode("ascii")).hexdigest()
    definitions, digest = _definitions()
    features = compute_sequence_features(sequence, definitions=definitions, definitions_sha256=digest)
    ss = SecondaryStructureEvidence(
        tool_name="PSIPRED",
        tool_version="4.0",
        source_file=tmp_path / "x.ss2",
        input_sha256=sequence_hash,
        states="C" * len(sequence),
        ss_fraction=0.0,
        longest_ss_run=0,
    )
    fusion = FusionToolEvidence(
        signalp_tool_version="6.0",
        signalp_source_file=tmp_path / "signalp.json",
        signal_peptide_with_clear_cleavage=False,
        deeptmhmm_tool_version="1.0",
        deeptmhmm_source_file=tmp_path / "tm.json",
        transmembrane_helix_count=0,
        aggregation_tool="PASTA2",
        aggregation_tool_version="2.0",
        aggregation_source_file=tmp_path / "pasta.txt",
        continuous_high_aggregation_hotspots=0,
    )

    result = screen_sequence_v3(
        features=features,
        sequence_kind="scaffold_linker",
        rules=_rules(),
        secondary_structure=ss,
        fusion_evidence=fusion,
    )

    assert result.verdict == "pass"
    assert result.rank_score is None


def test_v3_screen_blocks_when_required_predictor_outputs_are_missing() -> None:
    definitions, digest = _definitions()
    features = compute_sequence_features("GGGGSGGGGS", definitions=definitions, definitions_sha256=digest)
    result = screen_sequence_v3(
        features=features,
        sequence_kind="scaffold_linker",
        rules=_rules(),
        require_external_evidence=True,
    )

    assert result.verdict == "blocked"
    assert "PSIPRED_or_JPred_output" in result.missing_required_evidence
    assert "SignalP_full_fusion_output" in result.missing_required_evidence


def test_transport_level_mcp_server_lists_and_calls_m1_tool() -> None:
    from mcp import Client
    from igem_drylab.mcp.server import server

    async def exercise() -> None:
        async with Client(server) as client:
            tools = await client.list_tools()
            names = {item.name for item in tools.tools}
            assert "igem.m1.compute_features" in names
            response = await client.call_tool("igem.m1.compute_features", {"sequence": "GGGGS"})
            assert response.is_error is not True
            assert response.structured_content["result"]["length"] == 5

    asyncio.run(exercise())


def test_stdio_mcp_server_is_launchable_and_callable() -> None:
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters

    async def exercise() -> None:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "igem_drylab.mcp.server"],
            cwd=ROOT,
        )
        async with Client(params, read_timeout_seconds=20) as client:
            response = await client.call_tool("igem.m1.compute_features", {"sequence": "GGGGS"})
            assert response.is_error is not True
            assert response.structured_content["result"]["formula_version"] == "m1-v3-2026-09-27"

    asyncio.run(exercise())

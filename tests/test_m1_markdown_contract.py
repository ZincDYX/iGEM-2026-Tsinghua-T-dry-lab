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
    ProtParamEvidence,
    SegEvidence,
    SecondaryStructureEvidence,
    assemble_and_validate_construct,
    compute_protparam_evidence,
    compute_sequence_features,
    parse_iupred2a_output,
    parse_seg_fasta,
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
    # Ten distinct equally frequent residues => H=log2(10), GS=2/10, FWY=3/10.
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


def test_m1_step0_assembles_translates_and_records_boundaries() -> None:
    result = assemble_and_validate_construct(
        construct_id="construct",
        ordered_part_ids=["enzyme", "linker"],
        part_sequences={"enzyme": "MA", "linker": "GG"},
        coding_dna="ATGGCTGGTGGTTAA",
        forbidden_restriction_sites={"synthetic_test_site": "GGTGGT"},
        require_sequence_evidence=True,
    )

    assert result.status == "valid"
    assert result.full_protein_sequence == "MAGG"
    assert [(item.part_id, item.start_aa, item.end_aa) for item in result.part_boundaries] == [
        ("enzyme", 1, 2),
        ("linker", 3, 4),
    ]
    assert result.restriction_hits[0].start_nt == 7


def test_m1_step0_blocks_missing_sequence_evidence_and_rejects_translation_mismatch() -> None:
    missing = assemble_and_validate_construct(
        construct_id="missing",
        ordered_part_ids=["part"],
        part_sequences={"part": "MA"},
        coding_dna=None,
        forbidden_restriction_sites=None,
        require_sequence_evidence=True,
    )
    mismatch = assemble_and_validate_construct(
        construct_id="mismatch",
        ordered_part_ids=["part"],
        part_sequences={"part": "MA"},
        coding_dna="ATGGGTTAA",
        forbidden_restriction_sites={},
        require_sequence_evidence=True,
    )

    assert missing.status == "blocked"
    assert set(missing.missing_inputs) == {"sequenced_coding_dna", "wetlab_forbidden_restriction_site_list"}
    assert mismatch.status == "invalid"
    assert mismatch.errors == ["coding_dna_translation_does_not_match_assembled_protein"]


def test_seg_and_protparam_produce_versioned_cross_checks(tmp_path: Path) -> None:
    sequence = "AAGGSS"
    sequence_hash = sha256(sequence.encode("ascii")).hexdigest()
    seg_file = tmp_path / "seg.fasta"
    seg_file.write_text(">candidate\nAAggXX\n", encoding="utf-8")

    seg = parse_seg_fasta(
        seg_file,
        tool_version="2.16.0+",
        input_sha256=sequence_hash,
        expected_length=len(sequence),
    )
    protparam = compute_protparam_evidence(sequence, input_sha256=sequence_hash)

    assert seg.low_complexity_positions == [3, 4, 5, 6]
    assert seg.low_complexity_fraction == pytest.approx(4 / 6)
    assert protparam.input_sha256 == sequence_hash
    assert protparam.molecular_weight_da > 0
    assert 0 <= protparam.theoretical_pi <= 14


def test_iupred_parser_calculates_mean_fraction_and_runs(tmp_path: Path) -> None:
    output = tmp_path / "iupred.txt"
    output.write_text("1 A 0.8\n2 A 0.7\n3 A 0.2\n4 A 0.1\n", encoding="utf-8")
    evidence = parse_iupred2a_output(output, tool_version="2A", input_sha256=sha256(b"AAAA").hexdigest())

    assert evidence.disorder_mean == pytest.approx(0.45)
    assert evidence.disorder_fraction == pytest.approx(0.5)
    assert evidence.longest_disordered_run == 2
    assert evidence.longest_folded_run == 2


def test_v3_screen_blocks_unbound_external_evidence_declarations(tmp_path: Path) -> None:
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
        input_sha256=sequence_hash,
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
    seg = SegEvidence(
        tool_version="2.16.0+",
        source_file=tmp_path / "seg.fasta",
        input_sha256=sequence_hash,
        sequence_length=len(sequence),
        low_complexity_positions=[],
        low_complexity_fraction=0.0,
    )
    protparam = ProtParamEvidence(
        tool_version="1.85",
        input_sha256=sequence_hash,
        molecular_weight_da=700.0,
        theoretical_pi=6.0,
        amino_acid_counts={"G": 8, "S": 2},
    )

    result = screen_sequence_v3(
        features=features,
        sequence_kind="scaffold_linker",
        rules=_rules(),
        secondary_structure=ss,
        seg=seg,
        protparam=protparam,
        fusion_evidence=fusion,
        full_fusion_sha256=sequence_hash,
    )

    assert result.verdict == "blocked"  # declarations without real byte-bound artifacts never qualify
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
            listed = await client.list_tools()
            names = {item.name for item in listed.tools}
            assert "igem.m1.validate_construct_sequence" in names
            assert "igem.m1.compute_protparam" in names
            assert "igem.m1.parse_seg" in names
            response = await client.call_tool("igem.m1.compute_features", {"sequence": "GGGGS"})
            assert response.is_error is not True
            assert response.structured_content["result"]["formula_version"] == "m1-v3-2026-09-27"
            qc = await client.call_tool(
                "igem.m1.validate_construct_sequence",
                {
                    "construct_id": "stdio",
                    "ordered_part_ids": ["part"],
                    "part_sequences": {"part": "MA"},
                    "coding_dna": "ATGGCTTAA",
                    "forbidden_restriction_sites": {},
                },
            )
            assert qc.structured_content["result"]["status"] == "valid"

    asyncio.run(exercise())

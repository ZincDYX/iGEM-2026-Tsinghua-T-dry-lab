from __future__ import annotations

import asyncio
from pathlib import Path
import sys

import pytest

from igem_drylab.parsers.freesasa import compute_pocket_sasa_retention
from igem_drylab.scoring.m2_structure import M2StructureMetrics, score_m2_structure
from igem_drylab.scoring.m2_site_geometry import M2SiteGeometryInput, analyse_site_cooccupancy
from igem_drylab.structure_metrics import aligned_ca_rmsds, count_inter_module_clashes


ROOT = Path(__file__).resolve().parents[1]


def _atom_line(serial: int, name: str, residue: int, chain: str, xyz: tuple[float, float, float]) -> str:
    x, y, z = xyz
    return (
        f"ATOM  {serial:5d} {name:^4s} ALA {chain:1s}{residue:4d}    "
        f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00 80.00          {name[0]:>2s}\n"
    )


def _write_ca_pair(tmp_path: Path) -> tuple[Path, Path]:
    reference = tmp_path / "reference.pdb"
    model = tmp_path / "model.pdb"
    reference.write_text(
        "".join(
            _atom_line(index, "CA", residue, "A", xyz)
            for index, (residue, xyz) in enumerate(
                [(1, (0.0, 0.0, 0.0)), (2, (2.0, 0.0, 0.0)), (3, (0.0, 2.0, 0.0)), (4, (1.0, 1.0, 0.0))],
                start=1,
            )
        ),
        encoding="utf-8",
    )
    model.write_text(
        "".join(
            _atom_line(index, "CA", residue, "B", xyz)
            for index, (residue, xyz) in enumerate(
                [
                    (101, (5.0, -2.0, 3.0)),
                    (102, (7.0, -2.0, 3.0)),
                    (103, (5.0, 0.0, 3.0)),
                    (104, (6.0, -1.0, 8.0)),
                ],
                start=1,
            )
        ),
        encoding="utf-8",
    )
    return reference, model


def _complete_metrics(**updates: object) -> M2StructureMetrics:
    payload: dict[str, object] = {
        "candidate_id": "candidate",
        "core_ca_rmsd_angstrom": 0.5,
        "sasa_retention": 0.9,
        "pocket_rmsd_angstrom": 1.0,
        "mean_plddt": 85.0,
        "clash_count": 0,
        "clash_cutoff_angstrom": 2.5,
    }
    payload.update(updates)
    return M2StructureMetrics.model_validate(payload)


def test_m2_kabsch_formulas_use_explicit_residue_mapping(tmp_path: Path) -> None:
    reference, model = _write_ca_pair(tmp_path)
    result = aligned_ca_rmsds(
        reference,
        model,
        reference_chain="A",
        model_chain="B",
        core_residues=[],
        pocket_residues=[],
        core_residue_mapping=[(1, 101), (2, 102), (3, 103)],
        pocket_residue_mapping=[(4, 104)],
    )

    assert result["core_ca_rmsd_angstrom"] == pytest.approx(0.0, abs=1e-12)
    assert result["pocket_ca_rmsd_angstrom"] == pytest.approx(5.0)
    assert result["matched_core_ca_count"] == 3
    assert result["matched_pocket_ca_count"] == 1


def test_m2_clash_formula_counts_heavy_atom_pairs_below_reviewed_cutoff(tmp_path: Path) -> None:
    pdb = tmp_path / "clash.pdb"
    pdb.write_text(
        _atom_line(1, "C", 1, "A", (0.0, 0.0, 0.0))
        + _atom_line(2, "C", 2, "B", (2.49, 0.0, 0.0))
        + _atom_line(3, "N", 2, "B", (3.0, 0.0, 0.0)),
        encoding="utf-8",
    )

    result = count_inter_module_clashes(
        pdb,
        first_chain="A",
        first_residues=[1],
        second_chain="B",
        second_residues=[2],
        cutoff_angstrom=2.5,
    )

    assert result["clash_count"] == 1
    assert result["minimum_distance_angstrom"] == pytest.approx(2.49)


def test_m2_explicit_boundaries_and_confidence_gates() -> None:
    boundary = score_m2_structure(_complete_metrics(sasa_retention=0.70, core_ca_rmsd_angstrom=4.0))
    high_failure = score_m2_structure(_complete_metrics(sasa_retention=0.699, core_ca_rmsd_angstrom=4.01))
    medium_failure = score_m2_structure(
        _complete_metrics(mean_plddt=70.0, sasa_retention=0.6, core_ca_rmsd_angstrom=5.0)
    )
    low_confidence = score_m2_structure(_complete_metrics(mean_plddt=49.9))

    assert boundary.verdict == "pass"
    assert high_failure.verdict == "reject"
    assert high_failure.status == "valid"
    assert medium_failure.verdict == "review"
    assert medium_failure.recommended_for_m3 is False
    assert low_confidence.verdict == "blocked"


def test_pocket_rmsd_is_reported_without_an_unauthorized_numeric_reject_boundary() -> None:
    result = score_m2_structure(_complete_metrics(pocket_rmsd_angstrom=8.0))

    assert result.verdict == "pass"
    assert "pocket_rmsd_angstrom" in result.available_metrics


def test_single_rigid_clash_is_review_but_persistent_direct_occlusion_can_reject() -> None:
    rigid = score_m2_structure(_complete_metrics(clash_count=12))
    persistent = score_m2_structure(
        _complete_metrics(
            clash_count=12,
            independent_conformation_count=3,
            severe_clash_conformation_count=3,
            persistent_severe_clash=True,
            direct_pocket_occlusion=True,
            mean_interdomain_pae=5.0,
            crossdomain_geometry_reviewed=True,
            crossdomain_geometry_source_ref="synthetic-independent-conformations",
        )
    )

    assert rigid.verdict == "review"
    assert persistent.verdict == "reject"


def test_json_sasa_comparison_blocks_without_matching_configuration_hashes() -> None:
    result = compute_pocket_sasa_retention(
        model_json=Path("examples/real_metrics/freesasa_model.json"),
        reference_json=Path("examples/real_metrics/freesasa_reference.json"),
        chain="A",
        residues=[10, 11, 12],
        model_configuration_hash="model-config",
        reference_configuration_hash="reference-config",
    )

    assert result.status == "insufficient_data"
    assert result.same_configuration_verified is False
    assert result.passes is None


def test_site_conflict_graph_returns_species_specific_pareto_combinations() -> None:
    result = analyse_site_cooccupancy(
        M2SiteGeometryInput(
            scaffold_id="reviewed-test-scaffold",
            assembly_applicability_confirmed=True,
            assembly_subunit_count=1,
            sh3_sites_per_subunit=2,
            pdz_sites_per_subunit=1,
            sites=[
                {"site_id": "oc-1", "species": "OC"},
                {"site_id": "oc-2", "species": "OC"},
                {"site_id": "dmt-1", "species": "DMT"},
            ],
            conflict_edges=[("oc-1", "dmt-1"), ("oc-2", "dmt-1")],
            model_ids=["template-placement-1"],
            clash_rule_provenance="m2-v2:d_cut=2.5A-heavy-atoms",
        )
    )

    assert result.nominal_sh3_sites == 2
    assert result.nominal_pdz_sites == 1
    assert result.maximum_total_cooccupancy == 2
    assert {(item.oc_count, item.dmt_count) for item in result.pareto_cooccupancy_combinations} == {(0, 1), (2, 0)}
    assert result.eta_binding_geometry is None


def test_fth1_nominal_counts_are_withheld_without_assembly_applicability_confirmation() -> None:
    result = analyse_site_cooccupancy(
        M2SiteGeometryInput(
            scaffold_id="FTH1",
            sites=[{"site_id": "oc-1", "species": "OC"}],
            model_ids=["reference-only"],
            clash_rule_provenance="m2-v2:d_cut=2.5A-heavy-atoms",
        )
    )

    assert result.status == "insufficient_data"
    assert result.m3_ready is False
    assert result.nominal_sh3_sites is None


def test_official_mcp_server_lists_and_calls_m2_geometry(tmp_path: Path) -> None:
    from mcp import Client
    from igem_drylab.mcp.server import server

    reference, model = _write_ca_pair(tmp_path)

    async def exercise() -> None:
        async with Client(server) as client:
            tools = await client.list_tools()
            names = {item.name for item in tools.tools}
            assert {
                "igem.m2.calculate_geometry",
                "igem.m2.screen_structure",
                "igem.m2.pocket_sasa",
                "igem.m2.compare_docking",
                "igem.m2.site_cooccupancy",
            } <= names
            response = await client.call_tool(
                "igem.m2.calculate_geometry",
                {
                    "reference_pdb": str(reference),
                    "model_pdb": str(model),
                    "reference_chain": "A",
                    "model_chain": "B",
                    "core_residues": [1, 2, 3],
                    "pocket_residues": [4],
                    "core_residue_mapping": [
                        {"reference_residue": 1, "model_residue": 101},
                        {"reference_residue": 2, "model_residue": 102},
                        {"reference_residue": 3, "model_residue": 103},
                    ],
                    "pocket_residue_mapping": [{"reference_residue": 4, "model_residue": 104}],
                },
            )
            assert response.is_error is not True
            assert response.structured_content["result"]["pocket_ca_rmsd_angstrom"] == pytest.approx(5.0)
            assert len(response.structured_content["result"]["model_pdb_sha256"]) == 64
            screen = await client.call_tool(
                "igem.m2.screen_structure",
                {
                    "metrics": {
                        "candidate_id": "mcp-candidate",
                        "core_ca_rmsd_angstrom": 0.5,
                        "sasa_retention": 0.9,
                        "pocket_rmsd_angstrom": 1.0,
                        "mean_plddt": 85.0,
                        "clash_count": 0,
                        "clash_cutoff_angstrom": 2.5,
                    }
                },
            )
            assert screen.is_error is not True
            assert screen.structured_content["result"]["verdict"] == "pass"

    asyncio.run(exercise())


def test_stdio_mcp_server_calls_m2_screen() -> None:
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters

    async def exercise() -> None:
        params = StdioServerParameters(command=sys.executable, args=["-m", "igem_drylab.mcp.server"], cwd=ROOT)
        async with Client(params, read_timeout_seconds=20) as client:
            response = await client.call_tool(
                "igem.m2.screen_structure",
                {
                    "metrics": {
                        "candidate_id": "stdio-m2",
                        "core_ca_rmsd_angstrom": 0.5,
                        "sasa_retention": 0.9,
                        "pocket_rmsd_angstrom": 1.0,
                        "mean_plddt": 85.0,
                        "clash_count": 0,
                        "clash_cutoff_angstrom": 2.5,
                    }
                },
            )
            assert response.is_error is not True
            assert response.structured_content["result"]["formula_version"] == "m2-v2-2026-09-27"
            assert response.structured_content["result"]["verdict"] == "pass"

    asyncio.run(exercise())

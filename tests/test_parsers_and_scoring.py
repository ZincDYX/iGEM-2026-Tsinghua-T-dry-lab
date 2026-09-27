from __future__ import annotations

from pathlib import Path

from igem_drylab.kinetics import CascadeParameters
from igem_drylab.parsers.freesasa import compute_pocket_sasa_retention, parse_freesasa_json
from igem_drylab.parsers.vina import parse_vina_output
from igem_drylab.scoring.m2_structure import M2StructureMetrics, score_m2_structure
from igem_drylab.scoring.m4_reaction import compute_docking_penalty, score_m4_ode


def test_freesasa_json_parser_and_retention():
    areas = parse_freesasa_json(Path("examples/real_metrics/freesasa_model.json"))
    result = compute_pocket_sasa_retention(
        model_json=Path("examples/real_metrics/freesasa_model.json"),
        reference_json=Path("examples/real_metrics/freesasa_reference.json"),
        chain="A",
        residues=[10, 11, 12],
        model_configuration_hash="freesasa-default-v1",
        reference_configuration_hash="freesasa-default-v1",
    )

    assert len(areas) == 3
    assert round(result.retention, 3) == 0.907
    assert result.passes is True


def test_vina_parser_and_docking_penalty():
    parsed = parse_vina_output(Path("examples/real_metrics/vina_reference.txt"))
    penalty = compute_docking_penalty(
        candidate_id="demo",
        reference_vina_output=Path("examples/real_metrics/vina_reference.txt"),
        fusion_vina_output=Path("examples/real_metrics/vina_fusion.txt"),
        reference_configuration_hash="vina-config-v1",
        fusion_configuration_hash="vina-config-v1",
        reference_ligand_hash="ligand-v1",
        fusion_ligand_hash="ligand-v1",
    )

    assert parsed.best_affinity_kcal_mol == -7.8
    assert penalty.delta_delta_g_kcal_mol == 0.7
    assert penalty.status == "valid"
    assert penalty.passes is None


def test_m2_structure_rule_based_score_flags_bad_geometry():
    good = score_m2_structure(
        M2StructureMetrics(
            candidate_id="good",
            core_ca_rmsd_angstrom=0.6,
            sasa_retention=0.9,
            pocket_rmsd_angstrom=0.8,
            iptm=0.8,
            mean_plddt=85,
            interface_contact_count=30,
            clash_count=0,
            clash_cutoff_angstrom=2.5,
        )
    )
    bad = score_m2_structure(
        M2StructureMetrics(
            candidate_id="bad",
            core_ca_rmsd_angstrom=1.2,
            sasa_retention=0.6,
            pocket_rmsd_angstrom=2.5,
            iptm=0.3,
            mean_plddt=85,
            interface_contact_count=0,
            clash_count=8,
            clash_cutoff_angstrom=2.5,
        )
    )

    assert good.recommended_for_m3 is True
    assert bad.recommended_for_m3 is False
    assert good.verdict == "pass"
    assert bad.verdict == "reject"
    assert good.heuristic_structure_risk is None
    assert bad.heuristic_structure_risk is None


def test_m4_lightweight_ode_score_uses_docking_penalty():
    penalty = compute_docking_penalty(
        candidate_id="demo",
        reference_vina_output=Path("examples/real_metrics/vina_reference.txt"),
        fusion_vina_output=Path("examples/real_metrics/vina_fusion.txt"),
        reference_configuration_hash="vina-config-v1",
        fusion_configuration_hash="vina-config-v1",
        reference_ligand_hash="ligand-v1",
        fusion_ligand_hash="ligand-v1",
    )
    score = score_m4_ode(candidate_id="demo", params=CascadeParameters(), docking_penalty=penalty)

    assert 0 <= score.relative_yield <= 1
    assert score.recommendation in {"drop", "iterate", "test"}

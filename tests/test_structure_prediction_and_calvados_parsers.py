from __future__ import annotations

from pathlib import Path

import numpy as np

from igem_drylab.parsers.calvados import parse_calvados_output
from igem_drylab.parsers.structure_prediction import parse_structure_prediction_output


def test_parse_af3_style_summary_confidences():
    result = parse_structure_prediction_output(
        Path("examples/real_metrics/structure_prediction/af3"),
        candidate_id="demo_af3",
    )

    assert result.candidate_id == "demo_af3"
    assert result.source == "alphafold3_or_abcfold_af3"
    assert result.iptm == 0.68
    assert result.mean_plddt == 85.0
    assert result.mean_interdomain_pae == 16.5


def test_parse_boltz_style_confidence_json():
    result = parse_structure_prediction_output(Path("examples/real_metrics/structure_prediction/boltz"))

    assert result.source == "boltz_or_abcfold_boltz"
    assert result.confidence_score == 0.81
    assert result.mean_plddt == 84.5
    assert result.chain_pair_iptm is not None


def test_parse_colabfold_ranking_debug():
    result = parse_structure_prediction_output(Path("examples/real_metrics/structure_prediction/colabfold"))

    assert result.source == "colabfold_af2_multimer"
    assert result.iptm == 0.66
    assert result.ptm == 0.71
    assert result.mean_plddt == 84.2
    assert result.mean_interdomain_pae is None


def test_parse_chai_style_scores_npz(tmp_path):
    scores = tmp_path / "scores.model_idx_0.npz"
    np.savez(
        scores,
        aggregate_score=np.asarray([0.77]),
        ptm=np.asarray([0.72]),
        iptm=np.asarray([0.69]),
        plddt=np.asarray([0.82, 0.84]),
        has_inter_chain_clashes=np.asarray([False]),
        per_chain_pair_iptm=np.asarray([[0.9, 0.6], [0.6, 0.88]]),
    )

    result = parse_structure_prediction_output(tmp_path, candidate_id="chai_npz")

    assert result.source == "chai_or_npz_scores"
    assert result.confidence_score == 0.77
    assert result.mean_plddt == 83.0
    assert result.has_clash is False


def test_parse_calvados_summary_json():
    result = parse_calvados_output(Path("examples/real_metrics/calvados/summary.json"))

    assert result.dense_phase_concentration == 12.0
    assert result.dilute_phase_concentration == 0.4
    assert result.enrichment_factor == 30.0
    assert result.llps_score is None
    assert result.concentration_unit is None


def test_parse_calvados_density_csv_when_no_summary(tmp_path):
    density = tmp_path / "density_profile.csv"
    density.write_text("position,density\n0,0.2\n1,0.3\n2,5.0\n3,10.0\n", encoding="utf-8")

    result = parse_calvados_output(tmp_path)

    assert result.dense_phase_concentration is None
    assert result.dilute_phase_concentration is None
    assert result.enrichment_factor is None and result.llps_score is None
    assert len(result.raw_density_profile)==4
    assert "no_quantile_phase_guess_or_invented_LLPS_score" in result.notes

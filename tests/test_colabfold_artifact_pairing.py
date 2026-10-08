import json

import pytest

from igem_drylab.parsers.structure_prediction import parse_structure_prediction_output


def prediction(root, candidate, rank, model, scores):
    suffix = f"rank_{rank:03d}_alphafold2_ptm_model_{model}_seed_000"
    coordinates = root / f"{candidate}_unrelaxed_{suffix}.pdb"
    coordinates.write_text("END\n")  # Pairing fixture, not a scientific structure.
    confidence = root / f"{candidate}_scores_{suffix}.json"
    confidence.write_text(json.dumps({"plddt": scores, "ptm": 0.8,
        "pae": [[0] * len(scores) for _ in scores]}))
    return coordinates, confidence


def test_batch_requires_candidate_and_pairs_exact_rank_and_seed(tmp_path):
    first = prediction(tmp_path, "fusion", 1, 5, [80, 90])
    second = prediction(tmp_path, "baseline", 1, 2, [20, 30])
    prediction(tmp_path, "fusion", 2, 1, [60, 70])
    with pytest.raises(ValueError, match="multiple ColabFold candidates"):
        parse_structure_prediction_output(tmp_path)
    summary = parse_structure_prediction_output(tmp_path, candidate_id="fusion")
    assert (summary.model_file, summary.confidence_file) == first
    assert summary.mean_plddt == 85 and summary.residue_count == 2
    assert summary.mean_interdomain_pae is None  # Whole matrix is not interdomain PAE.
    assert summary.model_rank == 1 and summary.model_name.endswith("model_5_seed_000")
    assert parse_structure_prediction_output(tmp_path, candidate_id="fusion", model_rank=2).mean_plddt == 65
    assert parse_structure_prediction_output(second[1]).model_file == second[0]
    with pytest.raises(ValueError, match="does not match"):
        parse_structure_prediction_output(second[1], candidate_id="fusion")


def test_unmatched_coordinates_and_invalid_arrays_do_not_publish_summary(tmp_path):
    model, scores = prediction(tmp_path, "fusion", 1, 1, [80, 90])
    model.unlink()
    with pytest.raises(ValueError, match="exactly matching"):
        parse_structure_prediction_output(scores)
    model.write_text("END\n")
    scores.write_text(json.dumps({"plddt": [80, float("nan")]}))
    with pytest.raises(ValueError, match="finite per-residue"):
        parse_structure_prediction_output(scores)

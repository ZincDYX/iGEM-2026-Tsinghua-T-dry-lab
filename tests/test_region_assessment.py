"""Server-only scientific tests; synthetic fixtures test identities, not biology."""
import json
from pathlib import Path

import numpy as np
import pytest

from igem_drylab.region_assessment import RegionAssessmentInput, assess_regions, load_region_requests


def prediction(tmp_path):
    name = "actual_scores_rank_001_alphafold2_ptm_model_1_seed_000.json"
    scores = tmp_path / name
    scores.write_text(json.dumps(dict(plddt=[90, 85, 20, 30],
        pae=[[0,1,4,8], [2,0,6,10], [12,14,0,2], [16,18,3,0]], ptm=0.8)))
    pdb = tmp_path / name.replace("scores", "unrelaxed").replace(".json", ".pdb")
    lines = []
    for position, confidence in enumerate([90,85,20,30], 1):
        for offset, atom in enumerate(["N", "CA", "C", "O", "CB"]):
            lines.append(f"ATOM  {len(lines)+1:5d} {atom:^4s} ALA A{position:4d}    "
                f"{position*3.8:8.3f}{offset*0.8:8.3f}{0:8.3f}  1.00{confidence:6.2f}          {atom[0]:>2s}")
    pdb.write_text("\n".join(lines)+"\nEND\n")
    return RegionAssessmentInput(candidate_id="actual", sequence="AAAA", confidence_file=scores,
        calculate_accessibility=False, regions=[dict(name="enzyme", role="enzyme", start=1, end=2),
            dict(name="ligand", role="ligand", start=3, end=4)])


@pytest.mark.scientific_algorithm
def test_regions_use_actual_blocks_not_global_PAE(tmp_path):
    request = prediction(tmp_path)
    result = assess_regions(request)
    assert result["regions"][0]["mean_plddt"] == 87.5
    assert result["regions"][1]["confidence_gate"] == "low"
    pair = result["interdomain_pae"][0]
    assert pair["first_to_second_mean_angstrom"] == 7
    assert pair["second_to_first_mean_angstrom"] == 15
    assert pair["mean_interdomain_pae_angstrom"] == 11
    assert result["formal_verdict"] == "blocked"
    assert result["regions"][1]["burial_verdict"] is None


@pytest.mark.data_contract
@pytest.mark.parametrize("change", ["sequence", "length", "confidence", "duplicate", "overlap"])
def test_no_wrong_sequence_region_or_confidence_pair(tmp_path, change):
    request = prediction(tmp_path)
    if change == "sequence": request.sequence = "AAAG"
    if change == "length": request.regions[1].end = 5
    if change == "confidence":
        data = json.loads(request.confidence_file.read_text())
        data["plddt"][0] = 91
        request.confidence_file.write_text(json.dumps(data))
    if change == "duplicate": request.regions[1].name = "enzyme"
    if change == "overlap": request.regions[1].start = 2
    with pytest.raises(ValueError): assess_regions(request)


@pytest.mark.scientific_algorithm
def test_real_FreeSASA_isolated_selected_atoms(tmp_path):
    pytest.importorskip("freesasa")
    import freesasa
    request = prediction(tmp_path)
    request.calculate_accessibility = True
    result = assess_regions(request)
    # Independent library entry point over the complete fixture, not the
    # calculator's return value or a mocked SASA function.
    model_file = Path(result["model_file"])
    independent = freesasa.calc(freesasa.Structure(str(model_file))).residueAreas()
    expected = independent["A"]["1"].total + independent["A"]["2"].total
    assert result["regions"][0]["context_sasa_angstrom2"] == pytest.approx(expected)
    assert result["regions"][0]["sasa_retention"] <= 1
    assert result["regions"][1]["burial_verdict"] is None


@pytest.mark.data_contract
def test_relative_bound_confidence_path(tmp_path):
    request = prediction(tmp_path)
    payload = request.model_dump(mode="json")
    payload["confidence_file"] = request.confidence_file.name
    manifest = tmp_path / "requests.json"
    manifest.write_text(json.dumps([payload]))
    assert load_region_requests(manifest)[0].confidence_file == request.confidence_file


@pytest.mark.integration
def test_diagnostic_regions_survive_blocked_M1_without_promoting_M2(tmp_path):
    from hashlib import sha256
    from igem_drylab.pipeline import load_config
    from igem_drylab.pipeline.models import M1Candidate
    from igem_drylab.pipeline.stages import run_m2
    request = prediction(tmp_path)
    manifest = tmp_path / "regions.json"
    manifest.write_text(json.dumps([request.model_dump(mode="json")]))
    config = load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    config.stages.m2_fusion.region_assessments_file = manifest
    config.stages.m2_fusion.structure_metrics_file = None
    candidate = M1Candidate(candidate_id="candidate", construct_id="actual", construct_definition={},
        status="insufficient_data", full_sequence_sha256=sha256(b"AAAA").hexdigest())
    rows, _ = run_m2(config, tmp_path / "run", [candidate])
    assert rows[0].screen_verdict == "blocked" and not rows[0].recommended_for_m3
    assert rows[0].region_observations[0]["regions"][1]["confidence_gate"] == "low"
    assert rows[0].region_observations[0]["M1_eligibility"] == "blocked"
    assert "M1 construct screen must pass" in rows[0].missing_inputs

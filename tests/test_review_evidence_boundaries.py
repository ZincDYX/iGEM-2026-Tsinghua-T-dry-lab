from hashlib import sha256
from pathlib import Path

from igem_drylab.parameters import ParameterRecord, ParameterRegistry, m3_requirements
from igem_drylab.parameters.validation import condition_compatibility
from igem_drylab.pipeline import load_config
from igem_drylab.pipeline.models import M4CandidateContext, M3ConcentrationAssessment
from igem_drylab.pipeline.stages import _missing_m2_formal_evidence, run_m4
from igem_drylab.scoring.m2_structure import M2StructureMetrics


def test_missing_host_and_small_condition_differences_are_not_exact():
    record = ParameterRecord(parameter_id="fixture", name="phi", value=0.1, unit="1", parameter_type="phi",
                             source_type="wetlab", review_status="approved", source_reference="test-only")
    resolution = ParameterRegistry([record]).resolve(m3_requirements()[0], host="yeast")
    assert resolution.status == "unresolved"
    assert "host_not_reported" in resolution.reasons
    record.conditions = {"host": "yeast", "temperature_c": 30, "pH": 7}
    assert condition_compatibility(record, temperature_c=31, pH=7.1).level == "weak"


def test_formal_m4_unity_activity_is_blocked_without_inventing_parameters(tmp_path):
    project = load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    context = M4CandidateContext(candidate_id="candidate", construct_id="construct", condition_id="condition",
                                 phi=0, enzyme_distribution={})
    rows, _ = run_m4(project, tmp_path, [M3ConcentrationAssessment(candidate_id="candidate", construct_id="construct", m4_candidate_context=context)])
    assert rows[0].status == "insufficient_data"
    assert any("phase activity" in item for item in rows[0].missing_inputs)
    assert not rows[0].evidence_ready


def test_m2_sequence_and_all_resource_hashes_are_verified(tmp_path):
    paths = {}
    for name in ("model", "reference", "geometry", "sasa"):
        path = tmp_path / name
        path.write_bytes(name.encode())
        paths[name] = (str(path), sha256(path.read_bytes()).hexdigest())
    row = M2StructureMetrics(candidate_id="candidate", artifact_path=paths["model"][0], artifact_sha256=paths["model"][1],
        prediction_input_sequence_sha256="old-sequence", chain_sequence_sha256={"A": "old-sequence"},
        reference_artifact_path=paths["reference"][0], reference_artifact_sha256=paths["reference"][1],
        geometry_input_path=paths["geometry"][0], geometry_input_sha256=paths["geometry"][1],
        sasa_configuration_path=paths["sasa"][0], sasa_configuration_hash=paths["sasa"][1])
    missing = _missing_m2_formal_evidence(row, None, require_m3_geometry=False, expected_sequence_sha256="new-sequence")
    assert "M2 prediction input sequence SHA-256 matching M1" in missing
    for name, label in (("reference", "reference"), ("geometry", "geometry input"), ("sasa", "SASA configuration")):
        Path(paths[name][0]).write_bytes(b"changed")
        assert f"M2 {label} artifact SHA-256 match" in _missing_m2_formal_evidence(row, None, require_m3_geometry=False, expected_sequence_sha256="old-sequence")


def test_local_plddt_does_not_prove_crossdomain_occlusion():
    from igem_drylab.scoring.m2_structure import score_m2_structure
    row = M2StructureMetrics(candidate_id="c", core_ca_rmsd_angstrom=.1, sasa_retention=1,
        pocket_rmsd_angstrom=.1, mean_plddt=95, clash_count=0, clash_cutoff_angstrom=2.5, ligand_buried=True)
    scored = score_m2_structure(row)
    assert scored.verdict == "review" and not scored.recommended_for_m3

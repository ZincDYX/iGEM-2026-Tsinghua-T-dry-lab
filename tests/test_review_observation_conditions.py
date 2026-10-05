"""Reported-condition contracts; all numeric data are software fixtures."""
from copy import deepcopy
import json

import pytest

from igem_drylab.prediction import observe_prediction
from igem_drylab.research_validation import freeze_prediction, validate_holdout, _digest
from igem_drylab.wetlab.models import WetLabResult
from test_latest_review_validation import fixture


def conditional_fixture(tmp_path):
    snapshot, training, heldout = fixture(tmp_path)
    context = {"assay_mode": "substrate_feeding_functional", "expression_mode": "constitutive",
        "input_boundary": {"feed_mode": "batch_t0"}, "assay_conditions": {
        "host": "software_fixture_host", "strain": "software_fixture_strain",
        "temperature_c": 30., "pH": 7., "assay_system": "software_fixture_system"}}
    snapshot["prediction_contract"]["experiment_context"] = deepcopy(context)
    snapshot["experimental_contract"] = deepcopy(context)
    snapshot["claim_scope"] = "conditional_mechanism"
    snapshot["manifest_sha256"] = _digest({k: v for k, v in snapshot.items() if k != "manifest_sha256"})
    raw = json.loads(heldout.read_text())
    raw[0].update({k: v for k, v in context.items() if k != "assay_conditions"})
    raw[0]["assay_conditions"] = {**context["assay_conditions"], "condition_id": "d",
        "source_reference": "software_fixture_independent_batch", "raw_data_sha256": "b" * 64,
        "verified_by": "software_fixture_reviewer"}
    heldout.write_text(json.dumps(raw))
    return snapshot, training, heldout, raw[0]


def test_matching_scientific_facts_allow_independent_provenance(tmp_path):
    snapshot, _, heldout, raw = conditional_fixture(tmp_path)
    for digest in ("a" * 64, "c" * 64):
        raw["assay_conditions"]["raw_data_sha256"] = digest
        heldout.write_text(json.dumps([raw]))
        report = validate_holdout(snapshot, "independent", heldout)
        assert report["parameters_refitted"] is False
        assert report["records"][0]["series"]["13"]["rmse_uM"] == pytest.approx(0.)


@pytest.mark.parametrize("field,value", [("pH", 5.), ("temperature_c", 42.),
    ("host", "other"), ("strain", "other"), ("assay_system", "other"), ("pH", None)])
def test_same_condition_id_does_not_override_actual_facts(tmp_path, field, value):
    snapshot, _, heldout, raw = conditional_fixture(tmp_path)
    raw["assay_conditions"][field] = value
    heldout.write_text(json.dumps([raw]))
    with pytest.raises(ValueError, match="assay_condition_mismatch:" + field):
        validate_holdout(snapshot, "independent", heldout)


def test_missing_and_measurement_override_fail_before_observation_or_fit(tmp_path):
    snapshot, _, _, raw = conditional_fixture(tmp_path)
    raw["assay_conditions"] = None
    with pytest.raises(ValueError, match="missing_assay_conditions"):
        observe_prediction(snapshot["prediction_contract"], WetLabResult.model_validate(raw))
    target = snapshot["prediction_contract"]["experiment_context"]["assay_conditions"]
    override = {**target, "condition_id": "other", "pH": 5., "source_reference": "software_fixture",
        "raw_data_sha256": "f" * 64, "verified_by": "software_fixture"}
    raw.update(measurement_condition_ids={"metabolites": "other"}, measurement_conditions={"other": override})
    with pytest.raises(ValueError, match="assay_condition_mismatch:pH"):
        observe_prediction(snapshot["prediction_contract"], WetLabResult.model_validate(raw))


def test_freeze_rejects_conflicting_condition_copies(tmp_path):
    snapshot, training, _, _ = conditional_fixture(tmp_path)
    artifact = {"prediction_contract": snapshot["prediction_contract"],
        "experimental_contract": deepcopy(snapshot["experimental_contract"])}
    artifact["experimental_contract"]["assay_conditions"]["pH"] = 5.
    prediction = tmp_path / "conflicting.json"
    prediction.write_text(json.dumps(artifact))
    with pytest.raises(ValueError, match="freeze_experimental_contract_conflict:assay_conditions"):
        freeze_prediction(prediction, tmp_path / "parameters.json", {"training": training},
            freeze_id="scientific-conditions", construct_id="c", condition_id="d", claim_scope="conditional_mechanism")


@pytest.mark.parametrize("field,value", [("phase", "dense"), ("enzyme_sequence_sha256", "e"*64),
    ("cofactor_conditions", "software_fixture_cofactors"), ("enzyme_concentration_definition", "software_fixture_active_uM")])
def test_declared_phase_sequence_and_cofactor_limits_are_not_lost(tmp_path, field, value):
    snapshot, _, _, raw = conditional_fixture(tmp_path)
    contract = snapshot['prediction_contract']
    contract['experiment_context']['assay_conditions'][field] = value
    raw['assay_conditions'][field] = value
    assert len(observe_prediction(contract, WetLabResult.model_validate(raw))[0]) == 5
    raw['assay_conditions'][field] = None
    with pytest.raises(ValueError, match='assay_condition_mismatch:' + field):
        observe_prediction(contract, WetLabResult.model_validate(raw))

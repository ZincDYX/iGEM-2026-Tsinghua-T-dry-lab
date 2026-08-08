from igem_drylab.wetlab import MeasurementMapping, WetLabResult, parameter_updates_from_measurements, quality_control


def test_explicit_qc_passed_measurement_mapping_creates_unapproved_candidate():
    result = WetLabResult(
        experiment_id="E1", construct_id="c1", condition_id="cond", replicate_id="r1",
        control_available=True, biological_replicate_count=2, metabolite_time=[0, 1],
        metabolites={"15": [0.0, 1.0]}, enzyme_activity={"DMT": 2.5},
    )
    reports = quality_control([result])
    updates = parameter_updates_from_measurements(
        [result], reports,
        [MeasurementMapping(parameter_id="wet_dmt", name="activity_dense_dmt", source_field="enzyme_activity.DMT", unit="1/s")],
    )
    assert len(updates) == 1
    assert updates[0].review_status == "validated"
    assert updates[0].value == 2.5

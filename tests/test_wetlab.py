import numpy as np

from igem_drylab.wetlab import WetLabResult, diagnose_discrepancy, fit_scale_parameter, quality_control, recommend_measurements


def test_m5_fit_recovers_single_scale_with_synthetic_data():
    predicted = [1, 2, 3, 4, 5]
    observed = (np.asarray(predicted) * 1.8).tolist()
    fit = fit_scale_parameter(predicted, observed, bootstrap_samples=20, independent_samples=True)
    assert fit.best_fit == 1.8
    assert fit.confidence_interval is not None


def test_m5_preserves_outliers_but_flags_them():
    records = [WetLabResult(experiment_id=f"e{i}", construct_id="c", condition_id="x", replicate_id=str(i), metabolite_time=[0, 1], metabolites={"15": [0, value]}, biological_replicate_count=3, control_available=True) for i, value in enumerate([1, 1.1, 20])]
    reports = quality_control(records)
    assert records[-1].metabolites["15"][-1] == 20
    assert reports[-1].outlier_flags["final_metabolite"] is True


def test_m5_diagnosis_and_transparent_recommendation():
    diagnosis = diagnose_discrepancy(qc_passed=True, replicate_variation=0.1, trend_agreement=False, systematic_directional_error=True, significant_residual=True)
    assert diagnosis.category == "MODEL_MISMATCH"
    recommendation = recommend_measurements([{"target": "partition_oc", "measurement": "imaging", "sensitivity": 2, "uncertainty": 1, "cost_class": "low"}])
    assert recommendation[0].target_parameter_or_hypothesis == "partition_oc"

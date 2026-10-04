from igem_drylab.parameters import ParameterRecord, ParameterRegistry, m4_requirements
from igem_drylab.wetlab import WetLabResult, quality_control
from igem_drylab.wetlab.parameter_update import MeasurementMapping, parameter_updates_from_measurements
from igem_drylab.pipeline import load_config
from pathlib import Path


def test_direct_measurement_ranks_above_model_fit():
    requirement = next(item for item in m4_requirements() if item.name == "kcat_dmt_9")
    base = dict(name="kcat_dmt_9", unit="1/h", parameter_type="kcat", enzyme_id="DMT", substrate_id="9", product_id="13", source_type="wetlab", source_reference="experiment", review_status="approved")
    fitted = ParameterRecord(parameter_id="fit", value=1.0, derivation_type="model_fit", derived_from=["prediction"], **base)
    direct = ParameterRecord(parameter_id="direct", value=2.0, derivation_type="direct_measurement", **base)
    assert ParameterRegistry([fitted, direct]).resolve(requirement).selected_parameter.parameter_id == "direct"


def test_wetlab_parameter_candidate_keeps_scope_and_direct_provenance():
    from test_experimental_condition_chain import assay
    conditions=assay(condition_id='condition')
    result = WetLabResult(experiment_id="e", construct_id="construct", condition_id="condition", replicate_id="r", assay_conditions=conditions, protein_abundance={"OC": 3}, metabolite_time=[0], metabolites={"13": [0]}, control_available=True, biological_replicate_count=2)
    project = load_config(Path("configs/m1_m4_real_scoring_example.yaml"))
    candidate = parameter_updates_from_measurements(project, [result], quality_control([result]), [MeasurementMapping(target_stage="m3", target_requirement_name="oc_total", source_field="protein_abundance.OC", unit="uM")])[0]
    assert (candidate.construct_id, candidate.condition_id, candidate.derivation_type) == ("construct", "condition", "direct_measurement")
    assert candidate.conditions==conditions.parameter_conditions()


def test_lod_loq_are_per_timepoint_censor_masks():
    result = WetLabResult(experiment_id="e", construct_id="c", condition_id="x", replicate_id="r", metabolite_time=[0], metabolite_concentration_unit="uM", metabolites={"13": [0.2]}, metabolite_lod={"13": 0.3}, metabolite_loq={"13": 0.4})
    report = quality_control([result])[0]
    assert report.censor_masks["13"] == ["below_lod"]
    assert not any("censored:13" in flag for flag in report.flags)

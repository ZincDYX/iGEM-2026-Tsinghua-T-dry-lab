"""SERVER ONLY: independent analytic replay of the unchanged M5 comparison.

Synthetic linear reference, not biological evidence. No tolerance/formula is
changed; this checks the new persisted projection matches existing operations.
"""
import json
import pytest
from igem_drylab.wetlab import WetLabResult, compare_prediction


@pytest.mark.parametrize("all_censored",[False,True])
def test_saved_m5_alignment_units_censoring_and_existing_summary(tmp_path, all_censored):
    path=tmp_path/"linear-reference.json"
    path.write_text(json.dumps(dict(time=[0,1,2],x13=[0,2,4],concentration_unit="uM")))
    original=path.read_bytes()
    result=WetLabResult(experiment_id="ANALYTIC_NOT_BIOLOGY",construct_id="construct",condition_id="condition",
        replicate_id="replicate",raw_data_sha256="a"*64,measurement_compartment="intracellular",concentration_basis="cell_volume",
        metabolite_time=[0,60,120],metabolite_time_unit="min",metabolite_concentration_unit="mM",
        metabolites={"13":[0,.0005,.0006 if all_censored else .006]},metabolite_lod={"13":.001},metabolite_loq={"13":.002},
        metabolite_uncertainty={"13":[.0001,.0002,.0003]},metabolite_uncertainty_type="sd")
    before=result.model_dump(mode="json")
    comparison=compare_prediction(path,result)["13"]
    series=comparison.display_series
    assert series.time==[0,1,2] and series.predicted==[0,2,4]
    assert series.observed==pytest.approx([0,.5,.6 if all_censored else 6],abs=1e-12)
    assert series.uncertainty==pytest.approx([.1,.2,.3],abs=1e-12)
    assert series.uncertainty_type=="sd" and series.lod==1 and series.loq==2
    assert series.censor_mask==["below_lod","below_lod","below_lod" if all_censored else "quantified"]
    assert series.residual_observed_minus_predicted==[None,None,None if all_censored else 2]
    assert comparison.residual_final==(None if all_censored else 2)
    assert comparison.comparison_status==("all_observations_censored" if all_censored else "endpoint_only")
    assert comparison.fit is None
    assert series.comparison_adapter=="legacy_trajectory" and series.raw_data_sha256=="a"*64
    assert path.read_bytes()==original and result.model_dump(mode="json")==before

"""N06: optimization success is not identifiability."""
import numpy as np
import pytest

from igem_drylab.wetlab.fit import fit_mechanistic_parameter


@pytest.mark.parametrize('initial',[.2,1.,1.8])
def test_flat_perfect_fit_has_no_parameter_estimate_or_interval(initial):
    fit=fit_mechanistic_parameter(parameter_name='inactive_kcat',initial_value=initial,bounds=(0,2),
                                  observed=[0]*6,predictor=lambda value:np.zeros(6),bootstrap_samples=10)
    assert fit.status=='unidentifiable' and fit.best_fit is None and fit.confidence_interval is None
    assert fit.rmse==0 and fit.diagnostics['profile_prediction_span']==0
    assert fit.diagnostics['scaled_parameter_jacobian_norm']==0


def test_sensitive_parameter_is_recovered_without_iid_time_bootstrap():
    x=np.arange(1.,7.)
    fit=fit_mechanistic_parameter(parameter_name='fixture',initial_value=1,bounds=(0,2),observed=(1.3*x).tolist(),
                                  predictor=lambda value:value*x,bootstrap_samples=10)
    assert fit.status=='estimated' and fit.best_fit==pytest.approx(1.3,abs=1e-7)
    assert fit.confidence_interval is None and 'biological_replicates' in fit.identifiability_warning
    assert fit.diagnostics['scaled_parameter_jacobian_norm']>0


def test_flat_objective_is_unidentifiable_even_when_predictions_change():
    fit=fit_mechanistic_parameter(parameter_name='fixture',initial_value=1,bounds=(0,2),observed=[0]*4,
        predictor=lambda value:np.array([np.sin(value),np.cos(value),np.sin(value),np.cos(value)]))
    assert fit.status=='unidentifiable' and fit.best_fit is None


def test_boundary_limited_fit_is_not_registry_candidate():
    fit=fit_mechanistic_parameter(parameter_name='fixture',initial_value=1,bounds=(0,2),observed=[3]*6,
                                  predictor=lambda value:np.full(6,value))
    assert fit.status=='boundary_limited' and fit.best_fit is None and fit.confidence_interval is None
    assert fit.diagnostics['bound_hit']


@pytest.mark.parametrize('prediction',[np.zeros(3),np.full(6,np.nan)])
def test_invalid_predictor_is_explicit_error(prediction):
    with pytest.raises(ValueError,match='finite_aligned'):
        fit_mechanistic_parameter(parameter_name='fixture',initial_value=1,bounds=(0,2),observed=[0]*6,predictor=lambda value:prediction)


def test_declared_replicate_blocks_are_the_resampling_units():
    x=np.tile([1.,2.,3.],3)
    y=x*np.repeat([1.1,1.2,1.3],3)
    fit=fit_mechanistic_parameter(parameter_name='fixture',initial_value=1,bounds=(0,2),observed=y.tolist(),
                                  predictor=lambda value:value*x,bootstrap_samples=30,replicate_blocks=[[0,1,2],[3,4,5],[6,7,8]])
    assert fit.status=='estimated' and fit.best_fit==pytest.approx(1.2,abs=1e-7)
    assert fit.confidence_interval is not None and fit.confidence_interval[0]<=1.2<=fit.confidence_interval[1]


def test_pipeline_does_not_publish_flat_fit_candidate(tmp_path):
    from pathlib import Path
    from igem_drylab.pipeline import load_config
    from igem_drylab.pipeline.config import FitPlanConfig
    from igem_drylab.pipeline.models import M4ReactionPrediction
    from igem_drylab.pipeline.stages import _fit_plan_candidate
    from igem_drylab.prediction import dynamic_contract
    from igem_drylab.full_network import COMPOUNDS,simulate_full_network
    from igem_drylab.wetlab import WetLabResult,compare_prediction
    from test_new_review_m4 import single_reaction
    import json
    params=single_reaction()
    zero={c:0 for c in COMPOUNDS}
    result=simulate_full_network(params,initial_intracellular=zero,t_end=1,points=7)
    payload=dynamic_contract(params,result,zero,zero,1,7)
    path=tmp_path/'prediction.json'
    path.write_text(json.dumps({'prediction_contract':payload}),encoding='utf-8')
    observation=WetLabResult(experiment_id='fixture',construct_id='c',condition_id='d',replicate_id='r',
        metabolite_time=payload['time'],metabolite_concentration_unit='uM',measurement_compartment='intracellular',
        concentration_basis='cell_volume',metabolites={'15':[0]*7})
    config=load_config(Path('configs/m1_m4_real_scoring_example.yaml'))
    config.stages.m5_feedback.fit_plan=FitPlanConfig(parameter_name='kcat_r5',bounds=(1,2000),observables=['15'])
    prediction=M4ReactionPrediction(candidate_id='c',construct_id='c',condition_id='d',target_product='15',
        simulation_inputs={'prediction_contract':payload,'parameters':{'kcat_r5':1000}},parameter_ids=['fixture'])
    fit=_fit_plan_candidate(config,prediction,observation,compare_prediction(path,observation))
    assert fit['candidate'] is None and fit['fit']['status']=='unidentifiable' and fit['fit']['best_fit'] is None

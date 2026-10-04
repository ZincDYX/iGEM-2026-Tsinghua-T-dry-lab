"""MU01--MU03 independently derived software fixtures (uM, h, L).

No expected value is obtained from the production observation/statistics helper.
"""
from dataclasses import replace
import json
from math import sqrt
import pytest

from igem_drylab.full_network import COMPOUNDS,PhaseDistribution,TransportParameters,simulate_full_network
from igem_drylab.prediction import dynamic_contract,replay_prediction,observe_prediction
from igem_drylab.wetlab.models import WetLabResult
from igem_drylab.research_validation import freeze_prediction,validate_holdout
from test_new_review_m4 import single_reaction


def constant_contract():
    params = single_reaction()
    params = replace(params,reactions=tuple(replace(r,kcat=0.) for r in params.reactions),
        transport=TransportParameters(intracellular_volume_l=2.,extracellular_volume_l=5.))
    inside = {c:2. if c=='13' else 0. for c in COMPOUNDS}
    outside = {c:3. if c=='13' else 0. for c in COMPOUNDS}
    result = simulate_full_network(params,initial_intracellular=inside,initial_extracellular=outside,t_end=1.,points=3)
    return dynamic_contract(params,result,inside,outside,1.,3)


def test_MU01_active_kp_replay_matches_two_phase_initial_rate():
    params = replace(single_reaction(),phi=.2,scenario='galatea_spatial',
        enzyme_distributions={e:PhaseDistribution(2.,.5) if e=='DMT' else PhaseDistribution(0.,0.)
            for e in single_reaction().enzyme_distributions},
        reactions=tuple(replace(r,kcat=1. if r.reaction_id=='R5' else 0.) for r in single_reaction().reactions))
    initial = {c:float(c=='9') for c in COMPOUNDS}
    duration = 1e-6
    result = simulate_full_network(params,initial_intracellular=initial,t_end=duration,points=2,rtol=1e-11,atol=1e-15)
    contract = dynamic_contract(params,result,initial,{c:0. for c in COMPOUNDS},duration,2)
    changed = replay_prediction(contract,'partition_x9',10.)
    # S_dilute = 1/(.8+.2*10)=5/14; S_dense=25/7.
    # Initial v13=.2*2*(25/32)+.8*.5*(5/19).
    expected = (2/5)*(25/32)+(2/5)*(5/19)
    observed_rate = changed['concentrations']['intracellular']['13'][-1]/duration
    assert observed_rate == pytest.approx(expected,rel=0.,abs=1e-6)  # finite-time truncation uM/h
    assert result.intracellular[COMPOUNDS.index('13'),-1]/duration == pytest.approx(.4,rel=0.,abs=1e-6)


@pytest.mark.parametrize('name,value,expected',[('kcat_r5',2.,.8),('km_r5',3.,.2),
    ('activity_dense_dmt',2.,.6),('activity_dilute_dmt',2.,.6)])
def test_supported_replay_parameter_families_change_active_product_initial_rate(name,value,expected):
    params=single_reaction()
    params=replace(params,phi=.2,scenario='galatea_spatial',
        enzyme_distributions={e:PhaseDistribution(2.,.5) if e=='DMT' else PhaseDistribution(0.,0.)
            for e in params.enzyme_distributions},
        reactions=tuple(replace(r,kcat=1. if r.reaction_id=='R5' else 0.) for r in params.reactions))
    initial={c:float(c=='9') for c in COMPOUNDS}
    duration=1e-6
    result=simulate_full_network(params,initial_intracellular=initial,t_end=duration,points=2,rtol=1e-11,atol=1e-15)
    payload=dynamic_contract(params,result,initial,{c:0. for c in COMPOUNDS},duration,2)
    changed=replay_prediction(payload,name,value)
    assert changed['concentrations']['intracellular']['13'][-1]/duration==pytest.approx(expected,rel=0.,abs=1e-6)


@pytest.mark.parametrize('compartment,basis,expected',[
    ('intracellular','cell_volume',2.),('extracellular','medium_volume',3.),
    ('total_extract','extraction_volume',4.75)])
def test_MU02_observation_matches_independent_amount_normalization(compartment,basis,expected):
    record = WetLabResult(experiment_id='software-fixture',construct_id='c',condition_id='d',replicate_id='r',
        measurement_compartment=compartment,concentration_basis=basis,extraction_volume_l=4.,metabolite_time=[0.])
    _,series = observe_prediction(constant_contract(),record)
    # (2 uM * 2 L + 3 uM * 5 L) / 4 L = 4.75 uM, not 2+3.
    assert series['13'][0] == pytest.approx(expected,rel=0.,abs=1e-12)


def frozen_fixture(tmp_path):
    prediction = tmp_path/'prediction.json'
    prediction.write_text(json.dumps({'construct_id':'c','condition_id':'d','prediction_contract':constant_contract()}))
    parameters = tmp_path/'parameters.json';parameters.write_text('{"software_fixture_only":true}')
    train = tmp_path/'calibration.json'
    train.write_text(json.dumps([dict(experiment_id='calibration',construct_id='c',condition_id='d',replicate_id='r',
        metabolite_time=[0.,.5,1.],metabolite_concentration_unit='uM',measurement_compartment='intracellular',
        concentration_basis='cell_volume',metabolites={'13':[2.,2.,2.]})]))
    return freeze_prediction(prediction,parameters,{'training':train},freeze_id='fixture',construct_id='c',
        condition_id='d',claim_scope='software_fixture_only')


@pytest.mark.parametrize('censored',[False,True])
def test_MU03_holdout_nonzero_error_has_hand_computed_statistics(tmp_path,censored):
    snapshot = frozen_fixture(tmp_path)
    record = dict(experiment_id='holdout',construct_id='c',condition_id='d',replicate_id='r',
        metabolite_time=[0.,15.,60.],metabolite_time_unit='min',metabolite_concentration_unit='mM',
        measurement_compartment='intracellular',concentration_basis='cell_volume',metabolites={'13':[.001,.005,.004]})
    if censored:
        record['metabolite_lod']={'13':.002}
    path = tmp_path/'heldout.json';path.write_text(json.dumps([record]))
    out = validate_holdout(snapshot,'heldout',path)
    series = out['records'][0]['series']['13']
    assert out['parameters_refitted'] is False
    # Independent observed - predicted residuals: [-1,3,2] uM, or [3,2] after censoring.
    assert series['residual_uM'] == ( [3.,2.] if censored else [-1.,3.,2.] )
    assert series['quantified_indices'] == ([1,2] if censored else [0,1,2])
    assert series['rmse_uM'] == pytest.approx(sqrt(13/2) if censored else sqrt(14/3),rel=0.,abs=1e-12)
    assert series['mae_uM'] == pytest.approx(2.5 if censored else 2.,rel=0.,abs=1e-12)
    assert series['bias_uM'] == pytest.approx(2.5 if censored else 4/3,rel=0.,abs=1e-12)


def test_active_steady_F2_response_matches_independent_scalar_balance():
    from test_new_review_m4 import steady_fixture
    from igem_drylab.m4_steady_state import solve_m4_steady_state
    from igem_drylab.prediction import steady_contract
    from igem_drylab.design_analysis import analyze_prediction,M4AnalysisConfig
    payload = steady_fixture()
    payload.phi=.2
    payload.input_flux_um_per_h=.3
    # Unfed inactive pools have explicit drains in this fixture so their steady
    # concentrations are uniquely zero rather than free competitive inhibitors.
    payload.secretion_rate_per_h={c:1. if c in {'8','12','13','14','15'} else 0. for c in COMPOUNDS}
    payload.enzymes={e:item.model_copy(update=dict(dense_um=2. if e=='PTR' else 10.,dilute_um=.5 if e=='PTR' else 10.))
        for e,item in payload.enzymes.items()}
    for row in payload.reactions:
        row.kcat_per_h=1. if row.reaction_id in {'R1','R2','R3','R7'} else 0.
    def independent_yield(kp):
        # Only the 8 drain and R1 remove feed; every downstream active flux reaches 15.
        lo,hi=0.,.3
        for _ in range(70):
            dilute=(lo+hi)/2
            removal=.4*kp*dilute/(1+kp*dilute)+.4*dilute/(1+dilute)+dilute
            if removal>.3: hi=dilute
            else: lo=dilute
        return (.3-(lo+hi)/2)/.3
    result=solve_m4_steady_state(payload)
    assert result.status=='valid'
    expected=independent_yield(1.)
    assert expected>0
    assert result.yield_abs==pytest.approx(expected,rel=0.,abs=1e-6)
    out=analyze_prediction(steady_contract(payload,result),M4AnalysisConfig(local_parameter_names=['partition_x8']))
    for row in out['sensitivity']['local_forward_difference']['partition_x8']['steps']:
        delta=row['fraction']
        derivative=(independent_yield(1+delta)-expected)/delta
        assert row['derivative']==pytest.approx(derivative,rel=0.,abs=1e-4)


def test_competitive_OC_initial_flux_has_both_substrates_phase_weights_and_correct_products():
    params=single_reaction()
    params=replace(params,phi=.2,scenario='galatea_spatial',
        enzyme_distributions={e:PhaseDistribution(2.,.5) if e=='OC' else PhaseDistribution(0.,0.)
            for e in params.enzyme_distributions},metabolite_kp={c:5. if c=='10' else .5 if c=='14' else 1. for c in COMPOUNDS},
        reactions=tuple(replace(r,kcat=4. if r.reaction_id=='R3' else 6. if r.reaction_id=='R10' else 0.,
            km=2. if r.reaction_id=='R10' else 1.) for r in params.reactions))
    initial={c:1. if c in {'10','14'} else 0. for c in COMPOUNDS}
    duration=1e-7
    result=simulate_full_network(params,initial_intracellular=initial,t_end=duration,points=2,rtol=1e-11,atol=1e-15)
    # Dense competitive denominator=73/18; dilute=19/9, including both 10 and 14.
    v3=.2*(400/73)+.8*(10/19)
    v10=.2*(60/73)+.8*(15/19)
    assert result.fluxes[2,0]==pytest.approx(v3,rel=0.,abs=1e-12)
    assert result.fluxes[9,0]==pytest.approx(v10,rel=0.,abs=1e-12)
    assert result.intracellular[COMPOUNDS.index('11'),-1]/duration==pytest.approx(v3,rel=0.,abs=1e-6)
    assert result.intracellular[COMPOUNDS.index('15'),-1]/duration==pytest.approx(v10,rel=0.,abs=1e-6)
    for time_index in range(2):
        assert sum(result.intracellular[:,time_index])==pytest.approx(2.,rel=0.,abs=1e-12)

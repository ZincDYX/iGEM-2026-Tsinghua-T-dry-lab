"""N05: versions and numerical settings are enforced, never metadata-only."""
from copy import deepcopy

import numpy as np
import pytest

from igem_drylab.full_network import COMPOUNDS, simulate_full_network
from igem_drylab.prediction import PredictionContract, dynamic_contract, replay_prediction, steady_contract
from igem_drylab.m4_steady_state import solve_m4_steady_state
from test_new_review_m4 import single_reaction, steady_fixture


def contract(method='LSODA'):
    params=single_reaction()
    initial={c:float(c=='9') for c in COMPOUNDS}
    result=simulate_full_network(params,initial_intracellular=initial,t_end=.01,points=7,method=method,rtol=1e-10,atol=1e-13)
    return dynamic_contract(params,result,initial,None,.01,7)


@pytest.mark.parametrize('mutation',[
    lambda p:p.update(formula_version='unregistered-old-v1'),
    lambda p:p.update(time_unit='author_native_day_axis'),
    lambda p:p['concentrations']['intracellular'].pop('15'),
    lambda p:p['concentrations'].pop('extracellular'),
    lambda p:p['concentrations']['intracellular']['15'].pop(),
    lambda p:p['solver_settings'].update(method='fake-solver'),
    lambda p:p['solver_settings'].update(rtol=float('nan')),
    lambda p:p['solver_settings'].update(ignored_option=True),
    lambda p:p['solver_settings'].pop('integration_version'),
    lambda p:p['kernel_inputs']['parameters'].update(unit_mode='author_native_sensitivity'),
    lambda p:p.update(intracellular_volume_l=42),
    lambda p:p['time'].__setitem__(-1,42),
])
def test_corrupted_snapshots_cannot_be_replayed(mutation):
    payload=contract()
    mutation(payload)
    with pytest.raises(ValueError):
        replay_prediction(payload,'kcat_r5',1000)


@pytest.mark.parametrize('method',['LSODA','BDF','Radau'])
def test_replay_uses_saved_supported_solver_settings(method):
    payload=contract(method)
    replayed=replay_prediction(payload,'kcat_r5',1000)
    assert replayed['solver_settings']==payload['solver_settings']
    assert replayed['formula_version']==payload['formula_version']
    assert np.allclose(replayed['concentrations']['intracellular']['13'],payload['concentrations']['intracellular']['13'],atol=1e-12)


def test_environment_mismatch_requires_explicit_action():
    payload=contract()
    payload['solver_settings']['scipy_version']='1.10.1'
    with pytest.raises(ValueError,match='recorded_scipy_environment'):
        replay_prediction(payload,'kcat_r5',1000)


def test_steady_inner_version_settings_and_activity_migration_are_bound():
    inputs=steady_fixture()
    payload=steady_contract(inputs,solve_m4_steady_state(inputs))
    assert replay_prediction(payload,'ksec_8',1)['formula_version']==payload['formula_version']
    for key,value in [('formula_version','m4-step0-step8-phase-activity-v2-2026-10-04'),('relative_residual_tolerance',.01)]:
        changed=deepcopy(payload)
        changed['kernel_inputs'][key]=value
        with pytest.raises(ValueError):
            PredictionContract.model_validate(changed)
    with pytest.raises(ValueError,match='explicit_formula_migration'):
        replay_prediction(payload,'activity_dilute_dmt',2)

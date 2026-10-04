import numpy as np
import pytest

from igem_drylab.full_network import COMPOUNDS, simulate_full_network
from igem_drylab.prediction import dynamic_contract, replay_prediction
from igem_drylab.project_state import ProjectState
from igem_drylab.wetlab.models import MetabolitePartitionMeasurement
from test_new_review_m4 import single_reaction


def test_kp_forward_replay_repartitions_all_substrates():
    params = single_reaction()
    initial = {c: 0. for c in COMPOUNDS}
    initial['9'] = 1.
    result = simulate_full_network(params, initial_intracellular=initial, t_end=1., points=9)
    payload = dynamic_contract(params, result, initial, {c:0. for c in COMPOUNDS}, 1., 9)
    replay = replay_prediction(payload, 'partition_x9', 10.)
    assert replay['kernel_inputs']['parameters']['metabolite_kp']['9'] == 10.
    assert payload['kernel_inputs']['parameters']['metabolite_kp']['9'] == 1.
    # The fixture is homogeneous: no fabricated phase effect.
    assert np.allclose(replay['concentrations']['intracellular']['15'], result.intracellular[7])
    with pytest.raises(ValueError, match='must_be_positive'):
        replay_prediction(payload, 'partition_x9', 0.)
    with pytest.raises(ValueError, match='does_not_support'):
        replay_prediction(payload, 'phi', .2)


def test_direct_partition_requires_concentrations_and_source_evidence():
    evidence = MetabolitePartitionMeasurement(dense_concentration_um=2., dilute_concentration_um=.5,
        source_reference='software-fixture', raw_data_sha256='a'*64,
        calibration_reference='fixture', recovery_reference='fixture', phase_volume_reference='fixture')
    assert evidence.kp == 4.
    with pytest.raises(ValueError):
        MetabolitePartitionMeasurement(dense_concentration_um=2., dilute_concentration_um=0.)


def test_construct_changes_invalidate_dependents_without_deleting_old_artifacts():
    state = ProjectState(project_id='fixture', completed_stages=['m1','m2','m3','m4','m5'], available_artifacts=['old.json'])
    updated = state.invalidate_construct_change('site_topology')
    assert updated.completed_stages == ['m1']
    assert updated.stale_stages == ['m2','m3','m4','m5']
    assert updated.available_artifacts == ['old.json']
    assert state.completed_stages == ['m1','m2','m3','m4','m5']

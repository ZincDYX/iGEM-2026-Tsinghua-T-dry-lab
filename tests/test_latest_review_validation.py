import json
from copy import deepcopy

import numpy as np
import pytest

from igem_drylab.full_network import COMPOUNDS,simulate_full_network
from igem_drylab.prediction import dynamic_contract
from igem_drylab.research_validation import freeze_prediction,validate_holdout
from test_new_review_m4 import single_reaction


def fixture(tmp_path):
    params = single_reaction()
    initial = {c:float(c=='9') for c in COMPOUNDS}
    result = simulate_full_network(params,initial_intracellular=initial,t_end=.01,points=5)
    prediction = tmp_path/'prediction.json'
    prediction.write_text(json.dumps({'construct_id':'c','condition_id':'d','prediction_contract':
        dynamic_contract(params,result,initial,{c:0. for c in COMPOUNDS},.01,5)}))
    parameters = tmp_path/'parameters.json'
    parameters.write_text(json.dumps({'software_fixture':True}))
    def record(experiment):
        return {'experiment_id':experiment,'construct_id':'c','condition_id':'d','replicate_id':'r',
            'metabolite_time':result.time.tolist(),'metabolite_concentration_unit':'uM',
            'measurement_compartment':'intracellular','concentration_basis':'cell_volume',
            'metabolites':{'13':result.intracellular[5].tolist()}}
    training = tmp_path/'training.json'
    training.write_text(json.dumps([record('calibration')]))
    heldout = tmp_path/'holdout.json'
    heldout.write_text(json.dumps([record('heldout')]))
    snapshot = freeze_prediction(prediction,parameters,{'training':training},freeze_id='fixture',
                                 construct_id='c',condition_id='d',claim_scope='software_fixture_only')
    return snapshot,training,heldout


def test_holdout_uses_frozen_series_without_refitting(tmp_path):
    snapshot,training,heldout = fixture(tmp_path)
    result = validate_holdout(snapshot,'heldout',heldout)
    assert result['parameters_refitted'] is False
    assert result['records'][0]['series']['13']['rmse_uM']==pytest.approx(0.)
    assert result['records'][0]['temporal_scope']=='unconfirmed_measurement_timestamp'
    assert snapshot['validation_status'].startswith('pending')


def test_training_relabel_and_frozen_mutation_are_rejected(tmp_path):
    snapshot,training,heldout = fixture(tmp_path)
    with pytest.raises(ValueError,match='overlaps_calibration'):
        validate_holdout(snapshot,'new-label',training)
    alias = tmp_path/'renamed.json'
    alias.write_text(json.dumps(json.loads(training.read_text()),indent=4))
    with pytest.raises(ValueError,match='record_overlaps'):
        validate_holdout(snapshot,'new-label',alias)
    modified = deepcopy(snapshot)
    modified['prediction_contract']['concentrations']['intracellular']['13'][-1]+=1.
    with pytest.raises(ValueError,match='integrity'):
        validate_holdout(modified,'heldout',heldout)


def test_holdout_censor_and_units_are_not_ignored(tmp_path):
    snapshot,training,heldout = fixture(tmp_path)
    raw = json.loads(heldout.read_text())
    raw[0]['metabolite_lod']={'13':100.}
    heldout.write_text(json.dumps(raw))
    result = validate_holdout(snapshot,'heldout',heldout)
    assert result['records'][0]['series']['13']['rmse_uM'] is None
    assert result['records'][0]['series']['13']['status']=='all_censored'

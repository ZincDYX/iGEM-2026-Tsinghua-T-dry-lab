"""Independent Student-t and protocol fixtures, not biological validation."""
import numpy as np
import pytest
from scipy.stats import t
from igem_drylab import cg_sampling


def payload(seeds=(1,2,3)):
    return cg_sampling.SamplingInput(candidate_id='synthetic',observable='declared distance',unit='nm',
        traces=[dict(seed=s,values=([9.,11.]*8 if s==1 else [10.,12.]*8 if s==2 else [11.,13.]*8),source_reference='Synthetic trace only') for s in seeds],
        expected_seeds=[1,2,3],sampling_interval_ns=.125,confidence_level=.95,relative_halfwidth_target=.1,
        protocol_reference='Synthetic declared diagnostic protocol')


@pytest.mark.scientific_algorithm
def test_replicate_CI_uses_three_independent_means_not_48_frames(monkeypatch):
    monkeypatch.setattr(cg_sampling,'_statistical_inefficiency',lambda v:1.)
    result=cg_sampling.assess_sampling(payload())
    half=t.ppf(.975,2)/np.sqrt(3)
    assert result['mean_of_independent_replicate_means']==11
    assert result['independent_replicate_CI']==pytest.approx([11-half,11+half])
    assert result['sampling_status']=='sampling_not_converged' and not result['formal_M1_pass']


@pytest.mark.data_contract
def test_missing_seed_and_constant_trace_do_not_become_zero_uncertainty(monkeypatch):
    monkeypatch.setattr(cg_sampling,'_statistical_inefficiency',lambda v:1.)
    result=cg_sampling.assess_sampling(payload((1,2)))
    assert result['sampling_status']=='independent_replicates_incomplete' and result['independent_replicate_CI'] is None
    data=payload()
    for trace in data.traces:trace.values=[10.]*16
    result=cg_sampling.assess_sampling(data)
    assert result['sampling_status']=='sampling_not_converged'
    assert all(r['status']=='constant_trace_autocorrelation_undefined' for r in result['replicates'])


@pytest.mark.data_contract
def test_seed_aliases_are_not_independent_repeats():
    data=payload().model_dump();data['traces'][1]['seed']=1
    with pytest.raises(ValueError,match='distinct_declared'):cg_sampling.SamplingInput(**data)

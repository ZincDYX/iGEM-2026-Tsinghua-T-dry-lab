from dataclasses import replace
from pathlib import Path

import pytest

from igem_drylab.full_network import COMPOUNDS, simulate_full_network
from igem_drylab.pipeline import load_config
from igem_drylab.pipeline.config import M4Config
from igem_drylab.pipeline.stages import _formal_analysis_missing
from test_new_review_m4 import single_reaction


def test_branch_zero_is_undefined_and_existing_R5_indicator_is_preserved():
    initial = {c:float(c=='9') for c in COMPOUNDS}
    result = simulate_full_network(single_reaction(),initial_intracellular=initial,t_end=.01,points=2)
    assert result.diagnostics['q_10_to_11'] is None
    assert result.diagnostics['q_9_to_13']==pytest.approx(1.)
    assert result.diagnostics['q_9_to_13']==result.diagnostics['branch_9_to_13_fraction']
    assert result.diagnostics['final_13_extracellular_medium_volume']==0.


def test_competing_10_branch_uses_integrated_reaction_flux_not_enzyme_ratio():
    params = single_reaction()
    params = replace(params,enzyme_distributions={e:type(v)(0.,1.) for e,v in params.enzyme_distributions.items()},
                     reactions=tuple(replace(r,kcat=1. if r.reaction_id in {'R3','R6'} else 0.) for r in params.reactions))
    result = simulate_full_network(params,initial_intracellular={c:float(c=='10') for c in COMPOUNDS},
                                   t_end=.1,points=2)
    assert result.diagnostics['q_10_to_11']==pytest.approx(result.flux_integrals['R3']/
        (result.flux_integrals['R3']+result.flux_integrals['R6']))


def test_assay_boundary_and_formal_steady_observation_are_explicit():
    with pytest.raises(ValueError,match='intermediate'):
        M4Config(assay_mode='substrate_feeding_functional',feed_mode='continuous_feed',feed_compound_id='8')
    with pytest.raises(ValueError,match='input_8'):
        M4Config(assay_mode='full_pathway_production',feed_compound_id='10')
    config = load_config(Path('configs/m1_m4_real_scoring_example.yaml'))
    config.execution.mode='real'
    config.execution.analysis_grade='formal_measured'
    config.stages.m4_reaction.network_mode='markdown_steady_state'
    assert any('assay_mode' in reason for reason in _formal_analysis_missing(config))
    assert any('steady_state_observation_reference' in reason for reason in _formal_analysis_missing(config))

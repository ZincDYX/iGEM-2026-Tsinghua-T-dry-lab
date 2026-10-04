"""F3 public decision boundary. Upstream computations are explicitly mocked here."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import pytest

from igem_drylab.design_analysis import (FiniteDesignPlan,ScaffoldCandidate,scan_scaffold_designs,
    _candidate_comparison,M4AnalysisConfig,RangeEvidence,sample_range,analyze_response)
from igem_drylab.pipeline.models import M4ReactionPrediction,M4CandidateContext
from igem_drylab.full_network import COMPOUNDS,simulate_full_network
from igem_drylab.prediction import dynamic_contract
from test_new_review_m4 import single_reaction


def predictions():
    params = single_reaction()
    initial = {c:float(c=='9') for c in COMPOUNDS}
    result = simulate_full_network(params,initial_intracellular=initial,t_end=.01,points=2)
    contract = dynamic_contract(params,result,initial,{c:0. for c in COMPOUNDS},.01,2)
    contract['experiment_context'] = dict(assay_mode='substrate_feeding_functional',expression_mode='constitutive',
        measurement_compartment='intracellular',input_boundary={'feed_mode':'batch_initial_state','feed_compound_id':'9','feeding_time_h':0.},
        assay_conditions={'host':'fixture','strain':'fixture','pH':7.,'temperature_c':30.,'assay_system':'fixture'})
    rows = []
    for i in (1,2):
        context = M4CandidateContext(candidate_id=f'c{i}',construct_id=f'c{i}',condition_id=f'd{i}',phi=.2,
            nominal_site_counts={'SH3':i,'PDZ':1},m2_geometry_id=f'fixture-{i}',
            enzyme_distribution={'OC':{'dense':2.*i,'dilute':1.},'DMT':{'dense':1.,'dilute':1.}},
            evidence_ready=True,claim_scope='conditional_mechanism')
        rows.append(M4ReactionPrediction(candidate_id=f'c{i}',construct_id=f'c{i}',condition_id=f'd{i}',target_product='15',
            candidate_context=context,productivity=float(i),data_quality='measured',evidence_ready=True,
            claim_scope='conditional_mechanism',simulation_inputs={'prediction_contract':deepcopy(contract)}))
    return rows


def scan(monkeypatch,tmp_path,rows,**changes):
    import igem_drylab.pipeline as pipeline
    monkeypatch.setattr(pipeline,'run_through_m4',lambda config:(SimpleNamespace(model_dump=lambda **kw:{}),
        [rows[int(config.run.id.split('-')[1])]]))
    plan = FiniteDesignPlan(**{**dict(candidates=[ScaffoldCandidate(config_path=Path('configs/m1_m4_example.yaml'),
        candidate_id=f'c{i}',site_ratio=i,design_evidence_reference='software-fixture',synthesized=False) for i in (1,2)],
        objective='productivity',objective_reference='fixture',decision_id='fixture',
        decision_scope='formal_conditional_mechanism',comparison_contract=_candidate_comparison(rows[0],'productivity'),
        varying_design_factors=['site_topology']),**changes})
    return scan_scaffold_designs(plan,tmp_path)


def test_comparable_physical_candidates_with_different_condition_labels_rank(monkeypatch,tmp_path):
    out = scan(monkeypatch,tmp_path,predictions())
    assert [r['status'] for r in out['scaffold_scan']] == ['valid','valid']
    assert out['design_decision']['selected_candidate']['candidate_id']=='c2'
    assert out['design_decision']['r_target']==4.
    assert out['design_decision']['decision_scope']=='formal_conditional_mechanism'


@pytest.mark.parametrize('change',['demo','author_native','assay','unit','feed','interval','normalization','condition','sequence_grade'])
def test_higher_metric_ineligible_or_incomparable_candidate_never_sets_target(monkeypatch,tmp_path,change):
    rows = predictions()
    bad = rows[1]
    contract = bad.simulation_inputs['prediction_contract']
    if change=='demo':
        bad.data_quality='demo_fixture';bad.evidence_ready=False
    elif change=='author_native':
        bad.claim_scope='author_native_sensitivity'
    elif change=='sequence_grade':
        bad.candidate_context.evidence_ready=False
    elif change=='unit':
        contract['concentration_unit']='author_native'
    elif change=='normalization':
        contract['normalization']['intracellular']='medium_volume'
    elif change=='feed':
        contract['kernel_inputs']['initial_intracellular']['9']=2.
    elif change=='interval':
        contract['solver_settings']['t_end']=.02
    elif change=='condition':
        contract['experiment_context']['assay_conditions']['pH']=6.
    else:
        contract['experiment_context']['assay_mode']='full_pathway_production'
    out = scan(monkeypatch,tmp_path,rows)
    assert out['scaffold_scan'][1]['status'] in {'rejected','failed'}
    assert out['scaffold_scan'][1]['error']
    assert out['design_decision']['selected_candidate']['candidate_id']=='c1'
    assert out['design_decision']['r_target']==2.


def test_typo_constraint_is_explicit_failure_not_silent_infeasibility(monkeypatch,tmp_path):
    out = scan(monkeypatch,tmp_path,predictions(),minimum_metrics={'productivty':.1})
    assert out['design_decision']['selected_candidate'] is None
    assert all('missing_or_unknown_decision_metrics:productivty' in r['error'] for r in out['scaffold_scan'])


def test_discrete_empirical_inverse_cdf_retains_atoms_duplicates_and_seed():
    row = RangeEvidence(parameter_name='partition_x9',distribution='empirical',empirical_values=[1.,1.,3.],
        source_reference='software-fixture',parameter_ids=['fixture'],reviewed_by='fixture')
    assert [sample_range(row,q) for q in (0.,1/6,.5,2/3,.9,1.)] == [1.,1.,1.,1.,3.,3.]
    settings = M4AnalysisConfig(ranges=[row],samples=300,standard_deviation_ddof=0,
        independence_evidence_reference='one variable fixture')
    out = analyze_response(settings,{'partition_x9':1.},lambda v:v['partition_x9'],1.)
    samples = out['sensitivity']['global']['samples']
    assert sum(r['parameters']['partition_x9']==1. for r in samples)==200
    assert sum(r['parameters']['partition_x9']==3. for r in samples)==100
    assert out == analyze_response(settings,{'partition_x9':1.},lambda v:v['partition_x9'],1.)
    assert out['sensitivity']['global']['sampling_methods']['partition_x9'].startswith('discrete_inverse')
    with pytest.raises(ValueError,match='interpolation_reference'):
        RangeEvidence(**{**row.model_dump(),'distribution':'interpolated_empirical'})
    continuous = RangeEvidence(**{**row.model_dump(),'distribution':'interpolated_empirical',
        'interpolation_reference':'explicit reviewed software interpolation fixture'})
    assert sample_range(continuous,.75)==2.

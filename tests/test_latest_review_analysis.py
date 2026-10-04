import numpy as np
import pytest

from igem_drylab.design_analysis import M4AnalysisConfig, RangeEvidence, analyze_response, analyze_prediction


def settings():
    return M4AnalysisConfig(local_parameter_names=['partition_x9'],
        ranges=[RangeEvidence(parameter_name='partition_x9', distribution='uniform',lower=1.,upper=2.,
            source_reference='explicit-software-fixture-range-not-biology',parameter_ids=['fixture'],reviewed_by='fixture')],
        samples=32, standard_deviation_ddof=1, independence_evidence_reference='one-variable fixture')


def test_original_local_formula_and_LHS_are_distinct_and_repeatable():
    config = settings()
    result = analyze_response(config, {'partition_x9':1.}, lambda values: values.get('partition_x9',1.)**2, 1.)
    first = result['sensitivity']['local_forward_difference']['partition_x9']['steps'][0]
    assert first['derivative'] == pytest.approx(2.01)
    assert result['sensitivity']['global']['spearman']['partition_x9'] == pytest.approx(1.)
    ys = [row['yield_abs'] for row in result['sensitivity']['global']['samples']]
    assert result['robustness']['value'] == pytest.approx(1/np.std(ys,ddof=1))
    assert result == analyze_response(config, {'partition_x9':1.}, lambda v:v.get('partition_x9',1.)**2,1.)


def test_failed_samples_and_undefined_rank_are_preserved():
    config = settings()
    def evaluator(values):
        if values['partition_x9']>1.5:
            raise ValueError('fixture_solver_failure')
        return 1.
    result = analyze_response(config,{'partition_x9':1.},evaluator,1.)
    assert result['robustness']['failed_samples']>0
    assert result['robustness']['scope']=='conditional_on_valid_samples'
    assert result['robustness']['value'] is None
    assert result['sensitivity']['global']['spearman']['partition_x9'] is None


def test_no_implicit_uniform_bounds_independence_or_sigma_convention():
    with pytest.raises(ValueError):
        M4AnalysisConfig(ranges=settings().ranges)
    with pytest.raises(ValueError):
        RangeEvidence(parameter_name='partition_x9',distribution='uniform',
            source_reference='fixture',parameter_ids=['fixture'],reviewed_by='fixture')


def test_agent_local_registry_exposes_same_actual_capabilities():
    from igem_drylab.mcp.registry import create_default_registry
    registry = create_default_registry()
    assert {'igem.m4.analyze_prediction','igem.design.scan_scaffolds',
            'igem.research.freeze_prediction','igem.research.validate_holdout'} <= set(registry.names())
    result = registry.call('igem.design.scan_scaffolds',{'design_plan':{},'output_dir':'unused'})
    assert result.is_error  # Invalid plans do not execute or invent inputs.


def test_same_version_physical_steady_solver_is_actually_called():
    from test_new_review_m4 import steady_fixture
    from igem_drylab.m4_steady_state import solve_m4_steady_state
    from igem_drylab.prediction import steady_contract
    payload = steady_fixture()
    result = solve_m4_steady_state(payload)
    contract = steady_contract(payload,result)
    analysis = analyze_prediction(contract,M4AnalysisConfig(local_parameter_names=['partition_x9']))
    assert analysis['base_yield_abs']==pytest.approx(result.yield_abs)
    assert len(analysis['sensitivity']['local_forward_difference']['partition_x9']['steps'])==3


def test_idr_chain_uses_mapping_point_not_unrelated_measured_point():
    from igem_drylab.design_analysis import IDRMappingEvidence
    species = [str(i) for i in range(8,16)]
    mapping = IDRMappingEvidence(a=0., b=2., c=3., const=0.,
        logp={i:0. for i in species}, aromatic_counts={i:1. for i in species}, theta_hydro=0.,theta_aro=0.,
        source_reference='software-fixture-only', applicable_domain_reference='fixture', reviewed_by='fixture')
    config = M4AnalysisConfig(local_parameter_names=[f'partition_x{i}' for i in species],idr_mapping=mapping)
    base = {f'partition_x{i}':10. for i in species}
    def evaluator(values):
        return sum(v*v for v in {**base,**values}.values())
    result = analyze_response(config,base,evaluator,800.)
    chain = result['sensitivity']['idr_chain']
    assert chain['mapped_base_yield']==8.
    assert chain['dY_dtheta_hydro']==pytest.approx(8*2.01*2.,rel=1e-10)
    assert chain['dY_dtheta_aro']==pytest.approx(8*2.01*3.,rel=1e-10)


def test_scan_reruns_each_complete_project_and_checks_actual_site_counts(monkeypatch,tmp_path):
    from pathlib import Path
    from types import SimpleNamespace
    import igem_drylab.pipeline as pipeline
    from igem_drylab.pipeline.models import M4ReactionPrediction,M4CandidateContext
    from igem_drylab.design_analysis import FiniteDesignPlan,ScaffoldCandidate,scan_scaffold_designs
    calls = []
    def run(config):
        calls.append(config.run.id)
        count = 1 if config.run.id=='scan-0' else 3
        context = M4CandidateContext(candidate_id='fixture',construct_id='fixture',condition_id='fixture',phi=.1,
            enzyme_distribution={'OC':{'dense':2.,'dilute':1.},'DMT':{'dense':1.,'dilute':1.}},
            nominal_site_counts={'SH3':count,'PDZ':1},m2_geometry_id='actual-fixture-geometry')
        prediction = M4ReactionPrediction(candidate_id='fixture',construct_id='fixture',condition_id='fixture',
            target_product='15',candidate_context=context,yield_abs=.5*count)
        return SimpleNamespace(model_dump=lambda **kw: {'run_id':config.run.id}),[prediction]
    monkeypatch.setattr(pipeline,'run_through_m4',run)
    config = Path('configs/m1_m4_example.yaml')
    plan = FiniteDesignPlan(candidates=[ScaffoldCandidate(config_path=config,candidate_id='fixture',site_ratio=r,
            design_evidence_reference='fixture',synthesized=False) for r in [1,2]],
        objective='yield_abs',objective_reference='fixture',decision_id='fixture-decision',decision_scope='software_fixture_only')
    result = scan_scaffold_designs(plan,tmp_path)
    assert calls==['scan-0','scan-1']
    assert result['scaffold_scan'][1]['status']=='failed'
    assert result['design_decision']['selected_candidate']['site_ratio']==1
    assert result['design_decision']['r_target'] is None
    assert result['design_decision']['exploratory_dense_ratio']==2.


def test_stdio_MCP_analysis_calls_real_registered_solver():
    import asyncio,sys
    from pathlib import Path
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters
    from test_new_review_m4 import steady_fixture
    from igem_drylab.m4_steady_state import solve_m4_steady_state
    from igem_drylab.prediction import steady_contract
    payload = steady_fixture()
    async def exercise():
        async with Client(StdioServerParameters(command=sys.executable,args=['-m','igem_drylab.mcp.server'],
                cwd=Path.cwd()),read_timeout_seconds=30) as client:
            response = await client.call_tool('igem.m4.analyze_prediction',{'prediction_contract':
                steady_contract(payload,solve_m4_steady_state(payload)),'analysis_config':{'local_parameter_names':['partition_x9']}})
            assert not response.is_error
            assert response.structured_content['schema_version']=='m4-analysis-v1'
    asyncio.run(exercise())

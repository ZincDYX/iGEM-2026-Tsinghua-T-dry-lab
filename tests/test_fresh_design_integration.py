"""Actual software-fixture M1->M2->finite M3->M4 recomputation; no biology claims."""
from pathlib import Path
import json
import yaml
import pytest

from igem_drylab.pipeline import load_config
from igem_drylab.pipeline.config import M4Config,FullNetworkInitialStateConfig
from igem_drylab.parameters import ParameterRecord
from igem_drylab.parameters.requirements import requirements_for_stage,ParameterRequirement
from igem_drylab.full_network import COMPOUNDS,REACTIONS
from igem_drylab.design_analysis import FiniteDesignPlan,ScaffoldCandidate,scan_scaffold_designs


def test_actual_finite_scan_creates_new_M2_geometry_M3_distribution_and_M4_flux(tmp_path):
    configs=[]
    for ratio in (1,2):
        config=load_config(Path('configs/m1_m4_real_scoring_example.yaml'))
        config.execution.mode='demo';config.execution.require_provenance=False;config.execution.allow_assumptions=True
        config.inputs.protein_fasta=Path('examples/data/proteins.fasta').resolve()
        config.inputs.constructs=config.inputs.constructs[:1]
        config.inputs.constructs[0].sequences={'FTH1':'MA'}
        candidate_id='M1-'+config.inputs.constructs[0].id
        metric=json.loads(Path('examples/real_metrics/m2_structure_metrics.json').read_text())['records'][0]
        metric.update(s_sh3=ratio,s_pdz=1,eta_acc_sh3=1.,eta_acc_pdz=1.,eta_bind_sh3=1.,eta_bind_pdz=1.,
            site_count_basis='complete_assembly',joint_occupancy_independent=True,m2_geometry_id=f'fixture-geometry-{ratio}')
        metrics_file=tmp_path/f'metrics-{ratio}.json';metrics_file.write_text(json.dumps([metric]))
        config.stages.m2_fusion.structure_metrics_file=metrics_file
        config.stages.m3_concentration.recruitment_mode='finite_site'
        identities=tmp_path/'network.csv'
        identities.write_text('reaction_id,enzyme,substrate,product\n'+''.join(','.join(row)+'\n' for row in REACTIONS))
        config.stages.m4_reaction=M4Config(network_mode='galatea_full_competitive',scenario_mode='galatea_spatial',
            condition_id='fixture-condition',reaction_network_file=identities,t_end=.1,solver_points=3,
            full_network_initial_state=FullNetworkInitialStateConfig(intracellular={c:float(c=='10') for c in COMPOUNDS}))
        requirements=[*requirements_for_stage(config,'m3'),*requirements_for_stage(config,'m4'),
            *[ParameterRequirement(name=f'partition_x{c}',parameter_type='kp',species_id=c,dimension='dimensionless') for c in COMPOUNDS]]
        requirements=list({r.name:r for r in requirements}.values())
        values={'phi':.2,'c_dense_scaffold':5.,'kd_sh3':.5,'kd_pdz':1.,
            **{f'{e}_total':1. for e in ('ptr','pt','oc','dmt')},
            **{f'partition_{e}':1. for e in ('ptr','pt','oc','dmt')},
            **{f'partition_x{c}':5. if c=='10' else 1. for c in COMPOUNDS},
            **{f'kcat_r{i}':1. for i in range(1,11)},**{f'km_r{i}':1. for i in range(1,11)}}
        config.parameters=[ParameterRecord(parameter_id=f'fixture-{ratio}-{r.name}',name=r.name,value=values[r.name],
            unit=r.canonical_unit,parameter_type=r.parameter_type,enzyme_id=r.enzyme_id,substrate_id=r.substrate_id,
            product_id=r.product_id,species_id=r.species_id,source_type='assumption',source_reference='software-fixture-only',
            review_status='approved',conditions={'entity_basis':'complete_assembly'} if r.name=='c_dense_scaffold' else {}) for r in requirements]
        path=tmp_path/f'config-{ratio}.yaml';path.write_text(yaml.safe_dump(config.model_dump(mode='json')))
        configs.append(ScaffoldCandidate(config_path=path,candidate_id=candidate_id,site_ratio=ratio,
            design_evidence_reference='software-fixture-only',synthesized=False))
    plan=FiniteDesignPlan(candidates=configs,objective='productivity',objective_reference='software-fixture',
        decision_id='fixture',decision_scope='software_fixture_only',varying_design_factors=['site_topology'])
    out=scan_scaffold_designs(plan,tmp_path/'scan')
    assert [row['status'] for row in out['scaffold_scan']]==['valid','valid'], [row.get('error') for row in out['scaffold_scan']]
    dense=[]
    for ratio,row in zip((1,2),out['scaffold_scan'],strict=True):
        context=row['context']
        assert context['m2_geometry_id']==f'fixture-geometry-{ratio}'
        assert context['nominal_site_counts']=={'SH3':ratio,'PDZ':1}
        assert context['parameter_ids'] and all(p.startswith(f'fixture-{ratio}-') for p in context['parameter_ids'])
        # Independent E2 root with A=1, B=phi*N*c_dense=ratio, total=1, Kd=.5.
        b=.5+ratio-1.
        free=(-b+(b*b+2.)**.5)/2
        expected_dense=free+ratio*5.*free/(.5+free)
        actual=context['enzyme_distribution']['OC']
        assert actual['dense']==pytest.approx(expected_dense,rel=0.,abs=1e-10)
        assert .2*actual['dense']+.8*actual['dilute']==pytest.approx(1.,rel=0.,abs=1e-10)
        dense.append(actual['dense'])
        run_dir=Path(row['manifest']['run_dir'])
        predictions=json.loads((run_dir/'m4_glabridin_full_network'/'reaction_predictions.json').read_text())
        assert len(predictions)==1
        artifact=json.loads(Path(predictions[0]['trajectory_artifact']).read_text())
        initial_v3=.2*actual['dense']*(25/34)+.8*actual['dilute']*(5/14)
        assert artifact['reaction_fluxes']['R3'][0]==pytest.approx(initial_v3,rel=0.,abs=1e-10)
        assert row['metrics']['productivity']>0
    assert dense[0]!=dense[1]
    assert out['scaffold_scan'][0]['metrics']['productivity']!=out['scaffold_scan'][1]['metrics']['productivity']
    assert out['design_decision']['r_target'] is None

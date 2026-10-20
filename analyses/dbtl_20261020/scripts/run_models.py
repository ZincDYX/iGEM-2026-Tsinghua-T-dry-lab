"""Conditional matched controls using the frozen existing M3/ER amount kernel.

No LC measurements enter this script. No kinetic fit or source-file edit occurs.
"""
from pathlib import Path
import os
from copy import deepcopy
from datetime import datetime, timezone
import argparse
import csv
import hashlib
import json
import sys
import time
import numpy as np

ROOT=Path(os.environ.get('GALATEA_STUDY_ROOT',str(Path(__file__).resolve().parents[1]))).resolve()
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'native'))
from igem_drylab.m3_equilibrium import M3EquilibriumInput,solve_m3_equilibrium
from igem_drylab.m4_compartments import CompartmentNetworkInput,CompartmentComparisonInput,solve_compartment_network,compartment_evaluator
from igem_drylab.full_network import COMPOUNDS,REACTIONS,ENZYME_SUBSTRATES

def read(name):return json.loads((ROOT/name).read_text(encoding='utf8'))
def save(path,data):
    path=ROOT/path;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf8')
def csvrows(name):
    with (ROOT/name).open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
def writecsv(name,rows):
    path=ROOT/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
def q(value,unit,identity):
    return {'value':float(value),'unit':unit,'entity_basis':'explicit normalized physical reference; not a measured cell',
        'parameter_id':identity,'source_reference':'parameter_sources.csv; assumptions preregistered in simulation_protocol.json'}

PROJECT=read('inputs/PSv3_project.json')['project']['inputs']
ROWS=csvrows('inputs/PS-v3/m3_phase_recruitment.csv')
KP={c:float(next(r['value'] for r in ROWS if r['code_field']=='partition_x'+c)) for c in COMPOUNDS}
KIN={}
for row in csvrows('inputs/PS-v3/m4_kinetics.csv'):
    KIN[row['reaction'],row['parameter'].split('_')[0]]=float(row['value'])

DEFAULT={'oc_total':.1,'dmt_total':.1,'phi':.02,'kd_factor':1.,'kp_factor':1.,'sh3':3,
    'er_direct_g':.001,'reservoir_fraction':.8,'er_partition_x10':10.,'cyto_exchange_g':.01,'reservoir_bulk_g':.001}
SCENARIOS=('no_LLPS','cytosolic_LLPS','ER_anchored_LLPS')

def recruitment(config,scenario):
    inp=deepcopy(PROJECT['m3_E1']);phi=0. if scenario=='no_LLPS' else config['phi']
    inp.update(candidate_id='matched_'+scenario,construct_id='hypothetical_equal_expression_not_a_wetlab_construct',
        phi=phi,c_oc_total_um=config['oc_total'],c_dmt_total_um=config['dmt_total'],s_sh3=config['sh3'],
        kd_sh3_um=2.*config['kd_factor'],kd_pdz_um=5.*config['kd_factor'],
        c_dense_um=(.5-(1-phi)*.05)/phi if phi else 22.55,
        c_scaffold_total_um=.5 if phi else None,c_sat_um=.05 if phi else None,
        input_parameter_ids=['PS-v3-priors','matched-no-LC-fit'],m2_geometry_id='ASSUMED_equal_accessibility_not_ER_geometry_validation')
    result=solve_m3_equilibrium(M3EquilibriumInput.model_validate(inp)).model_dump(mode='json')
    if result['status']!='valid' or not result['m4_ready']:raise ValueError('M3 not admitted: '+str(result))
    return inp,result

def case(config,scenario,condition_id='matched-reference'):
    m3inp,m3=recruitment(config,scenario);phi=m3['phi']
    volumes={'bulk':1-phi,'reservoir':.05}
    if phi:volumes['droplet']=phi
    pools=[]
    for pool,volume in volumes.items():
        enzyme={e:0. for e in ENZYME_SUBSTRATES}
        if pool=='bulk':
            enzyme.update(OC=(1-phi)*m3['oc']['free_dilute_um'],DMT=(1-phi)*m3['dmt']['free_dilute_um'])
        if pool=='droplet':enzyme.update(OC=phi*m3['oc']['total_dense_um'],DMT=phi*m3['dmt']['total_dense_um'])
        pools.append({'pool_id':pool,'role':'anchored_droplet' if pool=='droplet' else 'cytosol',
            'volume':q(volume,'L','volume_'+pool),'geometry_ref':'ASSUMED_pool_geometry_NOT_a_membrane_structure',
            'enzyme_amounts':{e:q(v,'umol','M3_'+e+'_'+pool) for e,v in enzyme.items()},
            'enzyme_activity_ratios':{e:q(1.,'1','common_activity_no_scenario_gain') for e in ENZYME_SUBSTRATES}})
    kp={c:KP[c]*config['kp_factor'] for c in COMPOUNDS}
    kr={c:(config['er_partition_x10'] if c=='10' else 1.) for c in COMPOUNDS}
    def interface(identity,first,second,partition,g):
        return {'interface_id':identity,'first_pool':first,'second_pool':second,'mode':'finite_exchange',
            'second_over_first_partition':{c:q(partition[c],'1',identity+'_K_'+c) for c in COMPOUNDS},
            'conductance':{c:q(g,'L/h',identity+'_G_'+c) for c in COMPOUNDS},
            'applicability_reference':'Hypothesis only; finite exchange between cytosolic accessible pools, no membrane permeation claim',
            'timescale_evidence_reference':None}
    interfaces=[interface('reservoir_bulk','bulk','reservoir',kr,config['reservoir_bulk_g'])]
    if phi:
        interfaces.append(interface('bulk_droplet','bulk','droplet',kp,config['cyto_exchange_g']))
        if scenario=='ER_anchored_LLPS':
            # Thermodynamic cycle consistency: K(D/R)=K(D/C)/K(R/C).
            interfaces.append(interface('reservoir_droplet','reservoir','droplet',{c:kp[c]/kr[c] for c in COMPOUNDS},config['er_direct_g']))
    initial={p:{c:q(0.,'umol','initial_'+p+'_'+c) for c in COMPOUNDS} for p in volumes}
    initial['reservoir']['10']=q(2937.5*config['reservoir_fraction'],'umol','initial_reservoir_x10')
    initial['bulk']['10']=q(2937.5*(1-config['reservoir_fraction']),'umol','initial_bulk_x10')
    reactions=[{'reaction_id':rid,'enzyme':e,'substrate':s,'product':p,'kcat_per_h':KIN[rid,'kcat'],
        'km_um':KIN[rid,'km'],'parameter_ids':['PS-v3-'+rid+'-kcat','PS-v3-'+rid+'-Km']} for rid,e,s,p in REACTIONS]
    # PTR/PT pools start at zero in this feed-10 subnetwork. This is a model-
    # scope choice, not a claim of their absence in a wet-lab genotype.
    payload={'construct_id':'HYPOTHETICAL_'+scenario,'condition_id':condition_id,'scenario':scenario,
        'topology_evidence_ref':'ASSUMED_CYTOSOLIC_BODY_FOR_SENSITIVITY; actual Q10/Q13 orientation unresolved' if scenario=='ER_anchored_LLPS' else None,
        'reaction_location_reference':'Feed-10 branch only; enzyme species compete for shared enzyme pools; no activity in reservoir',
        'pools':pools,'interfaces':interfaces,'reactions':reactions,
        'reaction_locations':{rid:list(volumes) for rid,_,_,_ in REACTIONS},'boundaries':[],
        'initial_amounts_umol':initial,'time_grid_h':np.linspace(0,240,121).tolist(),
        'steady_initial_guesses_umol':[],
        'numerics':{'method':'BDF','relative_tolerance':1e-8,'amount_absolute_tolerance_umol':1e-9,
            'steady_relative_tolerance':1e-8,'steady_absolute_tolerance_umol_per_h':1e-8,
            'eigenvalue_tolerance_per_h':1e-8,'steady_max_evaluations':100},
        'evidence_mode':'conditional_model'}
    return CompartmentNetworkInput.model_validate(payload),m3inp,m3

def evaluate(config,scenario,run_id,detail=False,numerics=None):
    payload,m3inp,m3=case(config,scenario)
    if numerics:payload=payload.model_copy(update={'numerics':payload.numerics.model_copy(update=numerics)})
    start=time.perf_counter();result=solve_compartment_network(payload)
    if result['status']!='numerically_solved':
        save('failures/'+run_id+'.json',{'config':config,'input':payload.model_dump(mode='json'),'output':result})
        raise ValueError(run_id+': '+result['status'])
    t=np.asarray(result['time_h']);global_amount={c:sum(np.asarray(p['amounts_umol'][c]) for p in result['pools'].values()) for c in COMPOUNDS}
    arrays=np.array([v for p in result['pools'].values() for v in p['amounts_umol'].values()])
    rhs,distribute,aggregate,index,_=compartment_evaluator(payload)
    init=np.array([payload.initial_amounts_umol[p.pool_id][c].value for p in payload.pools for c in COMPOUNDS]);state=aggregate@init
    deriv,jac,*_=rhs(state);eps=1e-5
    # One-sided perturbations avoid testing outside the nonnegative physical domain.
    numeric=np.column_stack([(rhs(state+np.eye(len(state))[i]*eps)[0]-deriv)/eps for i in range(len(state))])
    jacerr=float(np.max(np.abs(jac-numeric)))/max(1.,float(np.max(np.abs(jac))))
    row={'run_id':run_id,'scenario':scenario,**config,'x15_24h_umol':float(global_amount['15'][12]),
        'x15_120h_umol':float(global_amount['15'][60]),'x15_240h_umol':float(global_amount['15'][-1]),
        'x10_240h_umol':float(global_amount['10'][-1]),'x11_240h_umol':float(global_amount['11'][-1]),
        'x14_240h_umol':float(global_amount['14'][-1]),'x14_max_umol':float(global_amount['14'].max()),
        'oc_dense_um':m3['oc']['total_dense_um'],'dmt_dense_um':m3['dmt']['total_dense_um'],
        'oc_bound_fraction':m3['oc']['bound_fraction_of_whole_cell_total'],
        'dmt_bound_fraction':m3['dmt']['bound_fraction_of_whole_cell_total'],
        'OC_fraction_of_dense_OC_DMT':m3['oc']['total_dense_um']/(m3['oc']['total_dense_um']+m3['dmt']['total_dense_um']) if m3['phi'] else None,
        'OC_fraction_of_total_OC_DMT':config['oc_total']/(config['oc_total']+config['dmt_total']),
        'M3_OC_mass_residual_uM':m3['oc']['mass_balance_residual_um'],
        'M3_DMT_mass_residual_uM':m3['dmt']['mass_balance_residual_um'],
        'max_backbone_closure_umol':result['max_mass_conservation_residual_umol'],
        'minimum_amount_umol':float(arrays.min()),'relative_jacobian_check_error':jacerr,
        'seconds':time.perf_counter()-start,'status':result['status'],'data_class':'conditional_model_prediction'}
    if abs(row['max_backbone_closure_umol'])>1e-4 or row['minimum_amount_umol'] < -1e-9 or jacerr>1e-4:
        raise ValueError('Independent numerical check failed: '+str(row))
    if detail:
        save('model_runs/'+run_id+'.json',{'config':config,'M3_input':m3inp,'M3_output':m3,'M4_input':payload.model_dump(mode='json'),'M4_output':result})
        curve=[]
        for j,tt in enumerate(t):
            record={'run_id':run_id,'scenario':scenario,'time_h':tt,**{f'x{c}_umol':float(global_amount[c][j]) for c in COMPOUNDS},
                'backbone_closure_umol':float(sum(global_amount[c][j] for c in COMPOUNDS)-2937.5)}
            for p,values in result['pools'].items():
                for c in ('10','11','14','15'):record[p+'_x'+c+'_uM']=float(values['concentrations_um'][c][j])
            curve.append(record)
        writecsv('curves/'+run_id+'.csv',curve)
    return row,result

def historical():
    reference=read('inputs/PSv3_reference.json');rows=[];recruit=[]
    for s in ('C1','C2','E1','E2','E3'):
        x=PROJECT['m3_'+s];p=PROJECT['m4_'+s]['method']['parameters']
        row={'scenario':s,'data_class':'historical_synthetic_calibrated','oc_total_uM':x['c_oc_total_um'],
            'dmt_total_uM':x['c_dmt_total_um'],'phi':x['phi'],'scaffold_dense_uM':x['c_dense_um'],
            'Kd_SH3_uM':x['kd_sh3_um'],'Kd_PDZ_uM':x['kd_pdz_um'],'enzyme_Kp_OC':x['k_oc'],'enzyme_Kp_DMT':x['k_dmt'],
            **{k:v['value'] for k,v in p.items() if k.startswith(('activity_','kcat_','km_','kp_'))},
            'export_fraction':p['export_fraction']['value']}
        rows.append(row)
        calc=solve_m3_equilibrium(M3EquilibriumInput.model_validate(x)).model_dump(mode='json')
        old=reference['m3'][s]['result']
        for e in ('oc','dmt'):
            for f in ('free_dilute_um','total_dense_um','bound_fraction_of_whole_cell_total'):
                recruit.append({'scenario':s,'enzyme':e,'field':f,'saved':old[e][f],'recomputed':calc[e][f],'delta':calc[e][f]-old[e][f]})
    writecsv('historical_scenarios.csv',rows);writecsv('historical_M3_recheck.csv',recruit)

def prepare():
    historical()
    protocol={'frozen_at_UTC':datetime.now(timezone.utc).isoformat(),'default':DEFAULT,
        'M3_version':'m3-s1-e10-2026-09-27','M4_version':'m4-compartment-amount-v1-2026-10-10',
        'LC_used_for_fit_or_range_selection':False,'activity_multipliers':'1.0 for every enzyme, every compartment and every case',
        'reference_volume_L':1.,'reservoir_volume_L':.05,'total_reference_volume_L':1.05,'initial_total_x10_umol':2937.5,
        'times_h':[0,240],'sampling_step_h':2,'reference_time_for_sensitivity_h':120,
        'mechanism':'Identical reservoir/bulk exchange in all cases; ER adds a finite reservoir-to-droplet interface with cycle-consistent K. No extra substrate source.',
        'reservoir_interpretation':'Hypothetical ER-near substrate-accessible cytosolic microvolume, NOT ER lumen or lipid membrane molarity.',
        'normalization':'umol per arbitrary 1 L reactive reference plus 0.05 L reservoir; do not equate with wet-lab sample uM or ug/mL.',
        'branch':'closed feed-10 four-reaction reachable subset of the existing competitive 10-reaction kernel; upstream species and PTR/PT inactive by model scope',
        'byproduct_limit':'x14 is a transient competing-branch intermediate that can reach x15 via R10. No irreversible byproduct sink in this branch.',
        'actual_ER_M3_geometry':'BLOCKED: body orientation, ER area/site density and compatible 24-chain ensemble not established; equal droplet recruitment is an explicit sensitivity assumption',
        'sensitivity':{'OC_total_ratio_to_DMT':[.25,.5,1,2,4],'SH3_sites':[1,2,3,4,6],
            'phi':[.005,.01,.02,.04,.08],'Kd_factor':[.25,.5,1,2,4],'metabolite_Kp_factor':[.25,.5,1,2,4],
            'ER_direct_conductance_L_h':[0,.0001,.001,.01,.1],'reservoir_initial_substrate_fraction':[0,.2,.5,.8,1.]},
        'range_basis':'All scan ranges are explicit exploratory assumptions around PS-v3 synthetic priors, not measured/literature confidence intervals.'}
    if (ROOT/'simulation_protocol.json').exists():raise ValueError('Protocol already frozen; do not overwrite it')
    save('simulation_protocol.json',protocol)
    rows=[{'parameter':k,'reference':v,'source_type':'historical_synthetic' if k in ('oc_total','dmt_total','phi','sh3') else 'explicit_hypothesis',
        'source':'PS-v3_project inputs' if k in ('oc_total','dmt_total','phi','sh3') else 'simulation_protocol.json; not measured and not LC-fitted'} for k,v in DEFAULT.items()]
    rows.extend([{'parameter':'Km/kcat all ten reactions','reference':'see inputs/PS-v3/m4_kinetics.csv','source_type':'historical_synthetic','source':'PS-v3 synthetic assay-context priors, no use of separate literature Km table'},
        {'parameter':'all enzyme activities','reference':'1.0','source_type':'matched_control_setting','source':'scenario-specific historical effective multipliers explicitly removed'},
        {'parameter':'metabolite/enzyme Kp, Kd, scaffold total/dilute','reference':'see frozen PS-v3 files','source_type':'historical_synthetic','source':'M3 partition, finite binding and scaffold lever rule retained; accessibility assumed equal'},
        {'parameter':'all scan ranges','reference':'see simulation_protocol.json','source_type':'hypothesis_range','source':'No measured or directly applicable literature interval available in supplied package'}])
    writecsv('parameter_sources.csv',rows)
    print('Protocol and parameter ranges frozen without reading LC.')

def run():
    if not (ROOT/'simulation_protocol.json').exists():raise ValueError('Freeze protocol first')
    if (ROOT/'matched_summary.csv').exists():raise ValueError('Results already exist; use a new execution directory')
    matched=[]
    for bg in (.1,1.2):
        config={**DEFAULT,'oc_total':bg,'dmt_total':bg}
        controls={s:case(config,s,'same-expression-'+str(bg))[0] for s in SCENARIOS}
        CompartmentComparisonInput.model_validate({'cases':controls,'matched_enzyme_relative_tolerance':1e-10})
        for s in SCENARIOS:
            identity=('low' if bg==.1 else 'high')+'_'+s
            row,_=evaluate(config,s,identity,True);matched.append(row);print(identity,round(row['x15_120h_umol'],6),flush=True)
    writecsv('matched_summary.csv',matched)
    scans=[]
    # A compact paired factorial, not a broad parameter-identification exercise.
    configs=[]
    for kd in (.25,.5,1,2,4):
        for kp in (.25,.5,1,2,4):configs.append(('Kd_Kp',f'kd{kd}_kp{kp}',{**DEFAULT,'kd_factor':kd,'kp_factor':kp}))
    for ratio in (.25,.5,1,2,4):
        for sites in (1,2,3,4,6):configs.append(('OC_sites',f'oc{ratio}_sites{sites}',{**DEFAULT,'oc_total':.1*ratio,'sh3':sites}))
    for phi in (.005,.01,.02,.04,.08):configs.append(('phi',f'phi{phi}',{**DEFAULT,'phi':phi}))
    for g in (0,.0001,.001,.01,.1):
        for fraction in (0,.2,.5,.8,1.):configs.append(('ER_benefit',f'g{g}_f{fraction}',{**DEFAULT,'er_direct_g':g,'reservoir_fraction':fraction}))
    for family,identity,config in configs:
        # Repeat all matched arms, not ratios against a mismatched baseline.
        for s in SCENARIOS:
            row,_=evaluate(config,s,family+'_'+identity+'_'+s);row['scan_family']=family;scans.append(row)
        if len(scans)%30==0:print('scan cases',len(scans),flush=True)
    writecsv('sensitivity.csv',scans)
    ablations=[]
    for identity,config in [('no_recruitment',{**DEFAULT,'sh3':0}),('no_reservoir_substrate',{**DEFAULT,'reservoir_fraction':0}),
        ('no_direct_ER_exchange',{**DEFAULT,'er_direct_g':0}),('fast_bulk_access',{**DEFAULT,'reservoir_bulk_g':.1}),
        ('fast_all_common_exchange',{**DEFAULT,'reservoir_bulk_g':10.,'cyto_exchange_g':10.})]:
        for s in SCENARIOS:
            row,_=evaluate(config,s,'ablation_'+identity+'_'+s);row['ablation']=identity;ablations.append(row)
    writecsv('ablations.csv',ablations)
    convergence=[]
    for s in SCENARIOS:
        row,_=evaluate(DEFAULT,s,'tight_'+s,numerics={'relative_tolerance':1e-10,'amount_absolute_tolerance_umol':1e-11})
        base=next(x for x in matched if x['scenario']==s and x['oc_total']==.1)
        convergence.append({'scenario':s,'x15_120h_default':base['x15_120h_umol'],'x15_120h_tight':row['x15_120h_umol'],
            'absolute_delta_umol':abs(row['x15_120h_umol']-base['x15_120h_umol'])})
    writecsv('convergence.csv',convergence)
    zero=next(x for x in scans if x['scan_family']=='ER_benefit' and x['er_direct_g']==0 and x['reservoir_fraction']==.8 and x['scenario']=='ER_anchored_LLPS')
    cyto=next(x for x in matched if x['oc_total']==.1 and x['scenario']=='cytosolic_LLPS')
    allrows=matched+scans+ablations
    tests={'completed_UTC':datetime.now(timezone.utc).isoformat(),'status':'PASS','primary_cases':len(matched),'scan_cases':len(scans),
        'ablation_cases':len(ablations),'tight_tolerance_cases':len(convergence),'historical_M3_cases':5,
        'max_backbone_closure_umol':max(r['max_backbone_closure_umol'] for r in allrows),
        'max_M3_enzyme_closure_uM':max(abs(r[k]) for r in allrows for k in ('M3_OC_mass_residual_uM','M3_DMT_mass_residual_uM')),
        'minimum_amount_umol':min(r['minimum_amount_umol'] for r in allrows),
        'max_relative_Jacobian_check_error':max(r['relative_jacobian_check_error'] for r in allrows),
        'zero_direct_exchange_ER_minus_cyto_x15_120h':zero['x15_120h_umol']-cyto['x15_120h_umol'],
        'max_tight_solver_delta_umol':max(r['absolute_delta_umol'] for r in convergence),
        'not_tests_of':['full membrane physical stability','measured ER topology','microscopic parameter identification','whole chemical mass including cofactors','irreversible off-pathway byproduct formation']}
    assert abs(tests['zero_direct_exchange_ER_minus_cyto_x15_120h'])<1e-8
    assert tests['max_tight_solver_delta_umol']<1e-3
    save('numerical_tests.json',tests);print(json.dumps(tests,indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run']);args=parser.parse_args()
    (prepare if args.action=='prepare' else run)()

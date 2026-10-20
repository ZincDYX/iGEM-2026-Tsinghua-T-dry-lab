"""Independent numerical edge cases and preservation checks for the final study."""
from pathlib import Path
import os
from copy import deepcopy
from datetime import datetime,timezone
from hashlib import sha256
import csv
import importlib.metadata
import json
import sys
import numpy as np
ROOT=Path(os.environ.get('GALATEA_STUDY_ROOT',str(Path(__file__).resolve().parents[1]))).resolve()
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'native'))
from run_models import DEFAULT,SCENARIOS,case
from igem_drylab.m3_equilibrium import M3EquilibriumInput
from igem_drylab.m4_compartments import CompartmentNetworkInput,CompartmentComparisonInput,solve_compartment_network

def read(name):return json.loads((ROOT/name).read_text(encoding='utf8'))
def digest(path):
    h=sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def main():
    tests=[]
    def check(name,condition):
        assert bool(condition),name
        tests.append({'test':name,'status':'PASS'})
    def rejects(name,operation):
        try:operation()
        except ValueError:check(name,True)
        else:raise AssertionError(name)
    models={s:case(DEFAULT,s,'same-test-condition')[0] for s in SCENARIOS}
    CompartmentComparisonInput.model_validate({'cases':models,'matched_enzyme_relative_tolerance':1e-10})
    check('native_three_arm_matched_contract',True)
    bad={k:v.model_dump(mode='json') for k,v in models.items()};bad['ER_anchored_LLPS']['pools'][0]['enzyme_amounts']['OC']['value']*=2
    rejects('unequal_enzyme_amount_rejected',lambda:CompartmentComparisonInput.model_validate({'cases':bad,'matched_enzyme_relative_tolerance':1e-10}))
    bad={k:v.model_dump(mode='json') for k,v in models.items()};bad['ER_anchored_LLPS']['initial_amounts_umol']['bulk']['10']['value']+=1
    rejects('unequal_initial_substrate_rejected',lambda:CompartmentComparisonInput.model_validate({'cases':bad,'matched_enzyme_relative_tolerance':1e-10}))
    bad=models['cytosolic_LLPS'].model_dump(mode='json');bad['interfaces'][0]['second_over_first_partition']['10']['value']=0
    rejects('nonpositive_partition_rejected',lambda:CompartmentNetworkInput.model_validate(bad))
    bad=models['cytosolic_LLPS'].model_dump(mode='json');bad['initial_amounts_umol']['bulk']['10']['value']=-1
    rejects('negative_initial_amount_rejected',lambda:CompartmentNetworkInput.model_validate(bad))
    _,inp,_=case(DEFAULT,'cytosolic_LLPS');inp['kd_sh3_um']=0
    rejects('nonpositive_M3_Kd_rejected',lambda:M3EquilibriumInput.model_validate(inp))
    # Closed exchange-only two-pool problem, independent analytic expectation.
    payload=models['no_LLPS'].model_dump(mode='json')
    for pool in payload['pools']:
        for value in pool['enzyme_amounts'].values():value['value']=0
    for row in payload['initial_amounts_umol'].values():
        for value in row.values():value['value']=0
    payload['initial_amounts_umol']['bulk']['10']['value']=1
    payload['numerics'].update(relative_tolerance=1e-11,amount_absolute_tolerance_umol=1e-12)
    result=solve_compartment_network(CompartmentNetworkInput.model_validate(payload))
    check('exchange_only_ODE_admitted',result['status']=='numerically_solved')
    expected=2/3+np.exp(-.003*np.asarray(result['time_h']))/3
    delta=float(np.max(np.abs(np.asarray(result['pools']['bulk']['amounts_umol']['10'])-expected)))
    check('finite_exchange_matches_analytic_two_pool_solution',delta<1e-8)
    closure=np.asarray(result['pools']['bulk']['amounts_umol']['10'])+np.asarray(result['pools']['reservoir']['amounts_umol']['10'])-1
    check('exchange_has_equal_opposite_amount_flux',float(np.max(np.abs(closure)))<1e-10)
    manifest=read('run_manifest.json')
    for row in manifest['inputs']:
        p=Path(row['original']);check('original_hash_unchanged:'+row['copy'],digest(p)==row['sha256'])
        check('original_mtime_unchanged:'+row['copy'],p.stat().st_mtime_ns==row['original_mtime_ns'])
        check('frozen_copy_hash:'+row['copy'],digest(ROOT/row['copy'])==row['sha256'])
    for row in manifest['native_code']:
        check('frozen_native_code_hash:'+row['copy'],digest(ROOT/row['copy'])==row['sha256'])
    archive=Path(manifest['original_archive']['path'])
    check('original_2_45_GB_results_archive_unchanged',digest(archive)==manifest['original_archive']['sha256'])
    check('original_archive_mtime_unchanged',archive.stat().st_mtime_ns==manifest['original_archive']['mtime_ns'])
    numerics=read('numerical_tests.json');lc=read('LC_tests.json');identity=read('identity_tests.json')
    check('all_scanned_numerics_PASS',numerics['status']=='PASS')
    check('all_LC_records_and_stars_preserved',lc['records']==78 and lc['starred']==18 and lc['independent_extraction_matches_previous'])
    check('selected_proteins_have_unchanged_DNA_identity',identity['all_saved_selected_proteins_found_in_unchanged_DNA'])
    check('actual_ER_membrane_validation_not_falsely_marked_complete',bool(identity['blocked']))
    for figure in read('figure_provenance.json'):
        for ext in figure['formats']:check('figure_export:'+figure['figure']+'.'+ext,(ROOT/'figures'/(figure['figure']+'.'+ext)).stat().st_size>1000)
    versions={name:importlib.metadata.version(name) for name in ['numpy','scipy','pandas','matplotlib','pydantic','biopython']}
    final={'status':'PASS','checks':len(tests),'tests':tests,'analytic_exchange_max_error_umol':delta,
        'tested_UTC':datetime.now(timezone.utc).isoformat(),'Python':sys.version,'dependencies':versions,
        'not_independently_validated':['native desktop software builds','wet-lab interpretation by an external reviewer','fresh environment dependency installation','full membrane dynamics']}
    (ROOT/'verification_tests.json').write_text(json.dumps(final,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:final[k] for k in ['status','checks','analytic_exchange_max_error_umol','dependencies']},indent=2))

if __name__=='__main__':main()

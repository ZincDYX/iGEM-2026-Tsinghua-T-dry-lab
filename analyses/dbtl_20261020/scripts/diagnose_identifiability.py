"""Exact active-enzyme/kcat confounding of the M4 layer; no parameter fitting."""
from pathlib import Path
import os
import csv,json,sys
import numpy as np
ROOT=Path(os.environ.get('GALATEA_STUDY_ROOT',str(Path(__file__).resolve().parents[1]))).resolve();sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'native'))
from igem_drylab.m4_compartments import CompartmentNetworkInput,solve_compartment_network

def main():
    path=ROOT/'identifiability_diagnostic.csv'
    if path.exists():raise ValueError('Do not overwrite this diagnostic')
    original=json.loads((ROOT/'model_runs/low_cytosolic_LLPS.json').read_text(encoding='utf8'))
    baseline=np.array([values for p in original['M4_output']['pools'].values() for values in p['amounts_umol'].values()])
    rows=[]
    for scale in (.5,2.):
        payload=json.loads(json.dumps(original['M4_input']))
        for pool in payload['pools']:
            for quantity in pool['enzyme_amounts'].values():
                quantity['value']*=scale
                quantity['source_reference']='M4 identifiability scaling diagnostic; not a new M3 equilibrium allocation'
        for reaction in payload['reactions']:reaction['kcat_per_h']/=scale
        output=solve_compartment_network(CompartmentNetworkInput.model_validate(payload))
        assert output['status']=='numerically_solved'
        array=np.array([values for p in output['pools'].values() for values in p['amounts_umol'].values()])
        error=float(np.max(np.abs(array-baseline)));assert error<1e-7
        rows.append({'active_enzyme_amount_scale':scale,'kcat_scale':1/scale,'all_species_all_pools_all_times_max_delta_umol':error,
            'status':'indistinguishable M4 trajectories','scope':'fixed allocation/kinetics layer, not re-solved M3 binding or a matched expression comparison'})
        (ROOT/f'model_runs/identifiability_scale_{scale}.json').write_text(json.dumps({'input':payload,'output':output},indent=2),encoding='utf8')
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps({'status':'PASS','additional_native_M4_runs':2,'maximum_delta_umol':max(r['all_species_all_pools_all_times_max_delta_umol'] for r in rows),
        'scope':'Exact confounding between active enzyme allocation and kcat; not a full identifiability proof for all M3/M4 parameters'},indent=2))

if __name__=='__main__':main()

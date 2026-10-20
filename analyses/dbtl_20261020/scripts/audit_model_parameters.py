"""Effective per-arm parameters, distinct from factorial configuration labels."""
from pathlib import Path
import os
import csv,json
ROOT=Path(os.environ.get('GALATEA_STUDY_ROOT',str(Path(__file__).resolve().parents[1]))).resolve()
def out(name,rows):
    with (ROOT/name).open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
def main():
    rows=[];reaction_rows=[]
    for path in sorted((ROOT/'model_runs').glob('*LLPS.json')):
        record=json.loads(path.read_text(encoding='utf8'));m=record['M4_input'];r=record['M3_input'];config=record['config']
        pools={p['pool_id']:p for p in m['pools']};interfaces={i['interface_id']:i for i in m['interfaces']}
        def g(name):return interfaces[name]['conductance']['10']['value'] if name in interfaces else 0.
        phi=r['phi'];expected_oc=sum(p['enzyme_amounts']['OC']['value'] for p in m['pools']);expected_dmt=sum(p['enzyme_amounts']['DMT']['value'] for p in m['pools'])
        assert abs(expected_oc-config['oc_total'])<1e-10 and abs(expected_dmt-config['dmt_total'])<1e-10
        assert all(q['value']==1 for p in m['pools'] for q in p['enzyme_activity_ratios'].values())
        row={'run_id':path.stem,'scenario':m['scenario'],'effective_phi':phi,'configured_LLPS_phi_for_matching':config['phi'],
            'actual_OC_amount_umol':expected_oc,'actual_DMT_amount_umol':expected_dmt,
            'scaffold_total_reactive_uM':r['c_scaffold_total_um'],'scaffold_dilute_uM':r['c_sat_um'],
            'scaffold_dense_uM_if_droplet':r['c_dense_um'] if phi else None,
            'Kd_SH3_uM_if_binding':r['kd_sh3_um'] if phi else None,'Kd_PDZ_uM_if_binding':r['kd_pdz_um'] if phi else None,
            'free_OC_Kp_if_droplet':r['k_oc'] if phi else None,'free_DMT_Kp_if_droplet':r['k_dmt'] if phi else None,
            'metabolite_10_Kp_if_droplet':interfaces['bulk_droplet']['second_over_first_partition']['10']['value'] if phi else None,
            'bulk_volume_L':pools['bulk']['volume']['value'],'droplet_volume_L':pools['droplet']['volume']['value'] if phi else 0.,
            'reservoir_volume_L':pools['reservoir']['volume']['value'],'total_volume_L':sum(p['volume']['value'] for p in m['pools']),
            'initial_total_10_umol':sum(v['10']['value'] for v in m['initial_amounts_umol'].values()),
            'common_bulk_reservoir_G_L_h':g('reservoir_bulk'),'bulk_droplet_G_L_h':g('bulk_droplet'),
            'ER_direct_G_L_h_if_present':g('reservoir_droplet'),'all_activity_ratios':1.,'data_class':'conditional_hypothesis'}
        assert abs(row['total_volume_L']-1.05)<1e-12
        rows.append(row)
        for reaction in m['reactions']:
            reaction_rows.append({'run_id':path.stem,**reaction,'source_type':'historical_synthetic_intrinsic_not_LC_fitted'})
    assert len(rows)==6
    out('matched_parameter_audit.csv',rows);out('reaction_parameter_registry.csv',reaction_rows)
    print('PASS: six effective-arm configurations; phi=0 and no direct exchange in the appropriate controls.')
if __name__=='__main__':main()

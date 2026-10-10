"""Approved independent synthetic demo through the same Web/CLI engine.

Run only on an authorized compute environment. Package input is supplied by the
user; archived scripts and reference output files are never executed/read as
newly computed results. No synthetic data are experimental validation.
"""
import argparse
import json
from pathlib import Path

from igem_drylab.software.application import ApplicationService
from igem_drylab.workflow.display_resources import DisplayResources
from igem_drylab.workflow.series_export import series_csv


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): raise SystemExit('Choose a new output directory; prior inputs/results are preserved.')
    application=ApplicationService(args.output/'workspace')
    project=application.create_project('PS-v3 synthetic reference demonstration')
    application.import_files(project['id'],[args.package])
    proposal=application.plan(project['id'],'ps-v3-demo')
    application.planning.decide(proposal.id,'accept')
    run=application.run_approved(proposal.id)
    if run['status']!='succeeded': raise SystemExit('Synthetic job failed; retained diagnostics are not a valid result.')
    repeated=application.run_approved(proposal.id)
    if repeated['id']!=run['id']: raise RuntimeError('Approved run was repeated instead of recovered.')
    output=run['nodes'][0]['output']
    assert output['source_type']=='synthetic' and output['formal_prediction_allowed'] is False
    assert output['E3']['status']=='blocked' and output['E3']['result'] is None
    display=DisplayResources(application.store,application.boundary)
    endpoints={}
    for case,item in output['cases'].items():
        result=item['m4']['result'];initial=sum(sum(q['value'] for q in pool.values()) for pool in item['solver_inputs']['m4']['initial_amounts_umol'].values())
        for i in range(len(result['time_h'])):
            total=sum(values[i] for pool in result['pools'].values() for values in pool['amounts_umol'].values())
            tolerance=result['numerical_admission']['mass_tolerance_umol'][i]
            assert abs(total-initial-result['cumulative_feed_umol'][i]+result['cumulative_loss_umol'][i])<=tolerance
        if item['m3']:
            phi=item['solver_inputs']['m3']['phi']
            for enzyme in ('oc','dmt'):
                e=item['m3'][enzyme];specified=item['solver_inputs']['m3']['c_'+enzyme+'_total_um']
                assert abs(phi*e['total_dense_um']+(1-phi)*e['free_dilute_um']-specified)<1e-8
        file_id=item['trajectory_artifact'].removeprefix('asset:')
        page=display.series(project['id'],file_id,0,1000)
        assert page['source_type']=='synthetic' and page['formal_prediction_allowed'] is False
        (args.output/(case+'-series.csv')).write_text(''.join(series_csv(display,project['id'],file_id)),encoding='utf-8')
        endpoint=sum(pool['amounts_umol']['15'][-1] for pool in result['pools'].values())
        endpoints[case]={'compound15_total_umol':endpoint,'endpoint_time_h':result['time_h'][-1],
            'source_type':'synthetic','formal_prediction_allowed':False,'experimental_validation':False}
    (args.output/'run.json').write_text(json.dumps(run,indent=2,allow_nan=False),encoding='utf-8')
    (args.output/'endpoints.json').write_text(json.dumps(endpoints,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'job':'completed','source_type':'synthetic','formal_prediction_allowed':False,
        'experimental_validation':False,'E3':'blocked','endpoints':endpoints},allow_nan=False))


if __name__=='__main__':main()

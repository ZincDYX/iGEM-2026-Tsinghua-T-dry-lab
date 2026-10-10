"""Recorded software-format samples, no solver or biological calculations."""
import csv
from io import StringIO
import json
import pytest
from fastapi.testclient import TestClient
from igem_drylab.software.dashboard import create_app
from igem_drylab.workflow.models import Project,WorkflowError
from igem_drylab.workflow.display_resources import DisplayResources
from igem_drylab.workflow.series_export import series_csv


def recorded():
    return {'source_type':'synthetic','formal_prediction_allowed':False,'result':{
        'schema_version':'m4-compartment-amount-v1','formula_version':'SOFTWARE_FORMAT_FIXTURE',
        'status':'numerically_solved','scenario':'ER_anchored_LLPS','time_h':[0,1,2],
        'numerical_settings':{'amount_absolute_tolerance_umol':1e-10,'relative_tolerance':1e-9},
        'pools':{'cytosol':{'role':'cytosol','volume_L':2,'volume_source':{'value':2,'unit':'L','source_reference':'SOFTWARE_ONLY'},
            'amounts_umol':{'15':[0,None,6]},'concentrations_um':{'15':[0,None,3]}},
            'droplet':{'role':'ER_droplet','volume_L':.5,'volume_source':{'value':.5,'unit':'L','source_reference':'SOFTWARE_ONLY'},
            'amounts_umol':{'15':[1,2,3]},'concentrations_um':{'15':[2,4,6]}}}}}


def environment(tmp_path,raw):
    app=create_app(data_dir=tmp_path/'workspace',session_token='test',discover_tools=False)
    store=app.state.platform_store
    store.save_project(Project(id='p',name='Display fixture'))
    source=tmp_path/'recorded.json';source.write_text(json.dumps(raw))
    asset=app.state.disclosure.asset(source,project_id='p')
    return app,DisplayResources(store,app.state.disclosure),asset['id']


def test_real_pool_units_nulls_synthetic_scope_catalog_and_csv_agree(tmp_path):
    app,display,file_id=environment(tmp_path,recorded())
    assert display.catalog('p',0,10,kind='series')['items'][0]['result_schema_version']=='m4-compartment-amount-v1'
    page=display.series('p',file_id,0,10)
    assert page['source_type']=='synthetic' and page['formal_prediction_allowed'] is False
    assert page['pool_volumes']['cytosol']['volume_L']==2
    assert [s['unit'] for s in page['series']]==['umol','uM','umol','uM']
    assert page['values']=={'0':[0,None,6],'1':[0,None,3],'2':[1,2,3],'3':[2,4,6]}
    exported=list(csv.reader(StringIO(''.join(series_csv(display,'p',file_id)))))
    assert exported[2][2:]==['','','2.0','4.0']
    assert exported[-1][2:]==['6.0','3.0','3.0','6.0']
    assert 'Synthetic demo' in exported[-1][0]
    with TestClient(app) as client:
        response=client.get(f'/api/platform/files/{file_id}/series.csv?project_id=p',headers={'X-FusionLab-Token':'test'})
        assert response.status_code==200
        assert list(csv.reader(StringIO(response.text)))==exported


@pytest.mark.parametrize('change',['missing_volume','mismatched_volume','bad_concentration'])
def test_never_guess_a_missing_volume_or_accept_inconsistent_pool_units(tmp_path,change):
    raw=recorded();pool=raw['result']['pools']['cytosol']
    if change=='missing_volume': del pool['volume_L']
    elif change=='mismatched_volume': pool['volume_source']['value']=1
    else: pool['concentrations_um']['15'][-1]=6
    _,display,file_id=environment(tmp_path,raw)
    with pytest.raises(WorkflowError,match='recorded_compartment_units_or_volume_missing'):
        display.series('p',file_id,0,10)


def test_conditional_real_scope_is_not_mislabelled_synthetic(tmp_path):
    raw=recorded()
    raw.update(source_type='literature_conditional',formal_prediction_allowed=False)
    _,display,file_id=environment(tmp_path,raw)
    page=display.series('p',file_id,0,10)
    assert page['source_type']=='literature_conditional'
    assert page['formal_prediction_allowed'] is False
    assert 'Synthetic demo' not in ''.join(series_csv(display,'p',file_id))

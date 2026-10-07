"""Read-only aligned artifact HTTP routing; no numerical comparison or solver."""
import json
from hashlib import sha256
import pytest
from test_r6_input_boundaries import api
from igem_drylab.wetlab.comparison import M5ComparisonSeries


def artifact():
    return M5ComparisonSeries(experiment_id='SOFTWARE',construct_id='c',condition_id='condition',replicate_id='r',
        raw_data_sha256=None,compartment=None,concentration_basis=None,source_time_unit='h',source_concentration_unit='uM',
        comparison_adapter='prediction_contract',time=[0,1],observed=[0,2],predicted=[0,3],
        residual_observed_minus_predicted=[None,-1],censor_mask=['below_lod','quantified'],lod=1,loq=None,
        observation_kind='concentration',uncertainty=None,uncertainty_type=None).model_dump(mode='json')


def bind(client,raw):
    text=json.dumps(raw)
    preview=client.post('/api/platform/imports/preview',json={'filename':'aligned.json','content':text}).json()
    response=client.post('/api/platform/projects',json={'project':{'id':'p','name':'SOFTWARE_ONLY','files':[preview['file']]}})
    assert response.status_code==200,response.text
    return preview['file']['id'],text


def test_original_alignment_routes_without_recomputation_or_approval(tmp_path):
    _,client=api(tmp_path);raw=artifact();file_id,text=bind(client,raw)
    catalog=client.get('/api/platform/projects/p/resources').json()
    assert catalog['items'][0]['kind']=='m5'
    assert catalog['items'][0]['identity']['source_sha256']==sha256(text.encode()).hexdigest()
    response=client.get(f'/api/platform/files/{file_id}/m5-comparison?project_id=p')
    assert response.status_code==200,response.text
    assert response.json()==raw
    assert response.json()['residual_observed_minus_predicted']==[None,-1]
    assert client.get(f'/api/platform/files/{file_id}?project_id=p').content==text.encode()
    assert client.get(f'/api/platform/files/{file_id}/m5-comparison?project_id=other').status_code in {403,404}
    assert client.get('/api/platform/runs').json()==[]
    assert client.get('/api/platform/projects/p').json()['scientific_project'] is None


@pytest.mark.parametrize('mutation',['length','legacy','missing_unit','approval'])
def test_invalid_alignment_is_not_repaired_or_approved_by_display(tmp_path,mutation):
    _,client=api(tmp_path);raw=artifact()
    if mutation=='length':raw['predicted']=[0]
    elif mutation=='legacy':raw={'predicted_final':1}
    elif mutation=='missing_unit':raw.pop('time_unit')
    else:raw['parameter_approval']='approved'
    file_id,text=bind(client,raw)
    assert client.get(f'/api/platform/files/{file_id}/m5-comparison?project_id=p').status_code==422
    assert client.get(f'/api/platform/files/{file_id}?project_id=p').content==text.encode()

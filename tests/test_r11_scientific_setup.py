"""Scientific configuration form and file grants only; never execute a stage."""
from copy import deepcopy
import json
import pytest
from test_r6_input_boundaries import api


def setup(client, project_id='p'):
    preview=client.post('/api/platform/imports/preview',json={'filename':'source.fasta','content':'>ACTUAL_SOFTWARE_SOURCE\nMAGSGS\n'}).json()
    project=client.post('/api/platform/projects',json={'project':{'id':project_id,'name':'SOFTWARE_SETUP','files':[preview['file']]}}).json()
    return project,dict(project_id=project_id,expected_revision=project['revision'],config={
        'execution':{'mode':'real','allow_assumptions':False},'experimental_context':{},
        'inputs':{'protein_fasta':project['files'][0]['path'],'enzymes':[],'scaffolds':[],'linkers':[],
            'constructs':[{'id':'SOFTWARE_CONSTRUCT','components':['ACTUAL_SOFTWARE_SOURCE']}]},
        'stages':{'m3_concentration':{'phi_source':'measured','binding_model':'independent','recruitment_mode':'finite_site','ptr_pt_phase_handling':'dilute_only','recruitment_bias_oc_vs_dmt':1},
            'm4_reaction':{'network_mode':'markdown_steady_state','scenario_mode':'homogeneous_constitutive','unit_mode':'physical','target_product':'USER_DECLARED_TARGET','t_end':1,
                'max_side_product_fraction_13':0.1,'min_13_reduction':0.2,'min_15_improvement':0,'min_productivity':0,'activity_mode':'sensitivity_parameters'}}})


def test_blank_scientific_project_from_explicit_fields_without_yaml_and_original_bindings(tmp_path):
    app,client=api(tmp_path)
    schema=client.get('/api/platform/scientific-projects/form-schema')
    assert schema.status_code==200,schema.text
    assert 'default' not in json.dumps(schema.json()) and 'ToolConfig' not in schema.json()['$defs']
    assert schema.json()['$defs']['ConstructDefinition']['properties']['m1_review']['readOnly']
    p,request=setup(client)
    preview=client.post('/api/platform/scientific-projects/create-preview',json=request)
    assert preview.status_code==200,preview.text
    science=preview.json()['scientific_project']
    assert client.get('/api/platform/projects/p').json()['scientific_project'] is None
    config=science['config']; assert config['execution']['mode']=='real' and not config['execution']['allow_assumptions']
    assert config['parameters']==[] and all(v is None for v in config['experimental_context'].values())
    assert config['stages']['m4_reaction']['initial_state'] is None and config['stages']['m4_reaction']['full_network_initial_state'] is None
    assert config['inputs']['constructs'][0]['m1_review'] is None
    assert config['stages']['m4_reaction']['target_product']=='USER_DECLARED_TARGET'
    assert science['sequence_index']['count']==1
    saved=client.post('/api/platform/projects',json={'project':{**p,'scientific_project':science},'expected_revision':p['revision']})
    assert saved.status_code==200,saved.text
    check=client.get('/api/platform/projects/p/precheck').json()
    assert check['missing'] and not check['scientific_approval_granted']
    assert client.get('/api/platform/runs').json()==[]


@pytest.mark.parametrize('section,value',[('execution',[]),('stages',None),('inputs','not an object'),('parameters',[None])])
def test_malformed_nested_form_values_are_validation_errors_without_mutation(tmp_path,section,value):
    _,client=api(tmp_path);p,request=setup(client)
    request['config'][section]=value
    response=client.post('/api/platform/scientific-projects/create-preview',json=request)
    assert response.status_code==422,response.text
    assert client.get('/api/platform/projects/p').json()['revision']==p['revision']
    assert client.get('/api/platform/runs').json()==[]


@pytest.mark.parametrize('variant',['stale','wrong_owner','private_path','default_control','approval','runtime'])
def test_scientific_creation_is_not_an_authorization_or_default_shortcut(tmp_path,variant):
    _,client=api(tmp_path);p,request=setup(client)
    if variant=='stale':request['expected_revision']=999
    elif variant=='wrong_owner':
        other=client.post('/api/platform/projects',json={'project':{'id':'other','name':'OTHER'}}).json()
        request.update(project_id='other',expected_revision=other['revision'])
    elif variant=='private_path':request['config']['inputs']['protein_fasta']=str(tmp_path/'private.fasta')
    elif variant=='default_control':request['config']['stages']['m4_reaction'].pop('t_end')
    elif variant=='approval':request['config']['inputs']['constructs'][0]['m1_review']={'approved':True}
    elif variant=='runtime':request['config']['tools']={}
    r=client.post('/api/platform/scientific-projects/create-preview',json=request)
    assert r.status_code in {403,409,422},r.text
    assert client.get('/api/platform/projects/p').json()['scientific_project'] is None
    assert client.get('/api/platform/runs').json()==[]

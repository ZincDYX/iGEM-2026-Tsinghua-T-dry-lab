"""Policy fixtures only; these outputs are not actual project predictions."""
import json
from hashlib import sha256
from pathlib import Path
import pytest
import yaml
from test_descriptive_comparison import candidate
from igem_drylab.m1_prioritization import (ComparisonContext,PrioritizationPolicy,
    M1PrioritizationInput,prioritize_m1)

ROOT=Path(__file__).resolve().parents[1]

def policy():
    data=yaml.safe_load((ROOT/'configs/m1_initial_equal_weight_20261015.yaml').read_text(encoding='utf-8'))
    return PrioritizationPolicy.model_validate({**data,'reference_id':'synthetic-reference-v1'})

def native_fixture(tmp_path,id,sequence,values,verdict='pass',conditions='same'):
    row=candidate(ROOT,tmp_path,id,sequence,values)
    row.screen.verdict=verdict;row.screen.missing_required_evidence=[]
    row.comparison_context=ComparisonContext(cohort_id='declared-before-scores',conditions_id=conditions,prediction_scope='synthetic-IDR-extrapolation')
    for observation in row.predictors:
        # Native-format synthetic files exercise the production parsers rather
        # than monkeypatching the scientific trust boundary.
        path=observation.source_file
        record=json.loads(observation.provenance.record_file.read_text())
        if observation.tool=='FuzDrop':
            path.write_text(json.dumps(dict(sequence=sequence,pLLPS=observation.raw_score,result=[
                dict(position=i,aa=aa,pDP=.5,Shae=.1) for i,aa in enumerate(sequence,1)])))
            record['native_format']='fuzdrop_response_json'
        elif observation.tool=='catGRANULE_2016':
            path.write_text(f'{id} {observation.raw_score}\n')
            fasta=path.with_suffix('.fa');fasta.write_text(f'>{id}\n{sequence}\n')
            record.update(native_format='catgranule2016_scores',sequence_file=str(fasta),record_id=id)
        else:
            record.update(origin='automated',returncode=0,command=['synthetic-fixture-not-real-job'])
            observation.provenance.origin='automated'
        record['output_sha256']=sha256(path.read_bytes()).hexdigest()
        observation.provenance.record_file.write_text(json.dumps(record))
        observation.provenance.output_sha256=record['output_sha256']
        observation.provenance.record_sha256=sha256(observation.provenance.record_file.read_bytes()).hexdigest()
    return row

@pytest.mark.scientific_algorithm
def test_midrank_equal_weights_ties_aliases_and_frozen_reference(tmp_path):
    rows=[native_fixture(tmp_path,'a','GSGS'*50,dict(FuzDrop=.8,catGRANULE_2016=2.,PScore=2.)),
          native_fixture(tmp_path,'b','SGSG'*50,dict(FuzDrop=.4,catGRANULE_2016=1.,PScore=3.)),
          native_fixture(tmp_path,'c','GGSS'*50,dict(FuzDrop=.4,catGRANULE_2016=1.,PScore=1.)),
          native_fixture(tmp_path,'alias','GSGS'*50,dict(FuzDrop=.8,catGRANULE_2016=2.,PScore=2.))]
    request=M1PrioritizationInput(candidates=rows,policy=policy())
    result=prioritize_m1(request);a,b,c,alias=result['candidates']
    # Independent hand calculation: (1+1+.5)/3, (.25+.25+1)/3,
    # (.25+.25+0)/3. Alias does not add a fourth observation.
    assert [r['rank_score'] for r in (a,b,c,alias)]==pytest.approx([5/6,1/2,1/6,5/6])
    assert [r['pareto_layer'] for r in (a,b,c)]==[1,1,2]
    assert result['ranked_IDR_candidate_ids']==['a','b','c']
    assert all(r['risk'] is None and r['risk_tier'] is None for r in result['candidates'])
    request.frozen_reference_manifest=result['reference_manifest']
    assert prioritize_m1(request)['reference_manifest']==result['reference_manifest']
    request.candidates=request.candidates[:2]
    with pytest.raises(ValueError,match='frozen_reference_changed'):prioritize_m1(request)

@pytest.mark.scientific_algorithm
def test_no_imputation_no_pending_pass_no_mixed_conditions(tmp_path):
    rows=[native_fixture(tmp_path,'a','GSGS'*50,dict(FuzDrop=.8,catGRANULE_2016=2.,PScore=2.)),
          native_fixture(tmp_path,'b','SGSG'*50,dict(FuzDrop=.4,catGRANULE_2016=1.,PScore=3.),conditions='other'),
          native_fixture(tmp_path,'missing','GGSS'*50,dict(catGRANULE_2016=1.,PScore=1.)),
          native_fixture(tmp_path,'pending','GSSG'*50,dict(FuzDrop=.9,catGRANULE_2016=5.,PScore=5.),verdict='blocked'),
          native_fixture(tmp_path,'fail','SSGG'*50,dict(FuzDrop=1.,catGRANULE_2016=9.,PScore=9.),verdict='reject')]
    result=prioritize_m1(M1PrioritizationInput(candidates=rows,policy=policy()))
    assert all(r['rank_score'] is None for r in result['candidates'])
    assert [r['ranking_status'] for r in result['candidates']]==[
        'insufficient_reference_cohort_for_percentiles','insufficient_reference_cohort_for_percentiles',
        'pending_required_evidence','pending_required_evidence','excluded_by_existing_hard_rule']
    assert result['ranked_IDR_candidate_ids']==[]

@pytest.mark.scientific_algorithm
def test_unknown_version_and_typed_scalar_are_not_native_evidence(tmp_path):
    row=candidate(ROOT,tmp_path,'typed','GSGS'*50,dict(FuzDrop=.8,catGRANULE_2016=2.,PScore=2.))
    row.screen.verdict='pass'
    row.comparison_context=ComparisonContext(cohort_id='test',conditions_id='test',prediction_scope='test')
    result=prioritize_m1(M1PrioritizationInput(candidates=[row],policy=policy()))
    assert result['candidates'][0]['rank_score'] is None
    assert 'verified_native_predictor_exports' in result['candidates'][0]['missing']


@pytest.mark.data_contract
def test_website_protocol_identifier_is_not_a_known_server_binary_version(tmp_path):
    row=native_fixture(tmp_path,'protocol-only','GSGS'*50,dict(FuzDrop=.8,catGRANULE_2016=2.,PScore=2.))
    provenance=row.predictors[0].provenance
    record=json.loads(provenance.record_file.read_text())
    record.update(version_scope='Observed website protocol; server binary not exposed',native_binary_version=None)
    provenance.record_file.write_text(json.dumps(record))
    provenance.record_sha256=sha256(provenance.record_file.read_bytes()).hexdigest()
    result=prioritize_m1(M1PrioritizationInput(candidates=[row],policy=policy()))['candidates'][0]
    assert result['rank_score'] is None and result['unknown_native_versions']==['FuzDrop']
    assert 'known_predictor_versions' in result['missing']

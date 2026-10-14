"""Midrank/Pareto independent oracle; synthetic reviewed outputs, not real jobs."""
from hashlib import sha256
import json
from pathlib import Path
import math
import pytest
from igem_drylab.m1_prioritization import (PrioritizationPolicy,PrioritizationCandidate,
    M1PrioritizationInput,PredictorScore,prioritize_m1)
from igem_drylab.constructs.linker_features import (M1FeatureDefinitions,compute_sequence_features,M1ScreenResult)
from igem_drylab.constructs.tool_evidence import ToolEvidenceProvenance


def candidate(root,tmp_path,id,sequence,values):
    definitions,digest=M1FeatureDefinitions.from_yaml(root/'configs/m1_feature_definitions.yaml')
    features=compute_sequence_features(sequence,definitions=definitions,definitions_sha256=digest)
    screen=M1ScreenResult(formula_version=features.formula_version,rule_version='synthetic',sequence_kind='idr',
        localization_context='cytosolic',features=features,verdict='blocked',missing_required_evidence=['synthetic absent full fusion'])
    observations=[]
    for name,value in values.items():
        path=tmp_path/(id+'-'+name+'.txt');path.write_text('PScore: '+str(value) if name=='PScore' else str(value))
        record=dict(origin='manual_review',reviewer='synthetic',source_reference='synthetic_oracle_not_tool_job',decision='approved',
            tool_name=name,tool_version='fixture',input_sha256=features.sequence_sha256,
            output_sha256=sha256(path.read_bytes()).hexdigest(),reviewed_observations={'raw_score':value})
        record_path=path.with_suffix('.review.json');record_path.write_text(json.dumps(record))
        observations.append(PredictorScore(tool=name,tool_version='fixture',input_sequence_sha256=features.sequence_sha256,
            source_file=path,raw_score=value,provenance=ToolEvidenceProvenance(origin='manual_review',record_file=record_path,
                output_sha256=record['output_sha256'],record_sha256=sha256(record_path.read_bytes()).hexdigest())))
    return PrioritizationCandidate(candidate_id=id,screen=screen,predictors=observations)


@pytest.mark.scientific_algorithm
def test_descriptive_ties_aliases_missing_scores_and_pareto_not_original_rank(tmp_path):
    root=Path(__file__).resolve().parents[1]
    import yaml
    policy=PrioritizationPolicy.model_validate(yaml.safe_load((root/'configs/m1_descriptive_policy_20261014.yaml').read_text(encoding='utf-8')))
    rows=[candidate(root,tmp_path,'a','GSGS'*50,{'catGRANULE_2016':2.,'PScore':2.}),
          candidate(root,tmp_path,'b','SGSG'*50,{'catGRANULE_2016':1.,'PScore':3.}),
          candidate(root,tmp_path,'c','GGSS'*50,{'catGRANULE_2016':1.,'PScore':1.}),
          candidate(root,tmp_path,'alias_a','GSGS'*50,{'catGRANULE_2016':2.,'PScore':2.})]
    result=prioritize_m1(M1PrioritizationInput(policy=policy,candidates=rows));a,b,c,alias=result['candidates']
    assert [r['pareto_layer'] for r in (a,b,c,alias)]==[1,1,2,1]
    assert [r['library_percentiles']['catGRANULE_2016'] for r in (a,b,c)]==[1,.25,.25]
    assert a['coverage']==pytest.approx(2/3) and a['aliases']==['alias_a']
    assert alias['alias_of']=='a' and a['comparison_group']['unique_sequences']==3
    assert all(r['rank_score'] is None and not r['risk_complete'] and not r['eligible_for_ranking'] for r in result['candidates'])
    assert result['ranked_IDR_candidate_ids']==[]
    # Current native scalar must still agree with its original reviewed bytes.
    rows[0].predictors[0].raw_score=3.
    with pytest.raises(ValueError,match='summary_or_array_mismatch'):prioritize_m1(M1PrioritizationInput(policy=policy,candidates=rows))


@pytest.mark.scientific_algorithm
def test_nominal_SCD_histidine_neutral_and_author_kappa_sentinel():
    pytest.importorskip('localcider')
    from igem_drylab.nominal_sequence_descriptors import NominalDescriptorsInput,compute_nominal_descriptors
    result=compute_nominal_descriptors(NominalDescriptorsInput(sequence='KHAAAD',sequence_family='other'))
    assert result['scd_nominal_KR_DE']==pytest.approx(-math.sqrt(5)/6,abs=1e-12)
    assert result['nominal_ncpr']==0 and result['nominal_fcr']==pytest.approx(2/6)
    assert result['fus_tyr_sticker_fraction'] is None
    result=compute_nominal_descriptors(NominalDescriptorsInput(sequence='GSGSGS',sequence_family='FUS_LC'))
    assert result['kappa_raw']==-1 and result['kappa'] is None and result['kappa_status']=='not_applicable'

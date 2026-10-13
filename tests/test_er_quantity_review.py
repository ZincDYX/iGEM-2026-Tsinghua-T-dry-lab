"""Canonical binding admission only; no ER numerical kernel or wet-lab oracle."""
from types import SimpleNamespace
import pytest
from pydantic import BaseModel
from igem_drylab.compartments import ScientificQuantity
from igem_drylab.parameters import ParameterRecord
from igem_drylab.pipeline.config import ProjectConfig
from igem_drylab.workflow.parameter_edits import validate_er_candidate


class BoundRequest(BaseModel):
    construct_id:str='SOFTWARE_ONLY_CONSTRUCT'
    condition_id:str='SOFTWARE_ONLY_CONDITION'
    formula_version:str='SOFTWARE_ONLY_MODEL'
    volume:ScientificQuantity


def test_er_human_review_uses_the_real_canonical_gate_and_never_changes_source_or_other_parameters():
    context={'host':'SOFTWARE_ONLY_HOST','temperature_c':30.,'pH':7.,'assay_system':'SOFTWARE_ONLY_ASSAY'}
    original=ParameterRecord(parameter_id='source',name='volume',value=.1,unit='L',parameter_type='other',
        construct_id='SOFTWARE_ONLY_CONSTRUCT',condition_id='SOFTWARE_ONLY_CONDITION',model_version='SOFTWARE_ONLY_MODEL',
        conditions={'entity_basis':'SOFTWARE_ONLY_POOL',**context},source_type='wetlab',derivation_type='direct_measurement',
        source_reference='SOFTWARE_ONLY_NOT_BIOLOGICAL_EVIDENCE',review_status='approved',approved_by='fixture')
    candidate=original.model_copy(update={'parameter_id':'candidate','value':.2,'supersedes':'source','parameter_version':2,'review_status':'validated','approved_by':None})
    request=BoundRequest(volume=ScientificQuantity(value=.2,unit='L',parameter_id='candidate',entity_basis='SOFTWARE_ONLY_POOL',source_reference=original.source_reference))
    config=ProjectConfig.model_validate({'run':{'id':'SOFTWARE_ONLY'},'inputs':{'protein_fasta':'SOFTWARE_ONLY.faa','enzymes':[],'scaffolds':[],'linkers':[]},'experimental_context':context})
    config=config.model_copy(update={'parameters':[original],'stages':SimpleNamespace(m3_concentration=SimpleNamespace(er_requests={'fixture':request}))})
    assert validate_er_candidate(config,candidate,'m3','volume','software reviewer') is True
    assert candidate.review_status=='validated' and original.value==.1
    assert config.parameters==[original]
    with pytest.raises(ValueError,match='canonical_value_or_unit_mismatch'):
        validate_er_candidate(config,candidate.model_copy(update={'unit':'uM'}),'m3','volume','software reviewer')
    with pytest.raises(ValueError,match='incompatible_supersedes'):
        validate_er_candidate(config,candidate.model_copy(update={'condition_id':'OTHER_SOFTWARE_CONDITION'}),'m3','volume','software reviewer')
    with pytest.raises(ValueError,match='source_reference_mismatch'):
        validate_er_candidate(config,candidate.model_copy(update={'source_reference':'OTHER_SOFTWARE_SOURCE'}),'m3','volume','software reviewer')

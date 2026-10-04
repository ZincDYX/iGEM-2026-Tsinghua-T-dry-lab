import numpy as np
import pytest
from igem_drylab.reference_validation import source_precision_verdict


def test_retained_precision_is_not_a_biological_tolerance():
    source=np.array([[0,1.23e-5],[1,0.]])
    near=source.copy();near[0,1]+=4e-8
    source_cells=[[0,'1.23e-5'],[1,0.]]
    assert source_precision_verdict(near,source,source_cells=source_cells)['source_precision_match']
    far=source.copy();far[0,1]+=1e-7
    assert not source_precision_verdict(far,source,source_cells=source_cells)['source_precision_match']
    zero=source.copy();zero[1,1]=1e-10
    assert not source_precision_verdict(zero,source,source_cells=source_cells)['source_precision_match']
    assert not source_precision_verdict(near,source)['source_precision_match']  # Numeric storage is not a decimal precision declaration.


def test_expected_contradiction_remains_visible_not_pass():
    result=source_precision_verdict([[0,2],[1,2]],[[0,1],[1,1]],expected_discrepancies=['known branch conflict'])
    assert result['verdict']=='expected_documentation_code_contradiction' and not result['source_precision_match']


def test_time_mismatch_and_nonfinite_values_cannot_pass():
    assert not source_precision_verdict([[0,1],[2,1]],[[0,1],[1,1]])['time_aligned']
    with pytest.raises(ValueError,match='finite'):
        source_precision_verdict([[0,np.nan],[1,1]],[[0,1],[1,1]])

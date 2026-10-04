"""Regression checks for source-data handling, not synthetic biological evidence."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip('matplotlib')
pytest.importorskip('openpyxl')
source = Path(__file__).resolve().parents[1] / 'scripts/reproduce_glabridin_paper.py'
spec = importlib.util.spec_from_file_location('publication_reproduction', source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_source_table_keeps_numeric_strings_and_measured_zero():
    result = module.source_table([(None,'0','0'),(None,0.01,'7.4e-5'),(None,None,None)],1,3)
    np.testing.assert_array_equal(result,[[0,0],[0.01,7.4e-5]])


def test_source_table_does_not_impute_missing_concentration():
    with pytest.raises(TypeError):
        module.source_table([(None,0.01,None)],1,3)


def test_source_table_rejects_missing_time_with_existing_measurement():
    with pytest.raises(ValueError,match='without a time'):
        module.source_table([(None,None,7.4e-5)],1,3)

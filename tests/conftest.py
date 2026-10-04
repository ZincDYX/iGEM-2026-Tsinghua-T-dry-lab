"""Explicit risk/scope metadata; no quality score inferred from assertions."""
from pathlib import Path
import pytest
import yaml


def pytest_addoption(parser):
    parser.addoption('--require-author-reference',action='store_true',default=False,
        help='Required immutable author regression: missing input is blocked/failure, never skip.')


def pytest_collection_modifyitems(config,items):
    manifest=yaml.safe_load((Path(__file__).parents[1]/'test_risk_manifest.yaml').read_text(encoding='utf-8'))
    for item in items:
        base=item.nodeid.split('[',1)[0]
        matched=[risk for risk in manifest['risks'] if base in risk['test_nodeids']]
        for risk in matched:
            item.add_marker(getattr(pytest.mark,risk['group']))
            item.user_properties.extend([('risk_id',risk['risk_id']),('fixture_scope',risk['fixture_scope']),
                ('test_group',risk['group']),
                ('oracle_type',risk['oracle_type']),('units',str(risk['units'])),('tolerance_basis',risk['tolerance_basis'])])
        if not matched:
            item.add_marker(pytest.mark.regression)
            item.user_properties.append(('fixture_scope','legacy_software_regression_not_biological_validation'))
            item.user_properties.append(('test_group','regression'))

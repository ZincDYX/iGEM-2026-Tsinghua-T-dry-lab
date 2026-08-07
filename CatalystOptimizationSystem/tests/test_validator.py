import pandas as pd
from CatalystOptimizationSystem.core.validator import clean_catalyst_data


def test_clean_validator():
    df = pd.DataFrame([
        {'doi': 'x', 'final_catalyst_name': 'A', 'final_reaction_temp': 200, 'final_co2_conversion': 0.1},
        {'doi': 'x', 'final_catalyst_name': 'A', 'final_reaction_temp': None, 'final_co2_conversion': None},
        {'doi': 'y', 'final_catalyst_name': 'B', 'final_reaction_temp': 250, 'final_co2_conversion': 0.2},
    ])
    tmp = 'tmp_mock.csv'
    df.to_csv(tmp, index=False)
    out = clean_catalyst_data(tmp)
    assert len(out) == 2

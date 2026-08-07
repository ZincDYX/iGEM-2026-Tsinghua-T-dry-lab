import pandas as pd
from CatalystOptimizationSystem.core.imputer import impute_median, impute_knn_scaled, impute_iter_bayes


def test_basic_imputers():
    df = pd.DataFrame({
        'a': [1.0, 2.0, None, 4.0],
        'b': [None, 1.5, 2.5, None],
    })
    out1 = impute_median(df)
    assert out1.isna().sum().sum() == 0
    out2 = impute_knn_scaled(df, n_neighbors=2)
    assert out2.isna().sum().sum() == 0
    out3 = impute_iter_bayes(df, seed=0, max_iter=3)
    assert out3.isna().sum().sum() == 0

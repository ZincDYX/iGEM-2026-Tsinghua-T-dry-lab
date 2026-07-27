import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.linear_model import BayesianRidge


def load_numeric_block(path: str, convert_object_threshold: float = 0.7) -> pd.DataFrame:
    df = pd.read_csv(path)
    numeric = {}
    for c in df.select_dtypes(include=[np.number]).columns:
        numeric[c] = df[c]
    for c in df.select_dtypes(include=['object']).columns:
        s2 = df[c].astype(str).str.strip()
        s2 = s2.str.replace(r'^\((.*)\)$', r'-\1', regex=True)
        for tok in [',', '%', '$', '?', '?']:
            s2 = s2.str.replace(tok, '', regex=False)
        s2 = s2.str.replace(' ', '', regex=False)
        s_num = pd.to_numeric(s2, errors='coerce')
        if s_num.notna().mean() >= convert_object_threshold:
            numeric[c] = s_num
    if not numeric:
        raise RuntimeError('no numeric-like columns found')
    return pd.DataFrame(numeric)


def robust_scale_df(X: pd.DataFrame):
    med = X.median(skipna=True)
    q1 = X.quantile(0.25, interpolation='linear')
    q3 = X.quantile(0.75, interpolation='linear')
    iqr = (q3 - q1).replace(0, np.nan)
    std = X.std(skipna=True, ddof=0).replace(0, np.nan)
    scale = iqr.fillna(std).fillna(1.0)
    Xs = (X - med) / scale
    return Xs, med, scale


def robust_unscale_df(Xs: pd.DataFrame, med: pd.Series, scale: pd.Series):
    return Xs * scale + med


def impute_median(X: pd.DataFrame) -> pd.DataFrame:
    imp = SimpleImputer(strategy='median')
    return pd.DataFrame(imp.fit_transform(X), columns=X.columns, index=X.index)


def impute_knn_scaled(X: pd.DataFrame, n_neighbors: int = 5) -> pd.DataFrame:
    Xs, med, scale = robust_scale_df(X)
    imputer = KNNImputer(n_neighbors=n_neighbors, weights='distance', metric='nan_euclidean')
    Xs_imp = pd.DataFrame(imputer.fit_transform(Xs), columns=X.columns, index=X.index)
    X_imp = robust_unscale_df(Xs_imp, med, scale)
    for c in X_imp.columns:
        if X_imp[c].isna().any():
            X_imp[c] = X_imp[c].fillna(X[c].median(skipna=True))
    return X_imp


def impute_iter_bayes(X: pd.DataFrame, seed: int = 0, max_iter: int = 20) -> pd.DataFrame:
    imp = IterativeImputer(
        estimator=BayesianRidge(),
        max_iter=max_iter,
        initial_strategy='median',
        sample_posterior=False,
        random_state=int(seed),
        skip_complete=True,
    )
    return pd.DataFrame(imp.fit_transform(X), columns=X.columns, index=X.index)


def train_iterative_imputer(df_num: pd.DataFrame, seed: int, max_iter: int = 20) -> pd.DataFrame:
    imp = IterativeImputer(
        estimator=BayesianRidge(),
        max_iter=max_iter,
        initial_strategy='median',
        sample_posterior=True,
        random_state=int(seed),
        skip_complete=True,
    )
    return pd.DataFrame(imp.fit_transform(df_num), columns=df_num.columns, index=df_num.index)

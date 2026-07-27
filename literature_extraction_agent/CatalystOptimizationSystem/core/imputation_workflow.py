import json
import math
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.linear_model import BayesianRidge

from CatalystOptimizationSystem.utils.logger import get_logger
from CatalystOptimizationSystem.core.imputer import load_numeric_block, robust_scale_df, robust_unscale_df
from CatalystOptimizationSystem.core.extractor import call_llm_openai

logger = get_logger(__name__)


@dataclass
class EvalConfig:
    mask_frac: float = 0.10
    repeats: int = 3
    seed: int = 42


# ===== mask & metrics =====

def _mask_random_entries(df: pd.DataFrame, frac: float, rng: np.random.Generator) -> Tuple[pd.DataFrame, Dict[str, np.ndarray]]:
    X = df.copy()
    pos: Dict[str, np.ndarray] = {}
    for c in df.columns:
        idx_obs = X[c].dropna().index.to_numpy()
        n_obs = len(idx_obs)
        if n_obs == 0:
            pos[c] = np.array([], dtype=int)
            continue
        k = max(1, int(round(n_obs * frac)))
        k = min(k, n_obs)
        chosen = rng.choice(idx_obs, size=k, replace=False)
        pos[c] = chosen
        X.loc[chosen, c] = np.nan
    return X, pos


def _metrics_for_mask(original: pd.DataFrame, imputed: pd.DataFrame, masked_pos: Dict[str, np.ndarray]) -> Dict[str, Any]:
    diffs_all: List[float] = []
    per_col_mae: Dict[str, float] = {}
    per_col_rmse: Dict[str, float] = {}
    per_col_nrmse: Dict[str, float] = {}

    q1 = original.quantile(0.25, interpolation='linear')
    q3 = original.quantile(0.75, interpolation='linear')
    IQR = (q3 - q1).astype(float)
    STD = original.std(skipna=True, ddof=0).astype(float)
    SCALE = IQR.replace(0, np.nan).fillna(STD.replace(0, np.nan)).fillna(1.0)

    for c in original.columns:
        idx = masked_pos.get(c, np.array([], dtype=int))
        if len(idx) == 0:
            per_col_mae[c] = math.nan
            per_col_rmse[c] = math.nan
            per_col_nrmse[c] = math.nan
            continue
        true = original.loc[idx, c].astype(float).to_numpy()
        pred = imputed.loc[idx, c].astype(float).to_numpy()
        diff = pred - true
        mae = float(np.mean(np.abs(diff)))
        rmse = float(np.sqrt(np.mean(diff**2)))
        nrmse = float(rmse / (SCALE.get(c, 1.0) or 1.0))
        per_col_mae[c] = mae
        per_col_rmse[c] = rmse
        per_col_nrmse[c] = nrmse
        diffs_all.extend(diff.tolist())

    overall_rmse = float(np.sqrt(np.mean(np.array(diffs_all, dtype=float)**2))) if diffs_all else math.nan
    overall_nrmse = float(np.nanmean(list(per_col_nrmse.values()))) if per_col_nrmse else math.nan
    score = -overall_nrmse if not math.isnan(overall_nrmse) else float('-inf')
    return {
        'per_col_mae': per_col_mae,
        'per_col_rmse': per_col_rmse,
        'per_col_nrmse': per_col_nrmse,
        'overall_rmse': overall_rmse,
        'overall_nrmse': overall_nrmse,
        'score': score,
    }


def evaluate_method(df_num: pd.DataFrame, method: str, params: Dict[str, Any], cfg: EvalConfig) -> Dict[str, Any]:
    rng = np.random.default_rng(cfg.seed)
    results: List[Dict[str, Any]] = []

    for _ in range(cfg.repeats):
        X_masked, pos = _mask_random_entries(df_num, cfg.mask_frac, rng)
        if method.lower() == 'median':
            imp = SimpleImputer(strategy='median')
            X_imp = pd.DataFrame(imp.fit_transform(X_masked), columns=df_num.columns, index=df_num.index)
        elif method.lower() == 'knn':
            n_neighbors = int(params.get('n_neighbors', 5))
            weights = params.get('weights', 'distance')
            metric = params.get('metric', 'nan_euclidean')
            Xs, med, scale = robust_scale_df(X_masked)
            imputer = KNNImputer(n_neighbors=n_neighbors, weights=weights, metric=metric)
            Xs_imp = pd.DataFrame(imputer.fit_transform(Xs), columns=df_num.columns, index=df_num.index)
            X_imp = robust_unscale_df(Xs_imp, med, scale)
            for c in X_imp.columns:
                if X_imp[c].isna().any():
                    X_imp[c] = X_imp[c].fillna(df_num[c].median(skipna=True))
        elif method.lower() in ('mice', 'iterative'):
            max_iter = int(params.get('max_iter', 20))
            sample_posterior = bool(params.get('sample_posterior', False))
            random_state = int(params.get('random_state', 0))
            estimator = BayesianRidge()
            imp = IterativeImputer(
                estimator=estimator,
                max_iter=max_iter,
                initial_strategy='median',
                sample_posterior=sample_posterior,
                random_state=random_state,
                skip_complete=True,
            )
            X_imp = pd.DataFrame(imp.fit_transform(X_masked), columns=df_num.columns, index=df_num.index)
        else:
            raise ValueError(f'unknown method: {method}')

        metrics = _metrics_for_mask(df_num, X_imp, pos)
        results.append(metrics)

    overall_nrmse = float(np.nanmean([x['overall_nrmse'] for x in results]))
    score = -overall_nrmse if not math.isnan(overall_nrmse) else float('-inf')
    return {
        'method': method,
        'params': params,
        'overall_nrmse': overall_nrmse,
        'score': score,
        'details': results,
    }


# ===== LLM suggestions =====

def build_llm_prompt_for_imputation(df_num: pd.DataFrame) -> str:
    miss = df_num.isna().mean().to_dict()
    stats = {
        'n_rows': int(df_num.shape[0]),
        'n_cols': int(df_num.shape[1]),
        'missing_ratio_per_col': miss,
    }
    instr = (
        "Propose parameter candidates for three imputation methods on a numeric dataset: "
        "(1) median; (2) knn; (3) mice (IterativeImputer with BayesianRidge). "
        "Return strict JSON with keys 'median', 'knn', 'mice'. "
        "For 'median', return an empty object. "
        "For 'knn', return list of 3 candidate objects with fields: n_neighbors (int, 3-15), weights ('uniform'|'distance'), metric ('nan_euclidean'). "
        "For 'mice', return list of 3 candidate objects with fields: max_iter (int, 5-50), sample_posterior (bool), random_state (int). "
    )
    return instr + "\nDataset stats JSON:\n" + json.dumps(stats, ensure_ascii=False) + "\nReturn JSON only."


def ask_llm_candidates(df_num: pd.DataFrame, api_key: str, api_base: str, model: str) -> Dict[str, Any]:
    prompt = build_llm_prompt_for_imputation(df_num)
    raw = call_llm_openai(api_key, api_base, model, prompt)
    try:
        js = json.loads(raw)
    except Exception:
        i = raw.find('{'); j = raw.rfind('}')
        js = json.loads(raw[i:j+1]) if (i != -1 and j != -1 and j > i) else {}
    out = {
        'median': js.get('median', {}) or {},
        'knn': js.get('knn', []) or [],
        'mice': js.get('mice', []) or [],
    }
    def _safe_int(x, lo=None, hi=None, default=None):
        try:
            v = int(x)
            if lo is not None and v < lo: v = lo
            if hi is not None and v > hi: v = hi
            return v
        except Exception:
            return default
    def _safe_bool(x, default=False):
        if isinstance(x, bool): return x
        if isinstance(x, str): return x.lower() in ('true','1','yes')
        return default
    knn_norm = []
    for cand in out['knn'][:5]:
        knn_norm.append({
            'n_neighbors': _safe_int(cand.get('n_neighbors'), 1, 50, 5),
            'weights': str(cand.get('weights', 'distance')) if str(cand.get('weights', 'distance')) in ('uniform','distance') else 'distance',
            'metric': 'nan_euclidean',
        })
    mice_norm = []
    for cand in out['mice'][:5]:
        mice_norm.append({
            'max_iter': _safe_int(cand.get('max_iter'), 5, 200, 20),
            'sample_posterior': _safe_bool(cand.get('sample_posterior'), False),
            'random_state': _safe_int(cand.get('random_state'), 0, 10**9, 0),
        })
    return {'median': {}, 'knn': knn_norm or [{'n_neighbors':5,'weights':'distance','metric':'nan_euclidean'}], 'mice': mice_norm or [{'max_iter':20,'sample_posterior':False,'random_state':0}]}


# ===== Apply imputation =====

def _apply_imputation(df_num: pd.DataFrame, method: str, final_params: Dict[str, Any]) -> pd.DataFrame:
    if method == 'median':
        imp = SimpleImputer(strategy='median')
        return pd.DataFrame(imp.fit_transform(df_num), columns=df_num.columns, index=df_num.index)
    if method == 'knn':
        n_neighbors = int(final_params.get('n_neighbors', 5))
        weights = final_params.get('weights', 'distance')
        metric = final_params.get('metric', 'nan_euclidean')
        Xs, med, scale = robust_scale_df(df_num)
        imputer = KNNImputer(n_neighbors=n_neighbors, weights=weights, metric=metric)
        Xs_imp = pd.DataFrame(imputer.fit_transform(Xs), columns=df_num.columns, index=df_num.index)
        X_imp = robust_unscale_df(Xs_imp, med, scale)
        for c in X_imp.columns:
            if X_imp[c].isna().any():
                X_imp[c] = X_imp[c].fillna(df_num[c].median(skipna=True))
        return X_imp
    if method == 'mice':
        max_iter = int(final_params.get('max_iter', 20))
        sample_posterior = bool(final_params.get('sample_posterior', False))
        random_state = int(final_params.get('random_state', 0))
        estimator = BayesianRidge()
        imp = IterativeImputer(
            estimator=estimator,
            max_iter=max_iter,
            initial_strategy='median',
            sample_posterior=sample_posterior,
            random_state=random_state,
            skip_complete=True,
        )
        return pd.DataFrame(imp.fit_transform(df_num), columns=df_num.columns, index=df_num.index)
    raise ValueError(f'unknown method: {method}')


# ===== Interactive helpers =====

def _print_suggestions_with_scores(report_sorted: List[Dict[str, Any]]):
    print('\n=== LLM candidates and scores (score = -NRMSE; higher is better) ===')
    by_method: Dict[str, List[Dict[str, Any]]] = {'median': [], 'knn': [], 'mice': []}
    for item in report_sorted:
        by_method.setdefault(item['method'], []).append(item)
    for m in ['median','knn','mice']:
        items = by_method.get(m, [])
        if not items:
            continue
        print(f"\n[{m}] candidates:")
        for it in items[:10]:
            print(f"  params={json.dumps(it['params'], ensure_ascii=False)}  score={it['score']:.6f}  nrmse={it['overall_nrmse']:.6f}")


def _input_with_default(prompt: str, default: Optional[str]) -> str:
    s = input(f"{prompt} [{default if default is not None else ''}]: ").strip()
    return s if s else ('' if default is None else str(default))


def interactive_loop(df_num: pd.DataFrame, report_sorted: List[Dict[str, Any]], suggestions: Dict[str, Any]):
    selected_method: Optional[str] = None
    selected_params: Dict[str, Any] = {}

    def best_params(method: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        for it in report_sorted:
            if it['method'] == method:
                return it['params']
        return fallback

    while True:
        _print_suggestions_with_scores(report_sorted)
        print("\nType median/knn/mice to set params; type run to proceed; type q to quit without applying.")
        cmd = input('> ').strip().lower()
        if cmd in ('q','quit','exit'):
            print('Quit without applying.')
            return None, None
        if cmd == 'run':
            if not selected_method:
                print('Please select method and params first.')
                continue
            print(f"Will apply: method={selected_method}, params={json.dumps(selected_params, ensure_ascii=False)}")
            return selected_method, selected_params
        if cmd not in ('median','knn','mice'):
            print('Invalid input. Try again.')
            continue
        if cmd == 'median':
            print('median has no parameters.')
            confirm = input('Confirm median as final? (y/n): ').strip().lower()
            if confirm.startswith('y'):
                selected_method = 'median'; selected_params = {}
            continue
        if cmd == 'knn':
            bp = best_params('knn', {'n_neighbors':5,'weights':'distance','metric':'nan_euclidean'})
            n_neighbors = int(_input_with_default('n_neighbors(3-50)', bp.get('n_neighbors', 5)))
            weights = _input_with_default("weights('uniform'|'distance')", bp.get('weights','distance'))
            metric = 'nan_euclidean'
            params = {'n_neighbors': n_neighbors, 'weights': 'distance' if weights not in ('uniform','distance') else weights, 'metric': metric}
            print(f"params: {json.dumps(params, ensure_ascii=False)}")
            confirm = input('Confirm as current final? (y/n): ').strip().lower()
            if confirm.startswith('y'):
                selected_method = 'knn'; selected_params = params
            continue
        if cmd == 'mice':
            bp = best_params('mice', {'max_iter':20,'sample_posterior':False,'random_state':0})
            max_iter = int(_input_with_default('max_iter(5-200)', bp.get('max_iter', 20)))
            sp_in = _input_with_default('sample_posterior(true/false)', str(bp.get('sample_posterior', False)).lower())
            sample_posterior = True if sp_in.lower() in ('true','1','yes','y') else False
            random_state = int(_input_with_default('random_state(int)', bp.get('random_state', 0)))
            params = {'max_iter': max_iter, 'sample_posterior': sample_posterior, 'random_state': random_state}
            print(f"params: {json.dumps(params, ensure_ascii=False)}")
            confirm = input('Confirm as current final? (y/n): ').strip().lower()
            if confirm.startswith('y'):
                selected_method = 'mice'; selected_params = params
            continue


# ===== Main =====

def _show_row_missingness(df_num: pd.DataFrame):
    try:
        miss_cnt = df_num.isna().sum(axis=1)
        rate = (miss_cnt / max(1, df_num.shape[1]))
        print(f"rows={len(df_num)}, cols={df_num.shape[1]}")
        print(f"row-missing-rate: mean={rate.mean():.4f}, median={rate.median():.4f}, p90={rate.quantile(0.9):.4f}")
        top = pd.DataFrame({'missing_count': miss_cnt, 'missing_rate': rate}).sort_values('missing_rate', ascending=False).head(10)
        print("Top-10 rows with highest missing rate:")
        print(top.to_string())
    except Exception as ex:
        print(f"failed to compute row-missingness: {ex}")


def main():
    import argparse
    p = argparse.ArgumentParser(description='Score three imputation methods; parameters suggested by LLM; final choice by user.')
    p.add_argument('--csv', required=True, help='cleaned CSV path')
    p.add_argument('--use-columns', nargs='*', default=None, help='subset of columns to evaluate (optional)')
    p.add_argument('--mask-frac', type=float, default=0.10)
    p.add_argument('--repeats', type=int, default=3)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--llm-key', default=None, help='OpenAI-compatible API key (optional)')
    p.add_argument('--llm-base', default='https://api.deepseek.com/v1/chat/completions', help='LLM API base')
    p.add_argument('--llm-model', default='deepseek-chat', help='LLM model name')
    p.add_argument('--apply', action='store_true', help='apply final method/params directly (skip interactive)')
    p.add_argument('--final-method', choices=['median','knn','mice'], help='final method')
    p.add_argument('--final-params', default='{}', help='final params as JSON')
    p.add_argument('--out', default=None, help='output CSV path when applying')

    args = p.parse_args()

    df = pd.read_csv(args.csv, encoding='utf-8')
    if args.use_columns:
        df_num = df[args.use_columns].copy()
    else:
        try:
            df_num = load_numeric_block(args.csv)
        except Exception:
            df_num = df.select_dtypes(include=[np.number]).copy()
    if df_num.empty:
        raise RuntimeError('no numeric columns for evaluation')

    # show row missingness and allow user to re-select columns
    _show_row_missingness(df_num)
    try:
        user_cols = input('Enter columns to keep (comma-separated), or leave empty to keep current: ').strip()
        if user_cols:
            cols = [c.strip() for c in user_cols.replace(',', ' ').split() if c.strip()]
            invalid = [c for c in cols if c not in df.columns]
            if invalid:
                print(f"columns not found and ignored: {invalid}")
            cols = [c for c in cols if c in df.columns]
            if cols:
                df_num = df[cols].copy()
                print(f"columns updated; {len(cols)} kept")
    except Exception as ex:
        print(f"failed to parse columns; keep current: {ex}")

    cfg = EvalConfig(mask_frac=args.mask_frac, repeats=args.repeats, seed=args.seed)

    suggestions: Dict[str, Any] = {'median': {}, 'knn': [{'n_neighbors':5,'weights':'distance','metric':'nan_euclidean'}], 'mice':[{'max_iter':20,'sample_posterior':False,'random_state':0}]}
    if args.llm_key:
        try:
            suggestions = ask_llm_candidates(df_num, args.llm_key, args.llm_base, args.llm_model)
        except Exception as ex:
            logger.warning('LLM suggestion failed, using defaults: %s', ex)

    report: List[Dict[str, Any]] = []
    report.append(evaluate_method(df_num, 'median', {}, cfg))
    for cand in suggestions.get('knn', [])[:5]:
        report.append(evaluate_method(df_num, 'knn', cand, cfg))
    for cand in suggestions.get('mice', [])[:5]:
        report.append(evaluate_method(df_num, 'mice', cand, cfg))
    report_sorted = sorted(report, key=lambda x: (x['score'],), reverse=True)

    # CSV summary
    ts = time.strftime('%Y%m%d-%H%M%S')
    try:
        df_summary = pd.DataFrame([
            {
                'method': it.get('method'),
                'params': json.dumps(it.get('params', {}), ensure_ascii=False),
                'overall_nrmse': it.get('overall_nrmse'),
                'score': it.get('score'),
            } for it in report_sorted
        ])
        summary_path = f"imputation_eval_summary_{ts}.csv"
        df_summary.to_csv(summary_path, index=False, encoding='utf-8', lineterminator='\n')
        print(f"Saved summary CSV: {summary_path}")
    except Exception as ex:
        print(f"failed to save summary CSV: {ex}")

    if args.apply:
        try:
            final_params = json.loads(args.final_params)
            if not isinstance(final_params, dict):
                raise ValueError('final_params must be a JSON object')
        except Exception as ex:
            raise SystemExit(f'parse --final-params failed: {ex}')
        X_imp = _apply_imputation(df_num, args.final_method, final_params)
        out_path = args.out or f'imputed_{args.final_method}_{ts}.csv'
        X_imp.to_csv(out_path, index=False, encoding='utf-8', lineterminator='\n')
        print('\n=== Score Summary ===')
        for item in report_sorted:
            print(f"method={item['method']}, params={item['params']}, overall_nrmse={item['overall_nrmse']:.6f}, score={item['score']:.6f}")
        print(f'Output written: {out_path}')
        return

    method, params = interactive_loop(df_num, report_sorted, suggestions)
    if method and params is not None:
        X_imp = _apply_imputation(df_num, method, params)
        out_path = args.out or f'imputed_{method}_{ts}.csv'
        X_imp.to_csv(out_path, index=False, encoding='utf-8', lineterminator='\n')
        print('\n=== Score Summary (LLM candidates) ===')
        for item in report_sorted:
            print(f"method={item['method']}, params={json.dumps(item['params'], ensure_ascii=False)}, overall_nrmse={item['overall_nrmse']:.6f}, score={item['score']:.6f}")
        print(f'Output written: {out_path}')


if __name__ == '__main__':
    main()

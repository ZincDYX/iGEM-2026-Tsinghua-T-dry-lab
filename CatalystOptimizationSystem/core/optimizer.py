import ast
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Tuple, List, Optional, Callable
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, ConstantKernel as C, WhiteKernel

from CatalystOptimizationSystem.core.imputer import train_iterative_imputer


@dataclass
class Columns:
    T: str = 'final_reaction_temp'
    P: str = 'final_pressure'
    conv: str = 'final_co2_conversion'
    sel: str = 'final_methanol_selectivity'
    yld: str = 'final_methanol_yield'


def robust_minmax_params(y_obs: pd.Series, p_lo: float = 5.0, p_hi: float = 95.0) -> Tuple[float, float]:
    y = pd.to_numeric(y_obs, errors='coerce').dropna()
    if y.empty:
        return 0.0, 1.0
    lo = float(np.percentile(y, p_lo))
    hi = float(np.percentile(y, p_hi))
    if hi <= lo:
        lo = float(y.min())
        hi = float(y.max()) if float(y.max()) > lo else lo + 1.0
    return lo, hi


def lhs_uniform(n_samples: int, bounds: List[Tuple[float, float]], rng: np.random.Generator) -> np.ndarray:
    dim = len(bounds)
    result = np.zeros((n_samples, dim))
    for d in range(dim):
        low, high = bounds[d]
        edges = np.linspace(0.0, 1.0, n_samples + 1)
        pts = edges[:-1] + (edges[1] - edges[0]) * rng.random(n_samples)
        rng.shuffle(pts)
        result[:, d] = low + pts * (high - low)
    return result


def expected_improvement(mu: np.ndarray, sigma: np.ndarray, f_best: float, xi: float = 0.0) -> np.ndarray:
    sigma = np.maximum(sigma, 1e-9)
    imp = mu - f_best - xi
    Z = imp / sigma
    ei = imp * norm.cdf(Z) + sigma * norm.pdf(Z)
    ei[sigma <= 1e-9] = 0.0
    return ei


def expand_bounds(x: pd.Series, margin_ratio: float = 0.05, non_negative: bool = True) -> Tuple[float, float]:
    x = pd.to_numeric(x, errors='coerce').dropna()
    if x.empty:
        return 0.0, 1.0
    lo = float(x.min()); hi = float(x.max()); rng = hi - lo
    lo2 = lo - margin_ratio * rng; hi2 = hi + margin_ratio * rng
    if non_negative:
        lo2 = max(0.0, lo2)
    if hi2 <= lo2:
        hi2 = lo2 + (rng if rng > 0 else 1.0)
    return lo2, hi2


def build_gp(alpha_vector: float | np.ndarray, gp_restarts: int = 1, random_state: int = 0) -> GaussianProcessRegressor:
    kernel = C(1.0, (1e-3, 1e3)) * Matern(length_scale=[1.0, 1.0], length_scale_bounds=(1e-2, 1e3), nu=2.5) \
             + WhiteKernel(noise_level=1e-6, noise_level_bounds=(1e-8, 1e-2))
    return GaussianProcessRegressor(kernel=kernel, alpha=alpha_vector, normalize_y=True,
                                    n_restarts_optimizer=gp_restarts, random_state=random_state)


# ---- safe objective compiler ----
_ALLOWED_NAMES = {'sel', 'conv', 'yld'}
_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Load, ast.Name,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd, ast.Mod,
    ast.Constant, ast.FloorDiv, ast.LParen if hasattr(ast, 'LParen') else ast.AST
)

def _compile_objective(expr: str) -> Callable[[float, float, Optional[float]], float]:
    tree = ast.parse(expr, mode='eval')
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id not in _ALLOWED_NAMES:
            raise ValueError(f'????: {node.id}. ??? {sorted(_ALLOWED_NAMES)}')
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError('??????????????????????????? sel/conv/yld')
    code = compile(tree, '<objective>', 'eval')
    def f(sel: Optional[float], conv: Optional[float], yld: Optional[float]) -> float:
        env = {'sel': sel, 'conv': conv, 'yld': yld}
        return float(eval(code, {'__builtins__': {}}, env))
    return f


class Optimizer:
    def __init__(self, df: pd.DataFrame, cols: Columns = Columns(), w_syn: float = 0.8, w_conv: float = 0.2,
                 w_yld: float = 0.0, objective: Optional[str] = None, seed: int = 0):
        self.df = df.copy()
        self.cols = cols
        self.w_syn = float(w_syn)
        self.w_conv = float(w_conv)
        self.w_yld = float(w_yld)
        self.rng = np.random.default_rng(seed)
        self._objective_func: Optional[Callable[[float, float, Optional[float]], float]] = None
        if objective:
            self._objective_func = _compile_objective(objective)

    def _objective(self, row: pd.Series) -> float:
        sel_v = row.get(self.cols.sel)
        conv_v = row.get(self.cols.conv)
        yld_v = row.get(self.cols.yld)
        sel = float(sel_v) if sel_v is not None and pd.notna(sel_v) else np.nan
        conv = float(conv_v) if conv_v is not None and pd.notna(conv_v) else np.nan
        yld = float(yld_v) if yld_v is not None and pd.notna(yld_v) else np.nan
        if self._objective_func is not None:
            try:
                return self._objective_func(sel, conv, yld)
            except Exception:
                return np.nan
        # default linear weights
        parts = []
        if not np.isnan(sel): parts.append(self.w_syn * sel)
        if not np.isnan(conv): parts.append(self.w_conv * conv)
        if not np.isnan(yld) and self.w_yld != 0.0: parts.append(self.w_yld * yld)
        return float(np.sum(parts)) if parts else np.nan

    def _prepare_training(self) -> tuple[np.ndarray, np.ndarray]:
        cols_needed = [self.cols.T, self.cols.P, self.cols.sel, self.cols.conv]
        if self.cols.yld in self.df.columns:
            cols_needed.append(self.cols.yld)
        use = self.df[cols_needed].copy()
        use = use.dropna(subset=[self.cols.T, self.cols.P])
        use['y'] = use.apply(self._objective, axis=1)
        use = use.dropna(subset=['y'])
        if use.empty:
            return np.zeros((0, 2)), np.zeros((0,))
        X = use[[self.cols.T, self.cols.P]].to_numpy(dtype=float)
        y = use['y'].to_numpy(dtype=float)
        return X, y

    def suggest(self, n_candidates: int = 2000, top_k: int = 5, gp_restarts: int = 1, xi: float = 0.0,
                bounds_margin: float = 0.05) -> pd.DataFrame:
        # ???????????????
        num_cols = [self.cols.T, self.cols.P, self.cols.conv, self.cols.sel]
        if self.cols.yld in self.df.columns:
            num_cols.append(self.cols.yld)
        num = self.df[num_cols].copy()
        if num[[self.cols.conv, self.cols.sel]].isna().mean().mean() > 0.1:
            try:
                imp = train_iterative_imputer(num, seed=0)
                for c in [self.cols.conv, self.cols.sel, self.cols.yld]:
                    if c in imp.columns and c in self.df.columns:
                        self.df[c] = imp[c]
            except Exception:
                pass

        X_train, y_train = self._prepare_training()
        if X_train.shape[0] < 3:
            # fallback: ????????
            T_lo, T_hi = expand_bounds(self.df[self.cols.T], margin_ratio=bounds_margin, non_negative=True)
            P_lo, P_hi = expand_bounds(self.df[self.cols.P], margin_ratio=bounds_margin, non_negative=True)
            cand = lhs_uniform(max(top_k, 10), [(T_lo, T_hi), (P_lo, P_hi)], self.rng)
            out = pd.DataFrame(cand, columns=[self.cols.T, self.cols.P])
            out['mu'] = np.nan; out['sigma'] = np.nan; out['ei'] = np.nan
            return out.head(top_k)

        T_lo, T_hi = expand_bounds(self.df[self.cols.T], margin_ratio=bounds_margin, non_negative=True)
        P_lo, P_hi = expand_bounds(self.df[self.cols.P], margin_ratio=bounds_margin, non_negative=True)
        candidates = lhs_uniform(n_candidates, [(T_lo, T_hi), (P_lo, P_hi)], self.rng)

        gp = build_gp(alpha_vector=1e-6, gp_restarts=gp_restarts, random_state=0)
        gp.fit(X_train, y_train)
        mu, std = gp.predict(candidates, return_std=True)
        f_best = float(np.max(y_train))
        ei = expected_improvement(mu, std, f_best, xi=xi)

        out = pd.DataFrame(candidates, columns=[self.cols.T, self.cols.P])
        out['mu'] = mu
        out['sigma'] = std
        out['ei'] = ei
        out = out.sort_values('ei', ascending=False).head(top_k).reset_index(drop=True)
        return out


def cli():
    """??????????????????????????"""
    import argparse, json, sys
    p = argparse.ArgumentParser()
    p.add_argument('--csv', required=True, help='?? CSV ??')
    p.add_argument('--top-k', type=int, default=5)
    p.add_argument('--n-candidates', type=int, default=2000)
    # ?????
    p.add_argument('--w-sel', type=float, default=0.8)
    p.add_argument('--w-conv', type=float, default=0.2)
    p.add_argument('--w-yld', type=float, default=0.0)
    p.add_argument('--objective', type=str, default=None, help="??????? '0.8*sel + 0.2*conv' ? 'sel + 0.5*conv + 0.1*yld'")
    # ????
    p.add_argument('--columns.T', dest='c_T', default='final_reaction_temp')
    p.add_argument('--columns.P', dest='c_P', default='final_pressure')
    p.add_argument('--columns.conv', dest='c_conv', default='final_co2_conversion')
    p.add_argument('--columns.sel', dest='c_sel', default='final_methanol_selectivity')
    p.add_argument('--columns.yld', dest='c_yld', default='final_methanol_yield')
    args = p.parse_args()

    df = pd.read_csv(args.csv, encoding='utf-8')
    cols = Columns(T=args.c_T, P=args.c_P, conv=args.c_conv, sel=args.c_sel, yld=args.c_yld)
    opt = Optimizer(df, cols=cols, w_syn=args.w_sel, w_conv=args.w_conv, w_yld=args.w_yld, objective=args.objective)
    res = opt.suggest(n_candidates=args.n_candidates, top_k=args.top_k)
    json.dump(res.to_dict(orient='records'), sys.stdout, ensure_ascii=False)
    print()


if __name__ == '__main__':
    cli()

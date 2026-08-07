import argparse
import os, json, numpy as np, pandas as pd
import io
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.linear_model import BayesianRidge
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, ConstantKernel as C, WhiteKernel
from scipy.stats import norm
import matplotlib.pyplot as plt

input_file_object='FinalCleanedDatabase.csv'

def robust_minmax_params(y_obs: pd.Series, p_lo=5.0, p_hi=95.0):
    y = pd.to_numeric(y_obs, errors="coerce").dropna()
    if y.empty:
        return (0.0, 1.0)
    lo = float(np.percentile(y, p_lo))
    hi = float(np.percentile(y, p_hi))
    if hi <= lo:
        lo = float(y.min())
        if float(y.max()) > lo:
            hi = float(y.max())
        else:
            hi = lo + 1.0
    return lo, hi

def robust_scale(y: np.ndarray, lo: float, hi: float):
    """将值缩放到[0, 1]区间"""
    z = (y - lo) / (hi - lo)
    return np.clip(z, 0.0, 1.0)

def robust_unscale(z: np.ndarray, lo: float, hi: float):
    """将缩放后的值还原"""
    return z * (hi - lo) + lo

def lhs_uniform(n_samples, bounds, rng):
    """拉丁超立方采样"""
    dim = len(bounds)
    result = np.zeros((n_samples, dim))
    for d in range(dim):
        low, high = bounds[d]
        edges = np.linspace(0.0, 1.0, n_samples + 1)
        pts = edges[:-1] + (edges[1]-edges[0]) * rng.random(n_samples)
        rng.shuffle(pts)
        result[:, d] = low + pts * (high - low)
    return result

def expected_improvement(mu, sigma, f_best, xi=0.0):
    """计算预期提升(EI)"""
    sigma = np.maximum(sigma, 1e-9)
    imp = mu - f_best - xi
    Z = imp / sigma
    ei = imp * norm.cdf(Z) + sigma * norm.pdf(Z)
    ei[sigma <= 1e-9] = 0.0
    return ei

def expand_bounds(x: pd.Series, margin_ratio: float = 0.05, non_negative: bool = True):
    """扩展参数的搜索边界"""
    x = pd.to_numeric(x, errors="coerce").dropna()
    if x.empty:
        return (0.0, 1.0)
    lo = float(x.min()); hi = float(x.max()); rng = hi - lo
    lo2 = lo - margin_ratio * rng; hi2 = hi + margin_ratio * rng
    if non_negative:
        lo2 = max(0.0, lo2)
    if hi2 <= lo2:
        hi2 = lo2 + (rng if rng > 0 else 1.0)
    return (lo2, hi2)

def build_gp(alpha_vector, gp_restarts: int = 1, random_state: int = 0):
    """构建高斯过程回归模型"""
    kernel = C(1.0, (1e-3, 1e3)) * Matern(length_scale=[1.0, 1.0],
                                          length_scale_bounds=(1e-2, 1e3), nu=2.5) \
             + WhiteKernel(noise_level=1e-6, noise_level_bounds=(1e-8, 1e-2))
    return GaussianProcessRegressor(
        kernel=kernel, alpha=alpha_vector, normalize_y=True,
        n_restarts_optimizer=gp_restarts, random_state=random_state
    )

def train_iterative_imputer(df_num: pd.DataFrame, seed: int, max_iter: int = 20):
    """训练迭代插补器来填充缺失值"""
    imp = IterativeImputer(
        estimator=BayesianRidge(),
        max_iter=max_iter,
        initial_strategy="median",
        sample_posterior=True,
        random_state=int(seed),
        skip_complete=True
    )
    X_imp = pd.DataFrame(imp.fit_transform(df_num), columns=df_num.columns, index=df_num.index)
    return X_imp

def main():
    output_dir = "bayesian_optimization_output"  # 未来可以考虑做成动态交互式页面，在这里懒得做了
    m_imputations = 7      # 多重插补的数量
    n_candidates = 3000    # 候选点数量
    top_k = 5              # 输出Top-K个推荐
    bounds_margin = 0.05   # 边界扩展比例
    gp_restarts = 1        # GPR优化器重启次数
    alpha_obs = 1e-6       # 观测数据的噪声
    alpha_imp = 0.05**2    # 插补数据的噪声
    ei_xi = 0.0            # EI中的探索参数
    w_syn = 0.8            # 协同项权重
    w_conv = 0.2           # 转化率项权重


    os.makedirs(output_dir, exist_ok=True)

    # 定义列名
    col_T = "final_reaction_temp"
    col_P = "final_pressure"
    col_conv = "final_co2_conversion"
    col_sel = "final_methanol_selectivity"
    col_yld = "final_methanol_yield"

    # =================================================================
    # 【步骤1：读取输入CSV数据】
    print("--- 步骤1：正在读取输入数据... ---")
    df = pd.read_csv(input_file_object)
    print("原始数据预览:")
    print(df.head())
    print("\n")
    # =================================================================

    for c in [col_T, col_P, col_conv, col_sel, col_yld]:
        if c not in df.columns:
            raise RuntimeError(f"列 '{c}' 在CSV中未找到。")

    print("--- 步骤2：正在执行数据预处理和贝叶斯优化... ---")
    df_num = df[[col_T, col_P, col_conv, col_sel, col_yld]].copy()
    miss_conv = df_num[col_conv].isna().to_numpy()
    miss_sel  = df_num[col_sel].isna().to_numpy()
    miss_yld  = df_num[col_yld].isna().to_numpy()
    miss_anyY = (miss_conv | miss_sel | miss_yld)

    lo_conv, hi_conv = robust_minmax_params(df_num[col_conv])
    lo_sel,  hi_sel  = robust_minmax_params(df_num[col_sel])
    lo_yld,  hi_yld  = robust_minmax_params(df_num[col_yld])

    bound_T = expand_bounds(df_num[col_T], margin_ratio=bounds_margin)
    bound_P = expand_bounds(df_num[col_P], margin_ratio=bounds_margin)
    bounds = [bound_T, bound_P]

    imputations = [train_iterative_imputer(df_num, seed=s) for s in range(m_imputations)]

    def train_gp_for_Jsyn(df_imp: pd.DataFrame):
        y_conv = df_imp[col_conv].to_numpy(float)
        y_sel  = df_imp[col_sel].to_numpy(float)
        y_yld  = df_imp[col_yld].to_numpy(float)
        z_conv = robust_scale(y_conv, lo_conv, hi_conv)
        z_sel  = robust_scale(y_sel,  lo_sel,  hi_sel)
        z_yld  = robust_scale(y_yld,  lo_yld,  hi_yld)
        z_syn = np.sqrt(np.maximum(z_yld * z_sel, 0.0))
        J = w_syn * z_syn + w_conv * z_conv
        X = df_imp[[col_T, col_P]].to_numpy(float)
        alpha = np.where(miss_anyY, alpha_imp, alpha_obs)
        gp = build_gp(alpha, gp_restarts=gp_restarts, random_state=0)
        gp.fit(X, J)
        return gp

    def train_gp_for_output(df_imp: pd.DataFrame, col_out: str, miss_mask: np.ndarray):
        y = df_imp[col_out].to_numpy(float)
        if col_out == col_conv: lo, hi = lo_conv, hi_conv
        elif col_out == col_sel: lo, hi = lo_sel, hi_sel
        else: lo, hi = lo_yld, hi_yld
        z = robust_scale(y, lo, hi)
        X = df_imp[[col_T, col_P]].to_numpy(float)
        alpha = np.where(miss_mask, alpha_imp, alpha_obs)
        gp = build_gp(alpha, gp_restarts=gp_restarts, random_state=0)
        gp.fit(X, z)
        return gp

    gps_J = [train_gp_for_Jsyn(df_imp) for df_imp in imputations]
    gps_conv = [train_gp_for_output(df_imp, col_conv, miss_conv) for df_imp in imputations]
    gps_sel  = [train_gp_for_output(df_imp, col_sel,  miss_sel)  for df_imp in imputations]
    gps_yld  = [train_gp_for_output(df_imp, col_yld,  miss_yld)  for df_imp in imputations]

    rng = np.random.default_rng(321)
    cands = lhs_uniform(n_candidates, bounds, rng)

    mus = []; vars_ = []
    for gp in gps_J:
        mu, std = gp.predict(cands, return_std=True)
        mus.append(mu); vars_.append(std**2)
    mus = np.vstack(mus); vars_ = np.vstack(vars_)
    mu_ens = mus.mean(axis=0)
    var_ens = vars_.mean(axis=0) + mus.var(axis=0, ddof=1)
    std_ens = np.sqrt(np.maximum(var_ens, 1e-12))

    obs_mask = ~(miss_anyY)
    if obs_mask.sum() >= 1:
        df_imp0 = imputations[0]
        y0_conv = robust_scale(df_imp0.loc[obs_mask, col_conv].to_numpy(float), lo_conv, hi_conv)
        y0_sel  = robust_scale(df_imp0.loc[obs_mask, col_sel].to_numpy(float),  lo_sel,  hi_sel)
        y0_yld  = robust_scale(df_imp0.loc[obs_mask, col_yld].to_numpy(float),  lo_yld,  hi_yld)
        zsyn0 = np.sqrt(np.maximum(y0_sel * y0_yld, 0.0))
        f_obs = w_syn * zsyn0 + w_conv * y0_conv
        f_best = float(np.max(f_obs))
    else:
        X0 = imputations[0][[col_T, col_P]].to_numpy(float)
        mu_obs, _ = gps_J[0].predict(X0, return_std=True)
        f_best = float(np.max(mu_obs))

    ei_vals = expected_improvement(mu_ens, std_ens, f_best, xi=ei_xi)
    top_idx = np.argsort(-ei_vals)[:top_k]
    top_cands = cands[top_idx]; top_ei = ei_vals[top_idx]
    top_mu = mu_ens[top_idx]; top_std = std_ens[top_idx]

    def ensemble_predict_outputs(Xnew):
        preds = {}
        for name, gps, (lo, hi) in [
            ("final_co2_conversion", gps_conv, (lo_conv, hi_conv)),
            ("final_methanol_selectivity", gps_sel, (lo_sel, hi_sel)),
            ("final_methanol_yield", gps_yld, (lo_yld, hi_yld)),
        ]:
            mus = []; vars_ = []
            for gp in gps:
                mu, std = gp.predict(Xnew, return_std=True)
                mus.append(mu); vars_.append(std**2)
            mus = np.vstack(mus); vars_ = np.vstack(vars_)
            mu_ens = mus.mean(axis=0)
            var_ens = vars_.mean(axis=0) + mus.var(axis=0, ddof=1)
            std_ens = np.sqrt(np.maximum(var_ens, 1e-12))
            y_mean = robust_unscale(mu_ens, lo, hi)
            y_std  = std_ens * (hi - lo)
            preds[name] = (y_mean, y_std)
        yld_mu_n = (preds["final_methanol_yield"][0] - lo_yld) / (hi_yld - lo_yld)
        sel_mu_n = (preds["final_methanol_selectivity"][0] - lo_sel) / (hi_sel - lo_sel)
        conv_mu_n= (preds["final_co2_conversion"][0] - lo_conv) / (hi_conv - lo_conv)
        J_mu = w_syn * np.sqrt(np.maximum(yld_mu_n * sel_mu_n, 0.0)) + w_conv * conv_mu_n
        preds["J_syn_mean_norm"] = J_mu
        return preds

    top_preds = ensemble_predict_outputs(top_cands)

    print("--- 步骤3：正在整理推荐结果... ---")
    recs = pd.DataFrame({
        "final_reaction_temp": top_cands[:,0],
        "final_pressure": top_cands[:,1],
        "EI": top_ei,
        "J_syn_mean_norm": top_mu,
        "J_syn_std_norm": top_std,
        "pred_co2_conv_mean": top_preds["final_co2_conversion"][0],
        "pred_co2_conv_std":  top_preds["final_co2_conversion"][1],
        "pred_selectivity_mean": top_preds["final_methanol_selectivity"][0],
        "pred_selectivity_std":  top_preds["final_methanol_selectivity"][1],
        "pred_yield_mean": top_preds["final_methanol_yield"][0],
        "pred_yield_std":  top_preds["final_methanol_yield"][1],
    })

    for col in ["pred_co2_conv", "pred_selectivity", "pred_yield"]:
        mcol = f"{col}_mean"; scol = f"{col}_std"
        recs[f"{col}_lo95"] = np.clip(recs[mcol] - 1.96*recs[scol], a_min=0.0, a_max=None)
        recs[f"{col}_hi95"] = np.clip(recs[mcol] + 1.96*recs[scol], a_min=None, a_max=100.0)

    recs = recs.sort_values("EI", ascending=False).reset_index(drop=True)

    # =================================================================
    # 【步骤4：输出最终推荐结果到CSV文件】
    print("--- 步骤4：正在保存推荐结果... ---")
    recs_path = os.path.join(output_dir, "recommendations_topK_synergy.csv")
    recs.to_csv(recs_path, index=False, float_format='%.4f')
    # =================================================================

    # --- 可视化与保存设置 (与原始代码相同) ---
    print("--- 步骤5：正在生成可视化图表并保存运行设置... ---")
    nT, nP = 80, 80
    Ts = np.linspace(bounds[0][0], bounds[0][1], nT)
    Ps = np.linspace(bounds[1][0], bounds[1][1], nP)
    TT, PP = np.meshgrid(Ts, Ps, indexing="xy")
    grid = np.column_stack([TT.ravel(), PP.ravel()])
    mus_g = []; vars_g = []
    for gp in gps_J:
        mu, std = gp.predict(grid, return_std=True)
        mus_g.append(mu); vars_g.append(std**2)
    mus_g = np.vstack(mus_g); vars_g = np.vstack(vars_g)
    mu_ens_g = mus_g.mean(axis=0)
    var_ens_g = vars_g.mean(axis=0) + mus_g.var(axis=0, ddof=1)
    std_ens_g = np.sqrt(np.maximum(var_ens_g, 1e-12))
    ei_grid = expected_improvement(mu_ens_g, std_ens_g, float(np.max(mu_ens)), xi=ei_xi).reshape(nP, nT)

    plt.figure(figsize=(6.8, 5.2))
    plt.contourf(TT, PP, ei_grid, levels=20, cmap='viridis')
    plt.colorbar(label="Expected Improvement (synergy)")
    plt.scatter(df[col_T], df[col_P], c='red', marker='x', label='Observed Data')
    plt.scatter(recs["final_reaction_temp"], recs["final_pressure"], c='white', marker='*', s=150, edgecolor='black', label='Top-K Recommendations')
    plt.xlabel("Reaction Temperature"); plt.ylabel("Pressure")
    plt.title("EI Surface with Recommendations")
    plt.legend()
    ei_png = os.path.join(output_dir, "ei_surface_synergy.png")
    plt.tight_layout(); plt.savefig(ei_png, dpi=160); plt.close()

    settings = {
        "objective": "J_syn = w_syn*sqrt(y_norm*sel_norm) + w_conv*conv_norm",
        "weights": {"synergy": w_syn, "conversion": w_conv},
        "m_imputations": m_imputations, "n_candidates": n_candidates, "top_k": top_k,
        "bounds": {"final_reaction_temp": list(bound_T), "final_pressure": list(bound_P)},
        "alpha_obs": alpha_obs, "alpha_imp": alpha_imp, "ei_xi": ei_xi
    }
    settings_path = os.path.join(output_dir, "run_settings_synergy.json")
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

    print(f"\n所有任务完成。结果已保存至 '{output_dir}' 目录。")
    print(f"已生成文件: {os.path.basename(recs_path)}, {os.path.basename(ei_png)}, {os.path.basename(settings_path)}")

    print("\n" + "="*50)
    print("最终推荐结果 (recommendations_topK_synergy.csv 内容):")
    print(recs.to_string())
    print("="*50)

if __name__ == "__main__":
    main()

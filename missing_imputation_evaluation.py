import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.linear_model import BayesianRidge

def load_numeric_block(path: str, convert_object_threshold: float = 0.7) -> pd.DataFrame:
    df = pd.read_csv(path)
    numeric = {}
    for c in df.select_dtypes(include=[np.number]).columns:
        numeric[c] = df[c]
    for c in df.select_dtypes(include=["object"]).columns:
        s2 = df[c].astype(str).str.strip()
        s2 = s2.str.replace(r'^\((.*)\)$', r'-\1', regex=True)
        for tok in [",", "，", "%", "％", "$", "¥", "€", "£"]:
            s2 = s2.str.replace(tok, "", regex=False)
        s2 = s2.str.replace(" ", "", regex=False)
        s_num = pd.to_numeric(s2, errors="coerce")
        # 如果转换后非空值的比例达到阈值，则采纳该列
        if s_num.notna().mean() >= convert_object_threshold:
            numeric[c] = s_num
    if not numeric:
        raise RuntimeError("未找到任何数值型或可转换为数值型的列。")
    return pd.DataFrame(numeric)

def robust_scale(X: pd.DataFrame):
    """使用中位数和IQR对数据进行稳健缩放。"""
    med = X.median(skipna=True)
    q1 = X.quantile(0.25, interpolation="linear")
    q3 = X.quantile(0.75, interpolation="linear")
    iqr = (q3 - q1).replace(0, np.nan)
    std = X.std(skipna=True, ddof=0).replace(0, np.nan)
    scale = iqr.fillna(std).fillna(1.0)
    Xs = (X - med) / scale
    return Xs, med, scale

def robust_unscale(Xs: pd.DataFrame, med: pd.Series, scale: pd.Series):
    """将稳健缩放后的数据还原。"""
    return Xs * scale + med

def impute_median(X: pd.DataFrame) -> pd.DataFrame:
    """使用中位数进行插补。"""
    imp = SimpleImputer(strategy="median")
    return pd.DataFrame(imp.fit_transform(X), columns=X.columns, index=X.index)

def impute_knn_scaled(X: pd.DataFrame, n_neighbors=5) -> pd.DataFrame:
    """使用稳健缩放后的KNN进行插补。"""
    Xs, med, scale = robust_scale(X)
    imputer = KNNImputer(n_neighbors=n_neighbors, weights="distance", metric="nan_euclidean")
    Xs_imp = pd.DataFrame(imputer.fit_transform(Xs), columns=X.columns, index=X.index)
    X_imp = robust_unscale(Xs_imp, med, scale)
    # 对于KNN可能无法填补的列（如果邻居也都是NaN），使用中位数进行最后填补
    for c in X_imp.columns:
        if X_imp[c].isna().any():
            X_imp[c] = X_imp[c].fillna(X[c].median(skipna=True))
    return X_imp

def impute_iter_bayes(X: pd.DataFrame) -> pd.DataFrame:
    """使用基于贝叶斯岭回归的多重插补（MICE）。"""
    imp = IterativeImputer(
        estimator=BayesianRidge(),
        max_iter=20,
        initial_strategy="median",
        sample_posterior=False,
        random_state=0,
        skip_complete=True
    )
    return pd.DataFrame(imp.fit_transform(X), columns=X.columns, index=X.index)

def evaluate_methods(df_num: pd.DataFrame, mask_frac=0.10, repeats=3, seed=42):
    """评估不同的插补方法。"""
    rng = np.random.default_rng(seed)
    methods = {
        "Median": impute_median,
        "KNN(k=5)+RobustScale": lambda X: impute_knn_scaled(X, n_neighbors=5),
        "MICE(BayesianRidge)": impute_iter_bayes,
    }

    # 计算用于标准化的SCALE值 (IQR优先，否则用STD)
    q1 = df_num.quantile(0.25, interpolation="linear")
    q3 = df_num.quantile(0.75, interpolation="linear")
    IQR = (q3 - q1).astype(float)
    STD = df_num.std(skipna=True, ddof=0).astype(float)
    SCALE = IQR.replace(0, np.nan).fillna(STD.replace(0, np.nan)).fillna(1.0)

    results_summary = []
    details_per_method = {}

    for label, func in methods.items():
        print(f"  - 正在评估方法: {label}")
        per_col_mae = {c: [] for c in df_num.columns}
        per_col_rmse = {c: [] for c in df_num.columns}
        per_col_nrmse = {c: [] for c in df_num.columns}
        overall_rmse_list = []

        for r in range(repeats):
            X = df_num.copy()
            mask_positions = {}
            # 在每列中随机隐藏一部分数据
            for c in df_num.columns:
                idx_obs = X[c].dropna().index.to_numpy()
                n_obs = len(idx_obs)
                if n_obs == 0:
                    mask_positions[c] = np.array([], dtype=int)
                    continue
                k = max(1, int(round(n_obs * mask_frac)))
                k = min(k, n_obs)
                chosen = rng.choice(idx_obs, size=k, replace=False)
                mask_positions[c] = chosen
                X.loc[chosen, c] = np.nan
            # 使用指定的插补方法进行填补
            X_imp = func(X)

            diffs_all = []
            for c in df_num.columns:
                pos = mask_positions[c]
                if pos.size == 0:
                    continue

                y_true = df_num.loc[pos, c].to_numpy(dtype=float)
                y_pred = X_imp.loc[pos, c].to_numpy(dtype=float)

                diff = y_pred - y_true
                mae = float(np.nanmean(np.abs(diff)))
                rmse = float(np.sqrt(np.nanmean(diff**2)))
                scale = float(SCALE.get(c, 1.0))
                nrmse = rmse / (scale if scale != 0 else 1.0)

                per_col_mae[c].append(mae)
                per_col_rmse[c].append(rmse)
                per_col_nrmse[c].append(nrmse)
                diffs_all.extend(diff.tolist())

            overall_rmse_list.append(float(np.sqrt(np.nanmean(np.array(diffs_all, dtype=float)**2))))

        col_metrics = []
        for c in df_num.columns:
            col_metrics.append({
                "column": c,
                "MAE_mean": float(np.nanmean(per_col_mae[c])) if len(per_col_mae[c]) > 0 else np.nan,
                "RMSE_mean": float(np.nanmean(per_col_rmse[c])) if len(per_col_rmse[c]) > 0 else np.nan,
                "NRMSE_IQR_mean": float(np.nanmean(per_col_nrmse[c])) if len(per_col_nrmse[c]) > 0 else np.nan,
                "R": repeats
            })

        col_df = pd.DataFrame(col_metrics)
        macro_nrmse = float(col_df["NRMSE_IQR_mean"].mean(skipna=True))
        overall_rmse = float(np.nanmean(overall_rmse_list))

        details_per_method[label] = col_df
        results_summary.append({
            "method": label,
            "macro_NRMSE_IQR": macro_nrmse,
            "overall_RMSE": overall_rmse
        })

    summary_df = pd.DataFrame(results_summary).sort_values("macro_NRMSE_IQR", ascending=True)
    return summary_df, details_per_method


if __name__ == "__main__":

    input_path = "FinalCleanedDatabase.csv"
    output_dir = "imputation_results"
    seed = 2778
    repeats = 3
    mask_fraction = 0.10

    if not os.path.exists(input_path):
        print(f"错误：输入文件未找到 -> '{input_path}'")
        print("正在创建一个名为 'sample_data.csv' 的示例文件供您测试...")
        sample_data = {
            'Patient_ID': range(1, 11),
            'Age': [25, 30, np.nan, 45, 50, 55, 60, 65, np.nan, 75],
            'BloodPressure': [120, 122, 125, 130, "135", 140, 142, np.nan, 150, 155],
            'Cholesterol': ["(200)", "210", "190", "220", "230", "215", np.nan, "240", "250", "260,0"],
            'Salary': ["$50,000", "$55,000", "$60,000", "$65,000", "$70,000", np.nan, "$80,000", "$85,000", "$90,000", "$95,000"]
        }
        pd.DataFrame(sample_data).to_csv("sample_data.csv", index=False)
        print("\n示例文件 'sample_data.csv' 已创建。")
        print("请将脚本中的 `input_path` 修改为 'sample_data.csv' 或您自己的文件路径后再运行。")
        exit()

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 加载数据
    print(f"正在从 '{input_path}' 加载数据...")
    try:
        df_num = load_numeric_block(input_path, convert_object_threshold=0.7)
        print(f"加载成功！识别出 {df_num.shape[0]} 行, {df_num.shape[1]} 个数值型/类数值型列。")
        print("列名:", df_num.columns.tolist())
    except (RuntimeError, FileNotFoundError) as e:
        print(f"加载数据时出错: {e}")
        exit()

    # 评估插补方法
    print(f"\n开始评估插补方法 (重复次数={repeats}, 隐藏比例={mask_fraction})...")
    summary_df, details = evaluate_methods(df_num, mask_frac=mask_fraction, repeats=repeats, seed=seed)
    print("评估完成！")

    # --- 保存结果 ---

    summary_csv = os.path.join(output_dir, "imputation_comparison_summary.csv")
    summary_df.to_csv(summary_csv, index=False)

    details_dir = os.path.join(output_dir, "per_method_details")
    os.makedirs(details_dir, exist_ok=True)
    for label, col_df in details.items():
        safe_label = label.replace(' ', '_').replace('(', '').replace(')', '').replace('+', 'plus')
        fname = f"per_column_{safe_label}.csv"
        col_df.to_csv(os.path.join(details_dir, fname), index=False)

    plt.figure(figsize=(8, 5))
    bars = plt.bar(summary_df["method"], summary_df["macro_NRMSE_IQR"])
    plt.ylabel("Macro NRMSE (IQR-normalized, a lower value is better)")
    plt.title("Comparison of Imputation Methods")
    plt.xticks(rotation=15, ha="right")

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval, f'{yval:.4f}', va='bottom', ha='center')
    plt.tight_layout()
    chart_path = os.path.join(output_dir, "macro_nrmse_barchart.png")
    plt.savefig(chart_path, dpi=160)
    plt.close()

    print("\n结果已保存:")
    print(f" - 概要文件: {summary_csv}")
    print(f" - 详细数据: {details_dir}")
    print(f" - 对比图表: {chart_path}")

import pandas as pd
import time

INPUT_CSV_FILENAME = 'main_database_20250911-050825.csv'


KEY_VALUE_COLUMNS = [
    'final_reaction_temp',
    'final_pressure',
    'final_co2_conversion',
    'final_methanol_selectivity',
    'final_methanol_yield'
]


REQUIRED_COLUMNS_FOR_VALID_RECORD = [
    'final_catalyst_name',
    'final_reaction_temp',
    'final_co2_conversion'
]


def clean_catalyst_data(input_filepath: str) -> pd.DataFrame:
    """
    一个完整的数据清洗流程，用于处理从ICL提取的原始催化剂数据。
    流程包括：初步过滤、按实体聚合、最终验证。
    """
    try:
        df = pd.read_csv(input_filepath)
        print(f"成功加载原始数据: {input_filepath} ({len(df)} 行)")
    except FileNotFoundError:
        print(f"[错误] 输入文件 '{input_filepath}' 未找到。请确保文件名正确且文件与脚本在同一目录下。")
        return pd.DataFrame()

    # --- 1. 初步过滤 ---
    # 过滤掉那些在所有关键数值列中都为空的行
    existing_key_cols = [col for col in KEY_VALUE_COLUMNS if col in df.columns]
    df_filtered = df.dropna(subset=existing_key_cols, how='all').copy()
    print(f"步骤 1: 初步过滤后，剩余 {len(df_filtered)} 行 (移除了 {len(df) - len(df_filtered)} 条完全无效的行)")

    # 清理催化剂名称列，去除可能存在的前后空格
    if 'final_catalyst_name' in df_filtered.columns:
        df_filtered['final_catalyst_name'].fillna('Unknown', inplace=True) # 用'Unknown'填充空的催化剂名
        df_filtered['final_catalyst_name'] = df_filtered['final_catalyst_name'].astype(str).str.strip()
    else:
        print("[错误] 找不到 'final_catalyst_name' 列，这是聚合的关键，程序无法继续。")
        return pd.DataFrame()

    # --- 2. 按实体分组聚合 ---
    # 我们将为每篇论文中的每一个催化剂创建一个唯一的记录
    grouping_keys = ['doi', 'final_catalyst_name']

    # 检查分组键是否存在
    if not all(key in df_filtered.columns for key in grouping_keys):
        print(f"[错误] 输入文件必须包含以下列才能进行聚合: {grouping_keys}")
        return pd.DataFrame()

    grouped = df_filtered.groupby(grouping_keys)

    def get_first_valid(series):
        first_valid_index = series.first_valid_index()
        return series[first_valid_index] if first_valid_index is not None else None

    agg_rules = {col: get_first_valid for col in df_filtered.columns if col not in grouping_keys}
    if 'main_sentence' in agg_rules:
        agg_rules['main_sentence'] = lambda s: ' | '.join(s.dropna().unique())

    df_cleaned = grouped.agg(agg_rules).reset_index()
    print(f"步骤 2: 按催化剂实体聚合后，得到 {len(df_cleaned)} 个唯一的数据点")

    # --- 3. 最终验证与格式化 ---
    existing_required_cols = [col for col in REQUIRED_COLUMNS_FOR_VALID_RECORD if col in df_cleaned.columns]
    df_final = df_cleaned.dropna(subset=existing_required_cols, how='any').copy()
    print(f"步骤 3: 最终验证后，剩余 {len(df_final)} 条信息完整的记录")

    ordered_columns = grouping_keys + KEY_VALUE_COLUMNS + ['main_sentence']

    final_columns_ordered = [col for col in ordered_columns if col in df_final.columns]
    df_final = df_final[final_columns_ordered]

    return df_final

if __name__ == "__main__":

    print("--- 开始数据清洗流程 ---")

    cleaned_df = clean_catalyst_data(INPUT_CSV_FILENAME)

    if not cleaned_df.empty:

        timestamp = time.strftime('%Y%m%d-%H%M%S')
        output_filename = f"cleaned_database_{timestamp}.csv"

        cleaned_df.to_csv(output_filename, index=False, encoding='utf-8-sig')

        print("\n--- 清洗完成！ ---")
        print(f"高质量的数据库已保存到: {output_filename}")
        print(f"最终包含 {len(cleaned_df)} 条干净、唯一的数据记录。")
        print("\n清洗后的数据预览:")
        print(cleaned_df.head())
    else:
        print("\n--- 清洗流程结束，但没有生成任何有效数据。 ---")
        print("可能的原因：")
        print("1. 输入的CSV文件为空或格式不正确。")
        print("2. 提取出的数据质量过低，经过过滤和聚合后没有剩下任何有效的完整记录。")

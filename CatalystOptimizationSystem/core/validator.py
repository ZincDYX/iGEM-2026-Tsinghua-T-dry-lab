import pandas as pd
import numpy as np
from typing import List, Optional
from CatalystOptimizationSystem.utils.config import (
    KEY_VALUE_COLUMNS,
    REQUIRED_COLUMNS_FOR_VALID_RECORD,
    GROUPING_KEYS,
    DEFAULT_COLUMNS,
)
from CatalystOptimizationSystem.utils.logger import get_logger

logger = get_logger(__name__)


def _first_valid(series: pd.Series):
    idx = series.first_valid_index()
    return series[idx] if idx is not None else None


def clean_catalyst_data(
    input_filepath: str,
    grouping_keys: Optional[List[str]] = None,
    key_value_columns: Optional[List[str]] = None,
    required_columns: Optional[List[str]] = None,
    nonzero_columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """??????????????
    ??????????????????????????0???????
    ?????? utils.config ?????
    """
    try:
        df = pd.read_csv(input_filepath, encoding='utf-8')
        logger.info("Loaded raw data: %s (%d rows)", input_filepath, len(df))
    except FileNotFoundError:
        logger.error("Input file '%s' not found.", input_filepath)
        return pd.DataFrame()

    grouping_keys = grouping_keys or GROUPING_KEYS
    key_value_columns = key_value_columns or KEY_VALUE_COLUMNS
    required_columns = required_columns or REQUIRED_COLUMNS_FOR_VALID_RECORD

    # Step 1: initial filter
    existing_key_cols: List[str] = [c for c in key_value_columns if c in df.columns]
    if not existing_key_cols:
        logger.warning("No key value columns found; returning original frame.")
        return df.copy()

    df_filtered = df.dropna(subset=existing_key_cols, how='all').copy()
    logger.info("After initial filter: %d rows (removed %d)", len(df_filtered), len(df) - len(df_filtered))

    # Clean catalyst name if present
    if 'final_catalyst_name' in df_filtered.columns:
        df_filtered['final_catalyst_name'] = df_filtered['final_catalyst_name'].fillna('Unknown').astype(str).str.strip()
    elif 'catalyst' in DEFAULT_COLUMNS and DEFAULT_COLUMNS['catalyst'] in df_filtered.columns:
        cname = DEFAULT_COLUMNS['catalyst']
        df_filtered[cname] = df_filtered[cname].fillna('Unknown').astype(str).str.strip()
    else:
        logger.warning("Catalyst name column not found in filtered frame.")

    # Step 2: group by entity
    if not all(k in df_filtered.columns for k in grouping_keys):
        logger.error("Missing grouping keys %s.", grouping_keys)
        return pd.DataFrame()

    grouped = df_filtered.groupby(grouping_keys)
    agg_rules = {col: _first_valid for col in df_filtered.columns if col not in grouping_keys}
    if 'main_sentence' in df_filtered.columns:
        agg_rules['main_sentence'] = lambda s: ' | '.join(s.dropna().astype(str).unique())

    df_cleaned = grouped.agg(agg_rules).reset_index()
    logger.info("After grouping: %d unique entities", len(df_cleaned))

    # Non-zero filter: drop rows where any specified column equals 0
    if nonzero_columns:
        cols_exist = [c for c in nonzero_columns if c in df_cleaned.columns]
        missing = [c for c in (nonzero_columns or []) if c not in df_cleaned.columns]
        if missing:
            logger.warning('Nonzero columns not found and ignored: %s', missing)
        if cols_exist:
            nz_mask = pd.Series(True, index=df_cleaned.index)
            for c in cols_exist:
                s_num = pd.to_numeric(df_cleaned[c], errors='coerce')
                is_zero_num = s_num.eq(0)
                is_zero_str = df_cleaned[c].astype(str).str.strip().eq('0')
                nz_mask &= ~(is_zero_num | is_zero_str)
            before = len(df_cleaned)
            df_cleaned = df_cleaned[nz_mask].copy()
            logger.info('Nonzero filter on %s removed %d rows', cols_exist, before - len(df_cleaned))

    # Step 3: final validation and ordering
    existing_required = [c for c in required_columns if c in df_cleaned.columns]
    if existing_required:
        df_final = df_cleaned.dropna(subset=existing_required, how='any').copy()
    else:
        df_final = df_cleaned.copy()
    logger.info("After final validation: %d valid rows", len(df_final))

    ordered = grouping_keys + key_value_columns + ([DEFAULT_COLUMNS['main_sentence']] if DEFAULT_COLUMNS['main_sentence'] in df_final.columns else [])
    final_cols = [c for c in ordered if c in df_final.columns]
    if final_cols:
        df_final = df_final[final_cols]

    return df_final


def main():
    import argparse, time
    p = argparse.ArgumentParser()
    p.add_argument('input_csv', help='?? CSV ??')
    p.add_argument('--out', default=None, help='?? CSV ??????')
    p.add_argument('--grouping', nargs='*', default=None, help='????????: utils.config.GROUPING_KEYS?')
    p.add_argument('--keys', nargs='*', default=None, help='??????????: utils.config.KEY_VALUE_COLUMNS?')
    p.add_argument('--required', nargs='*', default=None, help='??????????: utils.config.REQUIRED_COLUMNS_FOR_VALID_RECORD?')
    p.add_argument('--nonzero', nargs='*', default=None, help='???????????????0?????')
    args = p.parse_args()

    # Optional interactive prompt for required columns if not provided
    if args.required is None:
        try:
            s = input('Enter required columns for validation (space-separated), or leave empty for defaults: ').strip()
            if s:
                args.required = [t for t in s.split() if t]
        except Exception:
            pass

    out_df = clean_catalyst_data(
        args.input_csv,
        grouping_keys=args.grouping,
        key_value_columns=args.keys,
        required_columns=args.required,
        nonzero_columns=args.nonzero,
    )
    if out_df.empty:
        logger.warning('No valid rows produced.')
    else:
        ts = time.strftime('%Y%m%d-%H%M%S')
        out_path = args.out or f'cleaned_database_{ts}.csv'
        out_df.to_csv(out_path, index=False, encoding='utf-8', lineterminator='\n')
        logger.info('Saved cleaned data to %s (%d rows).', out_path, len(out_df))


if __name__ == '__main__':
    main()

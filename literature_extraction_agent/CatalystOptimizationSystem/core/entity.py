import hashlib
import re
import pandas as pd
from typing import Tuple, Dict

# Simple entity normalization and alignment for catalyst names
# We generate a canonical key and an entity_id (hash), then provide summary stats

def normalize_catalyst_name(name: str) -> str:
    if name is None:
        return ''
    s = str(name).lower().strip()
    s = re.sub(r'\s+', ' ', s)
    s = s.replace('-', ' ').replace('_', ' ')
    # split tokens, sort for order-insensitivity in common patterns like "cu zn al"
    toks = [t for t in re.split(r'[\s,;]+', s) if t]
    toks.sort()
    return ' '.join(toks)


def entity_id_from_canonical(canon: str) -> str:
    h = hashlib.sha1(canon.encode('utf-8')).hexdigest()[:12]
    return f'ent_{h}'


def align_entities(df: pd.DataFrame, name_col: str = 'final_catalyst_name') -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Return (df_with_ids, entity_map)
    - df_with_ids: original df with added columns entity_id, canonical_name
    - entity_map: mapping table original_name -> canonical_name -> entity_id -> count
    """
    if name_col not in df.columns:
        return df.copy(), pd.DataFrame()
    df2 = df.copy()
    df2['canonical_name'] = df2[name_col].astype(str).map(normalize_catalyst_name)
    df2['entity_id'] = df2['canonical_name'].map(entity_id_from_canonical)
    mp = df2.groupby([name_col, 'canonical_name', 'entity_id']).size().reset_index(name='count')
    return df2, mp


def summarize_entities(df_with_ids: pd.DataFrame, metrics: Tuple[str, ...]) -> pd.DataFrame:
    """Aggregate per entity across documents for metrics median & count."""
    use_cols = [c for c in metrics if c in df_with_ids.columns]
    if not use_cols:
        return pd.DataFrame()
    agg = {c: 'median' for c in use_cols}
    agg['__count'] = ('entity_id', 'size')
    out = df_with_ids.groupby(['entity_id', 'canonical_name']).agg(agg)
    out = out.reset_index().rename(columns={'__count': 'n_records'})
    return out

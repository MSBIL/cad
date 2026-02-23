from __future__ import annotations

import pandas as pd

DEFAULT_PREVDAY_COLUMNS = [
    'Opening_Gap_Percent', 'ORCL_O', 'ORCL_PD', 'ORCL_GX',
    'EOD_Close_to_OR', 'EOD_Close_to_PD', 'EOD_Close_to_GX', 'EOD_Close_to_Bar18',
    'EOD_Direction', 'EOD_Range', 'EMA_Dominance', 'Bull_100_12', 'Gap_Closed',
]


def build_prevday_features(daily_df: pd.DataFrame) -> pd.DataFrame:
    """Adds Prev_* columns (shifted by 1 trading day) for EOD and key context features."""
    if 'Date' not in daily_df.columns:
        raise ValueError('Missing Date column')
    df = daily_df.copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.normalize()
    df = df.sort_values('Date', kind='stable').reset_index(drop=True)
    out = pd.DataFrame({'Date': df['Date']})
    for col in DEFAULT_PREVDAY_COLUMNS:
        if col in df.columns:
            out[f'Prev_{col}'] = df[col].shift(1)
    return out

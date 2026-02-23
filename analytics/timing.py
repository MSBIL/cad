from __future__ import annotations

import pandas as pd


def event_bar_series(df: pd.DataFrame, mask: pd.Series, event_bar_col: str) -> pd.Series:
    """Return series of positive event bars."""
    if event_bar_col not in df.columns:
        raise KeyError(event_bar_col)
    m = mask.reindex(df.index).fillna(False).astype(bool)
    s = pd.to_numeric(df.loc[m, event_bar_col], errors='coerce')
    s = s[(s > 0) & s.notna()].astype(int)
    s.name = event_bar_col
    return s


def histogram_counts(s: pd.Series, bins: list[int] | None = None) -> pd.DataFrame:
    """Return bar->count table."""
    if s is None or len(s) == 0:
        return pd.DataFrame(columns=['bar', 'count'])
    vals = pd.to_numeric(s, errors='coerce').dropna().astype(int)
    if vals.empty:
        return pd.DataFrame(columns=['bar', 'count'])
    if bins:
        cat = pd.cut(vals, bins=bins, right=True, include_lowest=True)
        tbl = cat.value_counts().sort_index().reset_index()
        tbl.columns = ['bar', 'count']
        tbl['bar'] = tbl['bar'].astype(str)
        return tbl
    vc = vals.value_counts().sort_index()
    return pd.DataFrame({'bar': vc.index.astype(int), 'count': vc.values.astype(int)})


def survival_curve(s: pd.Series, max_bar: int = 81) -> pd.DataFrame:
    """Return t -> P(event <= t)."""
    vals = pd.to_numeric(s, errors='coerce').dropna()
    vals = vals[vals > 0].astype(int)
    if vals.empty:
        return pd.DataFrame({'t': list(range(1, max_bar + 1)), 'p_event_le_t': [0.0] * max_bar})
    n = len(vals)
    return pd.DataFrame({'t': list(range(1, max_bar + 1)), 'p_event_le_t': [float((vals <= t).sum() / n) for t in range(1, max_bar + 1)]})

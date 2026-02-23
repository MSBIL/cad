from __future__ import annotations

import numpy as np
import pandas as pd


def first_nonnull(s: pd.Series):
    nonnull = s[s.notna()]
    return nonnull.iloc[0] if not nonnull.empty else np.nan


def last_nonnull(s: pd.Series):
    nonnull = s[s.notna()]
    return nonnull.iloc[-1] if not nonnull.empty else np.nan


def maxevent(s: pd.Series) -> int:
    """Treat NaN as 0, return int max."""
    if s.empty:
        return 0
    vals = pd.to_numeric(s, errors="coerce").fillna(0)
    m = vals.max()
    if pd.isna(m):
        return 0
    return int(max(0, m))


def period_of_bar(bar: int) -> str:
    """Return 'Morning'/'Mid'/'Late' for 1..81, else 'NA'."""
    try:
        b = int(bar)
    except (TypeError, ValueError):
        return "NA"
    if 1 <= b <= 27:
        return "Morning"
    if 28 <= b <= 54:
        return "Mid"
    if 55 <= b <= 81:
        return "Late"
    return "NA"

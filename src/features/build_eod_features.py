from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from features.reducers import first_nonnull, last_nonnull


def _bucket_compare(value, low, high):
    if pd.isna(value) or pd.isna(low) or pd.isna(high):
        return pd.NA
    v = float(value)
    lo = float(low)
    hi = float(high)
    if v < lo:
        return -1
    if v > hi:
        return 1
    return 0


def _close_at_bar(g: pd.core.groupby.DataFrameGroupBy, bar: int) -> pd.Series:
    def extract(grp: pd.DataFrame):
        rows = grp.loc[grp["Bar5"] == bar, "Close_5m"]
        return last_nonnull(rows) if not rows.empty else np.nan

    return g.apply(extract)


def _maybe_last_nonnull(g: pd.core.groupby.DataFrameGroupBy, cols: Iterable[str]) -> pd.Series | None:
    for c in cols:
        if c in g.obj.columns:
            return g[c].apply(last_nonnull)
    return None


def build_daily_eod_features(intraday_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns one row per Date with terminal (EOD) features.
    Prefer provided EOD bucket columns if present, else compute from price/ranges.

    Assumptions for fallback buckets:
    - OR uses [OR_Low, OR_High]
    - PD uses [Prev_RTH_Low, Prev_RTH_High]
    - GX uses [Globex_Low, Globex_High]
    - Bar18 compares EOD close vs Bar18 close (below/equal/above)
    """
    if "Date" not in intraday_df.columns:
        raise ValueError("Missing Date column")

    df = intraday_df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.normalize()
    df = df.sort_values(["Date", "Bar5"], kind="stable").reset_index(drop=True)
    g = df.groupby("Date", sort=True, dropna=False)

    out = pd.DataFrame({"Date": list(g.size().index)})
    out["EOD_Close"] = g["Close_5m"].apply(last_nonnull).values

    # Prefer precomputed bucket columns if present.
    precomputed_specs = {
        "EOD_Close_to_OR": ["EOD_Close_to_OR"],
        "EOD_Close_to_PD": ["EOD_Close_to_PD"],
        "EOD_Close_to_GX": ["EOD_Close_to_GX"],
        "EOD_Close_to_Bar18": ["EOD_Close_to_Bar18"],
    }
    for out_col, candidates in precomputed_specs.items():
        s = _maybe_last_nonnull(g, candidates)
        if s is not None:
            out[out_col] = s.values

    # Fallback compute missing bucket columns.
    if "EOD_Close_to_OR" not in out.columns:
        or_low = g["OR_Low"].apply(last_nonnull) if "OR_Low" in df.columns else None
        or_high = g["OR_High"].apply(last_nonnull) if "OR_High" in df.columns else None
        if or_low is not None and or_high is not None:
            out["EOD_Close_to_OR"] = [
                _bucket_compare(v, lo, hi) for v, lo, hi in zip(out["EOD_Close"], or_low.values, or_high.values)
            ]
        else:
            out["EOD_Close_to_OR"] = pd.Series([pd.NA] * len(out), dtype="Int64")

    if "EOD_Close_to_PD" not in out.columns:
        pd_low = g["Prev_RTH_Low"].apply(first_nonnull) if "Prev_RTH_Low" in df.columns else None
        pd_high = g["Prev_RTH_High"].apply(first_nonnull) if "Prev_RTH_High" in df.columns else None
        if pd_low is not None and pd_high is not None:
            out["EOD_Close_to_PD"] = [
                _bucket_compare(v, lo, hi) for v, lo, hi in zip(out["EOD_Close"], pd_low.values, pd_high.values)
            ]
        else:
            out["EOD_Close_to_PD"] = pd.Series([pd.NA] * len(out), dtype="Int64")

    if "EOD_Close_to_GX" not in out.columns:
        gx_low = g["Globex_Low"].apply(first_nonnull) if "Globex_Low" in df.columns else None
        gx_high = g["Globex_High"].apply(first_nonnull) if "Globex_High" in df.columns else None
        if gx_low is not None and gx_high is not None:
            out["EOD_Close_to_GX"] = [
                _bucket_compare(v, lo, hi) for v, lo, hi in zip(out["EOD_Close"], gx_low.values, gx_high.values)
            ]
        else:
            out["EOD_Close_to_GX"] = pd.Series([pd.NA] * len(out), dtype="Int64")

    if "EOD_Close_to_Bar18" not in out.columns:
        if {"Bar5", "Close_5m"}.issubset(df.columns):
            bar18_close = _close_at_bar(g, 18)
            out["EOD_Close_to_Bar18"] = [
                pd.NA
                if pd.isna(v) or pd.isna(b18)
                else (-1 if float(v) < float(b18) else (1 if float(v) > float(b18) else 0))
                for v, b18 in zip(out["EOD_Close"], bar18_close.values)
            ]
        else:
            out["EOD_Close_to_Bar18"] = pd.Series([pd.NA] * len(out), dtype="Int64")

    # Optional terminal diagnostics.
    out["EOD_Range"] = (g["High_5m"].max() - g["Low_5m"].min()).values
    first_open = g["Open_5m"].apply(first_nonnull).values
    out["EOD_Direction"] = np.sign(pd.to_numeric(out["EOD_Close"]) - pd.to_numeric(first_open))
    out["EOD_Direction"] = pd.Series(out["EOD_Direction"]).fillna(0).astype(int)

    out = out.sort_values("Date", kind="stable").drop_duplicates(subset=["Date"]).reset_index(drop=True)
    return out

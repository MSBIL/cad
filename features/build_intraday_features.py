from __future__ import annotations

import pandas as pd

from features.reducers import first_nonnull, last_nonnull, maxevent, period_of_bar


_EVENT_MAP = {
    "Bull_BO_Hit_12": "Bull_BO_12_Bar",
    "Bear_BO_Hit_12": "Bear_BO_12_Bar",
    "Bull_50_Hit_12": "Bull_50_12_Bar",
    "Bull_100_Hit_12": "Bull_100_12_Bar",
    "Bear_50_Hit_12": "Bear_50_12_Bar",
    "Bear_100_Hit_12": "Bear_100_12_Bar",
    "Bull_BO_Hit_18": "Bull_BO_18_Bar",
    "Bear_BO_Hit_18": "Bear_BO_18_Bar",
    "Bull_50_Hit_18": "Bull_50_18_Bar",
    "Bull_100_Hit_18": "Bull_100_18_Bar",
    "Bear_50_Hit_18": "Bear_50_18_Bar",
    "Bear_100_Hit_18": "Bear_100_18_Bar",
    "Gap_Close_Bar": "Gap_Close_Bar",
    "PDH_BO": "PDH_BO_Bar",
    "PDL_BO": "PDL_BO_Bar",
    "GXH_BO": "GXH_BO_Bar",
    "GXL_BO": "GXL_BO_Bar",
    "HOD_Bar": "HOD_Bar",
    "LOD_Bar": "LOD_Bar",
}


def _flag_from_bar(v) -> int:
    return int(pd.notna(v) and float(v) > 0)


def _period_from_bar(v) -> str:
    if pd.isna(v) or float(v) <= 0:
        return "NA"
    return period_of_bar(int(v))


def build_daily_intraday_features(intraday_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns one row per Date with intraday-safe daily summary.
    Implements FEATURE.md reducers:
    - event bars via maxevent
    - buckets via last_nonnull
    - context via first_nonnull
    - derived flags and period labels
    """
    if "Date" not in intraday_df.columns:
        raise ValueError("Missing Date column")

    df = intraday_df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.normalize()
    df = df.sort_values(["Date", "Bar5"], kind="stable").reset_index(drop=True)
    g = df.groupby("Date", sort=True, dropna=False)

    out = pd.DataFrame(index=g.size().index)
    out.index.name = "Date"
    out = out.reset_index()

    first_cols = [
        "Opening_Gap_Percent",
        "Day_of_Week",
        "Day_of_Month",
        "Range_12_Percent",
        "Range_18_Percent",
    ]
    for col in first_cols:
        if col in df.columns:
            out[col] = g[col].apply(first_nonnull).values

    # Derive if absent.
    if "Day_of_Week" not in out.columns:
        out["Day_of_Week"] = pd.to_datetime(out["Date"]).dt.dayofweek + 1
    if "Day_of_Month" not in out.columns:
        out["Day_of_Month"] = pd.to_datetime(out["Date"]).dt.day

    last_cols = [
        "ORCL_O",
        "ORCL_PD",
        "ORCL_GX",
        "Closes_Above_EMA_5m",
        "Closes_Below_EMA_5m",
    ]
    for col in last_cols:
        if col in df.columns:
            out[col] = g[col].apply(last_nonnull).values

    # ORCL inside flags (derive even if provided source flag exists, to keep behavior deterministic).
    for base in ["ORCL_O", "ORCL_PD", "ORCL_GX"]:
        if base in out.columns:
            out[f"{base}_Inside"] = (out[base] == 0).astype(int)

    for src, dst in _EVENT_MAP.items():
        if src in df.columns:
            out[dst] = g[src].apply(maxevent).values
        else:
            out[dst] = 0

    # Boolean flags for OR12/OR18 event families and common events.
    event_flag_cols = [c for c in out.columns if c.endswith("_Bar")]
    for bar_col in event_flag_cols:
        flag_col = bar_col.removesuffix("_Bar")
        out[flag_col] = out[bar_col].map(_flag_from_bar).astype(int)

    # Timing period labels for event bars.
    for bar_col in event_flag_cols:
        out[f"{bar_col.removesuffix('_Bar')}_Period"] = out[bar_col].map(_period_from_bar)

    # Required named aliases from spec.
    if "Gap_Close" in out.columns:
        out["Gap_Closed"] = out["Gap_Close"]
    else:
        out["Gap_Closed"] = out["Gap_Close_Bar"].map(_flag_from_bar).astype(int)
    out["Gap_Not_Closed_By_27"] = (
        (out["Gap_Close_Bar"] == 0) | (out["Gap_Close_Bar"] > 27)
    ).astype(int)
    out["Gap_Close_By_27"] = ((out["Gap_Close_Bar"] > 0) & (out["Gap_Close_Bar"] <= 27)).astype(int)

    # Optional cutoff summaries for all event bars.
    for bar_col in event_flag_cols:
        stem = bar_col.removesuffix("_Bar")
        out[f"{stem}_By_54"] = ((out[bar_col] > 0) & (out[bar_col] <= 54)).astype(int)

    # Explicit spec example fields.
    for name in ["Bull_100_12_Bar", "Bear_100_12_Bar", "Bull_100_18_Bar", "Bear_100_18_Bar"]:
        if name in out.columns:
            stem = name.removesuffix("_Bar")
            out[f"{stem}_By_54"] = ((out[name] > 0) & (out[name] <= 54)).astype(int)

    if {"Closes_Above_EMA_5m", "Closes_Below_EMA_5m"}.issubset(out.columns):
        out["EMA_Dominance"] = out["Closes_Above_EMA_5m"] - out["Closes_Below_EMA_5m"]

    out = out.sort_values("Date", kind="stable").drop_duplicates(subset=["Date"]).reset_index(drop=True)
    return out

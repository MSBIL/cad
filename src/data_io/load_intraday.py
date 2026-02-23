from __future__ import annotations

from pathlib import Path

import pandas as pd


def _normalize_date_col(df: pd.DataFrame) -> pd.DataFrame:
    if "Date" not in df.columns:
        raise ValueError("Missing required column: Date")
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce").dt.normalize()
    if out["Date"].isna().any():
        bad = int(out["Date"].isna().sum())
        raise ValueError(f"Failed to parse {bad} Date values")
    return out


def load_intraday(path: str | Path) -> pd.DataFrame:
    """
    Load intraday dataset from xlsx/csv/parquet.
    Must return a DataFrame with at least Date and Bar5 and OHLC columns.
    Date is normalized to midnight pandas Timestamp.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    suffix = p.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(p)
    elif suffix == ".csv":
        df = pd.read_csv(p)
    elif suffix == ".parquet":
        df = pd.read_parquet(p)
    else:
        raise ValueError(f"Unsupported file type: {p.suffix}")

    df = _normalize_date_col(df)

    required = ["Date", "Bar5", "Open_5m", "High_5m", "Low_5m", "Close_5m"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["Bar5"] = pd.to_numeric(df["Bar5"], errors="coerce")
    if df["Bar5"].isna().any():
        bad = int(df["Bar5"].isna().sum())
        raise ValueError(f"Failed to parse {bad} Bar5 values as numeric")
    df["Bar5"] = df["Bar5"].astype(int)

    df = df.sort_values(["Date", "Bar5"], kind="stable").reset_index(drop=True)
    return df

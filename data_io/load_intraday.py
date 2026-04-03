from __future__ import annotations

import hashlib
import json
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


def _xlsx_cache_paths(path: Path) -> tuple[Path, Path]:
    cache_dir = path.parent / ".cad_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()[:12]
    parquet_path = cache_dir / f"{path.stem}.{key}.parquet"
    meta_path = cache_dir / f"{path.stem}.{key}.json"
    return parquet_path, meta_path


def _try_read_xlsx_cache(path: Path) -> pd.DataFrame | None:
    parquet_path, meta_path = _xlsx_cache_paths(path)
    if not parquet_path.exists() or not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        stat = path.stat()
        if meta.get("size") != stat.st_size or meta.get("mtime_ns") != stat.st_mtime_ns:
            return None
        return pd.read_parquet(parquet_path)
    except Exception:
        return None


def _write_xlsx_cache(path: Path, df: pd.DataFrame) -> None:
    parquet_path, meta_path = _xlsx_cache_paths(path)
    try:
        df.to_parquet(parquet_path, index=False)
        stat = path.stat()
        meta_path.write_text(
            json.dumps({"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}, indent=2),
            encoding="utf-8",
        )
    except Exception:
        # Caching is a performance optimization only.
        return


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
        # XLSX parsing is slow. Cache a normalized parquet copy keyed by source file path + mtime.
        if suffix == ".xlsx":
            cached = _try_read_xlsx_cache(p)
            if cached is not None:
                df = cached
            else:
                df = pd.read_excel(p, sheet_name=0, engine="openpyxl")
                _write_xlsx_cache(p, df)
        else:
            df = pd.read_excel(p, sheet_name=0)
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

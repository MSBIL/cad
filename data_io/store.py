from __future__ import annotations

from pathlib import Path

import pandas as pd


def append_intraday_partitioned(
    intraday_df: pd.DataFrame,
    root_dir: str | Path,
    partition_col: str = 'Date',
    maintain_duckdb: bool = False,
    duckdb_path: str | Path | None = None,
) -> Path:
    """Append intraday bars into a partitioned parquet dataset by date."""
    out_dir = Path(root_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = intraday_df.copy()
    if partition_col not in df.columns:
        raise ValueError(f'Missing partition column: {partition_col}')
    df[partition_col] = pd.to_datetime(df[partition_col], errors='coerce').dt.strftime('%Y-%m-%d')
    df.to_parquet(out_dir, partition_cols=[partition_col], engine='pyarrow', index=False)

    if maintain_duckdb and duckdb_path:
        try:
            import duckdb
            con = duckdb.connect(str(duckdb_path))
            con.execute("CREATE OR REPLACE TABLE intraday_bars AS SELECT * FROM read_parquet(?)", [str(out_dir / '**/*.parquet')])
            con.close()
        except Exception:
            pass
    return out_dir


def append_or_update_daily_features(
    daily_df: pd.DataFrame,
    path: str | Path,
    key_col: str = 'Date',
    maintain_duckdb: bool = False,
    duckdb_path: str | Path | None = None,
) -> Path:
    """Append/update daily features parquet by key column."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    new_df = daily_df.copy()
    if key_col not in new_df.columns:
        raise ValueError(f'Missing key column: {key_col}')
    new_df[key_col] = pd.to_datetime(new_df[key_col], errors='coerce').dt.normalize()

    if out_path.exists():
        old_df = pd.read_parquet(out_path)
        if key_col in old_df.columns:
            old_df[key_col] = pd.to_datetime(old_df[key_col], errors='coerce').dt.normalize()
        merged = pd.concat([old_df, new_df], ignore_index=True)
        merged = merged.sort_values(key_col, kind='stable').drop_duplicates(subset=[key_col], keep='last')
    else:
        merged = new_df.sort_values(key_col, kind='stable').drop_duplicates(subset=[key_col], keep='last')

    merged.to_parquet(out_path, index=False)

    if maintain_duckdb and duckdb_path:
        try:
            import duckdb
            con = duckdb.connect(str(duckdb_path))
            con.execute("CREATE OR REPLACE TABLE daily_features AS SELECT * FROM read_parquet(?)", [str(out_path)])
            con.close()
        except Exception:
            pass
    return out_path

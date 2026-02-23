from __future__ import annotations

import argparse
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_io.load_intraday import load_intraday
from features.build_intraday_features import build_daily_intraday_features
from features.build_eod_features import build_daily_eod_features
from features.build_prevday_features import build_prevday_features
from features.validate_features import validate_daily_features


def build_daily_features(intraday_df: pd.DataFrame) -> pd.DataFrame:
    """Build daily_intraday + daily_eod + prevday and merge on Date."""
    daily_intraday = build_daily_intraday_features(intraday_df)
    daily_eod = build_daily_eod_features(intraday_df)
    merged = daily_intraday.merge(daily_eod, on='Date', how='outer', validate='one_to_one')
    prev = build_prevday_features(merged)
    daily = merged.merge(prev, on='Date', how='left', validate='one_to_one')
    if {'Date', 'Bar5'}.issubset(intraday_df.columns):
        bar_counts = (intraday_df.assign(Date=pd.to_datetime(intraday_df['Date']).dt.normalize())
                      .groupby('Date')['Bar5'].nunique().rename('Bar_Count').reset_index())
        daily = daily.merge(bar_counts, on='Date', how='left')
    daily = daily.sort_values('Date', kind='stable').drop_duplicates(['Date']).reset_index(drop=True)
    validate_daily_features(daily)
    return daily


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', default=str(ROOT / 'data' / 'daily_features.parquet'))
    args = ap.parse_args()
    intraday = load_intraday(args.input)
    daily = build_daily_features(intraday)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(out, index=False)
    print(f'Wrote {len(daily)} rows to {out}')


if __name__ == '__main__':
    main()

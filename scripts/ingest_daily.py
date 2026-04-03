from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_io.freshness import write_latest_update
from data_io.load_intraday import load_intraday
from data_io.store import append_intraday_partitioned, append_or_update_daily_features
from scripts.build_daily_features import build_daily_features


def main() -> None:
    parser = argparse.ArgumentParser(description='Ingest intraday source and update local stores')
    parser.add_argument('--date', required=True, help='Trade date YYYY-MM-DD (metadata / selection hint)')
    parser.add_argument('--source', required=True, help='Path to xlsx/csv/parquet source file')
    parser.add_argument('--intraday-store', default=str(ROOT / 'data' / 'intraday_bars'))
    parser.add_argument('--daily-store', default=str(ROOT / 'data' / 'daily_features.parquet'))
    parser.add_argument('--duckdb', default=None, help='Optional DuckDB file path to refresh mirrors')
    parser.add_argument('--write-freshness', action='store_true', help='Write latest_update.json (disabled by default)')
    args = parser.parse_args()

    source = Path(args.source)
    intraday = load_intraday(source)
    if args.date:
        # Optional subset by provided trade date if a multi-date file is supplied.
        date_mask = (intraday['Date'].dt.strftime('%Y-%m-%d') == args.date)
        if date_mask.any():
            intraday = intraday.loc[date_mask].copy()

    daily = build_daily_features(intraday)

    append_intraday_partitioned(
        intraday,
        args.intraday_store,
        maintain_duckdb=bool(args.duckdb),
        duckdb_path=args.duckdb,
    )
    append_or_update_daily_features(
        daily,
        args.daily_store,
        maintain_duckdb=bool(args.duckdb),
        duckdb_path=args.duckdb,
    )

    if args.write_freshness:
        write_latest_update(ROOT / 'data' / 'latest_update.json', args.date, args.daily_store)

    print(f'Ingest complete: {len(intraday)} intraday rows, {len(daily)} daily rows')
    print(f'Intraday store: {args.intraday_store}')
    print(f'Daily store: {args.daily_store}')
    if not args.write_freshness:
        print('Freshness update skipped (use --write-freshness to enable).')


if __name__ == '__main__':
    main()

from pathlib import Path

from data_io.load_intraday import load_intraday
from scripts.build_daily_features import build_daily_features


def test_daily_builder_end_to_end():
    intraday = load_intraday(Path('data/filtered_data_20250103_034327.xlsx'))
    daily = build_daily_features(intraday)
    assert len(daily) == intraday['Date'].nunique()
    assert int(daily['Date'].duplicated().sum()) == 0
    for c in ['EOD_Close', 'Gap_Close_Bar', 'Prev_EOD_Close_to_OR']:
        assert c in daily.columns

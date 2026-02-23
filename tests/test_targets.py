import pandas as pd

from analytics.targets import Target, compute_target_stats


def test_compute_target_stats_hits_n_and_timing():
    df = pd.DataFrame({'Bull_100_12_Bar': [0, 10, 20, 0], 'Bull_BO_12_Bar': [0, 5, 8, 0]})
    mask = pd.Series([True, True, False, True])
    t = Target(id='T1', label='Bull100', occurred_expr='Bull_100_12_Bar > 0', event_bar_col='Bull_100_12_Bar')
    stats = compute_target_stats(df, mask, t)
    assert stats['n'] == 3
    assert stats['hits'] == 1
    assert abs(stats['p'] - (1/3)) < 1e-9
    assert stats['median_bar'] == 10.0
    assert stats['peak_bar'] == 10

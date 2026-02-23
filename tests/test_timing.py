import pandas as pd

from analytics.timing import event_bar_series, histogram_counts, survival_curve


def test_timing_helpers():
    df = pd.DataFrame({'e': [0, 2, 2, 5, None], 'm': [1, 1, 0, 1, 1]})
    s = event_bar_series(df, df['m'] == 1, 'e')
    assert s.tolist() == [2, 5]
    hist = histogram_counts(s)
    assert hist.to_dict(orient='records') == [{'bar': 2, 'count': 1}, {'bar': 5, 'count': 1}]


def test_survival_curve_synthetic_and_empty():
    surv = survival_curve(pd.Series([2, 4]), max_bar=5)
    assert surv['p_event_le_t'].tolist() == [0.0, 0.5, 0.5, 1.0, 1.0]
    empty = survival_curve(pd.Series(dtype=float), max_bar=3)
    assert empty['p_event_le_t'].tolist() == [0.0, 0.0, 0.0]

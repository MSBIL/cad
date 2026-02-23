import numpy as np
import pandas as pd

from features.reducers import first_nonnull, last_nonnull, maxevent, period_of_bar


def test_first_nonnull_and_last_nonnull():
    s = pd.Series([np.nan, 3, np.nan, 5])
    assert first_nonnull(s) == 3
    assert last_nonnull(s) == 5


def test_first_last_nonnull_all_missing():
    s = pd.Series([np.nan, np.nan])
    assert pd.isna(first_nonnull(s))
    assert pd.isna(last_nonnull(s))


def test_maxevent_treats_nan_as_zero():
    s = pd.Series([np.nan, 0, 7, np.nan, 3])
    assert maxevent(s) == 7


def test_maxevent_all_missing_or_zero_returns_zero():
    assert maxevent(pd.Series([np.nan, np.nan])) == 0
    assert maxevent(pd.Series([0, 0, np.nan])) == 0


def test_period_of_bar_boundaries():
    assert period_of_bar(27) == "Morning"
    assert period_of_bar(28) == "Mid"
    assert period_of_bar(54) == "Mid"
    assert period_of_bar(55) == "Late"
    assert period_of_bar(0) == "NA"
    assert period_of_bar(82) == "NA"

import pandas as pd

from analytics.filters import FilterClause, apply_filters


def test_apply_filters_each_op():
    df = pd.DataFrame({'a': [1, 2, 3, None], 'b': ['x', 'y', 'x', None]})
    assert apply_filters(df, [FilterClause('a', '==', 2)]).tolist() == [False, True, False, False]
    assert apply_filters(df, [FilterClause('a', '!=', 2)]).tolist() == [True, False, True, False]
    assert apply_filters(df, [FilterClause('a', '>', 1)]).tolist() == [False, True, True, False]
    assert apply_filters(df, [FilterClause('a', '>=', 2)]).tolist() == [False, True, True, False]
    assert apply_filters(df, [FilterClause('a', '<', 3)]).tolist() == [True, True, False, False]
    assert apply_filters(df, [FilterClause('a', '<=', 2)]).tolist() == [True, True, False, False]
    assert apply_filters(df, [FilterClause('b', 'in', ['x'])]).tolist() == [True, False, True, False]
    assert apply_filters(df, [FilterClause('a', 'between', (1, 2))]).tolist() == [True, True, False, False]


def test_apply_filters_nans_false():
    df = pd.DataFrame({'x': [1, None, 3]})
    assert apply_filters(df, [FilterClause('x', '>', 0), FilterClause('x', '<', 3)]).tolist() == [True, False, False]

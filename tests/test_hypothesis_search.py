import pandas as pd

from analytics.hypothesis_search import search_hypotheses
from analytics.targets import Target


def test_search_hypotheses_returns_ranked_rows():
    df = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=20, freq='D'),
        'Opening_Gap_Percent': [-1, -0.5, 0.0, 0.1, 0.7] * 4,
        'ORCL_O': [1, 1, 0, -1, 1] * 4,
        'Bull_BO_12_Bar': [0, 5, 10, 0, 12] * 4,
        'Gap_Close_Bar': [0, 1, 0, 2, 1] * 4,
    })
    target = Target(id='T_GAP_CLOSE', label='Gap Close', occurred_expr='Gap_Close_Bar > 0', event_bar_col='Gap_Close_Bar')
    out = search_hypotheses(
        df,
        target=target,
        allowed_fields=['Opening_Gap_Percent', 'ORCL_O', 'Bull_BO_12_Bar'],
        max_clauses=2,
        min_n=3,
        objective='max_probability',
        discovery_start='2024-01-01',
        discovery_end='2024-01-20',
        validation_start='2024-01-11',
        validation_end='2024-01-20',
        max_candidates_per_fieldset=500,
    )
    assert not out.empty
    assert {'clauses', 'label', 'n', 'p', 'p0', 'lift', 'score'}.issubset(out.columns)

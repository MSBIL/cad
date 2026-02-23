from __future__ import annotations

import pandas as pd
from analytics.targets import compute_target_stats
from analytics.timing import event_bar_series, histogram_counts, survival_curve


def render(ctx: dict) -> None:
    import streamlit as st
    daily = ctx['daily']
    mask = ctx['mask']
    target_id = st.session_state.get('selected_target_id')
    target = next((t for t in ctx['targets'] if t.id == target_id), None)
    if target is None and ctx['targets']:
        target = ctx['targets'][0]
    st.subheader('Timing')
    if target is None:
        st.info('No target selected.')
        return
    st.write(f'Selected target: **{target.label}**')
    if not target.event_bar_col or target.event_bar_col not in daily.columns:
        st.info('Selected target has no event bar column.')
        return
    s = event_bar_series(daily, mask, target.event_bar_col)
    hist = histogram_counts(s)
    surv = survival_curve(s)
    stats = compute_target_stats(daily, mask, target)
    c1, c2, c3 = st.columns(3)
    c1.metric('Median', stats['median_bar'] if stats['median_bar'] is not None else 'NA')
    c2.metric('IQR', f"{stats['iqr_bar']:.1f}" if stats['iqr_bar'] is not None else 'NA')
    c3.metric('Peak', stats['peak_bar'] if stats['peak_bar'] is not None else 'NA')
    st.markdown('**Histogram**')
    st.bar_chart(hist.set_index('bar')['count'] if not hist.empty else pd.Series(dtype=int))
    st.markdown('**Survival Curve**')
    st.line_chart(surv.set_index('t')['p_event_le_t'])

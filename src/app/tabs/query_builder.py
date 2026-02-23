from __future__ import annotations

from analytics.filters import FilterClause, apply_filters

BUCKET_LABELS = {'Below': -1, 'Inside': 0, 'Above': 1}


def render(ctx: dict) -> None:
    import streamlit as st
    daily = ctx['daily']
    st.subheader('Query Builder')
    clauses = []

    with st.expander('Gap range', expanded=True):
        gmin, gmax = st.slider('Opening_Gap_Percent', -5.0, 5.0, (-5.0, 5.0), 0.01)
        if (gmin, gmax) != (-5.0, 5.0):
            clauses.append(FilterClause('Opening_Gap_Percent', 'between', (gmin, gmax), 'Gap range'))

    with st.expander('ORCL buckets', expanded=True):
        for key in ['ORCL_O', 'ORCL_PD', 'ORCL_GX']:
            if key not in daily.columns:
                continue
            picks = st.multiselect(key, ['Below', 'Inside', 'Above'])
            if picks:
                clauses.append(FilterClause(key, 'in', [BUCKET_LABELS[p] for p in picks], key))

    with st.expander('OR ranges', expanded=False):
        if 'Range_12_Percent' in daily.columns:
            r12 = st.slider('Range_12_Percent <=', 0.0, 10.0, 10.0, 0.01)
            if r12 < 10.0:
                clauses.append(FilterClause('Range_12_Percent', '<=', r12, 'Range12 <= x'))
        if 'Range_18_Percent' in daily.columns:
            r18 = st.slider('Range_18_Percent <=', 0.0, 10.0, 10.0, 0.01)
            if r18 < 10.0:
                clauses.append(FilterClause('Range_18_Percent', '<=', r18, 'Range18 <= x'))

    with st.expander('Breakout occurred flags', expanded=True):
        flags = [c for c in ['Bull_BO_12_Bar','Bear_BO_12_Bar','Bull_BO_18_Bar','Bear_BO_18_Bar','Bull_100_12_Bar','Bear_100_12_Bar'] if c in daily.columns]
        selected = st.multiselect('Require event occurred (>0)', flags)
        for f in selected:
            clauses.append(FilterClause(f, '>', 0, f))

    with st.expander('Previous-day filters', expanded=True):
        if 'Prev_Gap_Closed' in daily.columns and st.checkbox('Prev_Gap_Closed == 1'):
            clauses.append(FilterClause('Prev_Gap_Closed', '==', 1, 'Prev gap closed'))
        if 'Prev_EOD_Direction' in daily.columns:
            pick = st.selectbox('Prev_EOD_Direction', ['Any', -1, 0, 1])
            if pick != 'Any':
                clauses.append(FilterClause('Prev_EOD_Direction', '==', pick, 'Prev EOD direction'))

    st.session_state.filter_clauses = clauses
    mask = apply_filters(daily, clauses)
    st.session_state.current_mask = mask
    st.write('Active filters:', ' | '.join([(c.label or f'{c.field} {c.op} {c.value}') for c in clauses]) if clauses else '(none)')
    st.metric('Filtered n', int(mask.sum()))

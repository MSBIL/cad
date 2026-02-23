from __future__ import annotations

import pandas as pd
from analytics.targets import compute_target_stats


def render(ctx: dict) -> None:
    import streamlit as st
    daily = ctx['daily']
    mask = ctx['mask']
    targets = ctx['targets']
    st.subheader('Targets Table')
    rows = [compute_target_stats(daily, mask, t) for t in targets]
    tbl = pd.DataFrame(rows)
    if tbl.empty:
        st.info('No targets loaded.')
        return
    sort_col = st.selectbox('Sort by', ['p', 'lift', 'reliability', 'n', 'hits'])
    asc = sort_col == 'reliability'
    tbl = tbl.sort_values(sort_col, ascending=asc, na_position='last').reset_index(drop=True)
    st.dataframe(tbl, use_container_width=True, hide_index=True)
    pick = st.selectbox('Select target for Timing tab', tbl['label'].tolist())
    row = tbl.loc[tbl['label'] == pick].iloc[0]
    st.session_state.selected_target_id = row['target_id']

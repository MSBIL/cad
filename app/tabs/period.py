from __future__ import annotations

import pandas as pd


def _period_table(df: pd.DataFrame, mask: pd.Series, col: str) -> pd.DataFrame:
    if col not in df.columns:
        return pd.DataFrame({'Period': [], 'Count': []})
    order = ['Morning', 'Mid', 'Late', 'NA']
    vc = df.loc[mask, col].fillna('NA').value_counts().reindex(order, fill_value=0)
    return pd.DataFrame({'Period': vc.index, 'Count': vc.values})


def render(ctx: dict) -> None:
    import streamlit as st
    daily = ctx['daily']
    mask = ctx['mask']
    target_id = st.session_state.get('selected_target_id')
    t = next((x for x in ctx['targets'] if x.id == target_id), None)
    st.subheader('Period Analysis')
    cols = st.columns(3)
    if t and t.event_bar_col:
        pcol = t.event_bar_col.removesuffix('_Bar') + '_Period'
        tbl = _period_table(daily, mask, pcol)
        cols[0].markdown(f'**{pcol}**')
        if not tbl.empty:
            cols[0].bar_chart(tbl.set_index('Period')['Count'])
    for i, col in enumerate(['HOD_Period', 'LOD_Period'], start=1):
        tbl = _period_table(daily, mask, col)
        cols[i].markdown(f'**{col}**')
        if not tbl.empty:
            cols[i].bar_chart(tbl.set_index('Period')['Count'])

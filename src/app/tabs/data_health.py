from __future__ import annotations

import pandas as pd


def render(ctx: dict) -> None:
    import streamlit as st
    daily = ctx['daily']
    intraday = ctx['intraday']
    qa = ctx.get('qa', {})
    freshness = ctx.get('freshness', {})
    st.subheader('Data Health')
    c1, c2, c3 = st.columns(3)
    c1.metric('QA Errors', qa.get('error_count', 0))
    c2.metric('QA Warnings', qa.get('warning_count', 0))
    c3.metric('Rows', len(daily))
    st.markdown('**Freshness**')
    st.json(freshness if freshness else {'status': 'missing latest_update.json'})
    st.markdown('**Null rates**')
    nulls = daily.isna().mean().sort_values(ascending=False).rename('null_rate').reset_index(names='column')
    st.dataframe(nulls.head(30), use_container_width=True)
    st.markdown('**Bar-count anomalies**')
    if {'Date','Bar5'}.issubset(intraday.columns):
        bc = (intraday.assign(Date=pd.to_datetime(intraday['Date']).dt.normalize())
              .groupby('Date')['Bar5'].nunique().rename('bar_count').reset_index())
        bad = bc[bc['bar_count'] != 81]
        st.write(f'Anomalies: {len(bad)}')
        if not bad.empty:
            st.dataframe(bad, use_container_width=True)

from __future__ import annotations


def render(ctx: dict) -> None:
    import streamlit as st
    daily = ctx['daily']
    mask = ctx['mask']
    st.subheader('Overview')
    c1, c2, c3 = st.columns(3)
    c1.metric('Daily rows', len(daily))
    c2.metric('Filtered n', int(mask.sum()))
    c3.metric('Coverage', f"{(float(mask.mean()) if len(mask) else 0):.1%}")
    st.write('Use Query Builder to define conditions, then inspect Targets, Timing, Period, and Case Studies.')

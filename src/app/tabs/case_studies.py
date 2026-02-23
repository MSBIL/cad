from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from analytics.filters import FilterClause, apply_filters
from analytics.targets import compute_target_stats
from reports.case_study_pdf import export_case_study_pdf

CASE_CFG = Path(__file__).resolve().parents[3] / 'config' / 'case_templates.yaml'


def _load_cases() -> list[dict]:
    if not CASE_CFG.exists():
        return []
    return (yaml.safe_load(CASE_CFG.read_text(encoding='utf-8')) or {}).get('templates', [])


def _apply_case_filters(daily: pd.DataFrame, template: dict) -> pd.Series:
    clauses = []
    any_groups = []
    for item in template.get('filters', []):
        if 'any' in item:
            any_groups.append(item['any'])
        else:
            clauses.append(FilterClause(item['field'], item['op'], item['value']))
    mask = apply_filters(daily, clauses)
    for group in any_groups:
        gmask = pd.Series(False, index=daily.index)
        for item in group:
            gmask |= apply_filters(daily, [FilterClause(item['field'], item['op'], item['value'])])
        mask &= gmask
    return mask


def _plotly_ok() -> bool:
    try:
        import plotly.graph_objects as go  # noqa: F401
        return True
    except Exception:
        return False


def _build_figure(day_intraday: pd.DataFrame, day_daily: pd.Series):
    import plotly.graph_objects as go
    x = day_intraday['Bar5']
    fig = go.Figure(data=[go.Candlestick(x=x, open=day_intraday['Open_5m'], high=day_intraday['High_5m'], low=day_intraday['Low_5m'], close=day_intraday['Close_5m'], name='5m')])
    # Explicit OR12/OR18 overlays computed from the first 12/18 bars.
    for n, dash in [(12, 'dot'), (18, 'dash')]:
        sub = day_intraday.loc[day_intraday['Bar5'] <= n]
        if not sub.empty:
            fig.add_hline(float(sub['High_5m'].max()), line_dash=dash, line_color='green', annotation_text=f'OR{n} High')
            fig.add_hline(float(sub['Low_5m'].min()), line_dash=dash, line_color='red', annotation_text=f'OR{n} Low')
    marker_specs = [('Bull_BO_12_Bar','Bull BO12','green'),('Bear_BO_12_Bar','Bear BO12','red'),('Bull_100_12_Bar','Bull100/12','darkgreen'),('Bear_100_12_Bar','Bear100/12','darkred'),('Bull_BO_18_Bar','Bull BO18','lime'),('Bear_BO_18_Bar','Bear BO18','orange'),('Gap_Close_Bar','Gap Close','blue'),('HOD_Bar','HOD','purple'),('LOD_Bar','LOD','brown')]
    for col, label, color in marker_specs:
        if col in day_daily and pd.notna(day_daily[col]) and float(day_daily[col]) > 0:
            bar = int(day_daily[col])
            row = day_intraday.loc[day_intraday['Bar5'] == bar]
            if not row.empty:
                fig.add_scatter(x=[bar], y=[float(row['Close_5m'].iloc[-1])], mode='markers+text', text=[label], textposition='top center', marker={'color': color, 'size': 10}, name=label)
    fig.update_layout(height=520, xaxis_title='Bar5', yaxis_title='Price')
    return fig


def render(ctx: dict) -> None:
    import streamlit as st
    daily = ctx['daily']
    intraday = ctx['intraday']
    targets = {t.id: t for t in ctx['targets']}
    current_mask = ctx['mask']
    st.subheader('Case Studies')
    cases = _load_cases()
    if not cases:
        st.info('No case templates available.')
        return
    labels = [f"{c['id']} - {c['name']}" for c in cases]
    pick = st.selectbox('Case template', labels)
    case = cases[labels.index(pick)]
    combine = st.checkbox('Combine with current Query Builder filters', value=True)
    case_mask = _apply_case_filters(daily, case)
    mask = case_mask & current_mask if combine else case_mask
    matches = daily.loc[mask, 'Date']
    date_options = pd.to_datetime(matches).sort_values().dt.strftime('%Y-%m-%d').tolist()
    st.write(f'Matching dates: {len(date_options)}')
    if not date_options:
        return
    sel_date = st.selectbox('Select date', date_options)
    day_daily = daily.loc[pd.to_datetime(daily['Date']).dt.strftime('%Y-%m-%d') == sel_date].iloc[0]
    day_intraday = intraday.loc[pd.to_datetime(intraday['Date']).dt.strftime('%Y-%m-%d') == sel_date].copy()
    fig = None
    if _plotly_ok() and not day_intraday.empty:
        fig = _build_figure(day_intraday, day_daily)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption('Plotly unavailable; replay chart skipped.')
    stats_rows = [compute_target_stats(daily, mask, targets[tid]) for tid in case.get('primary_targets', []) if tid in targets]
    if stats_rows:
        st.dataframe(pd.DataFrame(stats_rows), use_container_width=True, hide_index=True)
    out_dir = Path(ctx['root']) / 'outputs' / 'case_studies'
    if st.button('Export PDF report'):
        chart_path = None
        if fig is not None:
            chart_path = out_dir / f"{case['id']}_{sel_date}_chart.png"
            chart_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                fig.write_image(str(chart_path))
            except Exception:
                chart_path = None
        out = export_case_study_pdf(
            summary={'case_id': case['id'], 'case_name': case['name'], 'selected_date': sel_date, 'n': int(mask.sum())},
            stats_rows=stats_rows,
            chart_image_path=chart_path,
            output_dir=out_dir,
            trade_date=sel_date,
            filters=case.get('filters', []),
            metadata={'case_template': case['id']},
        )
        st.success(f'Exported {out}')
    with st.expander('Template JSON'):
        st.code(json.dumps(case, indent=2), language='json')

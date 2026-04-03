from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from analytics.filters import FilterClause
from analytics.hypothesis_search import search_hypotheses


def _target_by_label(targets, label: str):
    for t in targets:
        if f"{t.id} | {t.label}" == label:
            return t
    return targets[0] if targets else None


def _default_allowed_fields(daily: pd.DataFrame) -> list[str]:
    preferred = [
        'Opening_Gap_Percent', 'ORCL_O', 'ORCL_PD', 'ORCL_GX', 'Range_12_Percent', 'Range_18_Percent',
        'Gap_Close_Bar', 'Bull_BO_12_Bar', 'Bear_BO_12_Bar', 'Bull_BO_18_Bar', 'Bear_BO_18_Bar',
        'Prev_EOD_Direction', 'Prev_Gap_Closed', 'Prev_ORCL_O', 'Prev_ORCL_PD', 'Prev_ORCL_GX',
    ]
    return [c for c in preferred if c in daily.columns]


def _date_bounds(daily: pd.DataFrame) -> tuple[date, date]:
    d = pd.to_datetime(daily['Date'], errors='coerce').dropna().dt.date
    return (d.min(), d.max())


def _serialize_filter_clauses(clause_dicts: list[dict]) -> list[FilterClause]:
    return [FilterClause(field=c['field'], op=c['op'], value=c['value'], label=c.get('label')) for c in clause_dicts]


def render(ctx: dict) -> None:
    import streamlit as st

    daily: pd.DataFrame = ctx['daily']
    targets = ctx['targets']
    st.subheader('Hypothesis Lab')

    if not targets:
        st.info('No targets loaded.')
        return

    dmin, dmax = _date_bounds(daily)
    target_labels = [f"{t.id} | {t.label}" for t in targets]

    c1, c2 = st.columns(2)
    target_label = c1.selectbox('Target selection', target_labels)
    target = _target_by_label(targets, target_label)
    objective = c2.selectbox('Objective', ['max_probability', 'min_probability'])

    c3, c4, c5 = st.columns(3)
    max_clauses = c3.slider('Max clauses (1-3)', 1, 3, 2)
    min_n = c4.number_input('Min n', min_value=10, max_value=5000, value=100, step=10)
    top_k = c5.number_input('Top rows', min_value=5, max_value=200, value=30, step=5)

    allowed_defaults = _default_allowed_fields(daily)
    allowed_fields = st.multiselect('Allowed fields', [c for c in daily.columns if c != 'Date'], default=allowed_defaults)

    st.markdown('**Discovery / Validation ranges**')
    c6, c7 = st.columns(2)
    disc_range = c6.date_input('Discovery window', value=(dmin, dmax), min_value=dmin, max_value=dmax)
    use_validation = c7.checkbox('Use validation split', value=False)
    val_range = ()
    if use_validation:
        val_range = c7.date_input('Validation window', value=(dmin, dmax), min_value=dmin, max_value=dmax)

    run_clicked = st.button('Run hypothesis search')
    if run_clicked:
        disc_start = disc_end = None
        if isinstance(disc_range, tuple) and len(disc_range) == 2:
            disc_start, disc_end = str(disc_range[0]), str(disc_range[1])
        val_start = val_end = None
        if isinstance(val_range, tuple) and len(val_range) == 2:
            val_start, val_end = str(val_range[0]), str(val_range[1])

        with st.spinner('Searching hypotheses...'):
            results = search_hypotheses(
                daily,
                target=target,
                allowed_fields=allowed_fields,
                max_clauses=max_clauses,
                min_n=int(min_n),
                objective=objective,
                discovery_start=disc_start,
                discovery_end=disc_end,
                validation_start=val_start,
                validation_end=val_end,
            )
        st.session_state.hypothesis_results = results
        st.session_state.hypothesis_target_id = target.id

    results = st.session_state.get('hypothesis_results')
    if results is None or not isinstance(results, pd.DataFrame) or results.empty:
        st.caption('Run the search to generate ranked hypotheses.')
        return

    display_cols = [
        c for c in [
            'label', 'num_clauses', 'n', 'hits', 'p', 'p0', 'lift', 'reliability', 'score',
            'validation_n', 'validation_p', 'validation_p0', 'validation_lift', 'lift_sign_persisted'
        ] if c in results.columns
    ]
    st.dataframe(results[display_cols].head(int(top_k)), use_container_width=True, hide_index=True)

    row_count = min(int(top_k), len(results))
    row_idx = st.number_input('Select ranked row', min_value=0, max_value=max(0, row_count - 1), value=0, step=1)
    selected = results.iloc[int(row_idx)]
    selected_clauses = _serialize_filter_clauses(selected['clauses'])

    st.markdown('**Selected hypothesis**')
    st.code(json.dumps({k: (v if k != 'clauses' else selected['clauses']) for k, v in selected.to_dict().items()}, indent=2, default=str), language='json')

    c8, c9, c10 = st.columns(3)
    if c8.button('Save to library'):
        out_dir = Path(ctx['root']) / 'outputs' / 'hypotheses'
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / 'library.jsonl'
        payload = selected.to_dict()
        payload['target_id'] = target.id
        with out_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(payload, default=str) + '\\n')
        st.success(f'Saved to {out_path}')

    if c9.button('Apply as current filter'):
        st.session_state.filter_clauses = selected_clauses
        st.success('Applied selected hypothesis clauses to current filters.')

    if c10.button('Generate case study template'):
        out_dir = Path(ctx['root']) / 'outputs' / 'hypotheses'
        out_dir.mkdir(parents=True, exist_ok=True)
        template = {
            'id': f'GEN_{target.id}_{int(row_idx)}',
            'name': f'Generated from Hypothesis Lab ({target.label})',
            'filters': selected['clauses'],
            'primary_targets': [target.id],
            'overlays': ['or12', 'or18', 'gap_close', 'hod', 'lod'],
        }
        out_path = out_dir / f"generated_case_{target.id}_{int(row_idx)}.yaml"
        out_path.write_text(yaml.safe_dump(template, sort_keys=False), encoding='utf-8')
        st.success(f'Generated {out_path}')

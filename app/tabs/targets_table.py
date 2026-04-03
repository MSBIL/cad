from __future__ import annotations

import pandas as pd
from analytics.targets import compute_target_stats


def render(ctx: dict) -> None:
    import streamlit as st
    daily = ctx['daily']
    mask = ctx['mask']
    targets = ctx['targets']
    st.subheader('Targets Table')
    # Filter out HOD/LOD timing targets (100% probability, not useful for conditional analysis)
    filtered_targets = [t for t in targets if t.id not in ['T_HOD_TIMING', 'T_LOD_TIMING']]
    rows = [compute_target_stats(daily, mask, t) for t in filtered_targets]
    tbl = pd.DataFrame(rows)
    if tbl.empty:
        st.info('No targets loaded.')
        return
    
    # Format probability columns as percentages
    if 'p' in tbl.columns:
        tbl['Probability'] = tbl['p'].apply(lambda x: f"{x:.1%}" if pd.notna(x) else 'N/A')
    if 'p0' in tbl.columns:
        tbl['Baseline'] = tbl['p0'].apply(lambda x: f"{x:.1%}" if pd.notna(x) else 'N/A')
    if 'ci_low' in tbl.columns and 'ci_high' in tbl.columns:
        tbl['CI_Low'] = tbl['ci_low'].apply(lambda x: f"{x:.1%}" if pd.notna(x) else 'N/A')
        tbl['CI_High'] = tbl['ci_high'].apply(lambda x: f"{x:.1%}" if pd.notna(x) else 'N/A')
    
    # Select columns to display with better names
    display_cols = ['label', 'group', 'Probability', 'Baseline', 'lift', 'n', 'hits', 
                    'CI_Low', 'CI_High', 'reliability', 'median_bar', 'iqr_bar', 'peak_bar']
    display_cols = [c for c in display_cols if c in tbl.columns]
    
    # Sort options - use original column names for sorting
    sort_options = {'Probability': 'p', 'Lift': 'lift', 'Reliability': 'reliability', 
                    'Sample Size': 'n', 'Hits': 'hits'}
    sort_label = st.selectbox('Sort by', list(sort_options.keys()))
    sort_col = sort_options[sort_label]
    asc = sort_col == 'reliability'
    
    tbl_sorted = tbl.sort_values(sort_col, ascending=asc, na_position='last').reset_index(drop=True)
    st.dataframe(tbl_sorted[display_cols], use_container_width=True, hide_index=True)
    
    # Timing analysis for selected target
    st.markdown('---')
    st.markdown('#### Timing Analysis')
    pick = st.selectbox('Select target for timing analysis', tbl_sorted['label'].tolist())
    row = tbl_sorted.loc[tbl_sorted['label'] == pick].iloc[0]
    st.session_state.selected_target_id = row['target_id']
    
    # Get the target object
    target = next((t for t in ctx['targets'] if t.id == row['target_id']), None)
    
    if target and target.event_bar_col and target.event_bar_col in daily.columns:
        from analytics.timing import event_bar_series, histogram_counts, survival_curve
        
        s = event_bar_series(daily, mask, target.event_bar_col)
        if not s.empty:
            hist = histogram_counts(s)
            surv = survival_curve(s)
            
            # Display timing metrics
            c1, c2, c3 = st.columns(3)
            median_val = row.get('median_bar')
            iqr_val = row.get('iqr_bar')
            peak_val = row.get('peak_bar')
            
            c1.metric('Median Bar', f"{median_val:.1f}" if pd.notna(median_val) else 'N/A')
            c2.metric('IQR', f"{iqr_val:.1f}" if pd.notna(iqr_val) else 'N/A')
            c3.metric('Peak Bar', f"{int(peak_val)}" if pd.notna(peak_val) else 'N/A')
            
            # Display charts side by side
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('**Histogram**')
                if not hist.empty:
                    st.bar_chart(hist.set_index('bar')['count'])
                else:
                    st.info('No timing data available')
            
            with col2:
                st.markdown('**Survival Curve**')
                if not surv.empty:
                    st.line_chart(surv.set_index('t')['p_event_le_t'])
                else:
                    st.info('No timing data available')
        else:
            st.info(f'No occurrences of {target.label} in the filtered dataset')
    else:
        st.info('Selected target has no timing information available')
    
    # Period analysis section
    st.markdown('---')
    st.markdown('#### Period Analysis (Morning/Mid/Late)')
    st.caption('Morning: Bars 1-27 | Mid: Bars 28-54 | Late: Bars 55-81')
    
    def _period_table(df: pd.DataFrame, mask_series: pd.Series, col: str) -> pd.DataFrame:
        if col not in df.columns:
            return pd.DataFrame({'Period': [], 'Count': []})
        order = ['Morning', 'Mid', 'Late', 'NA']
        vc = df.loc[mask_series, col].fillna('NA').value_counts().reindex(order, fill_value=0)
        return pd.DataFrame({'Period': vc.index, 'Count': vc.values})
    
    cols = st.columns(3)
    
    # Selected target period
    if target and target.event_bar_col:
        pcol = target.event_bar_col.removesuffix('_Bar') + '_Period'
        tbl = _period_table(daily, mask, pcol)
        cols[0].markdown(f'**{target.label} Period**')
        if not tbl.empty and tbl['Count'].sum() > 0:
            cols[0].bar_chart(tbl.set_index('Period')['Count'])
        else:
            cols[0].info('No period data')
    
    # HOD and LOD periods
    for i, col_name in enumerate(['HOD_Period', 'LOD_Period'], start=1):
        tbl = _period_table(daily, mask, col_name)
        label = 'HOD Period' if col_name == 'HOD_Period' else 'LOD Period'
        cols[i].markdown(f'**{label}**')
        if not tbl.empty and tbl['Count'].sum() > 0:
            cols[i].bar_chart(tbl.set_index('Period')['Count'])
        else:
            cols[i].info('No period data')

from __future__ import annotations


def render(ctx: dict) -> None:
    import streamlit as st
    import pandas as pd
    from analytics.targets import load_targets_from_yaml, compute_target_stats
    
    daily = ctx['daily']
    mask = ctx['mask']
    
    st.subheader('Overview')
    
    # Section 1: Dataset Summary
    st.markdown('#### Dataset Summary')
    c1, c2, c3 = st.columns(3)
    c1.metric('Total Trading Days', len(daily))
    c2.metric('Filtered Sample', int(mask.sum()))
    c3.metric('Coverage', f"{(float(mask.mean()) if len(mask) else 0):.1%}")
    
    st.markdown('---')
    
    # Section 2: Baseline Event Probabilities
    st.markdown('#### Baseline Event Probabilities')
    st.caption('Probability of each event occurring across all trading days (no filters applied)')
    
    # Load targets
    targets = load_targets_from_yaml('config/target_catalog.yaml')
    baseline_mask = pd.Series(True, index=daily.index)
    
    # Key targets to display
    key_target_ids = [
        'T_GAP_CLOSE',
        'T_BULL_BO_OR12', 'T_BEAR_BO_OR12',
        'T_BULL_100_OR12', 'T_BEAR_100_OR12',
        'T_BULL_BO_OR18', 'T_BEAR_BO_OR18',
        'T_BULL_100_OR18', 'T_BEAR_100_OR18',
    ]
    
    # Compute baseline stats
    baseline_stats = []
    for tgt in targets:
        if tgt.id in key_target_ids:
            stats = compute_target_stats(daily, baseline_mask, tgt, baseline_mask)
            baseline_stats.append({
                'Event': stats['label'],
                'Group': stats['group'],
                'Probability': stats['p0'],
                'Occurrences': stats['baseline_hits'],
                'Sample Size': stats['baseline_n']
            })
    
    # Display by group
    if baseline_stats:
        df_stats = pd.DataFrame(baseline_stats)
        
        # Gap events
        gap_stats = df_stats[df_stats['Group'] == 'Gap']
        if not gap_stats.empty:
            st.markdown('**Gap Events**')
            for _, row in gap_stats.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(row['Event'])
                col2.metric('', f"{row['Probability']:.1%}" if pd.notna(row['Probability']) else 'N/A')
        
        # OR12 events
        or12_stats = df_stats[df_stats['Group'] == 'OR12']
        if not or12_stats.empty:
            st.markdown('**OR12 Events**')
            cols = st.columns(2)
            for idx, (_, row) in enumerate(or12_stats.iterrows()):
                with cols[idx % 2]:
                    st.metric(
                        row['Event'],
                        f"{row['Probability']:.1%}" if pd.notna(row['Probability']) else 'N/A',
                        delta=f"{row['Occurrences']} days"
                    )
        
        # OR18 events
        or18_stats = df_stats[df_stats['Group'] == 'OR18']
        if not or18_stats.empty:
            st.markdown('**OR18 Events**')
            cols = st.columns(2)
            for idx, (_, row) in enumerate(or18_stats.iterrows()):
                with cols[idx % 2]:
                    st.metric(
                        row['Event'],
                        f"{row['Probability']:.1%}" if pd.notna(row['Probability']) else 'N/A',
                        delta=f"{row['Occurrences']} days"
                    )
    
    st.markdown('---')
    
    # Section 3: Gap Statistics
    st.markdown('#### Gap Distribution')
    if 'Opening_Gap_Percent' in daily.columns:
        gap_col = daily['Opening_Gap_Percent']
        c1, c2, c3, c4 = st.columns(4)
        
        avg_gap = gap_col.mean() if not gap_col.isna().all() else 0
        bull_gaps = (gap_col > 0.1).sum() if not gap_col.isna().all() else 0
        bear_gaps = (gap_col < -0.1).sum() if not gap_col.isna().all() else 0
        neutral_gaps = ((gap_col >= -0.1) & (gap_col <= 0.1)).sum() if not gap_col.isna().all() else 0
        
        c1.metric('Avg Gap', f"{avg_gap:.2%}")
        c2.metric('Bull Gaps (>0.1%)', f"{bull_gaps} ({bull_gaps/len(daily):.1%})")
        c3.metric('Bear Gaps (<-0.1%)', f"{bear_gaps} ({bear_gaps/len(daily):.1%})")
        c4.metric('Neutral Gaps', f"{neutral_gaps} ({neutral_gaps/len(daily):.1%})")
    
    st.markdown('---')
    st.info('💡 Use **Query Builder** to define filter conditions, then inspect **Targets**, **Timing**, **Period**, and **Case Studies** tabs.')

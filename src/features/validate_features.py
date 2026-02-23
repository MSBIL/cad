from __future__ import annotations

from typing import Any
import pandas as pd

REQUIRED_COLUMNS = [
    'Date', 'Gap_Close_Bar', 'Bull_BO_12_Bar', 'Bull_100_12_Bar', 'Bear_BO_12_Bar', 'Bear_100_12_Bar',
    'Bull_BO_18_Bar', 'Bull_100_18_Bar', 'Bear_BO_18_Bar', 'Bear_100_18_Bar', 'HOD_Bar', 'LOD_Bar'
]
EVENT_BAR_COLUMNS = [
    'Gap_Close_Bar','Bull_BO_12_Bar','Bull_50_12_Bar','Bull_100_12_Bar','Bear_BO_12_Bar','Bear_50_12_Bar','Bear_100_12_Bar',
    'Bull_BO_18_Bar','Bull_50_18_Bar','Bull_100_18_Bar','Bear_BO_18_Bar','Bear_50_18_Bar','Bear_100_18_Bar',
    'PDH_BO_Bar','PDL_BO_Bar','GXH_BO_Bar','GXL_BO_Bar','HOD_Bar','LOD_Bar'
]

class DailyFeatureValidationError(ValueError):
    pass


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors='coerce')


def validate_daily_features(daily_df: pd.DataFrame) -> dict[str, Any]:
    """Returns dict of QA metrics + raises on critical errors."""
    errors, warnings = [], []
    missing = [c for c in REQUIRED_COLUMNS if c not in daily_df.columns]
    if missing:
        errors.append(f'Missing required columns: {missing}')
    dup_dates = None
    if 'Date' in daily_df.columns:
        dup_dates = int(pd.Series(daily_df['Date']).duplicated().sum())
        if dup_dates:
            errors.append(f'Duplicate Date rows: {dup_dates}')
    impossible = {}
    for full_col, bo_col in [('Bull_100_12_Bar','Bull_BO_12_Bar'),('Bear_100_12_Bar','Bear_BO_12_Bar'),('Bull_100_18_Bar','Bull_BO_18_Bar'),('Bear_100_18_Bar','Bear_BO_18_Bar')]:
        if full_col in daily_df.columns and bo_col in daily_df.columns:
            full = _num(daily_df[full_col]).fillna(0)
            bo = _num(daily_df[bo_col]).fillna(0)
            nbad = int(((full > 0) & (bo <= 0)).sum())
            impossible[f'{full_col}_implies_{bo_col}'] = nbad
            if nbad:
                errors.append(f'Impossible event combo ({full_col}>{0} and {bo_col}<=0): {nbad}')
    bad_ranges = {}
    for col in [c for c in EVENT_BAR_COLUMNS if c in daily_df.columns]:
        vals = _num(daily_df[col])
        nbad = int(((vals.notna()) & (vals != 0) & ((vals < 1) | (vals > 81))).sum())
        bad_ranges[col] = nbad
        if nbad:
            errors.append(f'Bars out of expected range in {col}: {nbad}')
    if 'Bar_Count' in daily_df.columns:
        bar_anoms = int((_num(daily_df['Bar_Count']) != 81).sum())
        if bar_anoms:
            warnings.append(f'Bar_Count anomalies (!=81): {bar_anoms}')
    else:
        warnings.append('Bar_Count missing; anomaly check skipped')
    null_rates = {}
    for col in [c for c in REQUIRED_COLUMNS if c in daily_df.columns]:
        r = float(pd.Series(daily_df[col]).isna().mean())
        null_rates[col] = r
        if r > 0.25:
            warnings.append(f'High null rate {col}: {r:.1%}')
    summary = {'rows': int(len(daily_df)), 'missing_required_columns': missing, 'duplicate_dates': dup_dates,
               'impossible_event_counts': impossible, 'out_of_range_event_bars': bad_ranges,
               'null_rates': null_rates, 'warnings': warnings, 'errors': errors,
               'warning_count': len(warnings), 'error_count': len(errors)}
    if errors:
        raise DailyFeatureValidationError('; '.join(errors))
    return summary

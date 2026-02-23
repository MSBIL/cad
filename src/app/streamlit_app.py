from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'src'
for p in (ROOT, SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    import streamlit as st
except Exception as exc:  # pragma: no cover
    raise RuntimeError('Install app deps: pip install -e .[app]') from exc

from analytics.filters import apply_filters
from analytics.targets import load_targets_from_yaml
from data_io.freshness import read_latest_update
from data_io.load_intraday import load_intraday
from features.validate_features import DailyFeatureValidationError, validate_daily_features
from scripts.build_daily_features import build_daily_features
from app.tabs import overview, query_builder, targets_table, timing, period, data_health, case_studies, hypothesis_lab

DEFAULT_INTRADAY = ROOT / 'data' / 'filtered_data_20250103_034327.xlsx'
DEFAULT_DAILY = ROOT / 'data' / 'daily_features.parquet'
TARGETS_YAML = ROOT / 'config' / 'target_catalog.yaml'
FRESHNESS_JSON = ROOT / 'data' / 'latest_update.json'


@st.cache_data(show_spinner="Loading daily features (first run may take 1-2 minutes)...")
def load_daily_features(path: str | None = None):
    import pandas as pd
    p = Path(path) if path else DEFAULT_DAILY
    if p.exists():
        return pd.read_parquet(p)
    intraday = load_intraday(DEFAULT_INTRADAY)
    daily = build_daily_features(intraday)
    try:
        daily.to_parquet(p, index=False)
    except Exception:
        pass
    return daily


@st.cache_data(show_spinner="Loading intraday bars...")
def load_intraday_cached(path: str | None = None):
    return load_intraday(Path(path) if path else DEFAULT_INTRADAY)


def main() -> None:
    st.set_page_config(page_title='SA2 CAD', layout='wide')
    st.title('SA2Academy CAD Dashboard')
    status = st.empty()
    status.info(
        'Initializing data. On first run, the app builds daily features from the XLSX before the sidebar appears.'
    )
    daily = load_daily_features(None)
    intraday = load_intraday_cached(None)
    status.empty()
    targets = load_targets_from_yaml(str(TARGETS_YAML))

    if 'filter_clauses' not in st.session_state:
        st.session_state.filter_clauses = []
    if 'selected_target_id' not in st.session_state and targets:
        st.session_state.selected_target_id = targets[0].id

    try:
        qa = validate_daily_features(daily)
    except DailyFeatureValidationError as exc:
        qa = {'error_count': 1, 'warning_count': 0, 'errors': [str(exc)], 'warnings': []}

    mask = apply_filters(daily, st.session_state.filter_clauses)
    st.session_state.current_mask = mask
    shared = {'daily': daily, 'intraday': intraday, 'targets': targets, 'mask': mask, 'qa': qa,
              'freshness': read_latest_update(FRESHNESS_JSON), 'root': ROOT}

    choice = st.sidebar.radio('Navigate', ['Overview','Query Builder','Targets Table','Timing','Period','Data Health','Case Studies','Hypothesis Lab'])
    if choice == 'Overview':
        overview.render(shared)
    elif choice == 'Query Builder':
        query_builder.render(shared)
    elif choice == 'Targets Table':
        targets_table.render(shared)
    elif choice == 'Timing':
        timing.render(shared)
    elif choice == 'Period':
        period.render(shared)
    elif choice == 'Data Health':
        data_health.render(shared)
    elif choice == 'Case Studies':
        case_studies.render(shared)
    else:
        hypothesis_lab.render(shared)


if __name__ == '__main__':
    main()

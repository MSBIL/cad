# ARCH.md
# Architecture & Module Plan

## Modules
- data_io/
  - load_intraday.py (read Parquet/DuckDB/XLSX)
  - write_store.py (append partitioned Parquet; update DuckDB)
  - freshness.py (latest_update.json helpers)

- features/
  - reducers.py (FIRST/LAST/MAXEVENT/PERIOD mapping)
  - build_intraday_features.py
  - build_eod_features.py
  - build_prevday_features.py
  - validate_features.py (QA checks)

- analytics/
  - filters.py (FilterClause, apply_filters)
  - targets.py (TargetCatalog, compute_target_stats)
  - ci.py (Wilson CI)
  - timing.py (histograms, survival curves)
  - hypothesis_search.py (enumerate + score + validate)

- app/
  - streamlit_app.py
  - tabs/
    - overview.py
    - query_builder.py
    - timing.py
    - period.py
    - case_studies.py
    - hypothesis_lab.py
    - data_health.py

- reports/
  - case_study_pdf.py (export)
  - templates/ (markdown templates)

## Data products
- intraday_bars (Parquet partitions)
- daily_features (Parquet + optional DuckDB)
- hypotheses/ (JSON)
- case_studies/ (PDF/MD exports)

## Lookahead policy
- separate filter groups in UI: Intraday-safe, Previous-day, Same-day EOD (research-only)
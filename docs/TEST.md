# TEST.md
# Testing Plan — Data, Feature Engineering, Probability Engine, UI

## 1. Testing principles
- Prevent silent lookahead leakage.
- Validate event sequencing and daily aggregation.
- Ensure probability computations are correct and stable.
- Provide regression protection with golden-day fixtures.

## 2. Unit tests

### 2.1 Feature reducers
Test reducers on synthetic mini-days (3–5 bars):
- FIRST returns first non-null
- LAST returns last non-null
- MAXEVENT returns max treating NaN as 0
- PERIOD_OF_BAR mapping correct at boundaries (27/28/54/55)

### 2.2 Event correctness
For each event family (OR12/OR18):
- If `Bull_100_*_Bar > 0` then `Bull_BO_*_Bar > 0` must be true.
- Ensure `Bull_50_*_Bar <= Bull_100_*_Bar` when both exist (or allow equal if same bar).
- Ensure event bars within [1..81] unless configured otherwise.

### 2.3 Gap close logic
- Gap_Close_Bar == 0 implies Gap_Closed flag is 0.
- Gap_Close_By_27 matches definition.
- Edge: close at bar 27 and bar 28 behave properly.

### 2.4 EOD buckets
- Given simple ranges, verify bucket encoding (-1/0/1) correct.
- Verify EOD_Close_to_* derived matches provided columns (if both exist).

### 2.5 Previous-day shifting
- For Date t, Prev_* equals day t-1 values.
- First day should have Prev_* = NaN.

### 2.6 Probability engine
- For a known subset, verify:
  - hits and n
  - p = hits/n
  - baseline p0 computed on full set (or defined cohort)
  - Wilson CI bounds correct (sanity tests + known values)

### 2.7 Filter parser
- Validate parsing for:
  - numeric >, <, between
  - categorical in set
  - event occurred flags
- Ensure max-3-field constraint enforced for “quick filters” mode.

## 3. Integration tests

### 3.1 Daily builder integration
- Run daily builder on a small fixture dataset.
- Confirm output columns exist and have expected dtypes.
- Confirm no duplicate dates.

### 3.2 End-to-end query
- Load daily_features fixture
- Apply filter
- Compute target table
- Ensure stable output schema and sorting.

### 3.3 Case study rendering
- For a known date:
  - chart builds without errors
  - overlay lines present
  - markers at expected bars.

## 4. Regression / golden tests
Create a `fixtures/` folder:
- `intraday_fixture.parquet` (a handful of hand-picked dates)
- `daily_expected.parquet` (expected daily features)
- `golden_stats.json` (expected probabilities for a few canonical filters)

## 5. Data QA checks (runtime)
On ingestion:
- expected bar count per day (81) or allow tolerance with warning
- Date monotonicity and duplicates
- null-rate dashboard panel:
  - missing columns
  - missing critical fields
- “impossible combinations” count

## 6. Performance tests
- Load-time benchmarks for Parquet/DuckDB
- Query-time benchmarks for:
  - common filter paths
  - hypothesis search runs
- Ensure caching is effective in Streamlit reruns.

## 7. CI Suggestions
- `pytest` + `ruff` (or `flake8`) + `mypy` optional
- run unit + integration tests on push
# TASKS.md
# Build Checklist & Agent Tasks — OR / Gap / MM Probability Dashboard

This file is designed for coding agents (Codex / Claude Code). It defines tasks, acceptance criteria, and exact interfaces.

---

## 0) Repo layout (target)
```
repo/
  app/
    streamlit_app.py
    tabs/
      overview.py
      query_builder.py
      targets_table.py
      timing.py
      period.py
      case_studies.py
      hypothesis_lab.py
      data_health.py
  analytics/
    targets.py
    filters.py
    ci.py
    timing.py
    hypothesis_search.py
  features/
    reducers.py
    build_intraday_features.py
    build_eod_features.py
    build_prevday_features.py
    validate_features.py
  data_io/
    load_intraday.py
    store.py
    freshness.py
  reports/
    case_study_pdf.py
    templates/
      case_study.md
  config/
    target_catalog.yaml
    fields.yaml
    case_templates.yaml
  fixtures/
    intraday_fixture.parquet
    daily_expected.parquet
    golden_stats.json
  scripts/
    build_daily_features.py
    ingest_daily.py
  PRD.md
  FEATURE.md
  CASE.md
  TEST.md
  ARCH.md
  CONFIG.md
  HYPOTHESIS.md
  DATA.md
  TASKS.md
  pyproject.toml (or requirements.txt)
```

---

## 1) Milestone M0 — Data contract + config scaffolding

### Task M0.1 — Create config files
**Create**
- `config/fields.yaml`
- `config/target_catalog.yaml`
- `config/case_templates.yaml`

**Acceptance**
- YAML loads without error.
- At minimum: fields include core columns from FEATURE.md.
- Targets include: Gap close, OR12/OR18 BO, 50% MM, 100% MM, HOD/LOD timing.
- Case templates include CS1–CS10 from CASE.md.

---

## 2) Milestone M1 — Data loading + reducers

### Task M1.1 — Implement intraday loader
**File:** `data_io/load_intraday.py`

**Interface**
```python
from pathlib import Path
import pandas as pd

def load_intraday(path: str | Path) -> pd.DataFrame:
    """
    Load intraday dataset from xlsx/csv/parquet.
    Must return a DataFrame with at least Date and Bar5 and OHLC columns.
    Date must be normalized to datetime.date or pandas Timestamp (no time component).
    """
```

**Acceptance**
- Loads XLSX via `pd.read_excel`.
- Loads CSV via `pd.read_csv`.
- Loads Parquet via `pd.read_parquet`.
- Ensures `Date` parsed to datetime (date).
- Ensures `Bar5` is int and sorted by (Date, Bar5).

---

### Task M1.2 — Implement reducer utilities
**File:** `features/reducers.py`

**Interface**
```python
import pandas as pd
import numpy as np

def first_nonnull(s: pd.Series):
    ...

def last_nonnull(s: pd.Series):
    ...

def maxevent(s: pd.Series) -> int:
    """Treat NaN as 0, return int max."""
    ...

def period_of_bar(bar: int) -> str:
    """Return 'Morning'/'Mid'/'Late' for 1..81, else 'NA'."""
    ...
```

**Acceptance**
- Unit tests cover boundary cases.
- `maxevent` returns 0 when all values missing/0.
- `period_of_bar` returns correct bucket at 27/28/54/55.

---

## 3) Milestone M2 — Feature layer builders

### Task M2.1 — Build daily intraday features
**File:** `features/build_intraday_features.py`

**Interface**
```python
import pandas as pd

def build_daily_intraday_features(intraday_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns one row per Date with intraday-safe daily summary.
    Must implement reducers from FEATURE.md:
    - event bars via maxevent
    - buckets via last_nonnull
    - context via first_nonnull
    - derived flags and period labels
    """
```

**Acceptance**
- Output has one row per Date.
- Output includes all columns in FEATURE.md section 2.1.*.
- Event columns use maxevent, not last().
- Derived fields computed (Gap_Closed, Gap_Not_Closed_By_27, *_Period, *_By_54).
- No duplicate Date rows.

---

### Task M2.2 — Build daily EOD features
**File:** `features/build_eod_features.py`

**Interface**
```python
import pandas as pd

def build_daily_eod_features(intraday_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns one row per Date with terminal (EOD) features.
    Prefer using provided EOD bucket columns if present, else compute from price & ranges.
    """
```

**Acceptance**
- Produces at least: EOD_Close, EOD_Close_to_OR/PD/GX/Bar18 (bucket encoding).
- Uses LAST(Close_5m) for EOD_Close.
- If bucket columns already exist in data, uses last_nonnull of those.
- If bucket columns absent, computes buckets robustly (document assumptions).

---

### Task M2.3 — Build previous-day features
**File:** `features/build_prevday_features.py`

**Interface**
```python
import pandas as pd

def build_prevday_features(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds Prev_* columns (shifted by 1 trading day) for EOD and key context features.
    """
```

**Acceptance**
- For each column listed in FEATURE.md 2.3, create Prev_* = shift(1).
- First date has Prev_* = NaN.
- Dates remain aligned and no reindexing errors.

---

### Task M2.4 — Merge into daily_features
**File:** `scripts/build_daily_features.py`

**Interface**
```python
def build_daily_features(intraday_df: pd.DataFrame) -> pd.DataFrame:
    """Build daily_intraday + daily_eod + prevday and merge on Date."""
```

**Acceptance**
- Produces a single DataFrame: `daily_features`.
- Contains layers: intraday, eod, prevday.
- Passes validation checks (next milestone).

---

## 4) Milestone M3 — Validation + QA

### Task M3.1 — Feature validation checks
**File:** `features/validate_features.py`

**Interface**
```python
import pandas as pd

def validate_daily_features(daily_df: pd.DataFrame) -> dict:
    """
    Returns dict of QA metrics + raises on critical errors.
    Critical errors: impossible event combos, missing required columns, duplicate dates.
    Non-critical: missing bar counts, high null rates -> warnings.
    """
```

**Acceptance**
- Checks:
  - Required columns exist
  - Duplicate Date rows = 0
  - If *_100_Bar > 0 then *_BO_Bar > 0
  - Bars within expected range
- Returns summary dict with counts of warnings/errors.

---

## 5) Milestone M4 — Probability engine

### Task M4.1 — Filter clauses + application
**File:** `analytics/filters.py`

**Interfaces**
```python
from dataclasses import dataclass
from typing import Any, Literal
import pandas as pd

Op = Literal["==", "!=", ">", ">=", "<", "<=", "in", "between"]

@dataclass(frozen=True)
class FilterClause:
    field: str
    op: Op
    value: Any  # scalar, list, or (low, high) tuple for between
    label: str | None = None

def apply_filters(df: pd.DataFrame, clauses: list[FilterClause]) -> pd.Series:
    """Return boolean mask."""
```

**Acceptance**
- Supports numeric ops, categorical `in`, numeric `between`.
- Handles NaNs safely (NaN -> False unless explicitly allowed).
- Unit tests cover each op.

---

### Task M4.2 — Confidence intervals
**File:** `analytics/ci.py`

**Interface**
```python
def wilson_ci(hits: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Return (low, high) in [0,1]."""
```

**Acceptance**
- Works for hits=0 and hits=n.
- Unit tests verify known values and monotonicity.

---

### Task M4.3 — Targets catalog + stats computation
**File:** `analytics/targets.py`

**Interfaces**
```python
from dataclasses import dataclass
import pandas as pd

@dataclass(frozen=True)
class Target:
    id: str
    label: str
    occurred_expr: str  # e.g., "Bull_100_12_Bar > 0"
    event_bar_col: str | None = None
    group: str | None = None

def load_targets_from_yaml(path: str) -> list[Target]:
    ...

def compute_target_stats(
    df: pd.DataFrame,
    mask: pd.Series,
    target: Target,
    baseline_mask: pd.Series | None = None
) -> dict:
    """
    Returns dict with n, hits, p, p0, lift, CI, median_bar/IQR/peak if event_bar_col exists.
    """
```

**Acceptance**
- For each target:
  - compute hits in filtered set
  - compute baseline p0 (default entire dataset or baseline_mask)
  - compute Wilson CI
  - compute timing stats when event_bar_col provided
- Outputs stable schema used by UI.

---

### Task M4.4 — Timing utilities
**File:** `analytics/timing.py`

**Interfaces**
```python
import pandas as pd

def event_bar_series(df: pd.DataFrame, mask: pd.Series, event_bar_col: str) -> pd.Series:
    """Return series of positive event bars."""
def histogram_counts(s: pd.Series, bins: list[int] | None = None) -> pd.DataFrame:
    """Return bar->count table."""
def survival_curve(s: pd.Series, max_bar: int = 81) -> pd.DataFrame:
    """Return t -> P(event <= t)."""
```

**Acceptance**
- Produces correct survival curve for synthetic tests.
- Handles empty series.

---

## 6) Milestone M5 — Streamlit v1

### Task M5.1 — App shell + caching
**File:** `app/streamlit_app.py`

**Acceptance**
- Loads daily_features with `st.cache_data`.
- Provides sidebar navigation to tabs.

### Task M5.2 — Query builder tab
**File:** `app/tabs/query_builder.py`

**Acceptance**
- UI for selecting filter clauses:
  - gap range
  - ORCL buckets
  - OR ranges
  - breakout occurred flags
  - previous-day filters separated
- Shows active filter chips and n.

### Task M5.3 — Targets table tab
**File:** `app/tabs/targets_table.py`

**Acceptance**
- Shows target stats table with sorting by probability/lift/reliability.
- Clicking a target sets selection for timing tab.

### Task M5.4 — Timing tab
**File:** `app/tabs/timing.py`

**Acceptance**
- Histogram + survival curve for selected target.
- Shows median/IQR and peak window.

### Task M5.5 — Period analysis tab
**File:** `app/tabs/period.py`

**Acceptance**
- Morning/Mid/Late breakdown for selected target and for HOD/LOD.

### Task M5.6 — Data health tab
**File:** `app/tabs/data_health.py`

**Acceptance**
- Displays freshness, QA metrics, null rates, bar-count anomalies.

---

## 7) Milestone M6 — Case studies + PDF export

### Task M6.1 — Case study browser
**File:** `app/tabs/case_studies.py`

**Acceptance**
- Shows dates matching current filters.
- Allows selection of a date.
- Renders replay candlestick chart (Plotly) with overlays:
  - OR12/OR18 lines
  - breakout + MM markers
  - gap close marker
  - HOD/LOD markers

### Task M6.2 — PDF export
**File:** `reports/case_study_pdf.py`

**Acceptance**
- Exports PDF including:
  - summary stats
  - chart image
  - key takeaways template
- Uses deterministic output name and includes metadata (date, filters).

---

## 8) Milestone M7 — Daily ingestion (“brew new data”)

### Task M7.1 — Store utilities
**File:** `data_io/store.py`

**Acceptance**
- Append intraday to partitioned Parquet.
- Append/update daily_features.
- Optionally maintain DuckDB mirror.

### Task M7.2 — Freshness marker
**File:** `data_io/freshness.py`

**Acceptance**
- Writes `latest_update.json` with:
  - last_trade_date
  - timestamp
  - data version hash

### Task M7.3 — Ingest script
**File:** `scripts/ingest_daily.py`

**Acceptance**
- CLI:
  - `python ingest_daily.py --date YYYY-MM-DD --source <path-or-connector>`
- Runs pipeline: load -> compute -> validate -> append -> update freshness.

---

## 9) Milestone M8 — Hypothesis Lab (automated discovery)

### Task M8.1 — Candidate generation
**File:** `analytics/hypothesis_search.py`

**Acceptance**
- Enumerates 1–3 clause filters from allowed fields and threshold grids.
- Enforces n>=Nmin.
- Computes score (lift, reliability).
- Returns ranked results.

### Task M8.2 — Validation split
**Acceptance**
- Supports discovery and validation date windows.
- Only promotes hypotheses that persist (same lift sign) in validation.

### Task M8.3 — Streamlit Hypothesis tab
**File:** `app/tabs/hypothesis_lab.py`

**Acceptance**
- Inputs:
  - target selection
  - allowed fields
  - max clauses (1–3)
  - min n
  - objective (max/min probability)
  - discovery/validation ranges
- Output:
  - ranked table
  - “save to library” button
  - “apply as current filter” button
  - “generate case study template” button

---

## 10) Testing tasks (must-do)

### Task T1 — Unit tests
- reducers
- filter ops
- wilson CI
- target stats (hits/n)
- survival curve

### Task T2 — Integration tests
- daily builder end-to-end on fixtures
- one representative Streamlit-free pipeline call

### Task T3 — Regression fixtures
- create `fixtures/` and `golden_stats.json`
- add `pytest` CI

---

## 11) Acceptance gates (definition of done)
- Daily builder produces stable daily_features with no critical validation errors.
- Targets table matches golden stats for fixture datasets.
- Case study replay renders without error and exports PDF.
- Hypothesis Lab can find at least 10 candidate filters with n>=100.
- No lookahead leakage: “previous-day filters” always use Prev_* columns.

---

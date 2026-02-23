# PRD.md
# Product Requirements Document — OR / Gap / MM Probability Dashboard (Streamlit)

## 1. Goal
Build a Streamlit dashboard that:
1) Computes **conditional probabilities** of intraday events (OR breakouts, measured moves, gap closes, HOD/LOD timing) under user-selected filters.
2) Presents results in CAD-like modules: **overall probability**, **timing**, **period analysis**, **case studies/replay**, and **hypothesis discovery**.
3) Supports daily ingestion (“brew new data”) and avoids lookahead bias via explicit feature layers: **Intraday**, **EOD**, **Previous Day**.

## 2. Users
- Discretionary intraday traders using event stats to set expectations.
- Researchers building/validating hypotheses and extracting case studies.
- Future: automated playbook generation for day types and traps.

## 3. Core Use Cases
### U1: Find high-probability setups
- User selects 1–3 filters (gap, ORCL buckets, OR range percent, regime proxy).
- Dashboard returns sorted target table (probability, lift vs baseline, n, confidence interval).

### U2: Find low-probability setups (“traps”)
- User selects “Minimize probability” objective or selects known trap templates.
- Dashboard returns contexts where 100% MM completion is rare with n >= threshold.

### U3: Timing suggestions (CAD-style)
- For a chosen target, show:
  - timing histogram of event bars
  - survival curve P(event by bar t)
  - period split (Morning/Mid/Late)
- Highlight “cutoffs” like bar 27 for gap close likelihood.

### U4: Case studies
- From current filters, list matching dates.
- Selecting a date renders intraday candlestick with overlays:
  - OR12/OR18 ranges, breakout points, MM hits, gap close, HOD/LOD
- Export a 1–3 page PDF report for that day.

### U5: Hypothesis generation (in-app)
- User selects target and allowable fields.
- App enumerates 1–3 clause filters under constraints (n>=100) and ranks by lift or “reliability score”.
- Split discovery/validation time windows to reduce p-hacking.

## 4. Data Inputs
### Intraday table (required)
One row per 5-minute bar.
Must include at least:
- Date, Bar5
- Open_5m, High_5m, Low_5m, Close_5m, Volume (or equivalent)
- Context columns used in filters:
  - Opening_Gap_Percent
  - ORCL_O, ORCL_PD, ORCL_GX (bucket encodings)
  - Range_12_Percent, Range_18_Percent
  - Closes_Above_EMA_5m, Closes_Below_EMA_5m (or compute)
  - PDH_BO, PDL_BO, GXH_BO, GXL_BO (event bar columns)
- Event bar columns (time-evolving):
  - Bull_BO_Hit_12, Bear_BO_Hit_12, Bull_50_Hit_12, Bull_100_Hit_12, Bear_50_Hit_12, Bear_100_Hit_12
  - Same for _18
  - Gap_Close_Bar
  - HOD_Bar, LOD_Bar

### Column dictionary (optional but recommended)
Data dictionary mapping field names to definitions.

## 5. Outputs / Data Products
- `intraday_bars` store (Parquet partitioned by year or date; optionally DuckDB)
- `daily_features` store with 3 layers:
  1) Intraday summary features (event bars, OR ranges, gap close)
  2) EOD terminal features (EOD location buckets)
  3) Previous-day features (shifted EOD and prior context)
- Saved hypothesis library: JSON files representing filter clauses + stats + validation.

## 6. Functional Requirements
### FR1: Filtering engine
- Supports:
  - numeric thresholds (>, <, between)
  - categorical selections (Above/Inside/Below)
  - event occurred flags (event_bar > 0)
- Restrict to max 3 fields for “quick filters”.
- Show active filter chips and a serialized query string.

### FR2: Probability engine
For any (filters, target):
- Return n, hits, p, baseline p0, lift (p-p0)
- Return Wilson CI (or Agresti–Coull)
- Return timing stats if target has event_bar: median, IQR, peak window
- Period breakdown: Morning/Mid/Late

### FR3: CAD suggestions module
- For selected target:
  - timing distribution and survival curve
  - highlight cutoff heuristics discovered from data (e.g., “after bar 27 chance ~ negligible”)
- Suggestions must be derived from data, not hard-coded (but can seed defaults).

### FR4: Case study module
- Filtered date list with sorting:
  - “most representative” (close to median timing)
  - “most extreme” (largest deviation)
- Candlestick chart + overlay lines and event markers.
- PDF export of case study report.

### FR5: Daily ingestion
- A batch job runs after market close:
  - fetch latest intraday
  - compute features and append stores
  - write `latest_update.json`
- Streamlit auto-refreshes based on this file.

### FR6: Lookahead guardrails
- UI separates filters into:
  - Same-day intraday-safe filters
  - Previous-day filters (safe)
  - Same-day EOD filters (research-only; warn user)

## 7. Non-Functional Requirements
- Performance: common queries render in < 1s with caching; heavy queries < 5s.
- Reproducibility: dataset version hash, pipeline version and config stored.
- Correctness: validated event sequencing and daily reduction (max/last/first rules).
- Extensibility: add new targets without rewriting code (config-driven target catalog).

## 8. UX / Information Architecture
Tabs:
1) Overview (KPIs + baseline rates)
2) Query Builder + Targets Table
3) Timing (histogram + survival)
4) Period Analysis
5) Case Studies (replay + export)
6) Hypothesis Lab (search + validation)
7) Data Freshness & QA

## 9. Milestones
- M0: Feature layer spec + daily builder
- M1: Probability engine + baseline tables
- M2: Streamlit v1 (Overview/Targets/Timing/Period)
- M3: Case studies + PDF export
- M4: Ingestion + persistence + freshness
- M5: Hypothesis Lab + validation split

## 10. Success Metrics
- User can find >= 5 actionable filters with n>=100 and lift >= 5pp.
- Case studies can be generated in < 30s and exported reliably.
- No lookahead leakage in “previous-day to today intraday” studies.
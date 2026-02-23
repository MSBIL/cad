# FEATURE.md
# Feature Spec — Intraday / EOD / Previous-Day Feature Layers

## 0. Conventions
- Bar index: `Bar5` in [1..81] for RTH (adjust if your session differs).
- Period buckets:
  - Morning = 1–27
  - Mid = 28–54
  - Late = 55–81
- Event bar columns are treated as:
  - 0 or NaN => not occurred
  - positive integer => bar index of first hit
- Bucket encoding: {-1, 0, 1}
  - -1 = Below
  - 0 = Inside
  - 1 = Above

## 1. Source tables
### 1.1 intraday_bars (input)
One row per (Date, Bar5).
Required columns (minimum):
- Date, Bar5
- Open_5m, High_5m, Low_5m, Close_5m
- Opening_Gap_Percent
- Range_12_Percent, Range_18_Percent
- ORCL_O, ORCL_PD, ORCL_GX
- Gap_Close_Bar
- Bull_BO_Hit_12, Bear_BO_Hit_12, Bull_50_Hit_12, Bull_100_Hit_12, Bear_50_Hit_12, Bear_100_Hit_12
- Bull_BO_Hit_18, Bear_BO_Hit_18, Bull_50_Hit_18, Bull_100_Hit_18, Bear_50_Hit_18, Bear_100_Hit_18
- HOD_Bar, LOD_Bar
- PDH_BO, PDL_BO, GXH_BO, GXL_BO (optional but recommended)
- Closes_Above_EMA_5m, Closes_Below_EMA_5m (optional; else compute)

### 1.2 daily_features (output)
One row per Date.
Built from 3 layers:
- daily_intraday_features
- daily_eod_features
- daily_prevday_features

## 2. Daily reduction rules (critical)
Define these reducers:
- FIRST(x): first non-null row of the day
- LAST(x): last non-null row of the day
- MAXEVENT(x): max(x) over day, treating NaN as 0; used for event bar columns
- BOOL_EVENT(x): 1 if MAXEVENT(x) > 0 else 0
- PERIOD_OF_BAR(b): Morning/Mid/Late based on b

### 2.1 Daily intraday features (same-day, intraday-safe)
These are usable for same-day conditional stats (some only after OR closes).

#### 2.1.1 Context / constants (FIRST)
- Date
- Opening_Gap_Percent = FIRST(Opening_Gap_Percent)
- Day_of_Week = FIRST(Day_of_Week) (or derive from Date)
- Day_of_Month = FIRST(Day_of_Month) (or derive)
- Range_12_Percent = FIRST(Range_12_Percent) or LAST (choose consistent)
- Range_18_Percent = FIRST(Range_18_Percent) or LAST

#### 2.1.2 OR close location buckets (LAST)
- ORCL_O = LAST(ORCL_O)
- ORCL_PD = LAST(ORCL_PD)
- ORCL_GX = LAST(ORCL_GX)
- ORCL_PD_Inside = 1 if ORCL_PD==0 else 0 (derived)
- ORCL_O_Inside = 1 if ORCL_O==0 else 0 (derived)
- ORCL_GX_Inside = 1 if ORCL_GX==0 else 0 (derived)

#### 2.1.3 Event bars (MAXEVENT)
OR12:
- Bull_BO_12_Bar = MAXEVENT(Bull_BO_Hit_12)
- Bear_BO_12_Bar = MAXEVENT(Bear_BO_Hit_12)
- Bull_50_12_Bar = MAXEVENT(Bull_50_Hit_12)
- Bull_100_12_Bar = MAXEVENT(Bull_100_Hit_12)
- Bear_50_12_Bar = MAXEVENT(Bear_50_Hit_12)
- Bear_100_12_Bar = MAXEVENT(Bear_100_Hit_12)

OR18:
- Bull_BO_18_Bar = MAXEVENT(Bull_BO_Hit_18)
- Bear_BO_18_Bar = MAXEVENT(Bear_BO_Hit_18)
- Bull_50_18_Bar = MAXEVENT(Bull_50_Hit_18)
- Bull_100_18_Bar = MAXEVENT(Bull_100_Hit_18)
- Bear_50_18_Bar = MAXEVENT(Bear_50_Hit_18)
- Bear_100_18_Bar = MAXEVENT(Bear_100_Hit_18)

Gap close:
- Gap_Close_Bar = MAXEVENT(Gap_Close_Bar)

HTF breakouts (if present):
- PDH_BO_Bar = MAXEVENT(PDH_BO)
- PDL_BO_Bar = MAXEVENT(PDL_BO)
- GXH_BO_Bar = MAXEVENT(GXH_BO)
- GXL_BO_Bar = MAXEVENT(GXL_BO)

Extremes:
- HOD_Bar = MAXEVENT(HOD_Bar) or LAST(HOD_Bar) depending on your data semantics
- LOD_Bar = MAXEVENT(LOD_Bar) or LAST(LOD_Bar)

#### 2.1.4 Derived flags + timing summaries
- Bull_BO_12 = 1 if Bull_BO_12_Bar > 0 else 0
- Bull_100_12 = 1 if Bull_100_12_Bar > 0 else 0
- Bear equivalents; OR18 equivalents
- Gap_Closed = 1 if Gap_Close_Bar > 0 else 0
- Gap_Not_Closed_By_27 = 1 if (Gap_Close_Bar==0 or Gap_Close_Bar>27) else 0

Timing periods:
- Bull_BO_12_Period = PERIOD_OF_BAR(Bull_BO_12_Bar) if occurred
- Bull_100_12_Period = PERIOD_OF_BAR(Bull_100_12_Bar) if occurred
- Gap_Close_Period = PERIOD_OF_BAR(Gap_Close_Bar) if occurred
- HOD_Period = PERIOD_OF_BAR(HOD_Bar) if occurred
- LOD_Period = PERIOD_OF_BAR(LOD_Bar) if occurred

Optional timing cutoffs (binary):
- Bull_100_12_By_54 = 1 if 0 < Bull_100_12_Bar <= 54 else 0
- Gap_Close_By_27 = 1 if 0 < Gap_Close_Bar <= 27 else 0

#### 2.1.5 Intraday regime proxies (LAST)
If you store running counts:
- Closes_Above_EMA_5m = LAST(Closes_Above_EMA_5m)
- Closes_Below_EMA_5m = LAST(Closes_Below_EMA_5m)
Derived:
- EMA_Dominance = (Closes_Above_EMA_5m - Closes_Below_EMA_5m)

---

### 2.2 Daily EOD features (same-day terminal; research-only for same-day decisions)
Computed from LAST bar of day.

- EOD_Close = LAST(Close_5m)
- EOD_Close_to_OR (bucket): compare EOD_Close to OR range (or use provided column)
- EOD_Close_to_PD (bucket)
- EOD_Close_to_GX (bucket)
- EOD_Close_to_Bar18 (bucket)
- EOD_Range = (max High_5m - min Low_5m) within day (optional)
- EOD_Direction = sign(EOD_Close - FIRST(Open_5m)) (optional)

---

### 2.3 Previous-day features (shifted EOD + prior context; safe for conditioning today)
Join prior day’s EOD onto current date.

For each Date t:
- Prev_Opening_Gap_Percent = Opening_Gap_Percent[t-1] (optional)
- Prev_ORCL_O / Prev_ORCL_PD / Prev_ORCL_GX = ORCL_*[t-1]
- Prev_EOD_Close_to_OR / PD / GX / Bar18 = EOD_Close_to_*[t-1]
- Prev_EOD_Direction = EOD_Direction[t-1]
- Prev_EOD_Range = EOD_Range[t-1]
- Prev_EMA_Dominance = EMA_Dominance[t-1]
- Prev_Bull_100_12 = Bull_100_12[t-1] (optional)
- Prev_Gap_Closed = Gap_Closed[t-1] (optional)

---

## 3. Target Catalog (v1)
Targets are config-driven entries:
- id, label, type, event_bar_col (optional), occurred_rule, timing_rule, plots

Examples:
- T_GAP_CLOSE:
  - occurred_rule: Gap_Close_Bar > 0
  - event_bar_col: Gap_Close_Bar
- T_BULL_100_OR12:
  - occurred_rule: Bull_100_12_Bar > 0
  - event_bar_col: Bull_100_12_Bar
- T_HOD_LATE:
  - occurred_rule: HOD_Bar >= 55
  - event_bar_col: HOD_Bar

---

## 4. Lookahead policy
- Intraday features: safe for same-day analysis if they are known by that bar.
- EOD features: only safe for:
  - classifying the day after the close
  - conditioning next-day outcomes using Prev_* features.
- Dashboard must label filter groups:
  - Intraday-safe
  - Previous-day
  - EOD (research-only)

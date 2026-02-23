# CASE.md
# Case Study Library (v1) — Templates + Outputs

## 0. Case Study Output Format (generated per template)
For each template:
- Summary card: name, filter clauses, sample size n, baseline p0, filtered p, lift
- Target table: key targets with p/lift/n/CI/median bar
- Timing plots: histogram + survival curve for 1–3 primary targets
- Period plot: Morning/Mid/Late breakdown
- Date picker: list matching dates (sorted by representativeness)
- Replay: candlestick + overlays + event markers
- Export: PDF report

## 1. CS1 — Large Bull Gap + Not Closed By Morning (“persistence”)
Filter:
- Opening_Gap_Percent > +0.5
- Gap_Close_Bar == 0 OR Gap_Close_Bar > 27
Primary targets:
- Gap_Close_Bar (prob + timing)
- HOD_Bar period distribution
- LOD_Bar period distribution
Notes:
- Expect low same-day gap close probability; HOD later; LOD earlier.

## 2. CS2 — Large Bear Gap + Not Closed By Morning
Filter:
- Opening_Gap_Percent < -0.5
- Gap_Close_Bar == 0 OR Gap_Close_Bar > 27
Primary targets:
- Gap close
- LOD timing (often later), HOD timing (often earlier)

## 3. CS3 — Large Bull Gap + ORCL Above Open (“gap control”)
Filter:
- Opening_Gap_Percent > +0.5
- ORCL_O == Above
Primary targets:
- Gap close
- Bull 100% MM OR12/OR18
- Late HOD probability

## 4. CS4 — Neutral Gap + OR12 Bull Breakout (“initiative day”)
Filter:
- -0.13 <= Opening_Gap_Percent <= +0.13
- Bull_BO_12_Bar > 0
Targets:
- Bull 50% / 100% OR12 completion
- HOD timing (expect late)

## 5. CS5 — Neutral Gap + OR12 Bear Breakout
Filter:
- -0.13 <= Opening_Gap_Percent <= +0.13
- Bear_BO_12_Bar > 0
Targets:
- Bear 50% / 100% completion
- LOD timing (expect late)

## 6. CS6 — Bull OR12 Breakout but 100% never hits (“failure mode”)
Filter:
- Bull_BO_12_Bar > 0
- Bull_100_12_Bar == 0
Targets:
- Alternative outcomes: Bear 50/100 OR12/OR18, HOD/LOD timing
Notes:
- Used to create “don’t assume follow-through” warnings.

## 7. CS7 — Bull OR12 Breakout and 100% hits (“success mode”)
Filter:
- Bull_BO_12_Bar > 0
- Bull_100_12_Bar > 0
Targets:
- HOD late probability
- LOD early probability

## 8. CS8 — HTF Confluence: PDH and GXH both break
Filter:
- PDH_BO_Bar > 0
- GXH_BO_Bar > 0
Targets:
- Bull 100% OR12/OR18
- HOD late

## 9. CS9 — Bull context: ORCL Above PD and Above Open
Filter:
- ORCL_PD == Above
- ORCL_O == Above
Targets:
- Bull 100% OR12/OR18
- Gap close probability
Notes:
- Use as a context classifier even without breakout constraints.

## 10. CS10 — Strong intraday dominance (EMA regime)
Filter:
- Closes_Above_EMA_5m >= 65
Targets:
- Bull 100% OR12/OR18
- HOD late; LOD early
Notes:
- Add symmetric “bear dominance” version later.

## 11. Case Study Ranking / Date Selection
Given filter subset, rank candidate dates by:
- Representativeness score = sum over primary targets of |event_bar - median_bar| normalized by IQR
- Optional: “extremeness score” = largest deviation from baseline lift

## 12. Export Template
PDF sections:
1) Setup & conditions
2) Stats table (baseline vs filtered)
3) Timing plots (bar histogram + survival)
4) Replay chart with markers
5) Notes / next steps
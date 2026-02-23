# AGENTS.md
# Agent Context for OR/Gap/MM Probability Dashboard

## Purpose
This repo is a planning and build scaffold for a Streamlit dashboard that computes
conditional probabilities of intraday events (OR breakouts, measured moves, gap
closes, HOD/LOD timing) under user-selected filters. It enforces strict lookahead
rules via separate feature layers (Intraday-safe, EOD, Previous-day).

## Primary Source Docs (read first)
- docs/PRD.md: product goals, UX, requirements, milestones.
- docs/FEATURE.md: feature definitions, reducers, lookahead policy.
- docs/TASKS.md: milestone tasks, acceptance criteria, target repo layout.
- docs/DATA.md: data assumptions, encodings, pitfalls.
- docs/CASE.md: case-study templates (CS1-CS10).
- docs/TEST.md: testing plan and QA checks.
- docs/ARCH.md: module plan and data products.
- docs/CONFIG.md: config file schemas.
- docs/HYPOTHESIS.md: hypothesis search design.

## Domain Glossary (short)
- OR12/OR18: Opening Range based on first 12/18 bars.
- MM: measured move (50%/100%).
- HOD/LOD: high/low of day.
- PDH/PDL: prior-day high/low.
- GXH/GXL: overnight or globex high/low.

## Data Contract (key facts)
- Bars are 5-minute. Bar index: Bar5 in [1..81] for RTH by default.
- Event bar columns: 0 or NaN means not occurred; positive int is first hit bar.
- Bucket encoding: -1 = Below, 0 = Inside, 1 = Above.

Intraday input table must include at least Date, Bar5, OHLC, gap, OR range, ORCL
buckets, event bar columns for OR12/OR18, Gap_Close_Bar, HOD_Bar, LOD_Bar.
See docs/FEATURE.md for the full list.

## Feature Layers and Lookahead Policy
- Intraday-safe features can be used for same-day conditioning (with bar-aware caveats).
- EOD features are research-only for same-day decisions; safe for next-day use.
- Previous-day features are shifted EOD/context and are safe for same-day use.

UI must clearly separate filter groups: Intraday-safe, Previous-day, EOD (research-only).
Never use same-day EOD for same-day prediction.

## Reducers (daily aggregation)
- FIRST: first non-null row of the day.
- LAST: last non-null row of the day.
- MAXEVENT: max of event bar columns, treating NaN as 0.
- PERIOD_OF_BAR: Morning 1-27, Mid 28-54, Late 55-81.

## Planned Modules (from docs/ARCH.md)
- data_io/: loading, store, freshness.
- features/: reducers and feature builders.
- analytics/: filters, targets, CI, timing, hypothesis search.
- app/: streamlit app + tabs.
- reports/: case study PDF generation.

## Target Repo Layout (from docs/TASKS.md)
This is the intended structure once code is implemented:
- app/, analytics/, features/, data_io/, reports/, config/, fixtures/, scripts/.
- Config files: config/fields.yaml, target_catalog.yaml, case_templates.yaml.
- Top-level docs mirrored from docs/.

## Testing Expectations (summary)
- Unit tests for reducers, filter ops, Wilson CI, target stats, survival curves.
- Integration test for daily builder on fixtures.
- Regression fixtures: intraday_fixture.parquet, daily_expected.parquet, golden_stats.json.
- QA checks for duplicates, invalid event combos, bar range, null rates.

## Case Studies
Case study templates CS1-CS10 are defined in docs/CASE.md and should be mapped to
filters and primary targets. PDF export follows the template in docs/CASE.md.

## Current State Notes
- src/ contains a Makefile and empty dependency files.
- Code scaffolding is not yet implemented; follow docs/TASKS.md for build order.

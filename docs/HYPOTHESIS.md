# HYPOTHESIS.md
# Hypothesis Lab Design

## Objective
Discover 1–3 clause filters that maximize/minimize target probability with n>=Nmin.

## Candidate clause types
- numeric: x > q, x < q, between(q1,q2)
- categorical: x in {A,B}
- event: event_bar > 0

## Threshold grids
- numeric q from quantiles {0.1..0.9} and/or domain thresholds (0.5 gap, 0.6 OR range)

## Scoring
- baseline p0, filtered p
- lift = p - p0
- reliability = lift * sqrt(n)
- optional log-odds lift

## Validation
- split by date:
  - discovery window
  - validation window
Keep hypotheses whose lift sign persists and exceeds minimum lift.
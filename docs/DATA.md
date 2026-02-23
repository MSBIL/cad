# DATA.md
# Data Assumptions & Dictionary

## Session
- 5-minute bars, Bar5 in 1..81 (RTH)
- If differs, define in config.

## Encodings
- event bar columns: 0/NaN = not occurred, positive int = bar index
- buckets: -1 Below, 0 Inside, 1 Above

## Required columns (minimum)
List the same as FEATURE.md required set.

## Optional columns
- Daily EMA streak fields (Closes_Above_EMA_Daily, Closes_Below_EMA_Daily)
- EOD bucket fields if already computed

## Known pitfalls
- Do not use groupby(last) for event columns; use max.
- Same-day EOD features must not be used for same-day predictions (lookahead).
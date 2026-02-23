# SA2Academy CAD (OR / Gap / MM Probability Dashboard)

This repository contains the data pipeline and application scaffolding for an intraday research dashboard focused on:

- Opening gap behavior
- OR12 / OR18 breakouts
- 50% / 100% measured-move outcomes
- HOD / LOD timing statistics
- Case-study and hypothesis-driven workflow (planned)

The project is spec-driven. Core requirements and task breakdown live in `docs/`.

## Project Layout

- `src/`: Python source code (`data_io/`, `features/`, later `analytics/`, `app/`, `reports/`)
- `config/`: YAML configuration (fields, targets, case-study templates)
- `data/`: local datasets / fixtures (raw or exported files)
- `docs/`: architecture, feature, config, test, and task specifications
- `tests/`: unit/integration tests
- `figs/`: reference images and UI mockups

## Current Status

Implemented so far:

- Config scaffolding (`config/*.yaml`)
- Intraday loader (`src/data_io/load_intraday.py`)
- Reducers (`src/features/reducers.py`)
- Daily intraday feature builder (`src/features/build_intraday_features.py`)
- Daily EOD feature builder (`src/features/build_eod_features.py`)

See `docs/TASKS.md` for milestone tracking and acceptance criteria.

## Requirements

- Python 3.9+
- Windows / macOS / Linux (developed on Windows)

## Installation (Recommended)

Create a virtual environment and install in editable mode:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[dev]
```

Optional app dependencies (for future Streamlit UI work):

```powershell
pip install -e .[app]
```

Install everything:

```powershell
pip install -e .[dev,app]
```

## Quick Smoke Test (Current Pipeline)

Run a simple end-to-end load + feature build against the provided sample workbook:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path("src").resolve()))

from data_io.load_intraday import load_intraday
from features.build_intraday_features import build_daily_intraday_features
from features.build_eod_features import build_daily_eod_features

# Example local file included in this repo
df = load_intraday("data/filtered_data_20250103_034327.xlsx")
daily_intraday = build_daily_intraday_features(df)
daily_eod = build_daily_eod_features(df)

print(len(df), len(daily_intraday), len(daily_eod))
print(daily_intraday.columns[:10].tolist())
print(daily_eod.head(1).to_dict(orient="records")[0])
```

## Running Tests

```powershell
pytest -q
```

Note: `tests/conftest.py` adds `src/` to `sys.path`, so package imports work with the `src` layout.

## Data Expectations

The intraday input is expected to contain (minimum):

- `Date`, `Bar5`
- `Open_5m`, `High_5m`, `Low_5m`, `Close_5m`
- Gap / OR / MM event columns defined in `docs/FEATURE.md`

Supported loader formats:

- `.xlsx` / `.xls`
- `.csv`
- `.parquet`

## Documentation Map

- `docs/ARCH.md`: module architecture and data products
- `docs/FEATURE.md`: feature definitions and reducers
- `docs/CONFIG.md`: YAML config schemas
- `docs/TASKS.md`: implementation tasks and acceptance criteria
- `docs/TEST.md`: testing strategy
- `docs/PRD.md`: product requirements and UI goals

## Development Notes

- Source code belongs under `src/`
- Keep docs/specs at repo root under `docs/`
- Prefer adding tests for reducers, feature builders, and analytics utilities as milestones progress
- Avoid lookahead leakage: use `Prev_*` features for next-day conditioning

## Next Planned Modules

- `src/features/build_prevday_features.py`
- `src/features/validate_features.py`
- `src/analytics/*` (filters, CI, targets, timing)
- `src/app/*` (Streamlit UI)

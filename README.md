# SA2Academy CAD (OR / Gap / MM Probability Dashboard)

## Overview

SA2Academy CAD is an intraday research dashboard and analytics pipeline for studying conditional probabilities of:

- Opening gap closes
- OR12 / OR18 breakouts
- 50% / 100% measured moves
- HOD / LOD timing behavior
- Case-study driven setups

The project is spec-driven. Product, feature, architecture, and milestone requirements live in `docs/`.

## Status

Current implementation covers the milestone path through **M6 (Case studies + PDF export)** in `docs/TASKS.md`, including:

- Config scaffolding (`config/*.yaml`)
- Intraday loader (`data_io/load_intraday.py`)
- Feature reducers and daily builders (`features/*`)
- Validation checks (`features/validate_features.py`)
- Probability engine (`analytics/*`)
- Streamlit app shell + tabs (`app/*`)
- Case-study replay + PDF export (`reports/*`)

## Repository Layout

This repo follows the target layout in `docs/TASKS.md`:

- `app/`: Streamlit app and tabs
- `analytics/`: filters, CI, timing, target stats
- `features/`: daily feature builders and validation
- `data_io/`: loading and freshness helpers
- `reports/`: case-study PDF export and templates
- `scripts/`: pipeline scripts (e.g. daily feature build)
- `config/`: YAML configuration (fields, targets, case templates)
- `data/`: local datasets and generated local feature parquet
- `docs/`: specifications (PRD, ARCH, TASKS, FEATURE, etc.)
- `tests/`: unit and integration tests
- `figs/`: reference images/mockups

## Requirements

- Python `>=3.9`
- Windows/macOS/Linux (development and verification were done on Windows)

## Dependencies

### Core Dependencies

Defined in `pyproject.toml`:

- `pandas`
- `numpy`
- `pyyaml`
- `openpyxl`
- `pyarrow`

### Optional Dependencies

- `dev`: `pytest`, `ruff`
- `app`: `streamlit`, `plotly`

Install all project + dev + app dependencies:

```powershell
pip install -e .[dev,app]
```

## Installation

Recommended setup (virtual environment):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[dev,app]
```

If you only need the data pipeline (no Streamlit UI):

```powershell
pip install -e .[dev]
```

## How To Run Streamlit

Run the app from the repository root:

```powershell
python -m streamlit run app/streamlit_app.py
```

Optional headless mode (useful for local testing):

```powershell
python -m streamlit run app/streamlit_app.py --server.headless true --server.port 8501
```

Then open:

- `http://127.0.0.1:8501`

### First-Run Behavior

On first run, the app may take time to parse the sample XLSX and build `data/daily_features.parquet`. During this step, the UI shows a loading message before the sidebar/tabs appear.

## How To Run the Pipeline (CLI)

Build daily features from an intraday file:

```powershell
python scripts/build_daily_features.py --input data/filtered_data_20250103_034327.xlsx
```

Default output:

- `data/daily_features.parquet`

## Quick Smoke Test (Python)

```python
from data_io.load_intraday import load_intraday
from scripts.build_daily_features import build_daily_features

intraday = load_intraday("data/filtered_data_20250103_034327.xlsx")
daily = build_daily_features(intraday)

print(len(intraday), len(daily))
print(daily.columns[:10].tolist())
```

## Running Tests

Standard run:

```powershell
pytest -q
```

If your Python environment has broken global pytest plugins (see Known Issues below), disable plugin autoload:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
pytest -q
```

Notes:

- `tests/conftest.py` adds the repo root to `sys.path` for local imports.
- Current verified test set includes reducers, filters, Wilson CI, timing, target stats, and daily pipeline integration.

## Data Expectations

Minimum intraday fields:

- `Date`, `Bar5`
- `Open_5m`, `High_5m`, `Low_5m`, `Close_5m`
- Gap/OR/MM event columns described in `docs/FEATURE.md`

Supported loader formats:

- `.xlsx` / `.xls`
- `.csv`
- `.parquet`

## Documentation

Primary specs:

- `docs/TASKS.md` (milestones + acceptance criteria)
- `docs/FEATURE.md` (feature definitions + reducers)
- `docs/ARCH.md` (module structure and data products)
- `docs/PRD.md` (product requirements)
- `docs/CASE.md` (case study templates)
- `docs/TEST.md` (testing strategy)
- `docs/CONFIG.md` (YAML config schemas)
- `docs/DATA.md` (data assumptions and pitfalls)

## Known Issues / Troubleshooting

### 1) `ImportError: DLL load failed while importing _ssl` (Windows / Anaconda)

Observed in this project environment.

Symptoms:

- `python -m streamlit ...` fails
- `pip` HTTPS access fails
- `import ssl` fails

Cause:

- Anaconda OpenSSL DLLs are not available on `PATH`
- Broken PowerShell profile may point to a non-existent `miniconda3` install

Fix:

- Ensure `C:\Users\msbil\anaconda3\Library\bin` is on `PATH`
- Fix PowerShell profile conda init path
- Verify with:

```powershell
python -c "import ssl; print(ssl.OPENSSL_VERSION)"
```

### 2) Streamlit page shows only title at startup

Observed on first run before `daily_features` parquet exists.

Cause:

- The app builds daily features from the sample XLSX before creating the sidebar tabs.

Expected behavior:

- A loading message appears while data initializes.
- Subsequent loads are faster after `data/daily_features.parquet` is created.

### 3) `pytest` fails due to unrelated global plugins / `ssl`

Observed when `pytest` autoloaded external plugins (e.g. `anyio`) in a broken Python environment.

Workaround:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
pytest -q
```

## Development Notes

- Keep the repo layout aligned with `docs/TASKS.md`
- Avoid lookahead leakage: same-day EOD features should not be used for same-day prediction
- Prefer adding tests when introducing analytics or feature logic changes
- Case-study templates in `config/case_templates.yaml` should stay aligned with `docs/CASE.md`

## License

Proprietary / internal use (see `pyproject.toml`).

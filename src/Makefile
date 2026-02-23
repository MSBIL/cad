SHELL := /bin/bash

PY ?= python
PIP ?= pip
APP ?= app/streamlit_app.py

.PHONY: help venv install install-dev run test cov lint format typecheck clean

help:
	@echo "Targets:"
	@echo "  make install       Install runtime dependencies"
	@echo "  make install-dev   Install runtime + dev dependencies"
	@echo "  make run           Run Streamlit app"
	@echo "  make test          Run tests"
	@echo "  make cov           Run tests with coverage"
	@echo "  make lint          Ruff lint"
	@echo "  make format        Ruff format"
	@echo "  make typecheck     Mypy typecheck"
	@echo "  make clean         Remove caches/build artifacts"

venv:
	@$(PY) -m venv .venv
	@echo "Activated with: source .venv/bin/activate"

install:
	@$(PIP) install -r requirements.txt

install-dev:
	@$(PIP) install -r requirements.txt
	@$(PIP) install -r requirements-dev.txt

run:
	@streamlit run $(APP)

test:
	@pytest

cov:
	@pytest --cov=app --cov=analytics --cov=features --cov=data_io --cov=reports --cov-report=term-missing

lint:
	@ruff check .

format:
	@ruff format .

typecheck:
	@mypy .

clean:
	@rm -rf .pytest_cache .ruff_cache .mypy_cache dist build **/__pycache__
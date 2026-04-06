# IBNR Reserving Tool

Production-conscious Streamlit app for **Accident Year** non-life reserving using `chainladder`.

## Features

- CSV/Excel upload + demo dataset from `chainladder.load_sample('genins')`
- Explicit column mapping and robust validation
- Accident Year triangle construction (no Underwriting Year support)
- Chain Ladder reserving outputs (AY reserves, total IBNR, LDFs)
- ODP Bootstrap uncertainty outputs (distribution, percentiles)
- Diagnostics: heatmaps, origin trends, calendar-year heuristic checks
- Link ratio outlier guidance + manual exclusion-aware factor selection
- JSON audit/context generation for reproducibility and AI usage
- AI assistant/reporting via OpenAI-compatible API with graceful fallback if no API key

## Project structure

- `app.py` - Streamlit app
- `src/` - ingestion, validation, triangle, reserving, diagnostics, AI context, AI assistant, reporting
- `tests/` - pytest automated tests
- `sample_outputs/` - output JSON artifacts
- `docs/` - validation notes

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run app

```bash
streamlit run app.py
```

## Test

```bash
pytest -q
```

## AI configuration

Set environment variables:

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-4o-mini"
```

If `OPENAI_API_KEY` is missing, AI features are disabled with a clear message; core reserving still works.

## Validation reference

A key calculation path is validated against the documented `genins` Chain Ladder example from the chainladder ecosystem (see `docs/validation.md`).


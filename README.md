# Solution Lab Refactor

A cleaned-up, runnable refactor of the original `solution-lab` concept.

## What changed

- Removed placeholder async endpoint that returned 501.
- Replaced vague stubs with deterministic, typed agents.
- Added a real orchestration loop with convergence handling.
- Added tests for the runner and FastAPI endpoints.
- Tightened API and configuration defaults.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

## Test

```bash
pytest
```

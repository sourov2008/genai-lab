# ClauseDesk

Quoted, verified, human-reviewed contract clause extraction. Not legal advice.

This repository is a scaffold. FastAPI (`app/main.py`), Pydantic Settings (`app/core/config.py`), and the async SQLAlchemy session (`app/db/session.py`) are filled in later labs.

## Layout

```text
app/           application package
  core/        global settings
  db/          database engine and session
  models/      SQLAlchemy models
  schemas/     Pydantic DTOs
  routers/     HTTP endpoints
  services/    business logic
  llm/         provider adapters
  prompts/     prompt files
tests/         unit and integration tests
scripts/       helpers (for example CUAD loaders)
```

## Local setup

```bash
cp .env.example .env
docker compose up -d
```

Install Python dependencies after the environment file is filled in:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

The API entrypoint is added in Part F.2.

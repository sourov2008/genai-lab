# ClauseDesk: Contract clause extraction with verified citations.

ClauseDesk reads English commercial contracts, extracts a fixed set of clause types, and keeps every result tied to a source quote. Code verifies citations; a human reviews what counts. This is not a chatbot and not a drafting tool.

**Current status:** backend skeleton, SQLAlchemy models, async Alembic migrations, and a CUAD seed loader. LLM extraction starts next week.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop

## Setup

1. Clone the repository and enter the project folder:

```bash
cd clausedesk
```

2. Create a local environment file:

```bash
cp .env.example .env
```

Match `DATABASE_URL` to the Postgres service in `docker-compose.yml` (user `postgres`, password `postgres`, database `clausedesk`) unless you change those values.

3. Create and activate a virtual environment, then install dependencies:

```bash
uv venv
source .venv/bin/activate
uv sync
```

4. Start Postgres:

```bash
docker compose up -d db
```

5. Apply migrations:

```bash
alembic upgrade head
```

6. Seed 50 unique CUAD contracts (idempotent):

```bash
python scripts/load_cuad.py
```

7. Run the API:

```bash
uvicorn app.main:app --reload
```

## Verify

- Health: [http://localhost:8000/health](http://localhost:8000/health) — expect `{"status": "ok", "db": "ok"}`
- Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Project structure

```text
app/
  core/        settings and shared config
  db/          async SQLAlchemy engine and sessions
  models/      persistence (User, Contract, Clause, PromptRun)
  schemas/     Pydantic request/response DTOs (next)
  routers/     HTTP endpoints only
  services/    business logic (extraction, verification, review)
  llm/         provider adapters (not implemented yet)
  prompts/     versioned prompt files (not implemented yet)
alembic/       async migrations
scripts/       CUAD loader and other helpers
tests/         unit and integration tests
```

Dependency flow is one-way: `routers` → `services` → `models` / `db` / `llm`. `core` is used by all layers.

## Disclaimer

Not legal advice. Extracted data requires human review.

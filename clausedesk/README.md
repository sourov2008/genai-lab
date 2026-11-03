# ClauseDesk: Contract clause extraction with verified citations.

ClauseDesk reads English commercial contracts, extracts a fixed set of clause types, and keeps every result tied to a source quote. Code verifies citations; a human reviews what counts. This is not a chatbot and not a drafting tool.

**Current status:** backend skeleton, SQLAlchemy models, async Alembic migrations, CUAD seed loader, and a Docker Compose stack for Postgres plus the API.

## Prerequisites

- Docker Desktop
- Python 3.12+ and [uv](https://docs.astral.sh/uv/) (only for host-machine development)

## Quick Start (Docker)

1. Clone the repository and enter the project folder:

```bash
cd clausedesk
```

2. Create a local environment file:

```bash
cp .env.example .env
```

3. Build and start the stack:

```bash
docker compose up -d --build
```

This single command starts Postgres and the FastAPI app. The API container waits until the database is healthy, then runs Alembic migrations (`alembic upgrade head`) before serving the API.

## Seeding Data

The database starts empty after Compose comes up. To load CUAD sample contracts into the API container:

```bash
docker compose exec api python scripts/load_cuad.py
```

## Verify

- Health: [http://localhost:8000/health](http://localhost:8000/health) — expect `{"status": "ok", "db": "ok"}`
- Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## API Endpoints

`POST /contracts/{contract_id}/extract` runs LLM extraction on an uploaded contract. It looks for the eight supported clause types: `termination`, `liability_cap`, `governing_law`, `payment_terms`, `confidentiality`, `ip_ownership`, `renewal`, and `non_compete`. The call requires a configured LLM provider (`LLM_PROVIDER=openai` or `LLM_PROVIDER=groq`) with a valid API key in `.env`.

Interactive OpenAPI docs for this and other routes: [http://localhost:8000/docs](http://localhost:8000/docs).

## Prompt Versioning & A/B Testing

Extraction prompts live in versioned files under `prompts/`:

- `prompts/extract_v1.md`
- `prompts/extract_v2.md`

Switch the active version with `PROMPT_VERSION` in `.env`. Use `PROMPT_VERSION=v1` or `PROMPT_VERSION=v2` (the loader reads `prompts/extract_{version}.md`). Restart the API after changing the variable so the new prompt is used on the next extract call.

## Local Development (without Docker)

Use this when you want uvicorn on the host and Postgres in Docker.

1. Create and activate a virtual environment, then install dependencies:

```bash
uv venv
source .venv/bin/activate
uv sync
```

2. Start Postgres only:

```bash
docker compose up -d db
```

3. Point `DATABASE_URL` in `.env` at localhost (user `postgres`, password `postgres`, database `clausedesk`), matching `docker-compose.yml` unless you change those values.

4. Apply migrations:

```bash
alembic upgrade head
```

5. Seed 50 unique CUAD contracts (idempotent):

```bash
python scripts/load_cuad.py
```

6. Run the API:

```bash
uvicorn app.main:app --reload
```

## Running Tests

Tests use an in-memory SQLite database and run independently of Docker. From the `clausedesk` directory, with the virtualenv activated:

```bash
pytest tests/ -v
```

## Project structure

```text
app/
  core/        settings and shared config
  db/          async SQLAlchemy engine and sessions
  models/      persistence (User, Contract, Clause, PromptRun)
  schemas/     Pydantic request/response DTOs
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

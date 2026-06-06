# AI Agent Instructions for capstone-backend

> **Workspace context**: This is part of a multi-project workspace. See root [AGENTS.md](../AGENTS.md) for overall architecture, data flow, and startup order.

## Role

FastAPI backend for receiving ElastAlert webhooks, storing incidents/raw logs, running LLM incident analysis, generating response plans, indexing RAG playbooks, and serving dashboard APIs.

## Environment and commands

- Package manager is `uv`, but agents must not run `uv sync`, `uv add`, `uv pip install`, or other dependency install/sync commands. If dependency work is needed, tell the user the exact command to run.
- Use the project interpreter directly for agent-run Python commands: `.venv/bin/python ...`.
- Runtime requires Python 3.11+ (`.python-version` is `3.11`; `pyproject.toml` says `>=3.11`).
- Run the API locally without `uv`: `.venv/bin/python -m uvicorn app.main:app --reload`.
- Run workers locally without `uv` when needed:
  - `.venv/bin/python -m app.workers.incident_agent_worker`
  - `.venv/bin/python -m app.workers.response_plan_agent_worker`
- Playbook indexing script: `.venv/bin/python -m app.scripts.index_playbooks --dry-run` before real indexing.
- Local API docs check: `http://127.0.0.1:8000/docs`.
- Standalone sample-log exercise: `.venv/bin/python run_samples_test.py`; it expects `sample_logs/*.log` and real LLM/DB env.

## Local services and env

- Copy `.env.example` to `.env`; `Settings` loads only `.env` via `pydantic-settings`.
- Required DB/auth envs include `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `SECRET_KEY`. Defaults include `DB_HOST=localhost`, `DB_PORT=3306`, `ALGORITHM=HS256`, `ACCESS_TOKEN_EXPIRE_MINUTES=30`.
- DB URL is always PostgreSQL (`postgresql://...`) even though the app default port is `3306`; `.env.example` and Docker Compose use `5432`.
- Docker Compose uses `pgvector/pgvector:pg16` on `${DB_PORT}:5432`; data persists under gitignored `postgres_data/`.
- LLM provider is selected by `LLM_PROVIDER`. Code supports aliases including `gemini`, `anthropic`/`claude`, and `openai`/`gpt`, plus the matching API key.
- RAG embeddings use `RAG_EMBEDDING_MODEL`; current pgvector playbook chunks expect 1536-dimensional embeddings.
- Expo push notifications use `EXPO_PUSH_ENABLED`, `EXPO_PUSH_URL`, optional `EXPO_PUSH_ACCESS_TOKEN`, and `EXPO_PUSH_REQUEST_TIMEOUT_SECONDS`; completed response plans notify active `push_tokens` rows when enabled.

## Architecture map

- FastAPI entrypoint is `app.main:app`; `create_app()` wires DI, calls `db.create_database()`, and includes `/webhook`, `/incidents`, `/playbooks`, response-plan routes, and `/push-tokens`.
- CORS in `app/main.py` allows only `http://localhost:8081` and `http://127.0.0.1:8081`.
- DI lives in `app/core/container.py`:
  - singleton `Database`
  - singleton `IncidentAgent` as `threat_agent`
  - singleton `ResponsePlanAgent`
  - factory services for playbooks, incidents, raw logs, reports, response plans, actions, action execution, push tokens, push notifications, and AI invocation.
- SQLAlchemy `Base` and session context manager live in `app/core/database.py`; service methods should use `with self.session_factory() as db` so rollback/close behavior is preserved.
- Workers poll persisted incidents/response-plan state and invoke agents outside the webhook request path.
- RAG playbooks live in `playbooks/*.md` and are indexed into `rag_playbooks` / `rag_playbook_chunks` tables by `app.scripts.index_playbooks`.

## Webhook contract

- Canonical endpoint is `POST /webhook`.
- `WebhookAlertRequest` requires `alert_name` and `severity`.
- It accepts normalized `logs[]` entries and also ElastAlert-style `title`, `rule_name`, `timestamp`, and `log_message` fields.
- `logs` defaults to an empty list; ElastAlert rules usually provide `timestamp`/`log_message` plus static `alert_name`/`severity`.

## MCP integrations

- Elasticsearch MCP settings: `ELASTICSEARCH_MCP_ENABLED`, `ELASTICSEARCH_MCP_URL`, `ELASTICSEARCH_MCP_ALLOWED_INDEX_PATTERN`, `ELASTICSEARCH_MCP_SERVICE_VALUE`, `ELASTICSEARCH_MCP_MAX_RESULTS`, `ELASTICSEARCH_MCP_LOOKBACK_MINUTES`, `ELASTICSEARCH_MCP_REQUEST_TIMEOUT_SECONDS`.
- Victim MCP settings: `VICTIM_MCP_URL`, `VICTIM_MCP_REQUEST_TIMEOUT_SECONDS`, `VICTIM_MCP_MAX_RESULT_CHARS`.
- Victim MCP uses exactly one server from `VICTIM_MCP_URL`; response-plan generation binds dynamically discovered MCP tools for tool-call proposals, and approved tools execute later by resuming the checkpointed LangGraph thread. Tool/MCP invocation performs schema and runtime validation.
- Only the Elasticsearch MCP integration is gated by a default-disabled `ELASTICSEARCH_MCP_ENABLED` flag. Victim MCP is always available through `VICTIM_MCP_URL`.

## Database and migrations

- Alembic scripts live in `migrations/`; run Alembic through `.venv/bin/python -m alembic ...`, not `uv run alembic`.
- `migrations/env.py` sets `sqlalchemy.url` from `app.core.config.settings.db_url` and imports all current SQLAlchemy models for autogenerate metadata.
- New SQLAlchemy models must be exported from `app/models/__init__.py` and imported by `migrations/env.py`, or Alembic autogenerate will miss them.
- App startup still calls `Base.metadata.create_all()`; do not treat that as a substitute for checked migration files.
- Carefully review autogenerated migrations: LangGraph/PostgresSaver checkpoint tables and other non-model tables may be present and should not be dropped accidentally.

## Verification notes

- Pyright is the only configured checker in `pyproject.toml`; it is configured for `.venv` and `extraPaths = ["./app"]`.
- No CI workflow, pre-commit config, pytest config, Ruff config, Makefile, tox, or nox config is present. Do not invent those commands as repo standards.
- `run_samples_test.py` is a manual integration script, not a pytest suite; it may call external LLM APIs and the database.

# TASK-005 evidence

No real-credential smoke run is recorded in this repository. When the opt-in
smoke procedure is run, append the date, Compose health/bootstrap result, two
ingestion exit statuses and summaries, and the collection count/ID comparison
that demonstrates no duplicate corpus.

## TASK-005 automated validation evidence

Executed from the repository root on 2026-09-01:

- `python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90`
  — PASS: 113 passed, 2 skipped; total coverage 96.44%.
- `$env:RUN_PGVECTOR_INTEGRATION='1'; python -m pytest tests/integration/test_pgvector_persistence.py -m pgvect_integration`
  — PASS: 1 passed. Docker Compose started the disposable PostgreSQL/pgVector
  service, seeded twelve 1536-dimensional documents, retrieved the ten
  relevance-ordered records through the Wave 2 adapter, and cleaned up the
  isolated resources.
- `python -c "import src.search; import src.chat"` — PASS.
- `docker compose -f tests/integration/compose.yaml config` — PASS.

The integration run used only deterministic local embeddings and a test key;
no OpenAI credential or persistent `postgres_data` volume was used.

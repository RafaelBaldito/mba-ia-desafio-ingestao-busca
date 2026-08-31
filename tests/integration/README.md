# Wave 1 integration and smoke validation

The pgVector integration test is opt-in and uses a unique Compose project,
database, network, and volume for each test invocation. It never uses the
persistent `postgres_data` volume or the operator's `DATABASE_URL`.

Run the deterministic suite as usual:

```powershell
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=90
```

Run the isolated database contract test only when Docker is available:

```powershell
$env:RUN_PGVECTOR_INTEGRATION = '1'
python -m pytest tests/integration/test_pgvector_persistence.py
```

The fixture waits for PostgreSQL health, runs the vector-extension bootstrap,
verifies the extension, and always executes `docker compose down --volumes`
cleanup. The application endpoint is supplied by the fixture's test settings,
not by a Compose literal.

Validate the isolated definition with:

```powershell
docker compose -f tests/integration/compose.yaml config
```

## Opt-in two-run smoke procedure

With operator-supplied credentials and the repository's `document.pdf`, first
start the existing Compose service and wait for health/bootstrap completion:

```powershell
docker compose up -d --wait postgres
docker compose run --rm bootstrap_vector_ext
python src/ingest.py
python src/ingest.py
```

Record both exit statuses and safe success summaries. Verify through the
configured collection that the second run has the same chunk count and no
duplicate IDs. Record the health/bootstrap output and the no-duplicate query
evidence in [EVIDENCE.md](EVIDENCE.md). This smoke is optional and does not
replace the automated test.

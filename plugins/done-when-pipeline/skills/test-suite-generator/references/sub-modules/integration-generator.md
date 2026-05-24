# Sub-step 4-C: Integration test generator

**Goal:** turn each `behavior.integration_tests` entry into multi-module tests that hit real services via testcontainers — no mocks.

**Output:** `tests/<feature>/integration/test_<flow>.<ext>` plus optionally a `conftest.py` (Python) / `setup.ts` (TS) that defines the container fixtures.

---

## Why no mocks (re-read before each integration test you generate)

Mocks hide interface drift. AI-generated code's #1 failure mode is "the function exists, the test passes, but the caller expected a different field name / type / serialization". A mock returns whatever you told it to return — including the wrong thing — and the integration test passes anyway.

testcontainers spins up a real Postgres / Redis / Kafka / SMTP-mock in Docker, runs the test against it, and shuts down. Cost: 5-20s per container startup; modules with shared fixtures amortize this.

If a service is genuinely external and uncontainerizable (Stripe production API, AWS, etc.), use the vendor's official sandbox endpoint, not a hand-rolled mock. WireMock with recorded responses is an acceptable middle ground if no sandbox exists.

---

## The fixture (Python, postgres example)

```python
# tests/<feature>/integration/conftest.py
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_url():
    with PostgresContainer("postgres:16-alpine") as pg:
        # apply migrations
        from src.db.migrate import migrate
        migrate(pg.get_connection_url())
        yield pg.get_connection_url()

@pytest.fixture
def db(postgres_url):
    from src.db import Session, reset_data
    s = Session(postgres_url)
    yield s
    reset_data(s)        # truncate between tests; do not drop schema
```

`scope="session"` is critical — container startup is slow; sharing across tests is the whole point.

---

## Example-based integration test (per WHEN-THEN flow)

```python
def test_cancel_api_returns_200_and_correct_payload(db, http_client):
    """REQ-001: WHEN POST /api/subscription/cancel → 200 + correct payload."""
    sub = create_active_subscription_via_api(http_client)
    resp = http_client.post(f"/api/subscription/cancel", json={"id": sub["id"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "cancelled_active"
    assert "end_date" in body
    # And the DB actually reflects this:
    row = db.execute("SELECT status FROM subscription WHERE id = %s", [sub["id"]]).fetchone()
    assert row[0] == "cancelled_active"
```

Notes:
- Assert at **both** the API boundary AND the DB. If they disagree, you have a serialization bug — exactly the boundary issue this layer is meant to catch.
- Use the real HTTP client (`httpx`, `supertest`, etc.) against the running app, not call the handler function directly.

---

## Cross-module side-effect test

For REQs that span multiple modules ("cancel triggers email AND stops billing AND ..."):

```python
def test_cancel_triggers_confirmation_email_and_stops_billing(db, http_client, smtp_mock):
    sub = create_active_subscription_via_api(http_client)
    http_client.post("/api/subscription/cancel", json={"id": sub["id"]})

    # Side effect 1: email
    assert smtp_mock.message_count() == 1
    assert "cancellation" in smtp_mock.latest().subject

    # Side effect 2: no future scheduled charges
    future_charges = db.execute(
      "SELECT count(*) FROM charges WHERE subscription_id = %s AND scheduled_for > now()",
      [sub["id"]]
    ).fetchone()
    assert future_charges[0] == 0

    # Side effect 3: access still works
    me = http_client.get("/api/me/access")
    assert me.json()["premium"] is True   # still has access — REQ-002
```

This single test crosses 3 modules. If any one is wired wrong, this catches it.

---

## Cross-module PBT (atomicity, state-machine)

For `property_type: invariant` or `state_machine` entries in `integration_tests.property_based`:

```python
from hypothesis import given, strategies as st, settings
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant

class SubscriptionWorkflowStateMachine(RuleBasedStateMachine):
    """REQ-001/002/004/006: state machine across API + DB + access layer."""

    def __init__(self):
        super().__init__()
        self.http = make_http_client()
        self.db = make_db_session()
        self.sub = create_active_subscription_via_api(self.http)

    @rule()
    def cancel(self):
        self.http.post("/api/subscription/cancel", json={"id": self.sub["id"]})

    @rule()
    def reactivate(self):
        status = self.current_status()
        if status == "cancelled_active":
            self.http.post("/api/subscription/reactivate", json={"id": self.sub["id"]})

    @invariant()
    def status_in_db_matches_api(self):
        api_status = self.http.get(f"/api/subscription/{self.sub['id']}").json()["status"]
        db_status = self.db.execute(
          "SELECT status FROM subscription WHERE id = %s", [self.sub["id"]]
        ).fetchone()[0]
        assert api_status == db_status, f"drift: api={api_status} db={db_status}"

    @invariant()
    def no_negative_balance_after_charges(self):
        balance = self.db.execute(...).fetchone()[0]
        assert balance >= 0

TestSubscriptionWorkflow = SubscriptionWorkflowStateMachine.TestCase
```

This is the highest-ROI integration test you can write — it explores combinations of cancel/reactivate/charge that example tests will never enumerate.

---

## TypeScript equivalent (vitest + testcontainers + fast-check)

```typescript
import { test, beforeAll, afterAll, expect } from 'vitest';
import { PostgreSqlContainer, StartedPostgreSqlContainer } from '@testcontainers/postgresql';
import { migrate } from '../../src/db/migrate';
import { makeApp } from '../../src/app';
import request from 'supertest';

let pg: StartedPostgreSqlContainer;
let app: ReturnType<typeof makeApp>;

beforeAll(async () => {
  pg = await new PostgreSqlContainer('postgres:16-alpine').start();
  await migrate(pg.getConnectionUri());
  app = makeApp({ dbUri: pg.getConnectionUri() });
}, 60_000);

afterAll(async () => { await pg.stop(); });

test('cancel API returns 200 and correct payload (REQ-001)', async () => {
  const create = await request(app).post('/api/subscription').send(/*...*/);
  const cancel = await request(app).post('/api/subscription/cancel').send({ id: create.body.id });
  expect(cancel.status).toBe(200);
  expect(cancel.body.status).toBe('cancelled_active');
});
```

---

## Container catalogue (testcontainers — Python and TS modules)

| Dependency | Image | Notes |
|---|---|---|
| Postgres | `postgres:16-alpine` | Apply migrations in fixture; truncate between tests |
| Redis | `redis:7-alpine` | Flush between tests |
| Kafka | `confluentinc/cp-kafka:latest` | Slow startup (~30s); use sparingly |
| MongoDB | `mongo:7` | – |
| Elasticsearch | `elasticsearch:8.x` | Heavy; use only if the feature actually uses ES |
| SMTP mock | `axllent/mailpit` | Has HTTP API to inspect sent messages |
| LocalStack | `localstack/localstack` | For S3 / SQS / SNS / DynamoDB local emulation |

---

## When to NOT generate an integration test

- REQ is purely a UI rendering concern → 4-D
- REQ has no external dependencies (pure logic) → 4-B was sufficient; do not duplicate
- testcontainers cannot run in the target environment (e.g. nested-Docker in some CI providers) — document the gap, propose a docker-compose fallback in a README note, do not silently switch to mocks

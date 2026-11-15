# Low-Level Design (LLD)
## Signal Atlas — AI-Powered Synthetic Criminal Network Analysis

| Field | Value |
|---|---|
| Product | Signal Atlas |
| Challenge reference | SIH26189 |
| Document version | 1.0 |
| Status | Implemented prototype |
| Last updated | 15 November 2026 |

## 1. Purpose

This document records module-level implementation details, data models, API contracts, algorithms, security behavior, and error handling observed in the Signal Atlas source code.

## 2. Backend module design

| Module | File | Responsibility |
|---|---|---|
| Application | `backend/app/main.py` | FastAPI creation, lifespan seeding, middleware, CORS, router and exception handler |
| Routes | `backend/app/api/routes.py` | HTTP endpoints, dependency wiring, report/anomaly orchestration |
| Configuration | `backend/app/config.py` | Environment-backed application settings |
| Database | `backend/app/database.py` | SQLAlchemy engine, session factory, request session dependency |
| Models | `backend/app/models.py` | ORM entities and database constraints |
| Schemas | `backend/app/schemas.py` | Pydantic request and response models |
| Security | `backend/app/security.py` | Password hashing, JWT issue/validation, analyst authorization |
| Analytics | `backend/app/services/analytics.py` | Graph construction, metrics, communities, anomaly detection |
| Reporting | `backend/app/services/reporting.py` | PDF and CSV bundle generation |
| Seed data | `backend/app/seed.py`, `synthetic.py` | Synthetic sample data initialization/generation |

## 3. Database design

All timestamps are initialized in UTC using `now_utc()` in the ORM models. SQLAlchemy JSON columns are used for flexible structured values.

### 3.1 Tables

| Table | Primary key | Important fields and constraints |
|---|---|---|
| `users` | `id` | `email` unique/indexed; `password_hash`; `role`; `created_at` |
| `entity_types` | `id` | `name` unique/indexed |
| `entities` | `id` (string) | `entity_type` FK to `entity_types.name`; `label`; `description`; JSON `extra_data`; `created_at` |
| `relationships` | `id` | source and target entity FKs; relationship type; weight; occurred_at; source/target composite index |
| `transactions` | `id` | unique reference; source/target entity FKs; amount with non-negative check; currency; occurred_at |
| `communications` | `id` | source/target entity FKs; duration_seconds; occurred_at |
| `locations` | `id` | entity FK; location_code; occurred_at |
| `investigations` | `id` | unique/indexed reference_id; title; creator FK; JSON selected_entities; created_at |
| `analysis_results` | `id` | nullable investigation FK; result_type; JSON payload; created_at |
| `audit_logs` | `id` | nullable user FK; action; resource; status_code; created_at |

### 3.2 Relationships

- One entity type can classify many entities.
- Entities can be referenced as source and/or target in relationship, transaction, and communication records.
- One entity can have many location records.
- One user can create many investigations and be associated with many audit events.
- An investigation can have multiple analysis results.
- An analysis result may have a null investigation reference, which is used for standalone analysis results.

### 3.3 Integrity and indexes

- User email and transaction reference are unique.
- Entity type name and investigation reference are unique.
- Transaction amount must be greater than or equal to zero.
- Foreign keys link event records to entities.
- Indexes support common lookups by entity type, relationship endpoints/type, transaction endpoints/time, communication endpoints/time, location entity/code/time, and analysis/audit result type/action.

## 4. API design

All routes are mounted under `/api`. Except health, registration, and login, the listed routes use the `require_analyst` dependency and require a bearer token.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | Public, rate limited | Create analyst account and return token |
| POST | `/api/auth/login` | Public, rate limited | Verify credentials and return token |
| GET | `/api/health` | Public | Health check |
| GET | `/api/dashboard/overview` | Analyst | Counts, network summary, recent activity, anomaly count |
| GET | `/api/dashboard/statistics` | Analyst | Entity counts by type and relationship/transaction counts |
| GET | `/api/entities/search?q=...` | Analyst | Search entity ID or label |
| GET | `/api/entities?entity_type=...&limit=...` | Analyst | List entities, optional type filter |
| GET | `/api/entities/{entity_id}` | Analyst | Retrieve entity |
| GET | `/api/entities/{entity_id}/activity` | Analyst | Combined entity activity timeline |
| GET | `/api/relationships?limit=...` | Analyst | List relationships |
| GET | `/api/relationships/graph/{entity_id}?depth=...` | Analyst | Retrieve ego graph, depth 1–3 |
| POST | `/api/analysis/network` | Analyst | Network summary and communities |
| GET | `/api/analysis/centrality` | Analyst | Centrality metrics |
| GET | `/api/analysis/communities` | Analyst | Community membership |
| GET | `/api/analysis/patterns` | Analyst | Dense community, shared location, repeated transaction-pair patterns |
| GET | `/api/analysis/shortest-path?source_id=...&target_id=...` | Analyst | Shortest path between entities |
| POST | `/api/ml/anomaly-detection` | Analyst | Run anomaly detection and persist result |
| GET | `/api/ml/results` | Analyst | Retrieve latest anomaly result |
| POST | `/api/reports/generate` | Analyst | Create investigation/report payload |
| GET | `/api/reports` | Analyst | List up to 100 recent reports |
| GET | `/api/reports/{reference_id}/download?format=csv|pdf` | Analyst | Download report |

### 4.1 Request schemas

**Credentials**
- `email`: string, 5–255 characters.
- `password`: string, 8–128 characters.

**ReportRequest**
- `title`: string, default `Synthetic network review`, 1–160 characters.
- `entity_ids`: string array, default empty, maximum 100 entries.

**AnomalyRequest**
- `contamination`: float, default `0.05`, minimum `0.01`, maximum `0.30`.

### 4.2 Response schemas

**TokenResponse**
- `access_token`: JWT string.
- `token_type`: `bearer` by default.

**EntityOut**
- `id`, `entity_type`, `label`, `description`, `extra_data`.

### 4.3 HTTP behavior

- Invalid login: HTTP 401.
- Invalid or expired bearer token: HTTP 401 with bearer challenge.
- Authenticated user with unsupported role: HTTP 403.
- Duplicate registration email: HTTP 409.
- Invalid email in registration: HTTP 422.
- Missing entity or report: HTTP 404.
- Entity search requires a query length of 1–100.
- Entity list limit defaults to 100 and is constrained to 1–500.
- Relationship list limit defaults to 200 and is constrained to 1–1000.
- Ego graph depth defaults to 2 and is constrained to 1–3.
- Report download accepts only `csv` or `pdf`.

## 5. Authentication and authorization

### 5.1 Registration

1. Receive `Credentials`.
2. Strip whitespace and lowercase email.
3. Validate that email contains `@`.
4. Check for an existing case-insensitive email.
5. Hash password using `PasswordHash.recommended()`.
6. Create user with role `analyst`.
7. Commit and refresh user.
8. Create JWT access token and return `TokenResponse`.

Registration rate limit: 5 requests per minute per remote address.

### 5.2 Login

1. Normalize email using strip/lowercase.
2. Find user by case-insensitive email.
3. Verify submitted password against stored password hash.
4. Return HTTP 401 for absent user or invalid password.
5. Issue JWT on success.

Login rate limit: 10 requests per minute per remote address.

### 5.3 JWT validation

The token includes:
- `sub`: user ID as a string.
- `role`: user role.
- `exp`: expiration timestamp.

The configured JWT algorithm and secret are read from application settings. The request dependency decodes the token, loads the user from the database, stores the user ID on request state, and returns the user. `require_analyst` accepts `analyst` and `admin`.

## 6. Analytics algorithms

### 6.1 Graph construction

`build_graph(db)` creates an undirected NetworkX graph:
- Each `Entity` becomes a node with `label` and `entity_type` attributes.
- Each `Relationship` becomes an edge with `type` and `weight` attributes.

### 6.2 Network summary

`network_summary(graph)` returns:
- `entity_count`: number of nodes.
- `relationship_count`: number of edges.
- `component_count`: number of connected components.
- `density`: NetworkX graph density, rounded to four decimal places; zero for graphs with at most one node.
- `largest_component`: IDs in the largest connected component, or an empty list.

### 6.3 Centrality

`centrality_results(graph)` calculates:
- Degree centrality.
- Normalized betweenness centrality.
- Closeness centrality.
- PageRank.

Values are rounded to four decimal places and returned with entity ID, label, and type.

### 6.4 Communities

`community_results(graph)` returns an empty list if there are no edges. Otherwise it uses NetworkX greedy modularity communities, sorts communities by descending size, and assigns sequential community IDs.

### 6.5 Pattern discovery

`GET /analysis/patterns` currently checks three structural/event patterns:
1. Communities of at least three members whose internal graph density is greater than the overall graph density.
2. Location codes associated with at least two distinct entities.
3. Source/target entity pairs appearing in at least two transaction records.

Each pattern includes an explanation and a disclaimer that the pattern does not establish intent or wrongdoing.

### 6.6 Shortest path

`GET /analysis/shortest-path` validates both entity IDs, then calls `networkx.shortest_path`. If no path exists, it returns an empty path and null length. Missing source/target entity returns HTTP 404.

### 6.7 Transaction anomaly detection

Input records are ordered by `occurred_at`. The method requires at least three transactions.

Feature construction:
- `f1 = log1p(amount)`
- `f2 = count(source endpoint) + count(target endpoint)`, where endpoint counts are accumulated over all transaction rows.

If fewer than three rows exist, or there is no feature variation, the service returns no findings and a limitation message.

Otherwise:
1. Fit `IsolationForest(contamination=..., random_state=42, n_estimators=100)` to the two-dimensional feature matrix.
2. Obtain predictions and negative score samples.
3. Normalize scores relative to the current sample using min-max scaling with a small epsilon.
4. Robust-scale transaction amounts.
5. Run DBSCAN with `eps=0.75` and `min_samples=min(5, number_of_rows)`.
6. Include a transaction when Isolation Forest marks it as an outlier or DBSCAN labels it as noise.
7. Add signal flags, reasons, amount, currency, entity IDs, exploratory confidence label, and limitations.
8. Sort findings by descending normalized score.

The score is relative to the analyzed sample and is not a calibrated probability. A finding is not proof of wrongdoing.

## 7. Report generation

`POST /api/reports/generate`:
1. Validates that every supplied entity ID exists.
2. Creates an `INV-` reference using a UUID fragment.
3. Creates an Investigation row and flushes it to obtain its database ID.
4. Builds the complete graph and runs anomaly detection.
5. If entity IDs are selected, includes those entities and their direct graph neighbors. If no IDs are selected, includes all graph nodes.
6. Builds a subgraph and computes its network summary.
7. Creates a payload containing report reference/title, selected IDs, network summary, anomaly findings and metadata, graph nodes/edges, disclaimer, and UTC creation time.
8. Stores an `AnalysisResult` of type `report`.
9. Writes an audit event and commits.
10. Returns the report payload.

Downloads:
- `format=pdf`: returns a PDF using `build_pdf_report`.
- `format=csv`: returns a ZIP archive using `build_csv_bundle`; the download filename ends in `.csv.zip`.

## 8. Audit logging

The HTTP middleware records an `api_request` event for `/api/` paths except:
- `/api/health`
- `/api/auth/login`
- `/api/auth/register`

It stores user ID when available, resource path (truncated to 255 characters), and response status code. SQLAlchemy errors during this audit write are logged and do not replace the original API response.

Anomaly analysis and report generation also write explicit audit records (`anomaly_analysis` and `report_generated`).

## 9. Frontend integration

The frontend API helper:
1. Reads `VITE_API_URL`, defaulting to `/api`.
2. Reads `access_token` from browser local storage.
3. Adds `Authorization: Bearer <token>` when present.
4. Adds JSON content type for non-FormData request bodies.
5. Calls `fetch`.
6. Parses API error JSON and raises an error using `detail` or the HTTP status.
7. Returns JSON for successful standard API calls.

The report download helper sends the bearer token, downloads the response as a Blob, creates a temporary object URL, and triggers a browser download. The UI stores/removes the token through `setToken`.

## 10. Configuration

Settings in `backend/app/config.py`:
- `DATABASE_URL`: defaults to `sqlite:///./network_analysis.db`.
- `JWT_SECRET_KEY`: local-only default; must be replaced in deployment.
- `JWT_ALGORITHM`: defaults to `HS256`.
- `ACCESS_TOKEN_MINUTES`: defaults to 60.
- `DEMO_EMAIL`: defaults to `analyst@fictional.test`.
- `DEMO_PASSWORD`: defaults to `demo-pass-01`.

Settings are loaded from environment variables and `.env`. Docker Compose sets a PostgreSQL `DATABASE_URL` for the backend and passes JWT/demo settings through environment variables.

## 11. Testing and migrations

Repository structure includes:
- `backend/tests/test_api.py`
- `backend/tests/test_analytics.py`
- `backend/migrations/versions/0001_initial_schema.py`
- `backend/alembic.ini`

The dependency list includes pytest and httpx. The existence of these tests and migration files is confirmed; test coverage percentages and CI execution status are not asserted in this document.

## 12. Operational and security notes

- Do not deploy with the checked-in local/demo secret values.
- Configure the allowed frontend origin in CORS for the actual deployment.
- Keep `.env` and database credentials out of version control.
- Use synthetic data for demonstrations unless a separate approved data governance process exists.
- Treat analytics as exploratory and require human review.
- Validate database configuration separately for local, Docker, and hosted environments.

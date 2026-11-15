# Product Requirements Document (PRD)
## Signal Atlas — AI-Powered Synthetic Criminal Network Analysis

| Field | Value |
|---|---|
| Product | Signal Atlas |
| Challenge reference | SIH26189 |
| Document version | 1.0 |
| Status | Implemented prototype |
| Last updated | 15 November 2026 |

## 1. Product summary

Signal Atlas is a web-based analytical prototype for exploring relationships among fictional entities and examining synthetic transaction, communication, and location records. It combines interactive network exploration, graph metrics, exploratory anomaly detection, entity activity timelines, and downloadable analytical reports.

The system is intended to help a human analyst navigate complex synthetic datasets. It is a decision-support prototype: statistical patterns and graph structures are not proof of wrongdoing, intent, or culpability.

## 2. Problem statement

When many entities are connected by relationships and event records, it can be difficult to understand the overall structure, inspect an individual entity's activity, identify unusual records for further review, and communicate findings. Signal Atlas brings these capabilities together in one interface backed by an API and relational data store.

## 3. Product goals

1. Present synthetic entities and their relationships in an explorable network.
2. Summarise network structure with counts, connected components, density, centrality, and communities.
3. Provide entity search, detail, and activity-timeline access.
4. Surface unusual synthetic transaction records using statistical outlier techniques.
5. Allow an analyst to generate and download reports for selected entities or the complete graph.
6. Protect analyst endpoints with authenticated access and record selected API and analysis/report events for auditability.

## 4. Users and roles

### Analyst
The implemented application creates registered users with the `analyst` role. Analysts can access protected dashboard, entity, relationship, analysis, anomaly, and report endpoints after authentication.

### Admin
The authorization dependency accepts either `analyst` or `admin` roles. The inspected registration flow creates `analyst` accounts; an admin provisioning workflow was not identified in the inspected code.

## 5. Scope

### 5.1 Implemented capabilities

- Account registration and login, returning a bearer access token.
- Password hashing and verification using the recommended `pwdlib` password-hashing configuration.
- JWT access tokens with configured signing algorithm and expiry.
- Dashboard overview and entity-type statistics.
- Entity listing, filtering by entity type, search, detail, and activity timeline.
- Relationship listing and bounded-depth ego-network retrieval.
- Network summary, centrality, community, pattern, and shortest-path analysis.
- Transaction anomaly analysis using Isolation Forest and DBSCAN.
- Persistence and retrieval of the latest anomaly analysis result.
- Investigation/report generation for selected entities or all entities.
- PDF report and ZIP bundle containing CSV report data downloads.
- API request audit events for applicable `/api/` requests, plus explicit analysis and report audit events.
- Health endpoint.
- Synthetic seed-data initialization during application lifespan.

### 5.2 Out of scope / not established by inspected implementation

- Real-world criminal records or integrations with law-enforcement databases.
- Automated determination that a person or entity committed an offence.
- Predictive judgments about individuals.
- Evidence-grade conclusions or calibrated probability of wrongdoing.
- A verified production role-management or admin-provisioning interface.
- Real-time streaming ingestion or external data-source connectors.
- Multi-tenant organization management.
- A claim that the deployed database is PostgreSQL in every environment. The backend defaults to SQLite; Docker Compose configures PostgreSQL.

## 6. Functional requirements

| ID | Requirement | Acceptance condition |
|---|---|---|
| FR-01 | Register an analyst account | Valid credentials create a user and return an access token; duplicate email is rejected. |
| FR-02 | Authenticate an analyst | Valid credentials return a bearer token; invalid credentials return HTTP 401. |
| FR-03 | Check service health | `GET /api/health` returns `{"status":"ok"}`. |
| FR-04 | View dashboard overview | Authenticated analyst receives network counts, transaction/anomaly counts, recent activity, and disclaimer. |
| FR-05 | Browse and search entities | Analyst can list entities, optionally filter by type, search by ID/label, and retrieve a detail record. |
| FR-06 | Inspect entity activity | Analyst receives a timeline combining related relationships, transactions, communications, and location records. |
| FR-07 | Explore relationships | Analyst can list relationships and retrieve a bounded-depth ego graph for an entity. |
| FR-08 | Analyse network structure | Analyst can retrieve network summary, centrality, communities, patterns, and shortest path. |
| FR-09 | Detect transaction outliers | Analyst can submit a contamination setting from 0.01 to 0.30 and receive exploratory findings and limitations. |
| FR-10 | Retrieve anomaly results | Analyst can retrieve the most recently stored anomaly result, or an empty result when none exists. |
| FR-11 | Generate an investigation report | Analyst can submit a title and up to 100 entity IDs; unknown IDs are rejected. |
| FR-12 | Download reports | Analyst can download a generated report as PDF or ZIP containing CSV data. |
| FR-13 | Audit applicable activity | Applicable API requests and explicit analysis/report actions are recorded in audit logs. |

## 7. Non-functional requirements and constraints

- **Security:** Protected endpoints use bearer-token authentication. Passwords are stored as hashes, not plaintext. Login and registration have rate limits.
- **Data integrity:** Entity references use foreign keys; transaction amounts have a non-negative database check constraint; transaction references are unique.
- **Availability/health:** A health endpoint is provided. Docker Compose defines database and backend health checks and service restart policies.
- **Maintainability:** Backend code is separated into API, models, schemas, services, security, configuration, and database modules.
- **Explainability:** Anomaly findings include method, input features, signals, explanation, and limitations.
- **Responsible use:** All analytical results must be interpreted as exploratory descriptions of synthetic data, not evidence or person-level judgments.
- **Deployment configuration:** Database URL, JWT secret, algorithm, and token lifetime are configurable. Safe deployment requires overriding local/demo defaults with secrets.

## 8. Data requirements

The backend models include users, entity types, entities, relationships, transactions, communications, locations, investigations, analysis results, and audit logs. Synthetic seed data is loaded when the FastAPI application lifespan starts.

The product is designed and demonstrated using synthetic data. Any future use with real data would require separate legal, privacy, security, governance, and data-quality review.

## 9. Success criteria

The prototype is considered functionally successful when:
- An analyst can register or log in and access protected features.
- Dashboard and entity data load from the API.
- Network analysis endpoints return graph metrics and communities.
- Anomaly detection returns findings or a clear limitation response for insufficient/constant data.
- A report can be generated and downloaded in supported formats.
- The frontend production build and backend tests pass in the target environment.

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Outlier score is mistaken for probability or proof | Label results exploratory; expose method, signals, and limitations. |
| Sparse or constant data produces unreliable analysis | Return explicit limitations when fewer than three transactions or insufficient feature variation exist. |
| Weak deployment secrets | Replace local/demo defaults through environment variables; keep secrets out of source control. |
| Large graph affects response time and browser rendering | Apply endpoint limits where implemented; profile larger datasets before production scaling. |
| Synthetic examples are mistaken for real intelligence | Label the product and sample data clearly as synthetic. |

## 11. Assumptions and open points

- The exact deployment environment variables and production database URL must be checked in the deployment provider; the repository configuration alone does not establish the live database engine.
- The inspected CORS configuration in `backend/app/main.py` allows `http://localhost:5173`; deployed-origin configuration should be verified before changing environments.
- Detailed UI behavior and visual acceptance criteria should be validated against the current frontend build.
- No service-level performance target or formal availability target was found in the inspected source.

## 12. Responsible-use statement

Signal Atlas is an educational/prototype analytical tool operating on synthetic records. A network connection, shared location record, repeated transaction, centrality score, community membership, or anomaly flag does not establish criminal intent or wrongdoing. Outputs are exploratory leads only and require independent human review and context.

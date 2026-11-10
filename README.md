# EY Todo App

## Quickstart

```bash
docker compose build
ENVIRONMENT=DEV docker compose up -d
```
The solution will be available on http://127.0.0.1:8080

### Developer Mode

**Backend**

* Python > 3.12
* uv

Backend will be available on http://localhost:9000

```bash
cd api
uv run sync
uv run uvicorn app.main:app --reload --port 9000
```

**Frontend**

* NodeJS 22.x

Webapp will be available on http://localhost:5173

```bash
cd webapp
npm ci
npm run dev
```
## Summary

In brief, my overall approach was to plan first and then implement. I started with the architecture and design, then implemented the data access layer, followed by authentication, CRUD operations, and the UI.

Once the UI was in place, I focused on security: I added CSRF protection for sensitive operations and rate limiting to protect the backend from excessive requests.

Finally, I packaged the application in a Docker container so it would be ready for deployment.

**Implemented Features**
* User registration
* Per-user todo list, with CRUD operations over its records and ability to re-order tasks
* API rate limiter
* CSRF route protection
* sparse ordering for todo list items

### Potential next steps / improvements (~2-3 man/days)
- **Idempotency key:** UUID key per intent — client generates a unique key per intent; server dedups (key → result) and have the 5sec short-lived cache for the order ID, preventing to send two parallel requests; retries are safe.
- **Full multi-session support:** Prevent one session from overwriting changes made by another (optimistic locking/versioning) and synchronize task lists across sessions using long polling, WebSockets, or Server-Sent Events (SSE).
- **Pagination:** Support paginated task retrieval.
- **Virtual scrolling:** Efficiently render large task lists without loading every item into the DOM.
- **Task status badges:** Make task statuses easier to identify at a glance.
- **End-to-end testing:** Add E2E test coverage using Playwright.
- **Database-agnostic data access layer:** Make it possible to switch from SQLite to another SQL database engine without changing business logic.
- **Shared rate limiter:** Support rate limiting across multiple application instances.

### Limitations

The current implementation relies on a local, file-based SQLite database, which limits the application to a single worker. It cannot be scaled across multiple workers without changing the persistence layer or introducing a shared database.

The same limitation applies to the built-in rate limiter. Each worker maintains its own rate-limit state, so running multiple workers would effectively give each one a separate quota. As a result, the aggregate request limit across all workers could exceed the configured limit.

Strictly speaking, addressing these concerns was outside the scope of the homework. The instructions did mention a "distributed cloud infrastructure," which I deliberately interpreted as an environment where a single application container has access to persistent storage.

Nevertheless, I believe these limitations are worth highlighting because they would need to be addressed before scaling the application horizontally.

## Architecture and Design

### Backend Surface
* Python with FastAPI
* REST API JSON payload
* Pydantic for request/response validation
* SQLAlchemy for database access
* Alembic for database schema migrations
* Pytest for testing

The backend organized by business features, separating HTTP endpoints, business logic and persistence.

* Router - HTTP endpoints, request/response handling
* Service - Business logic
* Schemas - Request/response validation (Pydantic)
* Models - SQLAlchemy database schemas
* Database - connection and session management
* Core - configuration and shared functionality

### Data Storage

SQLite, schema managed by Alembic (`api/migrations`). Foreign keys are enforced (`PRAGMA foreign_keys=ON`). UUIDs are stored as `CHAR(32)` hex; timestamps are timezone-aware UTC (naive datetimes are rejected on write). Defaults marked *(app)* are applied by SQLAlchemy, not by the database.

**Table `users`**
|Column|Type|Constraints|Notes|
|-|-|-|-|
|`id`|`CHAR(32)` (UUID)|PK (`pk_users`)|uuid4 *(app)*|
|`username`|`VARCHAR(50)`|NOT NULL, UNIQUE (`uq_users_username`)|trimmed + lower-cased by the API, 3–50 chars|
|`password_hash`|`VARCHAR(255)`|NOT NULL|Argon2id|

**Table `todos`**
|Column|Type|Constraints|Notes|
|-|-|-|-|
|`id`|`CHAR(32)` (UUID)|PK (`pk_todos`)|uuid4 *(app)*|
|`user_id`|`CHAR(32)` (UUID)|NOT NULL, FK → `users.id` ON DELETE CASCADE, indexed|owner|
|`label`|`VARCHAR(50)`|NOT NULL|trimmed, 1–50 chars|
|`text`|`VARCHAR(200)`|nullable|trimmed, max 200 chars|
|`status`|`VARCHAR(50)`|NOT NULL|default `""` *(app)*|
|`position`|`INTEGER`|NOT NULL, indexed|sparse ordering, step 1000, default 0 *(app)*|
|`created_at`|`DATETIME`|NOT NULL|UTC|
|`modified_at`|`DATETIME`|nullable|UTC, set on update|
|`removed_at`|`DATETIME`|nullable, indexed|UTC, set on soft delete|
|`is_removed`|`BOOLEAN`|NOT NULL|soft-delete flag, default `false` *(app)*|

**Table `sessions`**
|Column|Type|Constraints|Notes|
|-|-|-|-|
|`session_hash`|`VARCHAR(255)`|PK (`pk_sessions`)|SHA-256 of the cookie token; the raw token is never stored|
|`user_id`|`CHAR(32)` (UUID)|NOT NULL, FK → `users.id` ON DELETE CASCADE|not indexed|
|`expires_at`|`DATETIME`|NOT NULL|absolute expiry (7 days)|
|`last_seen_at`|`DATETIME`|NOT NULL|drives idle expiry (30 min)|
|`revoked_at`|`DATETIME`|nullable|set on logout|
|`csrf_token`|`VARCHAR(64)`|nullable|synchronizer token for the session|

Relationships
* `users.id` → `todos.user_id` (one-to-many, cascade delete)
* `users.id` → `sessions.user_id` (one-to-many, cascade delete)

> SQLite does not enforce `VARCHAR(n)` lengths: limits hold only where the API validates them.

### Business API surface

All routes are under `/api`, need a session cookie (401 `not_authenticated` otherwise) and only see the caller's own todos: someone else's id gives 404 `todo_not_found`. Unsafe methods also need the `X-CSRF-Token` header (403 `csrf_failed`).

|API|Method|Payload / query|Response|Note|
|-|-|-|-|-|
|`/todos`|GET|`?q=<text>` optional|`{items: Todo[], meta: {has_more}}`|active todos ordered by `position`; `q` = case-insensitive substring match on `label`; returns at most 100 items (no paging params yet)|
|`/todos`|POST|`{label, text?, status?}`|`Todo`|new todo is placed at the top of the list|
|`/todos/{id}`|GET||`Todo`||
|`/todos/{id}`|PATCH|`{label?, text?, status?}`|`Todo`|edit: only the fields sent are changed; `null` label/status are ignored|
|`/todos/{id}`|PATCH|`{lft?, rgt?}`|`Todo`|reorder: ids of the todos that should end up directly before (`lft`) and after (`rgt`) it; omit one to move to an end. Can't be combined with edit fields (422); 409 `stale_order` if `lft` no longer comes before `rgt` (e.g. the list changed in another session)|
|`/todos/{id}`|DELETE||`Todo`|soft delete: sets `is_removed`/`removed_at`; the todo disappears from all reads|

`Todo` = `{id, label, text, status, position, created_at, modified_at, removed_at}`. Field limits: `label` 1–50 chars, `text` up to 200 chars, both trimmed.

### Authentication
* password hashing - Argon2id
* session token - 256-bit random token
* database storage - sha-256 hash of token
* cookie - `__Host-session`
* session persistence - Sqlite
* session validation - server-side on every request
* session expiration - idle (30min) + absolute (7days)
* CSRF - sync token + origin validation

|API|Method|Payload|Note|
|-|-|-|-|
|/auth/register |POST|{username, password}|Register a new user|
|/auth/login    |POST|{username, password}|Creates per-session cookie|
|/auth/me       |GET||Returns the actual user|
|/auth/{user}   |PATCH|{password}|change password|
|/auth/logout   |POST||logout the user|

**Cookie Configuration**
* HttpOnly
* Secure
* SameSite=Lax
* Path=/

Sessions are stored in the `sessions` table (see [Data Storage](#data-storage)).


### Others
**Rate Limit**

Token bucket per key: *burst* = bucket capacity, *refill* = tokens added back over time. A rejected request gets `429 rate_limited` with a `Retry-After` header. Buckets are kept per route handler, so e.g. `GET /todos` and `POST /todos` have separate quotas.

|Endpoint|Key|Burst|Refill|Notes|
|-|-|-|-|-|
|`POST /auth/register`|client IP|5|1/s||
|`POST /auth/login`|client IP|5|5/min|brute-force guard per source|
|`POST /auth/login`|submitted username|10|10/15 min|guards one account against distributed guessing; checked in addition to the IP limit|
|`GET /auth/me`|user|20|2/s|called by the frontend on every page load|
|`POST /auth/logout`|user|5|1/s||
|`/todos` (all routes, incl. `?q=` search)|user|30|5/s|set on the router; the burst covers drag-reorder bursts|

Per-IP keys use the connection's client address: behind a load balancer or reverse proxy set `FORWARDED_ALLOW_IPS`, otherwise every client shares the proxy's IP and one quota. Limits are kept in memory per process (see [Limitations](#limitations)).

**CSRF origin check**

Unsafe requests (POST/PATCH/DELETE) are accepted when the browser sends `Sec-Fetch-Site: same-origin`, when `Origin`/`Referer` matches the scheme+host the request was sent to (SPA served by this server, or through the Vite dev proxy), when the origin is in `TRUSTED_ORIGINS`, or when neither header is present (non-browser clients). Everything else gets 403 `origin_not_allowed`.

Behind a reverse proxy, forward the original `Host` header (nginx: `proxy_set_header Host $host;`) and, when it terminates TLS, set `FORWARDED_ALLOW_IPS` to the proxy's address so the `https` scheme is recognised.

## Frontend Surface
* React with Typescript
* Vite as development and build tool
* React Router for navigation
* A centralized API client for backend communication

Frontend organized by application features, with shared components and centralized API communication.

## Implementation plan

1. Backend skeleton - application settings, database connection, migrations, logging and error handling
2. Authentication - registration/login, password hashing, cookies, session management, protected endpoints
2. CRUD API - request validation, business logic, persistence, response schemas, filtering (search)
3. React application
4. Cross-cutting - rate limiting, CSRF
5. Testing and delivery - docker container

## Docker

A single image serves the API and the built SPA on port 8080.

### Compose

```sh
docker compose build                 # build the image (ey-todo:latest)
docker compose up -d                 # run migrations, then start the app
PORT=80 docker compose up -d
```

|Var|Default|Note|
|-|-|-|
|`IMAGE` / `TAG`|`ey-todo` / `latest`|image name to build and run|
|`PORT`|`8080`|host port|
|`FORWARDED_ALLOW_IPS`|`127.0.0.1`|IPs of a reverse proxy whose `X-Forwarded-Proto` is trusted|
|`LOG_LEVEL`|`INFO`||

The `migrate` service runs `alembic upgrade head` and exits; `app` starts only after it succeeds. The SQLite DB lives in the `state` volume.

### Plain docker

```sh
docker build -t ey-todo .
docker volume create ey-todo-state

# apply migrations (once, and after every upgrade)
docker run --rm -v ey-todo-state:/app/.state ey-todo alembic upgrade head

docker run -d -p 8080:8080 -v ey-todo-state:/app/.state ey-todo
```

|Env|Default in image|Note|
|-|-|-|
|`TRUSTED_ORIGINS`|`[]`|extra front-end origins allowed to send unsafe requests; same-origin is always allowed|
|`DATABASE_PATH`|`sqlite+aiosqlite:///.state/db.sqlite`|relative to `/app`; keep `/app/.state` on a volume|
|`WEBAPP_DIR`|`/app/webapp`|built SPA; unset = API only|

SPA serving: `/assets/*` (hashed bundles) is cached as immutable; any other non-`/api` path returns a root file from `dist/` if present, else `index.html` (no-cache) so client routes like `/login` survive a reload.



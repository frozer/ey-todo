# EY Todo App

## Backend Surface
* Python with FastAPI
* REST API JSON payload
* Pydantic for request/response validation
* SQLAlchemy for database access
* Alembic for database schema migrations
* Pytest for testing

The backend organized by business features, separating HTTP endpoints, business logic and persistence.

```
api/
  src/
    auth/
      router.py
      schemas.py
      service.py
    core/
      config.py
    database/
      connection.py
      models.py
    todos/
      router.py
      schemas.py
      service.py
    users/
      router.py
      schemas.py
      service.py
    main.py
  tests/
```

* Router - HTTP endpoints, request/response handling
* Service - Business logic
* Schemas - Request/response validation (Pydantic)
* Models - SQLAlchemy database schemas
* Database - connection and session management
* Core - configuration and shared functionality

### Data Storage

Table `users`
* id (UUID) PK
* username
* password_hash

Table `todos`
* id (PK)
* label
* text
* priority
* status
* user_id (FK - users.id)

Relationships
* users.id -> todos.user_id (one-to-many)

### Business API surface
|API|Method|Payload|Note|
|-|-|-|-|
|/todos         |GET||return list of todos|
|/todos         |POST|{label, text}|create a new todo|
|/todos/{id}    |GET||return specific todo|
|/todos/{id}    |PATCH|{label, text, position}|update the given todo|
|/todos/{id}    |DELETE||remove the given todo|
|/todos/search? |POST|{q}||

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
|/auth          |POST|{username, password}|Creates per-session cookie|
|/auth/me       |GET||Returns the actual user|
|/auth/{user}   |PATCH|{password}|change password|
|/auth/logout   |POST||logout the user|

**Cookie Configuration**
* HttpOnly
* Secure
* SameSite=Lax
* Path=/

**Sessions Table**
* id (PK)
* session_hash
* user_id (FK - users.id)
* expires_at
* last_seen_at
* revoked_at


### Others
**Rate Limit**
|Endpoint|Dimension|Limit|Algorithm|Why|
|-|-|-|-|-|
|/auth/register |per-IP|5, 1/min|token bucket||
|/auth          |per-IP/per-user|5, 1/s|token bucket + uniq request id||
|/todos         |per-user|100, 1/s|token + uniq request id||
|/todos/{id}    |per-user|100, 1/s|token bucket||
|/todos/search? |per-user|100, 1/s|token bucket||

**Idempotency**
version??

## Frontend Surface
* React with Typescript
* Vite as development and build tool
* React Router for navigation
* A centralized API client for backend communication
* Playwright for e2e testing

Frontend organized by application features, with shared components and centralized API communication.

```
webapp/
  src/
```

## Implementation plan

1. Backend skeleton - application settings, database connection, migrations, logging and error handling
2. Authentication - registration/login, password hashing, cookies, session management, protected endpoints
2. CRUD API - request validation, business logic, persistence, response schemas, filtering (search)
3. React application
4. Cross-cutting - rate limiting
5. Testing and delivery - e2e tests, podman setup
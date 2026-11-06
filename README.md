## EY Todo

## Backend

### API surface
|API|Method|Payload|Note|
|-|-|-|-|
|/auth/register |POST|{username, password}|Register a new user|
|/auth          |POST|{username, password}|Creates per-session cookie containing JWT token, JWT token contains the username|
|/auth/reset    |POST|{username, pin}|default pin - 1234|
|/auth/{user}   |PATCH|{password}|change password|
|/todos         |GET||return list of todos|
|/todos         |POST|{label, text}|create a new todo|
|/todos/{id}    |GET||return specific todo|
|/todos/{id}    |PATCH|{label, text, position}|update the given todo|
|/todos/{id}    |DELETE||remove the given todo|
|/todos/search? |POST|{q}||

**Rate Limit**
|Endpoint|Dimension|Limit|Algorithm|Why|
|-|-|-|-|-|
|/auth/register |per-IP|5, 1/min|token bucket||
|/auth          |per-IP/per-user|5, 1/s|token bucket + uniq request id||
|/auth/reset    |per-IP/per-user|5, 1/min|token bucket||
|/todos         |per-user|100, 1/s|token + uniq request id||
|/todos/{id}    |per-user|100, 1/s|token bucket||
|/todos/search? |per-user|100, 1/s|token bucket||

**Idempotency**
version??

**Database**
Engine - Sqlite

|Table|Fields|Indices|Foreign keys|
|-|-|-|-|
|users|user, pwd, removed|Primary - user|
|todos|label, text, position, user, removed|id, user|user - user.id|

### Client Surface


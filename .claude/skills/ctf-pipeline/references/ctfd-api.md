# Site API — ctfd.nusgreyhats.org

**Pre-contest snapshot, 2026-05-26.** Contest opens `1780106400` (2026-05-30 10:00 SGT). All shapes here = best guess from `/api/v1/swagger.json` + bundle `D.fetch()` call sites + a few live probes. Mutation bodies are **mostly empty in swagger** — values inferred from CTFd upstream conventions (v3.7.x) and bundle JS. Verify first call of each mutation against live response before automating.

Future agent: read this **before** crafting any `mcp__playwright__browser_evaluate fetch(...)` against the API. Don't hardcode — re-snapshot if anything 4xx's unexpectedly.

## Base

| | |
|---|---|
| Base URL | `https://ctfd.nusgreyhats.org` |
| API root | `/api/v1` |
| Theme bundles | `/themes/greyctf/static/...` |
| Swagger | `GET /api/v1/swagger.json` (public, 80 routes, 37 defs) |

## Auth

- **Cookie session only.** Login: form POST `/login` (CSRF nonce from `/login` page). Sets HttpOnly `session=...` cookie (`document.cookie` shows empty — expected).
- **`Authorization: Token ctfd_...` rejected** by this instance — 302 → `/login`. Don't bother. Use browser cookie.
- **CSRF** required on every state-change (`POST`/`PATCH`/`PUT`/`DELETE`): header `CSRF-Token: <window.init.csrfNonce>` (64-hex, per page-load). Bundle `D.fetch` wrapper auto-injects when called inside `browser_evaluate`. If hand-crafting `fetch`, set it manually.
- **Identity check**: `GET /api/v1/users/me` → 200 JSON if session live; HTML 302 redirect if expired.

```js
// always works inside browser_evaluate (D.fetch handles CSRF + creds)
const r = await D.fetch('/api/v1/challenges/attempt', {
  method: 'POST',
  body: JSON.stringify({ challenge_id: 1, submission: 'grey{...}' })
});
const j = await r.json();
```

## Response envelope

Every JSON response follows one of these shapes:

```json
// success — single object
{ "success": true, "data": { /* fields */ } }

// success — list (may include meta.pagination on paginated endpoints)
{ "success": true, "data": [ ... ], "meta": { "pagination": { "page":1,"next":2,"prev":null,"pages":5,"per_page":50,"total":237 } } }

// error
{ "success": false, "errors": [ "..." ] }

// gated-by-time (live, observed)
{ "message": "GreyCTF Qualifiers 2026 has not started yet" }   // HTTP 403
```

List endpoints **cap `per_page` at 50**. Paginate via `?page=N`. Some endpoints also accept `?q=...&field=...` for filter.

## Reads (GET)

### Public — work pre-contest, no login

| path | returns |
|------|---------|
| `/api/v1/swagger.json` | full OpenAPI 2.0 spec |
| `/api/v1/users?page=N` | paginated user list (total 465, IDs 1–6 hidden) |
| `/api/v1/users/{id}` | single user (public fields only when not self/admin) |
| `/api/v1/teams?page=N` | paginated team list (total 237) |
| `/api/v1/teams/{id}` | single team |
| `/api/v1/scoreboard` | `[]` pre-contest, ranked list post-contest |
| `/api/v1/scoreboard/top/{n}` | `{}` pre-contest, top-N map post-contest |
| `/api/v1/brackets` | bracket list (`Local` id=3, `Open` id=4) |
| `/api/v1/brackets?type=teams` | filter |
| `/api/v1/notifications` | `[]` pre-contest |
| `/themes/greyctf/static/manifest.json` | bundle map |

### Authed — work with cookie, **also gated by contest start** for challenge data

| path | gated? | notes |
|------|--------|-------|
| `/api/v1/users/me` | no | self profile |
| `/api/v1/users/{id}/solves` | no | per-user solves; **404 for admin IDs 1–6** |
| `/api/v1/users/{id}/fails` | no | |
| `/api/v1/users/{id}/awards` | no | |
| `/api/v1/users/{id}/submissions?challenge_id={c}` | no | own subs only unless admin |
| `/api/v1/teams/me` | no | own team |
| `/api/v1/teams/me/members` | no | team roster |
| `/api/v1/teams/{id}/solves` | no | |
| `/api/v1/teams/{id}/fails` | no | |
| `/api/v1/teams/{id}/awards` | no | |
| `/api/v1/challenges` | **403 until start** | list |
| `/api/v1/challenges/{id}` | **403** | detail (see shape below) |
| `/api/v1/challenges/{id}/solves` | **403** | who solved + when |
| `/api/v1/challenges/{id}/solution` | **403** | author writeup (if unlocked) |
| `/api/v1/challenges/{id}/files` | **403** | attachments |
| `/api/v1/challenges/{id}/hints` | **403** | hint list (locked hints have no `content`) |
| `/api/v1/challenges/{id}/ratings` | **403** | community rating |
| `/api/v1/challenges/{id}/topics` | **403** | |
| `/api/v1/challenges/{id}/tags` | **403** | |
| `/api/v1/challenges/{id}/requirements` | **403** | unlock prereqs |
| `/api/v1/hints/{id}` | **403** | full hint after unlock |
| `/api/v1/solutions/{id}` | **403** | full solution after unlock |
| `/api/v1/notifications?since_id={n}` | no | polling fallback for SSE; `HEAD` returns `result-count` header |
| `/events` | no (403 unauth) | SSE stream: `notification`, `solve`, `counter` events |

### Admin-only (we are not admin — listed for completeness)

`/api/v1/configs`, `/api/v1/configs/{key}`, `/api/v1/files`, `/api/v1/flags`, `/api/v1/tags`, `/api/v1/topics`, `/api/v1/submissions`, `/api/v1/unlocks` (full list), `/api/v1/statistics/*`, `/api/v1/exports/raw`, `/plugins/ctfd-whale/admin/container(s)`.

## Mutations (POST/PATCH/PUT/DELETE)

CSRF header required on **all** of these. Body is JSON. `Content-Type: application/json`.

### Flag submit — **the only one solver pipeline must call**

```http
POST /api/v1/challenges/attempt
Content-Type: application/json
CSRF-Token: <nonce>

{ "challenge_id": <int>, "submission": "grey{...}" }
```

**Response (observed in upstream CTFd, shape inferred)**:
```json
{ "success": true, "data": { "status": "correct",     "message": "Correct" } }
{ "success": true, "data": { "status": "incorrect",   "message": "Incorrect" } }
{ "success": true, "data": { "status": "already_solved", "message": "You already solved this" } }
{ "success": true, "data": { "status": "paused",      "message": "CTF is paused" } }
{ "success": true, "data": { "status": "ratelimited", "message": "..." } }   // HTTP 429
```

Verdict vocab: `correct | incorrect | already_solved | paused | ratelimited`. Pipeline parser keys on `data.status`.

#### Flag spec (one shared extractor for every submit subagent)

- Canonical regex: `grey\{[^}\n]{1,256}\}`. Extract **all** matches from solver output, **dedup by value**, submit each distinct flag once.
- Trim surrounding whitespace/quotes. If the solver emits only inner text, wrap as `grey{<text>}`.
- **Reject placeholders**: `grey{...}`, `grey{FLAG}`, `grey{example}`, and any sample string from these docs — never submit them.
- Never re-submit a value already in the challenge's flag-attempts table with verdict `correct` / `already_solved` / `incorrect`.

#### Submit discipline (single serialized lane)

All `grey{...}` funnel through one submit queue — submissions are a **team-shared rate bucket**.

| `data.status` / HTTP | action |
|---|---|
| `ratelimited` / `429` | sleep ≥60s, retry same flag (assume ≤10 incorrect/min/team — unknowns #4; verify on first 429) |
| `paused` | **hold** the queue (rows stay `pending`, no tight-loop); solve subagents keep queuing; resume when `/users/me` or notifications show unpaused |
| `incorrect` | write verdict `incorrect`, move on — never re-loop the same challenge on the same flag |
| `correct` / `already_solved` | write verdict, mark folder solved |

### Hint unlock

```http
POST /api/v1/unlocks
{ "target": <hint_id>, "type": "hints" }   // type=solutions for writeup unlock
```

Response: `{ success: true, data: { id, user_id, team_id, target, type, date } }` or `{ success:false, errors:[...] }` (insufficient points).

Then re-`GET /api/v1/hints/{id}` to receive `content`.

### Rate a challenge

```http
PUT /api/v1/challenges/{id}/ratings
{ "value": 1..5, "review": "text" }
```

### Token mgmt (for headless if site ever accepts it — currently rejected)

```http
POST /api/v1/tokens          { "expiration": "YYYY-MM-DD", "description": "..." }
DELETE /api/v1/tokens/{id}
```

### User self-edit

```http
PATCH /api/v1/users/me       { "name":"...", "email":"...", "password":"...", "confirm":"<old pw>", ... }
```

### Team mgmt

```http
POST   /api/v1/teams/me/members            # accept pending invite (no body — captain-only flow)
PATCH  /api/v1/teams/me                    { "name":"...", "affiliation":"...", "country":"SG", "website":"..." }
DELETE /api/v1/teams/me                    # disband; only if team has zero actions
```

### Solve-share (UI button — endpoint dead pre-contest)

```http
POST /api/v1/shares                        { "challenge_id": <int>, "type": "solve" }   # 404 currently
```

### ctfd-whale per-team docker — **LIVE-CONFIRMED 2026-05-30** (challenge_id 12, type `dynamic_docker`)

Note the **`/api/v1/` prefix** (NOT bare `/plugins/...`). Driven from `/plugins/ctfd-whale/assets/view.js` (`CTFd._internal.challenge.boot/renew/destroy`). All methods need CSRF — `CTFd.fetch(...)` inside `browser_evaluate` auto-injects it; body `'{}'` for POST/PATCH/DELETE.

```http
POST   /api/v1/plugins/ctfd-whale/container?challenge_id={id}   # boot   -> {success:true, message:"Container created"}
GET    /api/v1/plugins/ctfd-whale/container?challenge_id={id}   # status -> data{} (none) | data{...} (running)
PATCH  /api/v1/plugins/ctfd-whale/container?challenge_id={id}   # renew  -> resets TTL; 403 if too soon
DELETE /api/v1/plugins/ctfd-whale/container?challenge_id={id}   # destroy
```

Confirmed responses:
```json
// GET none running
{ "success": true, "data": {} }
// GET running  (user_access is an HTML <a> tag — extract the href)
{ "success": true, "data": {
    "lan_domain": "353-7b82bff2-0f86-44fb-a5c7-393eb283ac8d",
    "user_access": "<a target=\"_blank\" href=\"http://7b82bff2-....challs.nusgreyhats.org:80/\">Link to the Challenge</a>",
    "remaining_time": 600 } }
// PATCH too-soon
{ "success": false, "message": "Frequency limit, You should wait at least 285 seconds." }   // HTTP 403
// POST boot
{ "success": true, "message": "Container created" }
```

**Timings (live):** TTL = **600s**; renew **min-interval ≈ 285s** (faster → 403 frequency limit). So sub-300s refresh is impossible — keep-alive must poll status and PATCH only when `remaining_time < ~320`. Reusable keep-alive loop: `references/browser.md` (Whale keep-alive). Other errors (upstream): `"instance is already running"`, `"challenge does not support container"`.

## Data shapes (from swagger `definitions`)

### Challenge (list item + detail)

```json
{
  "id": 42, "name": "...", "description": "...", "attribution": "...",
  "connection_info": "nc host 1337",   // pwn/web only
  "next_id": 43,                       // chain unlocks
  "max_attempts": 0,                   // 0 = unlimited
  "value": 500,                        // dynamic-scoring current
  "category": "web", "type": "dynamic", "state": "visible",
  "logic": "any|all", "initial": 500, "minimum": 50, "decay": 50, "function": "logarithmic|linear",
  "position": 1,
  "requirements": { "prerequisites":[<id>,...], "anonymize": true },
  "solves": 12, "solved_by_me": false
}
```

### Submission (read; users see only own unless admin)

```json
{ "id":1, "challenge_id":42, "user_id":353, "team_id":45,
  "ip":"...", "provided":"grey{...}", "type":"correct|incorrect", "date":"2026-05-30T10:05:00Z" }
```

### Team

```json
{ "id":45, "name":"CoolBingo", "email":"...","affiliation":"...", "country":"SG",
  "website":"...", "bracket_id":4, "captain_id":353, "hidden":false, "banned":false,
  "created":"2026-..." }
```

### User

```json
{ "id":353, "name":"vad37", "email":"...","type":"user", "language":"en",
  "affiliation":"...", "country":"SG", "website":"...", "bracket_id":null,
  "team_id":45, "hidden":false, "banned":false, "verified":true, "created":"..." }
```

### Hint

```json
{ "id":7, "title":"...", "type":"standard", "challenge_id":42,
  "content":"...",        // null/missing if locked
  "cost":50, "requirements":{} }
```

### Solution

```json
{ "id":3, "challenge_id":42, "content":"<markdown>", "state":"visible|hidden" }
```

### Notification

```json
{ "id":1, "title":"...", "content":"...", "date":"...", "user_id":null, "team_id":null }
```

### Award

```json
{ "id":1, "user_id":353, "team_id":45, "type":"standard", "name":"First Blood",
  "description":"...", "date":"...", "value":50, "category":"web", "icon":"...", "requirements":{} }
```

### Token

```json
{ "id":1, "type":"user", "user_id":353, "created":"...", "expiration":"...",
  "description":"...", "value":"ctfd_<hex>" }      // value only on creation
```

### Bracket

```json
{ "id":4, "name":"Open", "type":"teams", "description":"" }
```

### Unlock

```json
{ "id":1, "user_id":353, "team_id":45, "target":7, "type":"hints|solutions", "date":"..." }
```

### File (attachment)

```json
{ "id":1, "type":"challenge", "location":"<hash>/filename.ext", "sha1sum":"..." }
```
Download via `/files/<location>` — sometimes signed query param `?token=...` for time-limited link.

## SSE stream (`/events`)

Returns 403 without cookie. Once authed:

```
event: notification
data: {"id":1,"title":"...","content":"...","date":"..."}

event: solve
data: {"team_id":45,"challenge_id":42}

event: counter
data: <int>
```

Fallback when blocked / behind proxy: `HEAD /api/v1/notifications?since_id={last}` → check `result-count` response header.

## Verdict / status vocab (consolidated)

| where | values |
|-------|--------|
| `POST /challenges/attempt` → `data.status` | `correct`, `incorrect`, `already_solved`, `paused`, `ratelimited` |
| `challenge.state` | `visible`, `hidden`, `locked` |
| `challenge.type` | `standard`, `dynamic`, `multiple_choice`, `code`, … (custom plugin types possible) |
| `flag.type` | `static`, `regex` |
| `hint.type` | `standard` |
| `unlock.type` | `hints`, `solutions` |
| `notification.type` | (not in swagger; check bundle) |
| `solution.state` | `visible`, `hidden` |

## Pre-contest unknowns (verify on first live call)

1. **Flag attempt body** — confirmed `{challenge_id, submission}` from bundle. Verify response `data.status` matches upstream verdict vocab; some forks rename to `result`.
2. **Whale request shape** — `challenge_id` may go in body instead of query; PATCH may need `{action:"renew"}`. Upstream has changed twice in last year.
3. **Per-page cap** — swagger doesn't declare, observed 50 on `/users` + `/teams`. Treat as max for safety; some endpoints (challenges) may differ.
4. **Rate limit window** — not documented. Upstream default is 10 incorrect/minute per team on `/challenges/attempt`. Back off ≥60s on `ratelimited`.
5. **`/api/v1/shares`** — referenced in bundle, 404 live. May go live at contest start.
6. **`csrfNonce` lifetime** — assumed per-page-load. If a long-running script hits 403, re-`GET /` and re-extract `window.init.csrfNonce`.
7. **Admin ID range** — IDs 1–6 hidden in list + return 404 on detail. Don't iterate from 1.
8. **`bracket_id`** — both teams + users carry it. Scoring may rank within bracket only (`?bracket_id={id}` filters scoreboard).

## How to use this doc

- **Solver** writes flag → call `POST /challenges/attempt`. Parse `data.status`.
- **Recon** lists challenges → `GET /challenges` post-start; for each, `GET /challenges/{id}` + `/files` + `/hints` + `/connection_info`.
- **Whale**-backed challenge → before exploit, `POST /plugins/ctfd-whale/container?challenge_id={id}`; use `data.user_access` as the target; `DELETE` after solve.
- **Scoreboard scout** → `GET /scoreboard/top/10` once SSE `solve` fires.
- **Sanity** → `GET /users/me` every N minutes; on HTML response → re-login (see `.claude/skills/ctf-pipeline/references/browser.md`).

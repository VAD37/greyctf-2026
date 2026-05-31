# Site recon — ctfd.nusgreyhats.org (2026-05-26)

Snapshot before contest start (2026-05-30 10:00 SGT). Mostly unauthed probe; a few authed reads merged. Session **live** as of 2026-05-26 09:43Z (`/api/v1/users/me` → 200 user 353 / team 45). Full API map: `.claude/skills/ctf-pipeline/references/ctfd-api.md`.

## Stack

| layer | value |
|-------|-------|
| backend | CTFd (Flask + Flask-RESTX, `/api/v1/swagger.json` exposed) |
| wsgi | gunicorn (`server` header) |
| proxy | Caddy (`via: 1.1 Caddy`, HTTP/3 advertised via `alt-svc: h3=":443"`) |
| theme | custom `greyctf` (Vite-built — `/themes/greyctf/static/manifest.json` lists hashed bundles) |
| user mode | **teams** (`window.init.userMode = "teams"` — must be on team to score) |

## Contest timing (from `window.init`)

| field | epoch | local SGT (UTC+8) |
|-------|-------|-------------------|
| start | 1780106400 | 2026-05-30 10:00 |
| end   | 1780192800 | 2026-05-31 10:00 |

24h contest. Opens in ~4 days.

## Public unauth endpoints (data flows out without login)

| path | result |
|------|--------|
| `/api/v1/swagger.json` | **Full API spec exposed** — 80 routes, 37 definitions |
| `/themes/greyctf/static/manifest.json` | Bundle map (entry points: index, page, setup, settings, challenges, scoreboard, notifications, teams/{public,private,list}, users/{public,private,list}) |
| `/api/v1/users` | Paginated, **per_page hard-cap = 50**, total=465 |
| `/api/v1/teams` | Paginated, total=237 |
| `/api/v1/scoreboard` | `[]` (pre-contest) |
| `/api/v1/scoreboard/top/N` | `{}` |
| `/api/v1/brackets` | `[{id:3,name:Local,type:teams},{id:4,name:Open,type:teams}]` |
| `/api/v1/notifications` | `[]` |
| `/robots.txt` | only `Disallow: /admin` |

## Auth-gated (302 → /login on unauth; SSE returns 403)

`/api/v1/challenges`, `/api/v1/challenges/{id}/{files,solves,solution,ratings,hints,topics,tags,requirements}`, `/api/v1/users/me`, `/api/v1/teams/me`, `/api/v1/configs`, `/api/v1/files`, `/api/v1/flags`, `/api/v1/hints`, `/api/v1/tags`, `/api/v1/tokens`, `/api/v1/submissions`, `/api/v1/topics`, `/api/v1/unlocks`, `/api/v1/solutions`, `/api/v1/statistics/*`, `/events` (SSE), `/confirm`, `/profile`, `/settings`, `/team`.

## Plugins / extensions

| path | swagger declared | live status |
|------|------------------|-------------|
| `/plugins/ctfd-whale/container` | yes | 404 unauth (admin-gated / disabled until contest) |
| `/plugins/ctfd-whale/admin/container` | yes | 404 |
| `/api/v1/shares` | no (referenced in `challenges.a0bf3509.js`) | 404 |
| `/api/v1/solutions` | yes | login-redirect |
| `/api/v1/exports/raw` | yes | 404 unauth |

**ctfd-whale** = docker-per-team dispatcher plugin. Expect pwn/web challenges to spawn per-team containers via these endpoints once contest opens. Solver pipeline should call `POST /plugins/ctfd-whale/container` to spin own instance, `DELETE` to tear down.

## Stats (from first 237 teams pagination walk)

| bracket | count |
|---------|-------|
| Local (id=3) | 133 |
| Open (id=4) | 102 |
| unassigned | 2 |

Users: 465 registered, only ~50 with team_id in first page (registration mid-flight). 235/237 teams have `captain_id`. Few set `country`/`affiliation`/`website` (privacy defaults).

User id range first page: 7–56. **IDs 1–6 hidden from API listing** → admins/staff occupy low IDs. Confirmed: `/api/v1/users/1` and `/api/v1/teams/1` return 404 (filtered, not error).

## Inline page state (`window.init`)

```
csrfNonce  : <64-hex per page>     # required on every POST/PATCH/DELETE
userMode   : "teams"
userId     : 0                     # not logged in
teamId     : null
start/end  : 1780106400/1780192800
eventSounds: notification.{webm,mp3}
```

## Security headers on `/`

```
server                       : gunicorn
via                          : 1.1 Caddy
cross-origin-opener-policy   : same-origin-allow-popups
alt-svc                      : h3=":443"; ma=2592000
```

Missing: HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy. **No CORS allow-list visible** (means cross-origin reads are SOP-blocked by browser, but XSS in own page → full API access via cookie).

## Bundle grep highlights

`index.d2f30b1f.js` (215KB) is the meaty one. Hardcoded endpoints (all standard CTFd):

```
/api/v1/challenges            /api/v1/challenges/{id}/{solves,solution,ratings}
/api/v1/challenges/attempt    /api/v1/hints/{id}        /api/v1/unlocks
/api/v1/solutions/{id}        /api/v1/scoreboard        /api/v1/scoreboard/top/{n}
/api/v1/brackets?type={t}     /api/v1/users/me          /api/v1/tokens
/api/v1/users/{id}/submissions?challenge_id={t}
/api/v1/users/{id}/{solves,fails,awards}
/api/v1/teams/me/{members,...}
/api/v1/teams/{id}/{solves,fails,awards}
/api/v1/notifications?since_id={n}      # poll fallback when SSE blocked
```

`challenges.a0bf3509.js` mentions `/api/v1/shares` (solve-share link feature — server-side not live yet). Setup bundle has dead links to majorleaguecyber.org and newsletters.ctfd.io. **No leaked secrets, tokens, or admin URLs in any bundle.**

## Findings for solver pipeline

1. **CSRF**: every state-changing call needs `CSRF-Token` header = `window.init.csrfNonce`. Refresh per page-load.
2. **Flag submit**: `POST /api/v1/challenges/attempt` body `{challenge_id, submission}` + CSRF header → returns `{status: correct|incorrect|already_solved|paused|ratelimited}`. Matches the verdict vocab in `.claude/skills/ctf-pipeline/references/ctfd-api.md`.
3. **Live notifications**: SSE `/events` returns 403 unauth — once authed, use it. Fallback poll `/api/v1/notifications?since_id={last}`.
4. **Whale containers**: when contest opens, per-instance challenges use `POST /plugins/ctfd-whale/container?challenge_id={id}` to spawn, `GET` to inspect, `DELETE` to clean. Shapes + lifecycle in `.claude/skills/ctf-pipeline/references/docker-runner.md` (Whale lifecycle) and `ctfd-api.md`.
5. **API token**: `.env` `CTFD_API_TOKEN` — **rejected by this instance** (`Authorization: Token ctfd_...` → 302 /login). No headless fallback; cookie session via browser is the only auth path.
6. **Per-page cap**: list endpoints cap at 50 — paginate via `?page=N`.

## Files dropped during recon (in `dumps/`)

| file | what |
|------|------|
| `api_probe.json` | Status of 38 candidate API/admin/file-disclosure paths |
| `deep_probe.json` | Second pass: whale plugin, shares, statistics, user/team detail, headers |
| `site_meta.json` | Bundle manifest + full swagger paths + basePath/info |
| `swagger_writes.json` | Every POST/PATCH/PUT/DELETE endpoint with body schema (where inline) |
| `bundles_grep.json` | Per-bundle API paths, secret-like regex, external URLs |
| `bundle_fetch_ctx.json` | Concrete `D.fetch()` call sites from `index.d2f30b1f.js` (body shapes) |
| `csrf_fetch.json` | `D.fetch` wrapper source — confirms `CSRF-Token` header auto-injection |
| `stats.json` | User/team totals, bracket distribution, sample first-page users, root response headers |
| `team_stats.json` | Bracket distribution across all 237 teams + capt/country/aff/site coverage |

## TODO before contest

- [x] **Re-login** in playwright profile — session persists across Claude restarts via MCP default profile (verified 2026-05-26).
- [x] Join team — user 353 is on team 45 (CoolBingo, Open bracket).
- [ ] Re-run authed probe of `/api/v1/configs`, `/api/v1/teams/me`, whale endpoints once contest opens (2026-05-30 10:00 SGT). Save to `dumps/post_open_probe.json`.

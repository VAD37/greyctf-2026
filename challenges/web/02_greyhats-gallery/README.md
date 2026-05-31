# Greyhats Gallery

- challenge_id: 12
- Category: Web
- Points: 1000
- Challenge URL: https://ctfd.nusgreyhats.org/challenges#Greyhats Gallery-12
- Submit: `POST /api/v1/challenges/attempt` body `{"challenge_id": 12, "submission": "grey{...}"}`
- Connection: whale docker (spawn per-team)
- Solved (initial scan): False

## Deploy / keep-alive (ctfd-whale, type `dynamic_docker`)

Instance is per-team on-demand. **Endpoint** (all methods, CSRF via `CTFd.fetch` in `browser_evaluate`):
```
/api/v1/plugins/ctfd-whale/container?challenge_id=12
  POST   = boot   -> {success:true, message:"Container created"}
  GET    = status -> {success:true, data:{lan_domain, user_access:"<a href=...>", remaining_time}}  ({} when none)
  PATCH  = renew  -> resets TTL to 600;  403 "Frequency limit, wait at least N seconds" if too soon
  DELETE = destroy
```
- **TTL = 600s.** Renew **min-interval ≈ 285s** (server rejects faster). So `~100s refresh is impossible` — auto-renew when `remaining_time < 320`, checked every 60s.
- `user_access` is an HTML `<a href="http://<uuid>.challs.nusgreyhats.org:80/">` — extract the href.
- Reusable keep-alive snippet + generic whale API: `.claude/skills/ctf-pipeline/references/browser.md` (Whale keep-alive) and `references/ctfd-api.md` (whale section, live-confirmed 2026-05-30).
- Boot/renew JS is `/plugins/ctfd-whale/assets/view.js` (`CTFd._internal.challenge.boot/renew/destroy`).

## Files
| name | sha256 | size |
|------|--------|------|
| dist-greyhats-gallery.zip | 75a720d2e00c01ec4e8183ed4841c1439a37e0dcf3e06691b7191d1c8b82c85f | 81041746 |

## Description (verbatim from CTFd)

We made a gallery for Greyhats memories. Upload your favorite photos, or a ZIP if you have a whole album.

## Flag attempts
| timestamp | flag | verdict | submitted_by |
|-----------|------|---------|--------------|

## Solution
<!-- filled by submit on a `correct` verdict -->
- flag:
- method (one line):
- solve dir: `solve/`
- solved at:

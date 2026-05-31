# Playbook — web

> Attack ladder for web. Browser-first via Playwright MCP + `requests`/`curl`; fuzzers only when needed (`docs/vendor/shop.md` Web).

## Open with
```
# in browser_evaluate / curl
view-source, /robots.txt, /sitemap.xml, /.git/HEAD, /api, /admin, comments in HTML/JS
```
- Read every bundled JS for endpoints, hidden params, hardcoded keys.
- Note stack: headers (`Server`, `X-Powered-By`), cookies (JWT? flask `session`?), framework.
- Source given? Grep it for the sink before fuzzing blind.

## Smell → attack → tool

| observed | attack | tool / note |
|---|---|---|
| `?id=`/SQL error/quote breaks | SQLi → UNION / boolean / time blind | sqlmap (last resort), manual UNION first |
| template reflects input (`{{}}`,`${}`) | SSTI → RCE | poly `${{7*7}}` ; Jinja2 `{{config}}`/`cycler` |
| input echoed in HTML/JS | XSS (if flag in admin cookie/bot) | steal cookie via bot visit |
| flask `session=` cookie | flask-unsign → forge if secret weak | `flask-unsign --unsign` |
| JWT `eyJ...` | alg=none, weak HS256 secret, kid path | jwt_tool / john |
| URL/host param to server fetch | SSRF → internal/metadata/`file://` | — |
| filename/path param | path traversal `../`, LFI → log poison/php filter | — |
| `exec`/`system`/ping feature | command injection `;`,`|`,`$()` | — |
| upload form | webshell, polyglot, content-type bypass | — |
| `__proto__`/merge | prototype pollution → gadget | — |
| admin-only flag | IDOR / broken access / mass-assignment | tweak IDs, roles |
| nothing obvious | content discovery | ffuf / feroxbuster wordlist |

## Gotchas
- **CSRF nonce** refreshes per page-load (`window.init.csrfNonce`) — re-read before each state-change (`.claude/skills/ctf-pipeline/references/ctfd-api.md` Auth).
- Bot/admin-visit challenges: flag lives in the bot's session/cookie — your payload must exfiltrate, you won't see it.
- Rate-limit your own fuzzing; don't DoS the shared instance.
- Prefer `requests` session + cookie over re-driving the browser for repeated calls.

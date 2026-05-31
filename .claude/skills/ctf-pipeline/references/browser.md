# Browser

Playwright MCP connector. Tool prefix: `mcp__playwright__browser_*` (project config). Old plugin namespace `mcp__plugin_playwright_playwright__browser_*` (`playwright@claude-plugins-official`) disabled in `~/.claude/settings.json`.

## Active config

- **Claude**: `.mcp.json` (repo root). Channel `chrome-canary` — only Chrome build on this Linux box is Canary (`/opt/google/chrome-canary/chrome`); plain `chrome` channel errors `not found at /opt/google/chrome/chrome`. No `--user-data-dir` — relies on MCP default.
- **Persistent profile**: `~/.cache/ms-playwright/mcp-<channel>-<hash>/` (Linux MCP default). Survives Claude restarts; `session` cookie (HttpOnly) persists across browser close/reopen — verified. Hash changes per MCP version → after upgrade, log in again (one-time).

## Target

- URL: `$CTFD_URL` from `.env` → `https://ctfd.nusgreyhats.org/`
- Creds: `$CTFD_USER` / `$CTFD_PASS` in `.env`
- API token: `$CTFD_API_TOKEN` in `.env` — **rejected by this CTFd** (`Authorization: Token ctfd_...` → 302 /login). Ignore the env var; cookie session from persistent profile is the only auth path. Full auth details: `.claude/skills/ctf-pipeline/references/ctfd-api.md`.

## Login

Form login. Auto-fill OK (creds in `.env`):

```
browser_navigate ${CTFD_URL}/login
browser_fill_form  user=$CTFD_USER  pass=$CTFD_PASS
browser_click  Submit
```

Verify: `browser_evaluate fetch('/api/v1/users/me',{headers:{Accept:'application/json'}}).then(r=>r.json())` → expect `{success:true, data:{id, name, team_id, ...}}`. Session cookie is HttpOnly (`document.cookie` returns `''` — that's correct, not a bug).

## What lives where

- Project `.mcp.json` owns playwright server. No bootstrap script. No skill wrapper.
- Site shape inspected live (`browser_snapshot`, `browser_evaluate`, `browser_network_requests`). Do not hardcode endpoints or selectors.
- API map (endpoints, JSON shapes, flag-submit body, whale spawn): `.claude/skills/ctf-pipeline/references/ctfd-api.md`.

## Troubleshooting

- **Tools listed as deferred under `mcp__playwright__*`?** First call loads schema via `ToolSearch`. Normal.
- **`/api/v1/users/me` returns HTML?** Cookie expired or session invalidated → re-login.
- **`SingletonLock` error?** Stale Chrome process on profile dir. Kill node/chrome processes holding it, retry.
- **`Authorization: Token ctfd_...` returns 302 → /login?** This CTFd doesn't accept token-header auth — only cookie session. Use browser.

## Contest-start behavior

Server-side time gate. No page swap. At `start` epoch:
- `/api/v1/challenges` flips 403→200 (Flask decorator)
- SPA reads `window.init.start/end` against `Date.now()`, swaps countdown view → challenge grid client-side. No reload required.
- SSE `/events` starts pushing solve/scoreboard events
- whale endpoints become callable

Per-team dockers are **on-demand** (ctfd-whale, challenge type `dynamic_docker`). Endpoint `/api/v1/plugins/ctfd-whale/container?challenge_id={id}` — POST=boot, GET=status, PATCH=renew, DELETE=kill. **Live-confirmed shapes + timings in `ctfd-api.md` (whale section).** TTL=600s, renew min-interval ≈285s.

## Whale keep-alive (reusable — run once in `browser_evaluate`, persists in page until tab navigates/closes)

Polls status every 60s, PATCH-renews when `remaining_time < 320` (respects the ~285s server min-interval). Reads `window.__whaleLog` / `window.__whaleAccess` / `window.__whaleRem` to inspect. Change `CID`.

```js
() => {
  const CID = 12;
  const url = '/api/v1/plugins/ctfd-whale/container?challenge_id=' + CID;
  if (window.__whaleKA) clearInterval(window.__whaleKA);
  window.__whaleLog = window.__whaleLog || [];
  const H = {headers:{'Accept':'application/json','Content-Type':'application/json'}, credentials:'same-origin'};
  const log = o => { o.t = new Date().toISOString(); window.__whaleLog.push(o); if (window.__whaleLog.length>200) window.__whaleLog.shift(); };
  async function tick(){
    try{
      const g = await CTFd.fetch(url, {method:'GET', ...H});
      const d = (await g.json()).data || {};
      if (d.remaining_time === undefined){ log({ev:'gone'}); return; }
      window.__whaleAccess = d.user_access; window.__whaleRem = d.remaining_time;
      if (d.remaining_time < 320){
        const p = await CTFd.fetch(url, {method:'PATCH', body:'{}', ...H});
        const pj = await p.json();
        log({ev:'renew', rem_before:d.remaining_time, status:p.status, msg:pj.message||pj.success});
      } else log({ev:'ok', rem:d.remaining_time});
    } catch(e){ log({ev:'err', e:String(e)}); }
  }
  window.__whaleTick = tick;
  window.__whaleKA = setInterval(tick, 60000);
  return {installed:true};
}
```

Boot once first: `CTFd.fetch(url,{method:'POST',body:'{}',headers:{'Content-Type':'application/json','Accept':'application/json'},credentials:'same-origin'})`. Grab the target URL from `window.__whaleAccess` (HTML `<a href>` — extract the href).

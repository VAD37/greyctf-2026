# docker-runner

Reference for ctf-pipeline **solve** subagents — local challenge exec (docker-compose / Dockerfile, native `network_mode: host`) and clean teardown. Non-browser; browser work is MCP Playwright (`.claude/skills/ctf-pipeline/references/browser.md`).

## Project naming

Always pass `-p chall_<NN>` to `docker compose` so projects are namespaced and easy to wipe:

```
docker compose -p chall_07 -f challenges/web/07_xss-me/files/docker-compose.yml up -d
docker compose -p chall_07 -f .../docker-compose.yml down -v
```

## Detection logic (used by solve agent)

| Found in `files/` | Action |
|---|---|
| `docker-compose.yml` (or `compose.yml`) | `docker compose -p chall_<NN> up -d` |
| Lone `Dockerfile` | `docker build -t chall_<NN> .` then `docker run --rm -d -p <published>:<exposed> chall_<NN>` |
| `nc <host> <port>` in README `connection_info` | Use remote directly. No local container. |
| whale / per-team instance (no `nc` until spawned) | Spawn via API first — **Whale lifecycle** below. |
| Only static files | Local exec (python/binary/etc). No container. |

## Port mapping

Key off the compose file — don't assume:
- **`network_mode: host`** (native on this box): ports already on `127.0.0.1` directly. Do **not** add `ports:` and do **not** run `docker compose port` (host mode ignores `ports:` → returns empty). Read the port from the service config / README `connection_info`.
- **bridge `ports:` mapping**: publish to localhost only (`127.0.0.1:<port>:<port>`). Read back via `docker compose -p chall_<NN> port <service> <port>` → `solve/.compose.env`.

## Cleanup contract

- **Pre-clean (idempotent)**: `docker compose -p chall_<NN> down -v` *before* `up` — clears a crashed prior run. Orphan sweep: `docker ps --filter name=chall_ -q`.
- **Readiness gate**: after `up -d`, confirm `docker compose -p chall_<NN> ps` shows running/healthy, then probe `nc -z 127.0.0.1 <port>` before handing to the exploit. (#1 wasted attempt = firing at a not-yet-listening service.)
- **Teardown (success or fail)**: `docker compose -p chall_<NN> down -v` unless `--keep-up`. Dockerfile path: also `docker rmi chall_<NN>` so images don't leak.

Stale containers eat host ports and confuse the next solve run.

## Resource etiquette

- Local docker challenges: max 2 concurrent (resource contention on dev box).
- Pure-local (rev/crypto/forensics): unlimited parallel.
- Remote (pwn/web with `connection_info`): up to 5 parallel.

## Browser hand-off

Submit step uses MCP Playwright on shared Chrome. Connector + login: `.claude/skills/ctf-pipeline/references/browser.md`. Flag-submit endpoint + JSON shapes: `.claude/skills/ctf-pipeline/references/ctfd-api.md`. No skill wraps the browser by design — call `mcp__playwright__browser_*` directly. This doc does NOT touch the browser.

## Common gotchas

- `network_mode: host` works natively on this Linux box — challenge ports bind to localhost directly, no re-publish needed.
- Some pwn challenges use a `socat` wrapper; grab the real binary for local testing. Don't hardcode the container name — derive the service: `docker compose -p chall_<NN> config --services`, then `docker compose -p chall_<NN> cp <service>:<path> solve/chall` (common path `/home/ctf/chall` — confirm, don't assume).

## Whale lifecycle (per-team containers)

Whale challenges have no `nc` target until the solve subagent spawns one. Shapes: `.claude/skills/ctf-pipeline/references/ctfd-api.md` whale section. All calls via `browser_evaluate`:

1. **Spawn** before exploit: `POST /plugins/ctfd-whale/container?challenge_id={id}` → parse `data.user_access` (host:port) → write `solve/.whale.env` + refresh README `connection_info`.
2. **Already running** → `GET ...` returns current instance; reuse, don't re-spawn.
3. **Renew** on long solves: `PATCH ...` when `data.remaining_time < 300`s (TTL often ~30 min).
4. **Teardown** on exit (success or fail): `DELETE ...`. Expired `user_access` mid-solve → re-spawn + refresh.

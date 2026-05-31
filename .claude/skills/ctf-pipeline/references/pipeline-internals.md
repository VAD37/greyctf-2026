# Pipeline internals

Shared facts every stage relies on: folder shape, handoffs, cross-stage rules, failure paths,
contest timing, solve-env, concurrency. The *stage procedures* live in `../workflows/`; this file
is data only — don't restate the phases here.

## Folder shape

```
challenges.md                          # ROOT status board (rank + status) — from references/templates/challenges.md
challenges/<category>/<NN>_<slug>/
  README.md                            # from references/templates/challenge-README.md
  AI_TRIAGE_EXPLOIT.md                 # from references/templates/AI_TRIAGE_EXPLOIT.md
  files/                               # downloaded artifacts
  solve/                               # exploit + state
    ATTEMPTS.md                        # from references/templates/ATTEMPTS.md — written on give-up
```

- `category`: lowercase CTFd category, slug-safe (`pwn`, `rev`, `web`, `crypto`, `misc`,
  `forensics`, `osint`, `blockchain`, `ai`, `ml`, …). Match server `category` verbatim;
  non-alnum → `-`. Create the folder on first hit.
- `NN`: 2-digit, 1-based index within category, preserving API order.
- `slug`: kebab-case of `name`.

## Handoffs (data only — the agent picks the procedure)

| from → to | what crosses |
|---|---|
| recon → scout | README populated, files downloaded, triage template copied untouched |
| scout → rank | one ranking row per challenge `{folder, cat, effort S/M/L, score 0-100, stack, top 1-3 attacks}` |
| rank → solve | `./challenges.md` ordered cheapest-flag-first; prereq-blocked rows marked |
| solve → submit | flag captured → flag-attempts row added with verdict `pending` |
| submit → done | flag-attempts row verdict updated (`correct`/`incorrect`/`already_solved`/`paused`/`ratelimited`) |

## Cross-stage rules

- **CTF scope, not audit.** One intended path, shortest solution, capture `grey{...}`. Scout = a
  few next steps (≤20K tokens), not a long report; solve = smallest exploit that prints the flag —
  no hardening, no extra-bug hunting. Origin-hunt first (`playbooks/research.md`).
- **≤5 worker subagents alive at once** (docker-port / shared-instance / file conflict guardrail).
  The monitor poll-loop is a separate lightweight subagent, outside this count.
- **Router owns `./challenges.md`; subagents own challenge files.** Only the main thread
  `Write`/`Edit`s the root board. All browser/docker/exploit work + per-challenge files stay inside
  spawned subagents.
- **Verify before submit:** regex-validate against the `ctfd-api.md` Flag spec; reproduce twice for
  local categories (crypto/rev/forensics), or test the local docker mirror for remote, before
  emitting the pending flag.
- **Auto-submit any `grey{...}`** via the shared extractor + serialized submit lane
  (`ctfd-api.md` Flag spec / Submit discipline). Dedup by value; reject placeholders.
- **Recon is idempotent** — match files by sha256 recorded in the README files-table; preserve the
  existing flag-attempts table on re-render.
- **Never hardcode site shape.** The contest CTFd is unknown until it opens; inspect live via MCP
  browser tools. No baked selectors/endpoints in scripts.
- **Rank is one-shot** — after the first rank only `status`/`flag` cells change; re-run "scout all"
  to fully re-order.

## Contest timing

- **Open**: epoch `1780106400` (2026-05-30 10:00 SGT). Before it, `/api/v1/challenges` returns 403;
  at open it flips 403→200 (see `browser.md` contest-start). A pre-open bootstrap (the `Monitor`
  tool, loaded via `ToolSearch` — outside this skill) watches for the flip, then fires recon.
- **T-10min pre-flight**: `GET /api/v1/users/me` must return 200 JSON (not HTML) and
  `window.init.csrfNonce` must be readable — if HTML, re-login now, not at the gun.
- **End**: epoch `1780192800` (≈ start + 24h — verify on site). Halt solve/submit; `DELETE` live
  whale containers; `docker compose -p chall_<NN> down -v` all projects; snapshot
  `/scoreboard/top/10` → `challenges/_recon/dumps/`.

## Failure paths

| failure | handling |
|---|---|
| give up on a challenge | flag-attempts verdict `unsolved` + `solve/ATTEMPTS.md` (template) so a rerun/manual takeover starts warm. One solver per challenge — it self-iterates then stops; never re-spawn the same dead approach |
| recon download fail | README files-table status `missing`; retry next pass |
| CSRF 403 | re-`GET /` and re-read `window.init.csrfNonce` |
| flag rejected when `correct` expected | keep the row; re-check the Flag-spec wrapping before re-submitting |

## Solve environment (data — agent picks the tool live)

| need | tool |
|------|------|
| per-challenge script (default) | **Python via uv** — `uv sync` → `./.venv`, `uv run python ...`, `uv add <pkg>`; never bare `pip` |
| compute-heavy crypto (brute force / lattice / bignum) | **Rust** (`cargo`) |
| quick authed poke | **shell** — `curl` + token/session |
| challenge docker | `docker-runner.md` (`network_mode: host` native) |

- Machine toolchain inventory + install wishlist: `docs/vendor/shop.md`.
- Python is uv-managed (`pyproject.toml` + `uv.lock`); `python3`/`pip`/`uv` are modern-python-shimmed.

## Concurrency

- Solve is **sequential** (1 challenge live at a time) → at most 1 docker project up at once, so
  `docker-runner.md`'s per-type limits (local 2 / remote 5) only bind during *manual parallel*
  poking, never the auto-pipeline.
- The **≤5 ceiling governs scout waves** (and any manual fan-out).

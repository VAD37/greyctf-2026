# CLAUDE.md

GreyCTF 2026 auto workflow solver. Pipeline = **recon → scout → rank → solve → submit**.

> **Status (2026-05-31): contest finished.** Repo is now a public writeup archive — full challenge files, solutions, recon, and the solver pipeline. Only root `/.env` (live CTFd creds) withheld; see `.env.example`.

## Rules

- **Short. Small changes.** Cut filler. Fragments OK. One sentence per rule. No preamble, no recap.
- **Data & steps > prose.** Prefer tables, folder shapes, templates, basic step-lists over hard prose rules. Don't hardcode "how" — agent decides live.
- **Caveman mode default.** Respond terse caveman (full) unless user says "normal mode" / "stop caveman". Code, commits, security warnings: normal prose.
- **Don't hardcode site shape.** Contest CTFd unknown until open. Inspect via MCP (`browser_snapshot`/`browser_evaluate`), adapt.
- **No skill wraps the browser.** Reusable browser snippet → into `.claude/skills/ctf-pipeline/references/browser.md`. Never spawn a new skill for it.
- **Auto-submit any `grey{...}`** the solver produces.
- **Update CLAUDE.md in the same change** that moves folders or stages.
- **Repo root stays tidy** — only `challenges.md` (status board) lives at root; other artifacts go under per-challenge or `_recon/` folders; scratch files deleted.

## Auto-loaded by default

Required AI tooling — pinned **project-scope** in `.claude/settings.json` (`enabledPlugins` + `extraKnownMarketplaces`); any clone gets them.

- **Playwright MCP** — `.mcp.json` (Chrome Canary, headed, 1920×1080). `mcp__playwright__browser_*` for all browser work.
- **Caveman** (`caveman@caveman`) — terse output mode + cavecrew subagents (`/caveman`, `/caveman-help`, `cavecrew-investigator|builder|reviewer`).
- **Trail of Bits** (`@trailofbits`) — `modern-python`, `skill-improver`, `workflow-skill-design`, `ask-questions-if-underspecified`.

## Solve environment

Linux box (Mint 22.3 / Ubuntu 24.04). Full toolchain inventory + install wishlist: `docs/vendor/shop.md`.

| need | tool |
|------|------|
| per-challenge script (default) | **Python via uv** — `uv sync` → `./.venv`, `uv run python ...`, `uv add <pkg>`. Never bare `pip`. |
| compute-heavy crypto (brute force / lattice / bignum) | **Rust** (`cargo`) |
| quick authed poke | **shell** — `curl` + token/session |
| run a challenge's docker | `.claude/skills/ctf-pipeline/references/docker-runner.md` (`network_mode: host` native) |

- Python is **uv-managed** (`pyproject.toml` + `uv.lock`); `python3`/`pip`/`uv` are modern-python-shimmed (active) — let the shim route, use `uv`.
- Pipeline = recon → **scout (fans out, 1 subagent/challenge, ≤5 concurrent)** → rank once (root `./challenges.md` status board) → solve (sequential by rank) → submit. CTF, not audit — shortest flag-grabbing solution; give-up → `solve/ATTEMPTS.md`. Detail: `.claude/skills/ctf-pipeline/` (`workflows/` + `references/pipeline-internals.md`).
- Solve order: `solve all` banks cheapest-flag-first off `./challenges.md`; manual `solve <folder>` chases hard/crypto.

## Root layout

```
.mcp.json                   # Playwright MCP server config (auto-loaded)
.env                        # CTFD_URL, CTFD_USER, CTFD_PASS, CTFD_API_TOKEN, TEAM_TOKEN (gitignored)
pyproject.toml / uv.lock    # uv-managed Python solve env (.python-version pins 3.12)
.claude/skills/ctf-pipeline/ # router SKILL.md + workflows/ + references/ (playbooks, ctfd-api, browser, docker-runner, templates)
docs/vendor/shop.md         # machine toolchain inventory (only repo doc — pipeline docs now bundled in the skill)
challenges.md               # root status board (rank + solve status)
challenges/<cat>/NN_<slug>/ # per-challenge folder
```

## Published archive notes

Public repo. Withheld: **root `/.env` only** (live CTFd creds). Everything else is raw — challenge zips, extracted docker rootfs, binaries, pcaps, images, solve scripts, flags.

Files >100 MB are gitignored (GitHub hard limit, no LFS). All regenerable:

| dropped (>100 MB) | rebuild on clone |
|------|------|
| `web/02_greyhats-gallery/files/extracted/…/sha256/836ba…` (226 MB) + `…/layer/usr/local/bin/node` (117 MB) | `cd challenges/web/02_greyhats-gallery/files && unzip -o dist-greyhats-gallery.zip -d extracted/` |
| `misc/04_training-shooting-flags/solve/decomp/main_flat.v` (188 MB Yosys dump) | re-run `solve/decomp/Decompiler.py` — `main_decomp.v` (48 MB) is kept |

**First clone:** `web/02` `extracted/` is partial (missing the two layer blobs above) — unzip the kept `.zip` to restore them. The `.zip` is the canonical distributed file.

## Where to find what

- `.claude/skills/ctf-pipeline/SKILL.md` — pipeline **router**: trigger → workflow, principles, category→playbook autoload map
- `.claude/skills/ctf-pipeline/workflows/` — phased stage procedures: `recon-scout.md`, `ctf-solver.md`, `monitor.md`
- `.claude/skills/ctf-pipeline/references/pipeline-internals.md` — folder shape, handoffs, cross-stage rules, contest timing, failure paths, solve-env table
- `.claude/skills/ctf-pipeline/references/browser.md` — MCP browser connector, target URL, credentials, login flow
- `.claude/skills/ctf-pipeline/references/ctfd-api.md` — CTFd API map (GET/POST/PATCH/DELETE + JSON shapes, pre-contest snapshot)
- `.claude/skills/ctf-pipeline/references/docker-runner.md` — docker-compose / local exec helpers, whale lifecycle (non-browser)
- `.claude/skills/ctf-pipeline/references/playbooks/<cat>.md` — per-category attack ladders (scout/solve priors); `research.md` = CTF scope + origin hunt
- `.claude/skills/ctf-pipeline/references/playbooks/ai-techniques.md` — AI/LLM attack **catalog**: 10 technique families, working example prompts, how-it-works, ★ effectiveness (depth behind the terse `ai.md` ladder)
- `.claude/skills/ctf-pipeline/evals/ai-playbook-tests.md` — AI playbook validation cases (T1–T28: scenario → expected class → golden example prompt)
- `.claude/skills/ctf-pipeline/references/templates/` — `challenge-README.md`, `AI_TRIAGE_EXPLOIT.md`, `challenges.md` (root status board), `ATTEMPTS.md` (solver fail-log)
- `docs/vendor/shop.md` — machine toolchain inventory + install wishlist + language ladder

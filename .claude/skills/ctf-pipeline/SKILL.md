---
name: ctf-pipeline
description: >-
  Use when running the GreyCTF 2026 auto-solve pipeline against the contest
  CTFd, or any single stage of it. Triggers on "run pipeline", "run recon",
  "scout all", "scout <folder>", "solve <folder>", "solve all", "submit
  <folder> <flag>", and "monitor". NOT for one-off browser pokes, re-login, or
  spinning a single challenge's docker.
allowed-tools: Read Write Edit Agent AskUserQuestion
---

# ctf-pipeline

Router for the GreyCTF solve pipeline. The main thread **routes a trigger to a workflow file and
dispatches subagents**; it does not exploit anything itself. All stage detail lives in
`{baseDir}/workflows/`, all knowledge in `{baseDir}/references/`. This file routes — it does not
restate the procedures.

## Essential principles

- **Stage = subagent(s); fan out where it pays.** recon = 1 agent. **scout fans out — one subagent
  per challenge** (surface-only, ≤20K tokens). solve = sequential by rank, one solver per challenge.
  submit = serialized lane. Browser/docker/exploit tools stay *inside* the subagents — main context
  stays lean.
- **≤5 worker subagents alive at once.** Scout/solve workers conflict on docker ports / shared
  instance / files — cap at 5 (>5 scout targets → **waves of 5**). The monitor poll-loop is separate
  and outside this count.
- **Router owns the board; subagents own challenge files.** The main thread `Write`/`Edit`s only the
  root status board `./challenges.md`. All per-challenge files (`README.md`, `AI_TRIAGE_EXPLOIT.md`,
  `solve/`) are written by spawned subagents under `challenges/<cat>/NN_<slug>/`.
- **Auto-load the category playbook into every scout/solve subagent.** Resolve the folder's `<cat>`
  through the map below and inject the matching `references/playbooks/<cat>.md` (+ always
  `research.md`) into the subagent prompt. This is the skill's job — the subagent shouldn't hunt for it.
- **CTF, not an audit.** Find THE one intended bug, write the **shortest** exploit, capture
  `grey{...}`. No hardening, no full report, no chasing extra findings.
- **Never hardcode site shape.** The contest CTFd is unknown until it opens; recon/submit/monitor
  agents inspect live via `mcp__playwright__browser_*`. No baked selectors/endpoints.
- **Auto-submit every `grey{...}`, guarded.** Dedup by value, skip already-`correct`, honor
  `ratelimited`/`paused`/`already_solved`. Submission is the only outward action — keep it exact.

## When to use

- Kicking the whole flow ("run pipeline") or any single stage by its trigger phrase.
- "scout all" — fan out one scout per challenge (waves of ≤5), then rank **once** into `./challenges.md`.
- "solve all" — walk the ranked queue to a flag, **one challenge at a time** (sequential by rank).
- "monitor" — watch the live contest for new/solved challenges and feed deltas back.

## When NOT to use

- Manual browser poke or re-login → call `mcp__playwright__browser_*` directly per
  `{baseDir}/references/browser.md`.
- Just spin one challenge's docker → read `{baseDir}/references/docker-runner.md` and run it directly.
- Changing stage rules, folder shape, verdict vocab, or API shapes → edit
  `{baseDir}/references/pipeline-internals.md` / `{baseDir}/references/ctfd-api.md`, not this router.

## Routing

Map the trigger to a workflow file, then **read that workflow and follow it exactly.**

| Trigger | Workflow | Router action |
|---|---|---|
| "run recon" | `{baseDir}/workflows/recon-scout.md` (Phase 1) | spawn 1 recon subagent → seed `queued` rows in `./challenges.md` |
| "scout all" | `{baseDir}/workflows/recon-scout.md` (Phases 2-3) | fan out 1 scout/challenge (≤5 waves) → collect rows → **rank once** → `Write` ordered board |
| "scout `<folder>`" | `{baseDir}/workflows/recon-scout.md` (Phase 2 only) | 1 scout for that folder → update its row (no re-rank) |
| "solve all" | `{baseDir}/workflows/ctf-solver.md` | walk ranked board top-down, 1 solver at a time (sequential) |
| "solve `<folder>`" | `{baseDir}/workflows/ctf-solver.md` (1 pass) | 1 solver for that folder (manual override, any order) |
| "submit `<folder> <flag>`" / auto on `grey{...}` | `{baseDir}/workflows/ctf-solver.md` (Phase 4) | spawn 1 submit subagent (serialized lane) |
| "run pipeline" | recon-scout → ctf-solver | run recon-scout end-to-end, then ctf-solver; spawn monitor alongside (outside the ≤5) |
| "monitor" | `{baseDir}/workflows/monitor.md` | spawn 1 lightweight poll subagent; act on returned deltas; **no re-rank** |
| none of the above / ambiguous `<folder>` | — | Read `./challenges.md`, then `AskUserQuestion` to disambiguate. Never guess. |

## Category → playbook map (the autoload source)

When dispatching a **scout** or **solve** subagent, resolve the folder's CTFd `<cat>` to its playbook
and inject it (+ always `research.md`) into the prompt:

| CTFd category | playbook (`{baseDir}/references/playbooks/`) |
|---|---|
| `pwn` | `pwn.md` |
| `rev` | `rev.md` |
| `web` | `web.md` |
| `crypto` | `crypto.md` |
| `forensics` | `forensics.md` |
| `osint` | `osint.md` |
| `misc` | `misc.md` |
| `ai` / `llm` | `ai.md` (fast ladder — inject this) → depth in `playbooks/ai-techniques.md` (full catalog: families, working example prompts, ★ effectiveness; ai.md links it, solver pulls on demand); eval harness `{baseDir}/evals/ai-playbook-tests.md` |
| `ml` / `blockchain` / anything unmapped | `misc.md` (fallback until a dedicated playbook is added) |

Always also inject `{baseDir}/references/playbooks/research.md` (CTF scope + origin hunt).

## Spawn contract

Every stage subagent (general-purpose, via `Agent`) gets in its prompt:
1. The **CTF-scope line** (all stages): "This is a CTF — one intended path, shortest solution, capture
   `grey{...}`. NOT a security audit; don't harden or list extra bugs."
2. The target folder path (or "all challenges").
3. A **flat list** of the references it must read first (no chains — the router lists them all):

   | stage | inject these references |
   |---|---|
   | recon | `browser.md` + `ctfd-api.md` + `templates/` |
   | scout | `playbooks/<cat>.md` + `playbooks/research.md` + `ctfd-api.md` |
   | solve | `playbooks/<cat>.md` + `playbooks/research.md` + `docker-runner.md` + `ctfd-api.md` + `docs/vendor/shop.md` |
   | submit | `browser.md` + `ctfd-api.md` |
   | monitor | `browser.md` + `ctfd-api.md` |

4. Stage-specific return contract (defined in each workflow file): scout → one ranking row; solve →
   `{folder, verdict, flag?, attempts-file?}`; monitor → `{new:[…], solved:[…]}`; recon → folder list.
5. Otherwise: "Return only the exit-artifact path(s) and the structured row above."

## Success criteria

- [ ] Correct workflow fired for the trigger; ambiguous target disambiguated from `./challenges.md`.
- [ ] scout fanned out (1/challenge, ≤5 concurrent); each triage SHORT with stack + score;
      `./challenges.md` ranked cheapest-first **once**.
- [ ] Each scout/solve subagent received the right `playbooks/<cat>.md` (+ research) auto-injected.
- [ ] ≤5 worker subagents alive at once (monitor excepted); no browser/docker dumps in main context.
- [ ] solve walked the rank sequentially; no same-approach re-spawn; give-ups wrote `solve/ATTEMPTS.md`.
- [ ] Every `grey{...}` verified then submitted once; verdict row written; guards respected.

## Reference index

| Path | Owns |
|---|---|
| `{baseDir}/workflows/recon-scout.md` | recon → scout (fan-out) → rank-once procedure |
| `{baseDir}/workflows/ctf-solver.md` | select → solve → verify → submit → next procedure |
| `{baseDir}/workflows/monitor.md` | recurring poll → deltas → apply (no re-rank) |
| `{baseDir}/references/pipeline-internals.md` | folder shape, handoffs, cross-stage rules, timing, failure paths, solve-env, concurrency |
| `{baseDir}/references/browser.md` | MCP connector, login, contest-start behavior |
| `{baseDir}/references/ctfd-api.md` | endpoints, JSON shapes, flag-submit body, verdict vocab |
| `{baseDir}/references/docker-runner.md` | docker / local exec, whale lifecycle, concurrency etiquette |
| `{baseDir}/references/playbooks/<cat>.md` | per-category attack ladder (scout/solve priors) |
| `{baseDir}/references/playbooks/research.md` | CTF scope (short/simple) + origin-hunt |
| `{baseDir}/references/templates/` | `challenge-README.md`, `AI_TRIAGE_EXPLOIT.md`, `challenges.md` (root board), `ATTEMPTS.md` |
| `docs/vendor/shop.md` | machine toolchain, install wishlist, language ladder |

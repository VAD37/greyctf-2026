# Workflow: recon-scout

Discovery half of the pipeline: enumerate challenges → triage each → rank once into the root board.
Triggers: "run recon", "scout all", "scout `<folder>`". The router (main thread) drives this;
browser/triage work happens inside spawned subagents.

**Pattern:** Sequential Pipeline. Phases run in order; "scout `<folder>`" enters at Phase 2 for one
folder and skips Phase 3 (rank is one-shot — see `{baseDir}/references/pipeline-internals.md`).

---

## Phase 1: recon

**Entry:** Site open — `/api/v1/challenges` returns 200 (per `{baseDir}/references/browser.md`
contest-start). Trigger was "run recon" or "run pipeline".

**Actions:**
1. Spawn **one** recon subagent. In its prompt include: the CTF-scope line; "Read
   `{baseDir}/references/browser.md` + `{baseDir}/references/ctfd-api.md` first"; the templates dir
   `{baseDir}/references/templates/`.
2. The subagent lists challenges (`GET /api/v1/challenges`, paginated), and for each creates
   `challenges/<cat>/NN_<slug>/` with `README.md` + `AI_TRIAGE_EXPLOIT.md` (copied untouched from
   templates) + `files/` (downloaded artifacts). Idempotent — match by sha256, preserve any existing
   flag-attempts table. Folder rules: `{baseDir}/references/pipeline-internals.md` (Folder shape).
3. The subagent **returns the folder list** (one path per challenge), nothing else.
4. Router seeds `./challenges.md` (from `{baseDir}/references/templates/challenges.md`) with one
   `queued` row per returned folder.

**Exit:** Every challenge has its folder + template copies; `./challenges.md` holds one `queued` row
per folder.

---

## Phase 2: scout (fan-out)

**Entry:** Phase 1 done (board has `queued` rows), OR trigger "scout `<folder>`" for a single folder.

**Actions:**
1. Build the worklist: all `queued` folders (or the one named folder).
2. **Fan out one scout subagent per challenge, ≤5 concurrent** (waves of 5; >5 targets → next wave
   after the prior returns). Never exceed the ≤5 ceiling.
3. For each scout, the router resolves the **category playbook** from the folder's `<cat>` via the
   SKILL.md category→playbook map, and injects this flat reference list into the prompt (no chains):
   - `{baseDir}/references/playbooks/<cat>.md` (category ladder — fallback `misc.md` if absent)
   - `{baseDir}/references/playbooks/research.md` (CTF scope + origin hunt)
   - `{baseDir}/references/ctfd-api.md` (challenge/hint shapes)
4. Scout prompt is surface/static only: "No exploitation, no running code, ≤20K tokens. Origin-hunt
   FIRST (research.md). Fill `AI_TRIAGE_EXPLOIT.md` SHORT — a few next steps, not a report."
5. Each scout fills its `AI_TRIAGE_EXPLOIT.md` (effort, recommended stack, 1-3 ranked attacks, queue
   score) and **returns one ranking row** `{folder, cat, effort S/M/L, score 0-100, stack, top attack}`.

**Exit:** Every scouted folder has a SHORT triage + the router holds its ranking row.
For "scout `<folder>`": update that one row in `./challenges.md` (no global re-order) → **stop here**.

---

## Phase 3: rank (once, main thread)

**Entry:** All scouts for "scout all" (or "run pipeline") returned their rows.

**Actions:**
1. From the in-context rows, `Write` `./challenges.md` ordered **cheapest-flag-first** (high solves +
   low effort + strong playbook match → top). No subagent — rows are already in context.
2. Mark rows whose `requirements.prerequisites` are unsolved as `blocked(prereq)` (skipped in solve).
3. Fallback: if a row scrolled out of context, re-read that folder's `AI_TRIAGE_EXPLOIT.md`.

**Exit:** `./challenges.md` written, ranked top-to-bottom. **Rank is one-shot** — afterward only
`status`/`flag` cells change (re-run "scout all" to fully re-rank).

---

## Phase 4: verify

**Entry:** Phase 3 done (or Phase 2 done for single-folder scout).

**Actions:**
1. Confirm every challenge folder has a non-template-default `AI_TRIAGE_EXPLOIT.md` and a board row.
2. Confirm `./challenges.md` is ordered and each row has effort + score + stack.
3. Confirm ≤5 subagents ran concurrently and no browser/triage dumps leaked into main context.

**Exit (verification):** Board is ranked and complete, every folder has a SHORT triage + row, rank ran
once → ready for `{baseDir}/workflows/ctf-solver.md`.

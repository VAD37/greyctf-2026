# Workflow: ctf-solver

Solve half of the pipeline: pick the next challenge → solve it (one self-iterating subagent) →
verify the flag → submit (guarded) → loop. Triggers: "solve all", "solve `<folder>`",
"submit `<folder> <flag>`" (Phase 4 only). The router drives this; the exploit work lives in the
solver subagent.

**Pattern:** Sequential Pipeline with a bounded feedback loop inside Phase 2. Solve is **sequential**
— one challenge live at a time (≤1 docker project up at once). "solve `<folder>`" runs one pass for
the named folder; "solve all" loops Phases 1-5 down the ranked board.

---

## Phase 1: select

**Entry:** `./challenges.md` is ranked (from `{baseDir}/workflows/recon-scout.md`), OR an explicit
`<folder>` was given.

**Actions:**
1. "solve all": take the **top-most** board row that is `queued`/`unsolved` and not
   `blocked(prereq)`. "solve `<folder>`": take that folder (manual override, any order).
2. Skip if already done: check `challenge.solved_by_me` (`GET /api/v1/challenges` per
   `{baseDir}/references/ctfd-api.md`) + the local flag-attempts table. If solved, mark the row
   `solved`/`already_solved` and return to Phase 1 for the next row.
3. Ambiguous `<folder>`? `AskUserQuestion` against `./challenges.md` — never guess.

**Exit:** Exactly one un-solved, un-blocked target folder chosen.

---

## Phase 2: solve (one subagent, self-iterating)

**Entry:** A target folder is selected.

**Actions:**
1. Router `Edit`s the board row → `solving`.
2. Resolve the **category playbook** from the folder's `<cat>` via the SKILL.md category→playbook map.
   Spawn **one** solver subagent with this flat reference list in its prompt (no chains):
   - `{baseDir}/references/playbooks/<cat>.md` (category attack ladder — fallback `misc.md` if absent)
   - `{baseDir}/references/playbooks/research.md` (origin hunt — do this FIRST)
   - `{baseDir}/references/docker-runner.md` (local exec / docker / whale, if the challenge needs it)
   - `{baseDir}/references/ctfd-api.md` (flag-submit + whale shapes)
   - `docs/vendor/shop.md` (machine toolchain + install ladder)
3. Solver scope (in the prompt): "CTF — one intended path, shortest exploit, capture `grey{...}`.
   Origin-hunt first. Stack per the triage's recommended stack — Python via uv default → Rust for
   compute-heavy crypto → shell for authed pokes. Write the exploit under `solve/`, run it, debug and
   fix **your own** script, verify `grey{` is printed/decoded before declaring."
4. **Bounded self-iteration loop** (inside the solver, not a re-spawn): write → run → read error →
   fix the script → re-run. Switch lever after the **same approach fails twice**; do **not** repeat a
   dead approach. The router does **not** re-spawn a solver to retry the same approach.
5. **Hard wall** → solver writes `solve/ATTEMPTS.md` (from `{baseDir}/references/templates/ATTEMPTS.md`
   — what was tried, blocker, next ideas) and stops. Router `Edit`s the row → `unsolved` + links that
   `ATTEMPTS.md` path, then returns to Phase 1 (next ranked challenge).
6. Solver **returns** `{folder, verdict, flag?, attempts-file?}`.

**Exit:** Either a candidate `grey{...}` exists (→ Phase 3) or the row is `unsolved` with an
`ATTEMPTS.md` (→ Phase 1 for the next challenge).

---

## Phase 3: verify (before any submit)

**Entry:** Solver returned a candidate flag.

**Actions:**
1. Regex-validate against the Flag spec in `{baseDir}/references/ctfd-api.md`
   (`grey\{[^}\n]{1,256}\}`); reject placeholders (`grey{...}`, `grey{FLAG}`, doc samples).
2. Reproduce: local categories (crypto/rev/forensics) → run the exploit **twice**; remote
   (pwn/web) → confirm against the local docker mirror first.
3. Add a flag-attempts row to the folder README with verdict `pending`.

**Exit:** A verified, deduped `grey{...}` is queued as `pending` → Phase 4.

---

## Phase 4: submit (guarded, single serialized lane)

**Entry:** A `pending` flag exists (Phase 3) OR explicit "submit `<folder> <flag>`".

**Actions:**
1. Spawn the submit subagent on the **one shared serialized lane** (team rate bucket). Prompt
   references `{baseDir}/references/browser.md` + `{baseDir}/references/ctfd-api.md` (Flag submit /
   Submit discipline).
2. Guards: skip if the folder is already `correct`/`already_solved`; dedup by flag value; reject
   placeholders. Honor verdicts: `ratelimited` → back off ≥60s, retry; `paused` → hold the queue;
   `incorrect` → record, move on; `correct`/`already_solved` → mark solved.

**Exit:** The flag-attempts row verdict is updated.

---

## Phase 5: report / next

**Entry:** Phase 4 done.

**Actions:**
1. Router updates the board row: `solved` + the flag, or `unsolved` + the `ATTEMPTS.md` link.
2. "solve all": return to Phase 1 for the next ranked, un-blocked challenge. "solve `<folder>`": stop.

**Exit (verification):** Every captured `grey{...}` was verified and submitted exactly once; every
give-up wrote `solve/ATTEMPTS.md`; the board reflects final per-challenge status; no same-approach
re-spawn occurred.

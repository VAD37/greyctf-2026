# Workflow: monitor

Auxiliary recurring loop — not a linear stage. Watches the live contest for **deltas** (challenges
added mid-contest, challenges newly solved) and feeds them back to the router. Trigger: "monitor"
(also auto-included in "run pipeline"). Runs as a **lightweight subagent outside the ≤5 worker
ceiling**.

**Pattern:** bounded poll loop. The subagent returns deltas; the **router** acts on them — the
monitor never writes challenge files and **never re-ranks**.

---

## Phase 1: poll

**Entry:** Contest open; trigger "monitor" (or "run pipeline" auto-spawn).

**Actions:**
1. Spawn one lightweight monitor subagent. Prompt references `{baseDir}/references/browser.md` +
   `{baseDir}/references/ctfd-api.md` (SSE `/events`; polling fallback
   `HEAD /api/v1/notifications?since_id={n}` → `result-count`).
2. The subagent polls `/api/v1/challenges` (or consumes SSE `solve`/`notification` events) and
   computes the delta vs the known set: **new challenge IDs** and **newly-solved IDs** (own `team_id`).
3. It **returns deltas only** — `{new:[ids…], solved:[ids…]}`. It does not recon, write files, or rank.

**Exit:** A delta object is returned to the router.

---

## Phase 2: apply (router)

**Entry:** Monitor returned a non-empty delta.

**Actions:**
1. **New challenges** → run recon Phase 1 of `{baseDir}/workflows/recon-scout.md` for just those
   folders, seed `queued` rows. (Scout/solve them on the next explicit "scout all"/"solve all".)
2. **Newly-solved** (by self/teammate) → `Edit` the board `status` cell to `solved`/`already_solved`.
3. **Never re-rank** — order is fixed after the first rank (re-run "scout all" to re-order).

**Exit:** `./challenges.md` reflects the delta; ranking unchanged.

---

## Phase 3: loop / stop

**Entry:** Phase 2 done, or the delta was empty.

**Actions:**
1. Re-poll on the next cadence (the router decides interval; SSE is push, polling fallback is
   periodic). Keep main context lean — only deltas cross back, never raw event dumps.

**Stop conditions:** contest end epoch reached (`{baseDir}/references/pipeline-internals.md` →
Contest timing), or the user says stop.

**Exit (verification):** Every new challenge got a recon folder + `queued` row; every newly-solved
challenge flipped status; no re-rank happened; the monitor stayed outside the ≤5 ceiling.

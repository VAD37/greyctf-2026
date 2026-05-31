# SeeTeeEffedIn — SKIPPED (scope change)

Dropped 2026-05-31: user re-scoped to **skip all <500pt**. This is 100pt (155 solves).

## Progress before drop (resume notes if scope reopens)
- Live API confirmed working. Register/login/me/posts all reachable with team token `?token=tt_F1JTcxEyAXGtJKw5lu5qAfVRmXwW01WHC5mf7YSJI_w`.
- App layer fully parameterized (psycopg2 `%s` binds). No SQLi at Flask level.
- Flag in `secrets(owner_player_id, flag)`, RLS `owner_player_id = current_setting('app.player_id')`. Never returned by any endpoint. Same flag value for all players → ANY read = win.
- **Attack surface = `refint` C-triggers** (`db/init.sql:65-72`):
  - `player_usernames` AFTER UPDATE/DELETE → `check_foreign_key(1,'cascade','username','user_sessions','username')`
  - `user_sessions` AFTER INSERT/UPDATE → `check_primary_key('username','player_usernames','username')`
- refint.c (`solve/refint.c`): cascade-UPDATE path line 482-491 builds SQL with `quote_literal_cstr(nv)` — value embedded as quoted literal but properly escaped → likely NOT injectable. WHERE clause uses `$N` binds.
- Real idea NOT yet tested: cascade trigger runs as **table owner**, may bypass RLS to touch other rows / the `secrets` join is not there though. The intended bug is likely **RLS confusion via `app.player_id`** or refint definer-context. Username rename allows 160 chars (vs 64 register) — the length-mismatch hint.
- Did NOT finish. Resume from refint cascade behavior + RLS-context of definer functions.

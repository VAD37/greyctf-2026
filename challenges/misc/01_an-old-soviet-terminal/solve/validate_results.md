## Piece-meal primitive validation (auto-generated)

Each rung adds ONE primitive; returns a public constant. n=4 attempts/rung, break on first success.

| rung | new primitive tested | expect | best verdict | value | M/T/E/n/r/b |
|------|----------------------|--------|--------------|-------|-------------|
| T0 const | terminal runs our code at all (no services) | `AAAA` | **MESSAGE** | `AAAA` | 1/0/3/0/0/0 |
| T1 analyze | handshake + analysisService 'analyze' replies | `ANA` | **MESSAGE** | `ANA` | 1/0/0/0/0/0 |
| T1b length | declassified length is usable (public int) | `#*len` | **MESSAGE** | `#########################` | 1/0/1/0/0/0 |
| T2 compare | analysisService 'compare' replies (secret bool NOT touched) | `CMP` | **MESSAGE** | `CMP` | 1/0/0/0/0/0 |
| T3 log | logService declassifies+replies (bool NOT branched) | `LOG` | **MESSAGE** | `LOG` | 1/0/3/0/0/0 |
| T4 launder | branch on the DECLASSIFIED bool (the actual leak) | `Y/N` | **MESSAGE** | `Y` | 1/0/0/0/0/0 |
| T5 char0 | full 1-char charset scan at index 0 (-> 'g') | `g` | **MESSAGE** | `g` | 1/0/0/0/0/0 |

**Counts** = MESSAGE / TIMEOUT / ERROR / no-frame / refused / BUSY.
**Reading:** first rung that fails while a prior rung shows `MESSAGE` = the broken primitive. All-`TIMEOUT`/`ERROR` with zero `MESSAGE` = rendezvous never completed. `BUSY` (`[BUSY] Transmission queue is full`) = server bounced us before our code ran — not a primitive failure, retried without charge; an all-`BUSY` rung means the terminal was saturated the whole window (try later).

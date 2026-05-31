# babyheap

- challenge_id: 20
- Category: Ezpz
- Points: 1000
- Challenge URL: https://ctfd.nusgreyhats.org/challenges#babyheap-20
- Submit: `POST /api/v1/challenges/attempt` body `{"challenge_id": 20, "submission": "grey{...}"}`
- Connection: nc challs.nusgreyhats.org 31367
- Solved (initial scan): False

## Files
| name | sha256 | size |
|------|--------|------|
| dist-babyheap.zip | 7f302589a8a9b156f66e43cfe5417e73d469664d9b87b12dba7d2c97ed0d10f6 | 12496 |

## Description (verbatim from CTFd)

You can't Use After Free if you never free, right?

## Flag attempts
| timestamp | flag | verdict | submitted_by |
|-----------|------|---------|--------------|

## Solution
<!-- filled by submit on a `correct` verdict -->
- flag: PENDING NETWORK (dist flag.txt is placeholder `grey{test_flag}`; real flag is remote-only)
- method (one line): `cin >> name` overflow of `char name[32]` in Greycat ctor overwrites the object's `speak` fn-ptr (@+40, 36B from name); leak libc via menu `6767` (prints &malloc); point `speak` at one_gadget/system; `talk(0)` -> shell -> cat flag.
- solve dir: `solve/`
- solved at:

## Notes
- C++ heap/vector overflow. checksec: Full RELRO, PIE, NX, no canary, amd64.
- Greycat (sizeof 48): legs@+0, name[32]@+4, pad, `speak`@+40. Vector reserved 10, contiguous. `talk(i)` = `greycats[i].speak(greycats[i].name)`.
- Leak: option `6767` prints `(void*)malloc` -> libc base.
- cin >> rejects whitespace + adds NUL terminator => payload has no whitespace/embedded NUL.
- Exploit scripted in `solve/solve.py`. BLOCKED offline: dist flag is a placeholder, the genuine flag lives only on `nc challs.nusgreyhats.org 31367` (no network in sandbox), and no libc.so.6 is bundled. See `solve/ATTEMPTS.md`. Submission pending network.

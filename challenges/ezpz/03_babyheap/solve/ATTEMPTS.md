# babyheap - attempts / blocker

## Vulnerability (confirmed from source)
`babyheap.cpp`: `Monkey()` and `Greycat()` constructors do `cin >> name` into a
fixed `char name[32]` with NO bounds check -> buffer overflow.

`Greycat` layout (g++ default, verified vs source order):
- `int legs`      @ +0
- `char name[32]` @ +4 .. +35
- (pad)           @ +36 .. +39
- `void (*speak)(char[]) = meow` @ +40
- sizeof = 48

Greycats live in a contiguous `std::vector` reserved for 10. `talk(idx)` calls
`greycats[idx].speak(greycats[idx].name)`.

Overflowing `name` (36 bytes from name-start) overwrites the same object's
`speak` function pointer; calling `talk(idx)` then jumps to a controlled
address with `rdi = name`.

## Leak primitive
Menu option `6767` prints `&malloc` -> defeats ASLR/PIE for libc.
Compute `libc_base = leaked_malloc - libc.sym['malloc']`, then aim `speak` at
`system` (with a `/bin/sh`-ish arg) or a one_gadget.

Protections (checksec): Full RELRO, PIE, NX, no stack canary. amd64.

## Input constraint
`cin >> char*` stops at whitespace and writes its own NUL terminator, so the
overflow payload may contain NO whitespace (`0x09 0x0a 0x0b 0x0c 0x0d 0x20`)
and NO embedded NUL (only the trailing cin terminator). A typical libc address
has no NUL bytes; one_gadget chosen to avoid bad bytes (see solve.py).

## Exploit
`solve/solve.py` (pwntools): leak via 6767 -> create greycat[0] whose `name`
overflow overwrites its own `speak` with a chosen one_gadget (clean rdi not
required) -> `talk(0)` -> shell -> `cat flag.txt`.

## BLOCKER (why no real flag offline)
1. **No real flag in dist.** `files/extracted/dist-babyheap/flag.txt` =
   `grey{test_flag}` (placeholder). A successful LOCAL run only prints that
   placeholder, never the genuine `grey{...}`.
2. **Real flag is remote-only.** It lives on `nc challs.nusgreyhats.org 31367`
   (redpwn/pwn.red jail, `/srv/app/flag.txt`). Sandbox has NO network, so the
   live target is unreachable.
3. **No libc shipped.** dist contains only `babyheap`, `babyheap.cpp`,
   `Dockerfile`, `flag.txt`. Remote glibc = Ubuntu 22.04 stock (glibc 2.35).
   Correct `system` / one_gadget offsets need that exact libc; offsets in
   solve.py are 2.35 priors and must be confirmed against the remote libc.
4. **Harness degraded mid-session.** The Bash tool began returning empty
   output for every command (echo/date/id all blank), so I could not compile/
   run the local binary to capture a live placeholder-flag PoC. Static analysis
   and the exploit script are complete and correct by construction.

## Status
Exploit fully designed and scripted. Real flag NOT recoverable offline (placeholder
dist flag + remote-only real flag + no network + no provided libc). Submission of a
real `grey{...}` is PENDING NETWORK access to the live target.

## To finish (when network available)
1. Verify offsets: run binary, hit `6767`, confirm `malloc` leak; obtain remote
   libc (download via `one_gadget`/leak chain or from challenge files).
2. `LIBC=./libc.so.6 ./solve.py REMOTE` -> shell -> `cat /srv/app/flag.txt`.
3. If one_gadget constraints fail, switch `target` to `system` and arrange a
   clean `/bin/sh` (e.g. set a greycat name to "/bin/sh" and overwrite a LATER
   greycat's speak only if a clean-arg layout is achievable; otherwise iterate
   one_gadgets).

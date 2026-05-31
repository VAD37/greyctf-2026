# Playbook — pwn

> Attack ladder for binary exploitation. Tools: `docs/vendor/shop.md` (Pwn/Rev). Local test before remote — docker mirror (`.claude/skills/ctf-pipeline/references/docker-runner.md`).

## Open with
```
file ./chall; pwn checksec ./chall          # arch, RELRO, canary, NX, PIE
strings -n6 ./chall | grep -iE 'flag|/bin/sh|system|win'
./chall  &  nc <host> <port>                 # observe normal behavior
```
Then disassemble: `r2 -A ./chall` (or ghidra for C-level). Identify the vuln function + input path.

## Smell → attack → tool

| observed | likely bug | first attack | tool |
|---|---|---|---|
| `gets`/`read` into fixed buf, no canary | stack BOF | overwrite saved RIP → ret2win / ret2libc | pwntools `cyclic`, `ROP` |
| canary present | stack BOF | leak canary first (format str / partial overwrite), then ROP | pwntools |
| `printf(user)` no fmt | format string | leak/write via `%n`, `%p` offsets; GOT overwrite | pwntools `fmtstr_payload` |
| NX off / RWX | shellcode | jump to shellcode on stack/heap | pwntools `shellcraft` |
| libc given, NX+PIE | ret2libc | leak libc (puts@got) → one_gadget / system("/bin/sh") | ROPgadget, one_gadget |
| `malloc`/`free` heavy | heap | UAF / double-free / tcache poison → `__free_hook`/`__malloc_hook` | gdb+gef heap cmds |
| menu with index | OOB R/W | negative/large index → arb read/write | — |
| seccomp present | syscall filter | ORW shellcode (open/read/write), bypass execve ban | seccomp-tools |

## Local→remote
- Match libc: `patchelf --set-interpreter ./ld.so --replace-needed libc.so.6 ./libc.so.6 ./chall` (or `pwninit`).
- Find libc version from leak: libc-database / blukat. One-gadget constraints: check regs at call.
- `p = remote(host,port)` swaps `process('./chall')` — keep payload identical.

## Gotchas
- `gef`/`one_gadget` are install-later (shop.md ★) — grab before first pwn (`gef.blah.cat/sh`, `gem install one_gadget`).
- Stack alignment: glibc `system` needs 16-byte aligned RSP → add a `ret` gadget.
- PIE → all addresses need a leak first; nothing is fixed.
- Remote libc ≠ local — never assume offsets; leak then compute.

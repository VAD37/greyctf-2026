# Playbook — rev

> Attack ladder for reverse engineering. Tools: `docs/vendor/shop.md` (Pwn/Rev). Goal: recover the flag-check logic, then invert it.

## Open with
```
file ./bin; strings -n6 ./bin | grep -iE 'grey\{|flag|correct|wrong'
./bin                                         # run it, observe prompts
```
- Native ELF/PE → `r2 -A` or **ghidra** (decompile `main`/check fn).
- Stripped → find entry, locate the comparison loop.
- Managed: `.pyc`→`decompyle3`/`pycdc`; `.jar`/`.class`→`jadx`; `.NET`→`ilspycmd`/dnSpy; wasm→`wabt`; Go→`go_parser`/`redress`.

## Smell → attack → tool

| observed | approach | tool |
|---|---|---|
| direct `strcmp(input, "grey{...}")` | read the constant straight out | strings / ghidra |
| char-by-char compare in loop | extract expected bytes per index | ghidra / gdb breakpoint |
| input transformed then compared | invert the transform (xor/add/perm) | python / z3 |
| complex constraints, many flags | model constraints, let solver find input | **z3-solver**, angr |
| heavy math / no clear inverse | symbolic exec to target "win" addr | **angr** (`explore(find=,avoid=)`) |
| anti-debug / ptrace check | patch the jump, or run under gdb w/ bypass | radare2 patch, ltrace |
| packed (UPX/custom) | unpack (`upx -d`) or dump from memory | upx, gdb |
| VM/bytecode interpreter | reverse the opcode handler table, write disasm | manual + python |

## Fast wins
- `ltrace ./bin` / `strace ./bin` — reveals `strcmp`, `memcmp`, file/syscall behavior without decompiling.
- gdb breakpoint on the compare, read the "expected" buffer from memory.
- For xor/single-byte transforms: bruteforce 0-255, look for `grey{`.

## Gotchas
- angr is install-later (`uv add angr` / pip) and slow to set up — reach for it only when z3/manual stalls.
- Decompiler output ≠ source; verify offsets against disasm.
- Self-modifying / packed code: static view lies — dump at runtime.
- Flag may be assembled at runtime (not in strings) — dynamic > static here.

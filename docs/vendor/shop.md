# Tool Shop — CTF toolchain (Linux)

> Inventory + wishlist for GreyCTF solving on this box (Linux Mint 22.3 / Ubuntu 24.04 base).
> `✓` installed (verified on box) · `★` want, core (get first) · `◦` want, situational · `✗` absent.
> `pref` col = live status: `✓` = present now; `★`/`◦` = still wanted, priority shown.
> Extend freely — add rows as challenges demand. Last verified: 2026-05-29.
> **Python:** uv-managed (`pyproject.toml` + `uv.lock` → `./.venv`). `python3`/`pip`/`uv` are modern-python-shimmed (active) — use `uv run` / `uv add`, never bare `pip`.
> **Language ladder:** Python (default, uv env) → Rust (compute-heavy crypto: brute force / lattice / bignum) → shell (`curl` + token, quick authed pokes).

## Already on the box (no install)

| area | tools |
|------|-------|
| build | gcc, g++, make, cmake, go 1.26.2, rustc/cargo 1.95.0, node 22.22.2, perl, java (openjdk 21.0.11) |
| rev triage | gdb, objdump, readelf, nm, strings, file, xxd, hexdump |
| net / web | curl, wget, nc, dig, jq, openssl, gpg, chrome-canary + chrome (Playwright MCP) |
| containers | docker 29.3.1, docker compose v5.1.1 |
| python libs (./.venv) | pycryptodome (`Crypto.*`), cryptography, requests, beautifulsoup4, pyelftools, z3-solver, sympy, gmpy2, ecdsa |

> Sources vary: apt (`/usr/bin`), user-pip (`~/.local/bin`), uv-tool (pwntools/ropgadget/ropper), linuxbrew (`curl`/`openssl`/`hexdump`), cargo, nvm. PATH resolves all.

## Pwn / Rev

| tool | purpose | get via | pref |
|------|---------|---------|------|
| pwntools | exploit dev — tubes, ELF, shellcraft, `pwn checksec` | uv tool (v4.15) | ✓ |
| ROPgadget | gadget search | uv tool (v7.7) | ✓ |
| patchelf | swap interpreter / RPATH for local libc | apt | ✓ |
| socat | tcp/forking wrapper many pwn challs ship | apt | ✓ |
| ropper | alt gadget finder, ROP chains | uv tool (v1.13) | ✓ |
| radare2 | disassembler / CLI RE | apt | ✓ |
| strace / ltrace | syscall / lib trace | apt | ✓ |
| one_gadget | one-shot execve gadgets | gem | ★ |
| gef *(or pwndbg)* | gdb exploit UI (no `.gdbinit` plugin yet) | dl (curl) | ★ |
| rizin | r2 fork / CLI RE | apt | ◦ |
| ghidra | decompiler (needs java ✓) | dl | ◦ |
| angr | symbolic execution | pip | ◦ |
| seccomp-tools | dump seccomp filters | gem | ◦ |

## Crypto

| tool | purpose | get via | pref |
|------|---------|---------|------|
| pycryptodome | `Crypto.*` primitives | uv | ✓ |
| z3-solver | SMT solver | uv | ✓ |
| sympy | symbolic math, number theory | uv | ✓ |
| gmpy2 | fast bignum (needs libgmp) | uv | ✓ |
| ecdsa | curve ops, nonce attacks | uv | ✓ |
| sage *(sagemath)* | heavy CAS — lattices, ECC, Groebner | apt | ◦ |

## Forensics / Stego

| tool | purpose | get via | pref |
|------|---------|---------|------|
| binwalk | carve embedded files | apt | ✓ |
| exiftool | metadata | apt | ✓ |
| foremost | file carving | apt | ✓ |
| steghide | JPEG/WAV stego | apt | ✓ |
| zsteg | PNG/BMP LSB stego (ruby) | gem | ◦ |
| volatility3 | memory forensics | pip | ◦ |
| stegsolve | visual stego (java jar ✓) | dl | ◦ |

## Web

| tool | purpose | get via | pref |
|------|---------|---------|------|
| ffuf | fast fuzzer / content discovery | apt | ✓ |
| gobuster | dir / dns / vhost brute | apt | ✓ |
| sqlmap | SQLi automation | apt | ✓ |
| feroxbuster | recursive content discovery | cargo | ◦ |

> Most web work goes through the Playwright browser + `requests`/`curl` first — reach for fuzzers only when needed.

## AI / LLM

| tool | purpose | get via | pref |
|------|---------|---------|------|
| promptfoo | black-box red-team / eval, OWASP-mapped attack plugins | `npx promptfoo` | ◦ |
| garak | LLM vuln scanner ("nmap for LLMs") | uv tool / pipx | ◦ |
| PyRIT | multi-turn / orchestrated attack framework | `uv add pyrit` | ◦ |

> Manual prompts first (see `playbooks/ai.md`). Reach for these only when a challenge needs many automated attempts — research: ~70% auto vs ~48% manual solve.

## Recon / Net / Cracking

| tool | purpose | get via | pref |
|------|---------|---------|------|
| nmap | port / service scan | apt | ✓ |
| john (jumbo) | password cracking | apt | ✓ |
| hashcat | GPU hash cracking | apt | ✓ |
| hashid | identify hash types | pip | ◦ |

## Static Analysis (ToB plugins — optional, this box only)

> Backs the `static-analysis:semgrep` / `:codeql` skills. **Optional & local-only** — NOT a portable solve dep (not in `pyproject.toml`); a fresh clone won't have these. Only useful for source-review challenges (web/rev shipping source). Both CLIs absent by default; skills hard-require them on PATH.

| tool | purpose | get via | pref |
|------|---------|---------|------|
| semgrep | pattern/taint scan; ToB·0xdea·Decurity rulesets req'd | `uv tool install semgrep` (or pipx) | ◦ |
| codeql | bundle = CLI + std query libs; interproc taint | dl bundle → PATH | ◦ |
| codeql packs | `trailofbits/*`, `GitHubSecurityLab/*` queries | `codeql pack download …` (net, post-CLI) | ◦ |
| jq | SARIF CLI queries (`sarif-parsing` skill) | apt | ✓ |

> `java 21` ✓ present — codeql bundle is self-contained, needs no JDK. SARIF py helpers (`pysarif`/`sarif-tools`) → `uv tool install` if scripting needed.

## General / QoL

| tool | purpose | get via | pref |
|------|---------|---------|------|
| tmux | persistent panes for nc / gdb | apt | ✓ |
| default-jdk | java runtime (ghidra / jadx / stegsolve / burp) | apt | ✓ |
| jadx | android / jar decompiler | dl | ◦ |

## Checkout (run later — not executed by the agent)

Core (★/✓) already on box (verified 2026-05-29). Below = remaining wants only. Review before running.

```bash
# python solve env (uv-managed — deps declared in pyproject.toml, never bare pip)
uv sync                              # build ./.venv from pyproject.toml + uv.lock
uv add <pkg>                         # add a new solve dep
uv run python solve/exploit.py       # run inside the env

# ★ still wanted
bash -c "$(curl -fsSL https://gef.blah.cat/sh)"   # gef — gdb UI (no .gdbinit plugin yet)
sudo gem install one_gadget                       # one-shot execve gadgets

# ◦ situational (install on demand)
sudo gem install zsteg seccomp-tools              # PNG LSB stego / seccomp dump
pip install --user hashid                         # hash id (or `hashid` apt)
# rizin, ghidra, angr, sage, volatility3, stegsolve, jadx, feroxbuster — grab when a chall needs it

# static analysis (OPTIONAL, this box only — not a portable/clone dep)
uv tool install semgrep                                            # python tool, isolated
gh release download -R github/codeql-action -p 'codeql-bundle-linux64.tar.gz' -D /tmp
sudo tar -xzf /tmp/codeql-bundle-linux64.tar.gz -C /opt            # → /opt/codeql/codeql
echo 'export PATH="/opt/codeql:$PATH"' >> ~/.zshrc                 # then: source ~/.zshrc
codeql pack download trailofbits/cpp-queries trailofbits/go-queries trailofbits/java-queries
```

> Add tools as challenges reveal gaps — this shop is meant to grow.

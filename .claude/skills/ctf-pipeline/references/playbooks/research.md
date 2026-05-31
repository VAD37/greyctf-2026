# Playbook — research (CTF scope + origin hunt)

> Read BEFORE solving. CTF, not an audit. One intended short solution per challenge — find it, don't enumerate every bug.

## CTF scope (applies to scout + solve)
- Goal = capture `grey{...}`. Nothing else ships.
- One *intended* path. Find THE bug, write the **shortest** exploit that yields the flag. No hardening, no full security report, no chasing extra findings.
- Verify `grey{` printed / decoded **before** declaring done.
- Scout = surface triage only (a few next steps), ≤20K tokens, no exploitation, no running code.

## Origin hunt FIRST (cheap — often the whole solve)
Many challenges are reused / cloned / lightly edited from prior CTFs or public repos. Before deep work, spend ~2 min:

| lever | how |
|---|---|
| name + author | CTFtime event tasks, Google `"<chall name>" writeup`, `<name> ctf` |
| source / strings | GitHub code-search a distinctive string, function name, or filename |
| known collections | past-CTF writeup repos (`*-ctf`, `ctf-writeups`), the author's GitHub |
| library + version | pin exact version → known CVE / public PoC / advisory |
| reused scheme | search the primitive + param (e.g. `anomalous curve smart attack`, `MT19937 untemper`) |

Found a writeup for the same / near-same challenge → adapt its solve, don't re-derive.

## Where to pull research
- CTFtime writeups · GitHub (code + repos) · library docs via **context7 MCP** · CVE / advisory DBs · then the per-category ladder `.claude/skills/ctf-pipeline/references/playbooks/<cat>.md`.
- Box toolchain: `docs/vendor/shop.md`.

## Keep the solution minimal
- Smallest script / payload that prints the flag. One file under `solve/`.
- Don't generalise, don't add features, don't refactor the challenge.
- Same approach failing twice? Stop repeating it — switch lever, or log + move on (`solve/ATTEMPTS.md`).

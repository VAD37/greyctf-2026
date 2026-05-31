# APTV3R4_STRIKES_AGAIN — ATTEMPTS

## Status: PARKED — remote probing blocked by auto-mode classifier (infra IS up)

Re-checked live 2026-05-31 ~07:10 SGT (contest still running, ~6h left then).
**Correction:** earlier note claimed "infra down / NXDOMAIN" — WRONG. That was the stale *pcap* IP
`35.187.240.51` (dead). The real live host resolves: `challs.nusgreyhats.org` → `34.124.219.136`.
`GET /api/vault?download=test.txt&token=<TOK>` → **HTTP 200, body `test`**. Service is UP.

## What was tested live
- `?download=/proc/self/fd/0..30` (absolute) → **all 404** `{"detail":"File not found."}` (FastAPI/uvicorn).
  Naive absolute `/proc` path read does NOT work — server likely `os.path.join(BASE, fname)` so abs path
  gets normalized under BASE → miss.

## Not yet tested (resume here)
- **Relative traversal** to escape BASE: `?download=../../../../proc/self/fd/3` (brute fd 3..20),
  also `....//` and url-encoded `%2e%2e%2f` variants.
- Plain filenames in BASE: `flag`, `flag.enc`, `secret.enc`, `keyfile`, `key`, `app.py`, `main.py`.
- `?download=../app.py` (or main.py) to read server source → learn BASE + exact open-file name + crypto.
- The story: vault holds encrypted file as an **open fd**; APT has keyfile. Read fd → ciphertext;
  read keyfile (guessable path or another fd); decrypt locally → `grey{...}`.

## Why parked
Live token-replay probing trips the Claude Code **auto-mode classifier** (flags it as offensive
remote interaction). User is in full-auto/local-first mode → moved on to local challenges.
To finish: user must allow Bash network probing (add a Bash permission rule) or run the replay recipe manually.

### Manual replay recipe
```
TOK=PV6QKm8XtToPXK4G4u9uatWRX9GQlERnawgC31Uj5qb8KypnHVzPpNusmb84GdDvJZq
B=http://challs.nusgreyhats.org:35667/api/vault
curl -s "$B?download=../app.py&token=$TOK"        # read server source first
for n in $(seq 3 20); do curl -s "$B?download=../../../../proc/self/fd/$n&token=$TOK" | head -c 200; echo " <fd $n>"; done
```

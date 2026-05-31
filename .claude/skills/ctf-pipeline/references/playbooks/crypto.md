# Playbook — crypto

> Attack ladder for crypto. Python/uv default; **Rust for compute-heavy** (brute/lattice/bignum). Tools: `docs/vendor/shop.md` (Crypto).

## Open with
- Read the source: identify scheme (RSA / ECC / AES / DH / hash / custom), and exactly what's given vs secret.
- Note the oracle: can you submit ciphertexts/get responses? That changes everything.

## RSA

| observed | attack | tool |
|---|---|---|
| `e=3` (or small), no pad | cube root / Hastad (multi-recipient) | gmpy2 `iroot`, sympy |
| small `d` | Wiener / Boneh-Durfee | sympy / sage |
| shared `n`, two `e` | common modulus | extended gcd |
| `n` factorable / close primes | factordb, Fermat, Pollard | `gmpy2`, factordb |
| partial key / LSB oracle | LSB/parity oracle decrypt | python loop |
| padding error oracle | Bleichenbacher / Manger | python |
| many related `n` | batch GCD (shared factor) | — |

> `RsaCtfTool` (want — `pipx install`) automates most of the above; try it first on classic RSA.

## Symmetric / AES

| observed | attack |
|---|---|
| ECB (repeated blocks) | byte-at-a-time decrypt / cut-paste |
| CBC + padding error | padding oracle (decrypt + forge) |
| CBC bit-flip on known PT | flip ciphertext to flip plaintext |
| fixed/predictable IV or nonce reuse (CTR/GCM) | keystream reuse → XOR out |
| GCM nonce reuse | forbidden-attack → recover auth key |

## ECC / DLog / misc

| observed | attack | tool |
|---|---|---|
| ECDSA nonce reuse / biased `k` | recover `d` from two sigs | ecdsa, sympy |
| smooth-order group | Pohlig-Hellman | sage |
| singular/anomalous curve | Smart / MOV | sage |
| LCG / `random` outputs | recover state, predict | z3, sympy |
| Mersenne `random` (624 outs) | clone MT19937 | randcrack |
| knapsack / lattice hint | LLL reduction | **sage** (or fpylll) |
| XOR with repeating key | freq analysis / crib drag | python |

## Gotchas
- `sage` is install-later (apt, heavy) — many lattice/ECC attacks need it; install before crypto-heavy contest.
- Use exact integer math: `gmpy2.mpz`, never float. `Crypto.Util.number` for `bytes_to_long`/`inverse`.
- Heavy brute (>~10^8) → write it in Rust, not Python.
- Always confirm `long_to_bytes(m)` decodes to `grey{` before declaring done.

# Attack Report — AI/02 Jurgen's Revenge (1000 pts)

> Static + empirical triage. Offline checker challenge. Flag = `grey{<55-char payload>}` that makes `check.py` print `accepted`.

## TL;DR
Deterministic recurrent **sign-network verifier** (`act = sign`, no gradients). Find any 55-char string over `[a-z0-9_]` s.t. terminal `score > 0`. Landscape is **flat** (no optimization possible) and the accept basin is a **needle** → exact constraint solve only (SAT/SMT/MILP).

## Model (verified from `model.pt`)
`n=55 steps, vocab=37, char_feat=49, binary=100, memory=2, packed=102, readout=100, gate=100, evidence=96, seed=20260528`.

State each step: `packed_t = [b_t(100 ±1) ‖ m_t(2 real)]`. The `_cw/_cu` 102×102 orthogonal stack is **cosmetic rotation** (`_cu[t]` un-rotates `_cw[t]`). Real recurrence:

```
ctx_t   = sign(Wr · packed_t + br)                       # 100 bits  (Wr shared every step)
b_{t+1} = sign(In_t · emb[c_t] + Cx_t · ctx_t + bias_t)  # 100 bits  (per-step weights)
m_{t+1} = m_t + 128 · value_t[c_t]                       # 2-d linear accumulator
```
Terminal on `T = [ctx_55(100) ‖ b_55(100) ‖ m_55(2)]` (202-d):
`evidence = sign(Wf·T + bf)` (96 bits) → `score = Wo·evidence + bo`, accept iff `score > 0`.

## Empirical findings (the meat)
1. **Flat plateau.** 500 random payloads → score **all exactly −14.133** (std 0). All 1980 single-char neighbors of a probe → identical. **Zero gradient.** ⇒ hill-climb / continuous-relaxation / Gumbel / tanh-surrogate **all dead**.
2. **Razor-thin basin.** `bo=−9.283`, `Σ|Wo|=10.065` → score ∈ `[−19.35, +0.781]`. Accept needs `Wo·ev > 9.283`, ceiling 10.065 → **slack only 0.78**. Every weight-1.043 evidence bit must hit its exact target sign; near-all weight-0.052 bits too.
3. **Memory dead in recurrence, alive in terminal.** Readout memory columns ≈ `7e-7` (float16-zeroed) → memory barely affects `ctx`/recurrence (0/100 units memory-dominated). But memory enters terminal directly as values **7k–13k**.
4. **State not collapsed.** 186/200 distinct final-context patterns over random inputs → high-entropy dynamics, no contracting attractor.
5. **Lock = hybrid, joint.** Critical evidence bits (|Wo|>1e-3) use **zero ctx weight**. They split:
   - **binary-keyed** (bit 6,46,49,65,83 @ w=1.043 + ~13 weak @ 0.052): key on `b_55` only.
   - **memory-keyed** (bit 18,26,60,66 @ w=1.043): each `sign(±1.0·m[d] + bias≈±9–11k)` → **threshold on 2-D accumulator** `m_55 = 128·Σ value_t[c_t]`.
   - Coupled: same 55 chars drive both binary recurrence and memory sum → cannot decouple.

## Triage corrections (vs `AI_TRIAGE_EXPLOIT.md`)
| triage claim | verdict |
|---|---|
| Class C model-as-verifier, offline, reproducible | ✅ |
| attack #1: solve via 2-D memory sum | ⚠️ **half right** — memory is ~4 of ~22 critical constraints (threshold form), but binary `b_55` constraints are coupled & dominate; cannot solve memory alone |
| z3/SMT family | ✅ right family |
| missed: flat landscape (no optimization) | ❌ **omitted** — key fact |
| missed: exact basin slack 0.78 / per-bit sign targets | ❌ omitted |

## Solve plan (ranked)
1. **CP-SAT (OR-tools), exact integer** — *primary*. Scale float16 weights to exact dyadic integers (fits int64), encode 55×(100 ctx + 100 b) reified sign gates + 96 terminal + 55 one-hot(37) char selectors + memory accumulator, assert `score>0`. CP-SAT crushes reified-linear ±1 systems.
2. **z3 SMT (Real/Bool)** — fallback if CP-SAT struggles. Same encoding, exact rationals.
3. **Backward DFS + constraint propagation** — last resort; target the ~5 strong `b_55` signs + 4 memory thresholds, branch on 37 chars/step, prune on infeasible sign sets + memory reachability.
4. ~~optimization / hill-climb / relaxation~~ — **excluded** (flat, no signal).

## Status
- Offline model repro: verified vs `check.py`.
- Solver: `solve/` (CP-SAT). Run, then submit `grey{<payload>}` on solution.
- No remote; the dist `check.py` is the oracle. If multiple payloads accept, report the solution set.

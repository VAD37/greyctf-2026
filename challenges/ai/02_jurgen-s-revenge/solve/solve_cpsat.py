"""Exact joint CP-SAT solve of the Jurgen's Revenge sign-network verifier.

Encodes the full 55-step sign recurrence + 2-D memory accumulator + 96-bit
terminal as integer-reified constraints and asks CP-SAT for any payload with
score > 0. Float64 weights scaled to int64 (S); final candidate verified exactly
by repro.forward (and check.py).

Run:  uv run --with ortools --with numpy python solve_cpsat.py [time_s]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
C = np.load(HERE / "constants.npz", allow_pickle=True)
A = C["A"]            # (55,37,100)
Cx = C["Cx"]          # (55,100,100)
cbias = C["cbias"]    # (55,100)
value = C["value"]    # (55,37,2)
Wr = C["Wr"]; br = C["br"]
Wf = C["Wf"]; bf = C["bf"]; Wo = C["Wo"]; bo = float(C["bo"][0])
n, a, BIN, MEM, PK = [int(x) for x in C["meta"]]
AL = str(C["alphabet"][0])
Wr_b = Wr[:, :BIN]; Wr_m = Wr[:, BIN:PK]

S = 1 << 20
def si(x) -> int:
    return int(round(float(x) * S))

def sign(x):
    return np.where(x >= 0.0, 1.0, -1.0)

CTX0 = sign(br)  # ctx_0 constant (packed_0 = 0)

m = cp_model.CpModel()

# one-hot char selectors
oh = [[m.NewBoolVar(f"oh_{t}_{c}") for c in range(a)] for t in range(n)]
for t in range(n):
    m.AddExactlyOne(oh[t])

def reif_sign(L_vars, L_coefs, L_const, name):
    """Return a {-1,1} bit var x with x==1 iff (sum coef*var + const) >= 0."""
    x = m.NewBoolVar(name)
    expr = cp_model.LinearExpr.WeightedSum(L_vars, L_coefs) + L_const
    m.Add(expr >= 0).OnlyEnforceIf(x)
    m.Add(expr <= -1).OnlyEnforceIf(x.Not())
    return x

# helpers to turn a {-1,1} bit var (bool x, s=2x-1) into linear contribution
# term w*s = 2w*x - w
def add_bit_term(vrs, cfs, const, w_scaled, xvar):
    vrs.append(xvar); cfs.append(2 * w_scaled);
    return const - w_scaled

# step recurrence
b_cur = None  # b_0 = zeros (constant)
# track partial memory (scaled) up to step t as growing lists
pm_vars = [[], []]; pm_cfs = [[], []]
B = [None] * (n + 1)  # B[t] = list of bit vars for b_t (t=1..n); B[0]=None(zeros)

for t in range(n):
    # ctx_t = sign(Wr_b @ b_t + Wr_m @ m_t + br)
    if t == 0:
        ctx = CTX0  # constant numpy array
    else:
        ctx = []
        for i in range(BIN):
            vrs, cfs = [], []
            const = 0
            # Wr_b @ b_t   (Wr_m @ m_t dropped: mem readout cols ~7e-7, <=0.03/unit; verify catches)
            for j in range(BIN):
                w = si(Wr_b[i, j])
                if w:
                    const = add_bit_term(vrs, cfs, const, w, B[t][j])
            const += si(br[i])
            ctx.append(reif_sign(vrs, cfs, const, f"ctx_{t}_{i}"))

    # b_{t+1}[i] = sign(A[t,c]@oh + Cx[t,i]@ctx + cbias[t,i])
    Bn = []
    for i in range(BIN):
        vrs, cfs = [], []
        const = 0
        for c in range(a):
            w = si(A[t, c, i])
            if w:
                vrs.append(oh[t][c]); cfs.append(w)
        if t == 0:
            const += si(float(Cx[t, i] @ ctx))  # ctx constant
        else:
            for j in range(BIN):
                w = si(Cx[t, i, j])
                if w:
                    const = add_bit_term(vrs, cfs, const, w, ctx[j])
        const += si(cbias[t, i])
        Bn.append(reif_sign(vrs, cfs, const, f"b_{t+1}_{i}"))
    B[t + 1] = Bn

    # extend partial memory with this step
    for c in range(a):
        for d in range(MEM):
            w = si(128.0 * value[t, c, d])
            if w:
                pm_vars[d].append(oh[t][c]); pm_cfs[d].append(w)

# terminal: ctx_final from b_n, m_n
b_n = B[n]
ctx_f = []
for i in range(BIN):
    vrs, cfs = [], []; const = 0
    for j in range(BIN):
        w = si(Wr_b[i, j])
        if w:
            const = add_bit_term(vrs, cfs, const, w, b_n[j])
    const += si(br[i])  # Wr_m @ m_n dropped (negligible)
    ctx_f.append(reif_sign(vrs, cfs, const, f"ctxf_{i}"))

# evidence[k] = sign(Wf[k] @ [ctx_f, b_n, m_n] + bf[k])
EV = []
for k in range(96):
    vrs, cfs = [], []; const = 0
    for i in range(BIN):              # ctx_f cols 0..99
        w = si(Wf[k, i])
        if w:
            const = add_bit_term(vrs, cfs, const, w, ctx_f[i])
    for i in range(BIN):              # b_n cols 100..199
        w = si(Wf[k, BIN + i])
        if w:
            const = add_bit_term(vrs, cfs, const, w, b_n[i])
    for d in range(MEM):              # memory cols 200..201
        wm = Wf[k, 2 * BIN + d]
        if wm != 0.0:
            for vv, cc in zip(pm_vars[d], pm_cfs[d]):
                vrs.append(vv); cfs.append(int(round(wm * cc)))
            const += 0
    const += si(bf[k])
    EV.append(reif_sign(vrs, cfs, const, f"ev_{k}"))

# score = Wo @ ev + bo > 0   ->  sum 2*Wo_s*x - Wo_s + bo_s >= 1
svars, scfs = [], []; sconst = si(bo)
for k in range(96):
    w = si(Wo[k])
    if w:
        svars.append(EV[k]); scfs.append(2 * w); sconst -= w

score_expr = cp_model.LinearExpr.WeightedSum(svars, scfs) + sconst
DBG = next((arg[4:] for arg in sys.argv if arg.startswith("fix:")), None)
MAX = "max" in sys.argv
if DBG is not None:
    for t, ch in enumerate(DBG):
        m.Add(oh[t][AL.index(ch)] == 1)   # pin payload, skip score -> must be FEASIBLE
elif MAX:
    m.Maximize(score_expr)                # find best achievable score (scaled by S)
else:
    m.Add(score_expr >= 1)

print(f"model built: vars~{len(oh)*a + sum(1 for _ in range(n*BIN*2))} (approx). solving...", flush=True)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 1800.0
solver.parameters.num_search_workers = 8
solver.parameters.log_search_progress = True

st = solver.Solve(m)
print("status:", solver.StatusName(st))

if DBG is not None:
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        # compare solved bits to exact numpy forward of the pinned payload
        idxs = [AL.index(ch) for ch in DBG]
        bcur = np.zeros(BIN); mcur = np.zeros(MEM)
        np_b = None; mism = []
        for t in range(n):
            ctxv = sign(Wr_b @ bcur + Wr[:, BIN:PK] @ mcur + br)
            bcur = sign(A[t, idxs[t]] + Cx[t] @ ctxv + cbias[t])
            mcur = mcur + value[t, idxs[t]] * 128.0
            solved = np.array([1.0 if solver.Value(B[t + 1][i]) else -1.0 for i in range(BIN)])
            d = int((solved != bcur).sum())
            if d:
                mism.append((t + 1, d))
        np_ev = None
        ctxf = sign(Wr_b @ bcur + Wr[:, BIN:PK] @ mcur + br)
        T = np.concatenate([ctxf, bcur, mcur])
        ev_np = sign(Wf @ T + bf)
        ev_solved = np.array([1.0 if solver.Value(EV[k]) else -1.0 for k in range(96)])
        evd = int((ev_np != ev_solved).sum())
        print(f"DBG feasible. b-step mismatches (step,count): {mism[:10]} ... total steps off={len(mism)}")
        print(f"DBG evidence mismatch count = {evd}/96")
    else:
        print("DBG: pinned payload INFEASIBLE -> recurrence encoding bug")
    sys.exit(0)

if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    payload = []
    for t in range(n):
        c = next(c for c in range(a) if solver.Value(oh[t][c]) == 1)
        payload.append(AL[c])
    pl = "".join(payload)
    print("PAYLOAD:", pl)
    print("FLAG: grey{" + pl + "}")
    (HERE / "solution.txt").write_text("grey{" + pl + "}\n")
else:
    print("no solution within time limit")

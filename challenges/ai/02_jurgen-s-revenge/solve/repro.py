"""Exact offline reproduction of RevengeModel.

Extracts all weights to float64 numpy (float16 -> float64 is exact), precomputes
per-step constants, and provides a pure-numpy forward that matches model.run_payload.
Dumps everything to constants.npz for the (torch-free) CP-SAT solver.

Run:  uv run --with 'torch==2.9.0' --with numpy python repro.py
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
import torch

from model import RevengeModel

HERE = Path(__file__).resolve().parent
DIST = HERE.parent / "files" / "extracted" / "dist-jurgens_revenge"


def load():
    m = RevengeModel.from_paths(DIST / "model.pt", DIST / "alphabet.json")
    return m


def extract(m: RevengeModel) -> dict:
    n, a = m.n, m.a
    d = lambda t: t.detach().to(torch.float64).numpy()
    emb = d(m.embed.weight)                       # (37,49)
    In = d(m.core.input.weight)                   # (55,100,49)
    Cx = d(m.core.context.weight)                 # (55,100,100)
    cbias = d(m.core.bias)                         # (55,100)
    value = d(m.core.value.weight)                # (55,37,2)
    Wr = d(m.readout.weight)                      # (100,102)
    br = d(m.readout.bias)                         # (100,)
    Wf = d(m.classifier.features.weight)          # (96,202)
    bf = d(m.classifier.features.bias)            # (96,)
    Wo = d(m.classifier.output.weight).reshape(-1)  # (96,)
    bo = float(d(m.classifier.output.bias).reshape(-1)[0])
    # A[t,c] = In[t] @ emb[c]   (100,)  -- computed in float64 exactly as model does
    A = np.einsum("toi,ci->tco", In, emb)         # (55,37,100)
    return dict(
        n=n, a=a, emb=emb, A=A, Cx=Cx, cbias=cbias, value=value,
        Wr=Wr, br=br, Wf=Wf, bf=bf, Wo=Wo, bo=bo,
        binary=m.binary_dim, memory=m.memory_dim, packed=m.packed_dim,
        alphabet=m.alphabet,
    )


def sign(x):
    return np.where(x >= 0.0, 1.0, -1.0)


def forward(C: dict, idxs):
    """Pure-numpy forward over char indices. Returns (score, accepted)."""
    binary, packed = C["binary"], C["packed"]
    b = np.zeros(binary)           # b_0 part of packed_0 = 0
    m = np.zeros(C["memory"])      # m_0 = 0
    Wr_b = C["Wr"][:, :binary]
    Wr_m = C["Wr"][:, binary:packed]
    for t, c in enumerate(idxs):
        packed_vec = np.concatenate([b, m])
        ctx = sign(Wr_b @ b + Wr_m @ m + C["br"])
        b = sign(C["A"][t, c] + C["Cx"][t] @ ctx + C["cbias"][t])
        m = m + C["value"][t, c] * 128.0
    # terminal
    ctx_final = sign(Wr_b @ b + Wr_m @ m + C["br"])
    T = np.concatenate([ctx_final, b, m])
    ev = sign(C["Wf"] @ T + C["bf"])
    score = float(C["Wo"] @ ev + C["bo"])
    return score, score > 0.0


def main():
    m = load()
    C = extract(m)
    AL = C["alphabet"]
    c2i = {ch: i for i, ch in enumerate(AL)}

    # verify pure-numpy forward matches the real model on random probes
    random.seed(0)
    bad = 0
    for _ in range(50):
        p = "".join(random.choice(AL) for _ in range(C["n"]))
        idxs = [c2i[ch] for ch in p]
        _, acc = forward(C, idxs)
        ref = m.run_payload(p)["accepted"]
        if acc != ref:
            bad += 1
    print(f"verify: {50 - bad}/50 match real model (accepted-bool)")
    assert bad == 0, "numpy repro diverges from model!"

    # save torch-free constants
    out = HERE / "constants.npz"
    np.savez(
        out,
        A=C["A"], Cx=C["Cx"], cbias=C["cbias"], value=C["value"],
        Wr=C["Wr"], br=C["br"], Wf=C["Wf"], bf=C["bf"], Wo=C["Wo"],
        bo=np.array([C["bo"]]), meta=np.array([C["n"], C["a"], C["binary"], C["memory"], C["packed"]]),
        alphabet=np.array([AL]),
    )
    print(f"saved {out}  (n={C['n']} a={C['a']} binary={C['binary']} packed={C['packed']})")


if __name__ == "__main__":
    main()

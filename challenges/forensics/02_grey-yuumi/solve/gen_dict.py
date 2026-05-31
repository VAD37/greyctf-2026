#!/usr/bin/env python3
"""Build ranked dict.txt for Grey Yuumi flag.
Visual read: grey{ yuum1 _ <MID> _ 4ttach3d }
  MID = [C0][C1] g g 3 r   (C0 = tall straight stroke; C1 = round loop)
Per-position confidence -> cartesian product -> score -> sort desc -> dedup vs tried.txt.
"""
import itertools, pathlib
HERE = pathlib.Path(__file__).parent

# word1 (clearly read "uum1" with leet style)
W1 = {"yuum1": 1.0, "yuumi": 0.30}

# word3 (read "4ttach" + "3d"); keep variants
W3 = {"4ttach3d": 1.0, "attach3d": 0.45, "4tt4ch3d": 0.18,
      "att4ch3d": 0.15, "4ttach_3d": 0.08, "attach_3d": 0.05,
      "4ttatch3d": 0.05, "4ttached": 0.05, "attached": 0.04}

# MID = C0 + C1 + "gg" + DIG + "r"  (DIG = 3 or e)
# C0: tall straight stroke -> l strongest, then t,j,1,i ; round-top letters far lower
C0 = {"l": 1.0, "t": 0.55, "j": 0.45, "1": 0.30, "i": 0.12, "h": 0.10,
      "d": 0.10, "n": 0.10, "b": 0.10, "r": 0.06, "f": 0.06, "k": 0.05,
      "s": 0.05, "m": 0.05, "c": 0.05, "p": 0.05, "w": 0.04, "g": 0.04,
      "y": 0.04, "v": 0.03, "z": 0.02,
      # capitalized
      "L": 0.20, "T": 0.18, "J": 0.10}
# C1: round closed loop -> o strongest, then a, then u, then 0/i
C1 = {"o": 1.0, "a": 0.35, "u": 0.30, "0": 0.18, "i": 0.10, "e": 0.06}
DIG = {"3": 1.0, "e": 0.12}

mids = {}
for c0, p0 in C0.items():
    for c1, p1 in C1.items():
        for d, pd in DIG.items():
            m = f"{c0}{c1}gg{d}r"
            mids[m] = max(mids.get(m, 0), p0 * p1 * pd)

flags = {}
for (w1, a) in W1.items():
    for (m, b) in mids.items():
        for (w3, c) in W3.items():
            f = f"grey{{{w1}_{m}_{w3}}}"
            flags[f] = max(flags.get(f, 0), a * b * c)

tried_p = HERE / "tried.txt"
tried = set(x.strip() for x in tried_p.read_text().splitlines() if x.strip()) if tried_p.exists() else set()

ranked = sorted(flags.items(), key=lambda kv: -kv[1])
out = [f for f, s in ranked if f not in tried]
(HERE / "dict.txt").write_text("\n".join(out) + "\n")
print(f"generated {len(out)} candidates (skipped {len(flags)-len(out)} already-tried)")
print("TOP 25:")
for f in out[:25]:
    print(" ", f)

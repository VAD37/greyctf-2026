#!/usr/bin/env python3
"""
Solve: Duality in All Things (GreyCTF 2026, ai/5)

The pickle is a linear SVM stored in DUAL form (SimpleNamespace of numpy arrays):
  support_vectors_ (554,12), dual_coef_ (1,554), intercept_, C=0.05.

Geometry of the data:
  Every support vector is essentially  t_i * d  (a single 1D direction d) plus a
  tiny perpendicular offset. SVD shows the data is rank ~2:
    - PC1 = position along the line  (an evenly-spaced grid from -4..+4)  -> carries nothing
    - PC2 = a small perpendicular displacement quantised to 4 bands:
            +0.165 / +0.075  (positive class)  and  -0.075 / -0.165  (negative class)
  So each support vector encodes exactly ONE bit = which band (inner vs outer) it sits in.

Decode:
  Sort SVs by PC1 (left->right along the grid), drop the 2 endpoint/free SVs
  (|PC2| ~ 0.30 outliers), read 1 bit per point (inner band = 1), pack MSB-first
  into bytes. The byte stream is  b"SVSLACK\x00\x007" + flag + trailer; the flag
  is the embedded grey{...}.
"""
import hashlib
import pickle
import re

import numpy as np

PKL = "../files/extracted/dist-duality_in_all_things/svc_dual_params.pkl"
EXPECTED_SHA256 = "3263da4c5a5c8bab9cc722ebb46341a79fda7b17062d7295d1a37355a149ec52"


def main() -> None:
    o = pickle.load(open(PKL, "rb"))
    sv = np.asarray(o.support_vectors_)  # (554, 12)

    # Rank-2 structure: project onto the top 2 right-singular vectors (no centering,
    # rows are t*d so the line passes through the origin).
    _, _, vt = np.linalg.svd(sv, full_matrices=False)
    pc1 = sv @ vt[0]   # position along the 1D grid
    pc2 = sv @ vt[1]   # perpendicular displacement = the payload

    order = np.argsort(pc1)            # read left -> right along the line
    pc2 = pc2[order]
    pc2 = pc2[np.abs(pc2) < 0.25]      # drop the 2 free-SV endpoint outliers (|pc2|~0.30)

    # bit = inner band (|pc2| ~ 0.075) -> 1, outer band (|pc2| ~ 0.165) -> 0
    bits = (np.abs(pc2) < 0.12).astype(int)

    out = bytearray()
    for i in range(0, len(bits) // 8 * 8, 8):
        v = 0
        for b in bits[i : i + 8]:
            v = (v << 1) | int(b)
        out.append(v)
    blob = bytes(out)

    flag = re.search(rb"grey\{[^}]*\}", blob).group().decode()
    print("decoded blob :", blob)
    print("flag         :", flag)
    digest = hashlib.sha256(flag.encode()).hexdigest()
    print("sha256       :", digest)
    assert digest == EXPECTED_SHA256, "sha256 mismatch!"
    print("VERIFIED -> " + flag)


if __name__ == "__main__":
    main()

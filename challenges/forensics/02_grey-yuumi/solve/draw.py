#!/usr/bin/env python3
"""Reconstruct mouse drawing from USB HID capture (Grey Yuumi).
Report (13B): [buttons, 0, dXlo, dXhi, dYlo, dYhi, 0,0, const tail].
dX/dY = signed 16-bit LE relative deltas. Integrate -> cursor path.
Pen-down = left button (bit0) held. Render strokes -> PNG."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = []
with open("reports.txt") as f:
    for line in f:
        line = line.strip()
        if len(line) != 26:
            continue
        rows.append(bytes.fromhex(line))
a = np.array([list(r) for r in rows], dtype=np.uint8)

btn = a[:, 0]
dx = (a[:, 2].astype(np.int16) | (a[:, 3].astype(np.int16) << 8)).astype(np.int16)
dy = (a[:, 4].astype(np.int16) | (a[:, 5].astype(np.int16) << 8)).astype(np.int16)
dx = dx.astype(np.int64)
dy = dy.astype(np.int64)

x = np.cumsum(dx)
y = np.cumsum(dy)
print("points", len(x), "x range", x.min(), x.max(), "y range", y.min(), y.max())
print("button values:", np.unique(btn, return_counts=True))

# pen-down = left button held (bit0)
pen = (btn & 1) != 0
print("pen-down frames:", pen.sum())

fig, ax = plt.subplots(figsize=(24, 12), dpi=120)
# break strokes where pen lifts: mask non-pen points with NaN so plot leaves gaps
xs = x.astype(float).copy()
ys = y.astype(float).copy()
xs[~pen] = np.nan
ys[~pen] = np.nan
ax.plot(xs, ys, color="black", linewidth=0.6)
ax.set_aspect("equal")
ax.invert_yaxis()  # screen coords: +Y is down
ax.axis("off")
fig.savefig("drawing_pen.png", bbox_inches="tight", facecolor="white")
print("wrote drawing_pen.png")

# fallback: full path (all movement) in case button mapping differs
fig2, ax2 = plt.subplots(figsize=(24, 12), dpi=120)
ax2.plot(x, y, color="blue", linewidth=0.3, alpha=0.6)
ax2.set_aspect("equal")
ax2.invert_yaxis()
ax2.axis("off")
fig2.savefig("drawing_all.png", bbox_inches="tight", facecolor="white")
print("wrote drawing_all.png")

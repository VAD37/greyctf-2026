#!/usr/bin/env python3
"""Clamped-cursor raster reconstruction of the mouse drawing.
Relative mouse deltas integrated but CLAMPED to screen bounds (as the
real cursor/drawing app sees them). Pen-down (right button) -> ink pixel."""
import sys
import numpy as np
from PIL import Image

rows = [bytes.fromhex(l.strip()) for l in open("reports.txt") if len(l.strip()) == 26]
a = np.array([list(r) for r in rows], dtype=np.uint8)
btn = a[:, 0]
dx = (a[:, 2].astype(np.int16) | (a[:, 3].astype(np.int16) << 8)).astype(np.int64)
dy = (a[:, 4].astype(np.int16) | (a[:, 5].astype(np.int16) << 8)).astype(np.int64)

for W, H in [(1920, 1080), (2560, 1440), (3840, 2160), (1280, 720)]:
    canvas = np.full((H, W), 255, dtype=np.uint8)
    x = W // 2
    y = H // 2
    pendown = (btn & 2) != 0  # right button = draw
    ink = 0
    for i in range(len(a)):
        x += int(dx[i]); y += int(dy[i])
        if x < 0: x = 0
        elif x >= W: x = W - 1
        if y < 0: y = 0
        elif y >= H: y = H - 1
        if pendown[i]:
            canvas[y, x] = 0
            ink += 1
    Image.fromarray(canvas).save(f"canvas_{W}x{H}.png")
    print(f"{W}x{H}: ink px set (events) {ink}")

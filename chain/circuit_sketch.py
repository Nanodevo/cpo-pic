#!/usr/bin/env python3
"""Stage 4 sketch: the ring-bank channel (7 in, 8 out) as a chain of scattering matrices.
Each box is one component with its own S-matrix; the circuit solver multiplies them along
the layout's connections. Output: chain/img/circuit-ringbank.png"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import figstyle
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
fig, ax = plt.subplots(figsize=figstyle.size(7.6, 4.2)); ax.set_xlim(0, 112); ax.set_ylim(0, 55); ax.axis("off")
def box(x, y, w, h, label, fc="#e8eef5", ec="#1b6ca8"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3", fc=fc, ec=ec, lw=1.4)); ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=10)
def arrow(x0, y0, x1, y1, col="#1b6ca8"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="->", mutation_scale=12, lw=1.4, color=col))
# forward row: taper in, bus straights, four rings
box(2, 30, 12, 9, "taper\nch 7 in", fc="#fdf1e0", ec="#8a5a1b"); arrow(14, 34.5, 19, 34.5)
box(17, 30, 9, 9, "straight\n400 µm"); arrow(26, 34.5, 29, 34.5)
x = 29
for k, r in enumerate((10.00, 10.05, 10.10, 10.15)):
    box(x, 30, 12, 9, f"bus+ring\nR {r:.2f}"); ax.add_patch(Circle((x + 6, 45), 3.6, fc="none", ec="#6b4fa0", lw=1.6)); ax.text(x + 6, 45, "ring", ha="center", va="center", fontsize=8, color="#6b4fa0")
    ax.plot([x + 6, x + 6], [39.3, 41.4], color="#6b4fa0", lw=1.2)
    if k < 3: arrow(x + 12, 34.5, x + 15.5, 34.5); ax.text(x + 13.8, 37.2, "110 µm", ha="center", va="bottom", fontsize=7, color="#444")
    x += 15.5
arrow(x, 34.5, x + 3, 34.5); box(x + 3, 30, 9, 9, "bend\n180°"); x -= 1; 
# return row
arrow(x + 8.5, 30, x + 8.5, 18); box(x + 4, 9, 9, 9, "route\nback"); arrow(x + 4, 13.5, 14, 13.5); box(2, 9, 12, 9, "taper\nch 8 out", fc="#fdf1e0", ec="#8a5a1b")
ax.text(56, 3, "each box is one scattering matrix; the circuit solver multiplies them along the layout's connections", ha="center", fontsize=9, color="#444")
ax.text(56, 52.5, "channel 7 → 8 of the die: four all-pass rings in series on one bus, then the loopback", ha="center", fontsize=11)
out = pathlib.Path(__file__).parent / "img" / "circuit-ringbank.png"; fig.savefig(out, bbox_inches="tight", facecolor="white"); print("wrote", out)

#!/usr/bin/env python3
"""Figure: the rung-2 eigenmode-expansion setup. Top: the cross-section the solver sees
at one z. Bottom: how the 2 mm taper is sliced into cells, with the ports at both ends.
Numbers match chain/taper_eme.py. Output: chain/img/eme-setup.png"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import figstyle
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
import numpy as np

fig, (ax, bx) = plt.subplots(2, 1, figsize=figstyle.size(7.6, 8.4))
# --- top: cross-section at z = 1000 um (box 16 x 12 um, silicon 156 nm wide here)
ax.add_patch(Rectangle((-8, -10), 16, 14, fc="#f4f4f4", ec="none"))              # oxide background n = 1.444
ax.add_patch(Rectangle((-8, -10), 16, 10, fc="#a9c4d8", ec="none"))              # glass n = 1.500
ax.add_patch(Rectangle((-3, -4), 6, 4, fc="#c8698a", ec="none"))                 # IOX guide n = 1.512
ax.add_patch(Rectangle((-8, 0), 16, 1, fc="#e9d8a6", ec="none"))                 # adhesive n = 1.500
ax.add_patch(Rectangle((-0.078, 1.0), 0.156, 0.22, fc="#1b6ca8", ec="#1b6ca8"))  # silicon n = 3.4757
ax.set_xlim(-8, 8); ax.set_ylim(-8, 4); ax.set_aspect("equal")
ax.set_xlabel("x (µm)"); ax.set_ylabel("y (µm)"); ax.set_title("what the mode solver sees at z = 1000 µm (silicon 156 nm wide there)")
ax.text(-7.6, 3.3, "oxide, n = 1.444 (background)", color="#555")
ax.text(-7.6, -7.4, "glass, n = 1.500", color="#2a4a60")
ax.text(0, -2, "ion-exchanged guide\n6 × 4 µm, n = 1.512", ha="center", va="center", color="white")
ax.text(-7.6, 0.28, "adhesive, 1 µm, n = 1.500", color="#5a4a10")
ax.annotate("silicon, 220 nm tall, n = 3.476", (0.08, 1.11), (2.2, 2.4), color="#1b6ca8", arrowprops=dict(arrowstyle="->", color="#1b6ca8", lw=0.8))
ax.text(7.6, -7.6, "mesh: 20 nm on the silicon,\n120 nm on the glass guide", ha="right", va="bottom", color="#333")
# --- bottom: the slicing along z
L, lead = 2000.0, 20.0
bx.add_patch(Rectangle((0, -6), L + lead, 6, fc="#a9c4d8", ec="none"))
bx.add_patch(Rectangle((0, -4), L + lead, 4, fc="#c8698a", ec="none"))
bx.add_patch(Rectangle((0, 0), L + lead, 1, fc="#e9d8a6", ec="none"))
bx.add_patch(Rectangle((0, 1), L + lead, 0.6, fc="#1b6ca8", ec="none"))          # silicon band (height not to scale)
for k in range(0, 121, 10): bx.axvline(k * (L + lead) / 120, color="white", lw=0.6, alpha=0.8)
bx.add_patch(Rectangle((0, -6.6), 0, 0, fc="none"))
for x, name in ((0, "port 1"), (L + lead, "port 2")):
    bx.axvline(x, color="#d33", lw=2)
    bx.text(x + (40 if x == 0 else -40), 2.1, name, ha="left" if x == 0 else "right", color="#d33")
bx.set_xlim(-60, L + lead + 60); bx.set_ylim(-6.6, 2.8); bx.set_xlabel("z (µm), along the light"); bx.set_yticks([])
bx.set_title("the taper sliced into 120 cells, 8 modes solved in each cell")
bx.text(L / 2, -2, "ion-exchanged guide", ha="center", color="white"); bx.text(L / 2, 0.5, "adhesive", ha="center", va="center", color="#5a4a10", fontsize=10)
bx.text(L / 2, 1.3, "silicon taper, 130 → 500 nm (height not to scale)", ha="center", va="center", color="white", fontsize=10)
bx.text(40, -5.4, "light in: glass mode", color="#2a4a60"); bx.text(L - 20, -5.4, "light out: silicon mode", ha="right", color="#2a4a60"); bx.text(L / 2, -5.4, "glass", ha="center", color="#2a4a60")
fig.tight_layout(); out = pathlib.Path(__file__).parent / "img" / "eme-setup.png"; fig.savefig(out); print("wrote", out)

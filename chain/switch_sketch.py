#!/usr/bin/env python3
"""Sketch of the 2x2 thermo-optic switch cell: two 2x2 couplers, two arms, a heater on one.
Output: chain/img/switch-sketch.png"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import figstyle
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
fig, ax = plt.subplots(figsize=figstyle.size(7.6, 3.6)); ax.set_xlim(0, 100); ax.set_ylim(-1, 40); ax.axis("off")
B = "#1b6ca8"
for y in (14, 26):                                   # inputs and outputs
    ax.plot([4, 18], [y, y], color=B, lw=4); ax.plot([82, 96], [y, y], color=B, lw=4)
for x in (18, 70):                                   # the two couplers
    ax.add_patch(FancyBboxPatch((x, 11), 12, 18, boxstyle="round,pad=0.4", fc="#e8eef5", ec=B, lw=1.6)); ax.text(x + 6, 20, "2×2\ncoupler\n50 : 50", ha="center", va="center", fontsize=9)
ax.plot([30, 70], [26, 26], color=B, lw=4); ax.plot([30, 70], [14, 14], color=B, lw=4)      # arms
ax.add_patch(Rectangle((38, 27.5), 24, 3.2, fc="#c9a227", ec="#8a5a1b", lw=1)); ax.text(50, 33.5, "heater on the upper arm: current → heat → index → phase φ", ha="center", fontsize=9, color="#8a5a1b")
ax.text(50, 7.6, "lower arm 10 µm longer: a fixed extra phase, and a wavelength dependence", ha="center", fontsize=9, color="#444")
ax.text(3, 16.5, "o1  in", fontsize=10, color=B); ax.text(3, 29, "o2", fontsize=10, color=B)
ax.text(90, 16.5, "o4  (bar)", fontsize=10, color=B); ax.text(90, 29, "o3  (cross)", fontsize=10, color=B)
ax.add_patch(FancyArrowPatch((5, 14), (14, 14), arrowstyle="->", mutation_scale=16, lw=2, color="#e67e22"))
ax.text(50, 0.5, "the first coupler splits the light in two, the arms give the halves a phase difference, the second coupler recombines them:\nwith equal phases everything exits one port, with a difference of π the other, and in between the light divides", ha="center", va="bottom", fontsize=8.6, color="#333")
ax.set_title("The 2×2 thermo-optic switch cell of channels 9 and 10")
out = pathlib.Path(__file__).parent / "img" / "switch-sketch.png"; fig.savefig(out, bbox_inches="tight", facecolor="white"); print("wrote", out)

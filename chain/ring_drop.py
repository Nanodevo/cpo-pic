#!/usr/bin/env python3
"""All-pass ring against add-drop ring: what happens to the light that enters the ring.
Output: chain/img/ring-drop.png"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import figstyle
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
COLS = ["#d62728", "#ff7f0e", "#bcbd22", "#2ca02c", "#17becf", "#1f77b4", "#9467bd", "#e377c2"]   # eight wavelengths
fig, (a, b) = plt.subplots(2, 1, figsize=figstyle.size(7.6, 8.2), gridspec_kw=dict(hspace=0.35))
def bus(ax, y, x0=4, x1=96): ax.plot([x0, x1], [y, y], color="#1b6ca8", lw=6, solid_capstyle="butt")
def rainbow(ax, x, y, drop=None, dy=2.2, size=12):
    for i, c in enumerate(COLS):
        if drop is not None and i == drop: continue
        ax.add_patch(FancyArrowPatch((x, y + (i - 3.5) * dy * 0.45), (x + 9, y + (i - 3.5) * dy * 0.45), arrowstyle="->", mutation_scale=size, lw=1.6, color=c))
for ax in (a, b): ax.set_xlim(0, 100); ax.set_ylim(0, 46); ax.axis("off")
# --- all-pass
bus(a, 12); a.add_patch(Circle((50, 25), 10, fc="none", ec="#6b4fa0", lw=6)); a.text(50, 25, "ring", ha="center", va="center", color="#6b4fa0")
rainbow(a, 8, 12); a.text(12, 4, "8 wavelengths in", ha="center", fontsize=10)
rainbow(a, 80, 12, drop=2); a.text(85, 4, "7 out, the 8th mostly gone", ha="center", fontsize=10)
a.add_patch(FancyArrowPatch((50, 15.5), (58, 18.5), arrowstyle="->", mutation_scale=14, lw=2.2, color=COLS[2], connectionstyle="arc3,rad=-0.4"))
a.text(81, 30, "the resonant wavelength enters,\ncirculates round after round, and\nis used up by the ring's own loss;\nwhat leaks back arrives out of\nstep and cancels: a dip, not an exit", fontsize=9.5, ha="center", va="center", color="#333")
a.set_title("All-pass ring, one bus: what the die has. A filter that removes, not one that sorts")
# --- add-drop
bus(b, 12); bus(b, 38); b.add_patch(Circle((50, 25), 10, fc="none", ec="#6b4fa0", lw=6)); b.text(50, 25, "ring", ha="center", va="center", color="#6b4fa0")
rainbow(b, 8, 12); b.text(12, 4, "8 wavelengths in", ha="center", fontsize=10)
rainbow(b, 80, 12, drop=2); b.text(85, 4, "through port: 7 continue", ha="center", fontsize=10)
b.add_patch(FancyArrowPatch((50, 15.5), (58, 18.5), arrowstyle="->", mutation_scale=14, lw=2.2, color=COLS[2], connectionstyle="arc3,rad=-0.4"))
b.add_patch(FancyArrowPatch((44, 33), (36, 36.5), arrowstyle="->", mutation_scale=14, lw=2.2, color=COLS[2], connectionstyle="arc3,rad=-0.4"))
b.add_patch(FancyArrowPatch((30, 38), (10, 38), arrowstyle="->", mutation_scale=18, lw=3.5, color=COLS[2], zorder=5)); b.text(20, 42.8, "drop port: the 8th, alone,\nto its photodetector", ha="center", va="center", fontsize=10, color=COLS[2])
b.text(78, 42.8, "second bus on the far side", ha="center", va="center", fontsize=10, color="#1b6ca8")
b.set_title("Add-drop ring, two buses: the demultiplexer. The resonant wavelength crosses over")
out = pathlib.Path(__file__).parent / "img" / "ring-drop.png"; fig.savefig(out, bbox_inches="tight", facecolor="white"); print("wrote", out)

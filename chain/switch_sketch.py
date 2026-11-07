#!/usr/bin/env python3
"""Sketch of the die's thermo-optic MZI: a 1x2 splitter, two arms with a heater on one, a 2x2 combiner.
Output: chain/img/switch-sketch.png"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import figstyle
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
fig, ax = plt.subplots(figsize=figstyle.size(7.6, 3.6)); ax.set_xlim(0, 100); ax.set_ylim(-1, 40); ax.axis("off")
B = "#1b6ca8"
ax.plot([4, 18], [20, 20], color=B, lw=4)                                         # one input
for y in (14, 26): ax.plot([82, 96], [y, y], color=B, lw=4)                      # two outputs
ax.add_patch(FancyBboxPatch((18, 11), 12, 18, boxstyle="round,pad=0.4", fc="#e8eef5", ec=B, lw=1.6)); ax.text(24, 20, "1×2\nsplitter\n50 : 50", ha="center", va="center", fontsize=9)
ax.add_patch(FancyBboxPatch((70, 11), 12, 18, boxstyle="round,pad=0.4", fc="#e8eef5", ec=B, lw=1.6)); ax.text(76, 20, "2×2\ncombiner\n50 : 50", ha="center", va="center", fontsize=9)
ax.plot([30, 70], [26, 26], color=B, lw=4); ax.plot([30, 70], [14, 14], color=B, lw=4)      # arms
ax.add_patch(Rectangle((38, 27.5), 24, 3.2, fc="#c9a227", ec="#8a5a1b", lw=1)); ax.text(50, 33.5, "heater on the upper arm: current → heat → index → phase φ", ha="center", fontsize=9, color="#8a5a1b")
ax.text(50, 7.6, "lower arm 100 µm longer: a fixed extra phase that changes with wavelength", ha="center", fontsize=9, color="#444")
ax.text(2, 22.5, "o1 in, ch16", fontsize=9, color=B)
ax.text(88, 16.5, "o2 → ch18", fontsize=10, color=B); ax.text(88, 28.5, "o3 → ch17", fontsize=10, color=B)
ax.add_patch(FancyArrowPatch((5, 20), (14, 20), arrowstyle="->", mutation_scale=16, lw=2, color="#e67e22"))
ax.text(50, 0.5, "the splitter gives the arms equal halves in step, the arms add a phase difference, the combiner sends the light\nto one output or the other depending on that difference; both outputs come back to the glass", ha="center", va="bottom", fontsize=8.6, color="#333")
ax.set_title("The thermo-optic MZI of channels 16 to 18")
out = pathlib.Path(__file__).parent / "img" / "switch-sketch.png"; fig.savefig(out, bbox_inches="tight", facecolor="white"); print("wrote", out)

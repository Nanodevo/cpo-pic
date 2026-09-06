#!/usr/bin/env python3
"""What rung 2 caught: the silicon branch the design used against the branch the light is on.
Effective index against width for the 2D sweep of the fundamental silicon mode (which is
the vertically polarized mode below 220 nm) and for the horizontally polarized mode in the
3D cross-section, with the glass TE mode and both crossings.  -> chain/img/branches.png"""
import pathlib
import matplotlib.pyplot as plt
import numpy as np
import figstyle
from branch import load
ey, te = load("ey2d"), load("te3d")
fig, ax = plt.subplots(figsize=figstyle.size(7.6, 5.0))
ax.plot(ey.w_pts, ey.n_pts, "o--", lw=1.6, ms=4, color="#888780", label="2D sweep, fundamental silicon mode (E$_y$ below 220 nm)")
ax.plot(te.w_pts[1:], te.n_pts[1:], "o-", lw=2.4, ms=5, color="#1b6ca8", label="3D cross-section, E$_x$ (TE) silicon mode")
ax.axhline(te.n_glass, ls="--", lw=1.6, color="#1D9E75", label=f"glass TE mode, n$_{{eff}}$ = {te.n_glass:.4f}")
for b, col, xy in ((ey, "#888780", (138, 1.522)), (te, "#1b6ca8", (203, 1.530))):
    ax.plot([b.w_cross], [b.n_glass], "o", ms=9, color=col, mfc="white", mew=2)
    ax.annotate(f"crossing at {b.w_cross:.0f} nm", (b.w_cross, b.n_glass), xy, ha="center", color=col, arrowprops=dict(arrowstyle="->", color=col, lw=0.8))
ax.set_xlim(120, 260); ax.set_ylim(1.49, 1.60)
ax.set_xlabel("silicon width  (nm)"); ax.set_ylabel("effective index")
ax.set_title("Two branches, two crossings: the design followed the dashed one")
ax.grid(alpha=.22); ax.legend(loc="upper left")
out = pathlib.Path(__file__).parent / "img" / "branches.png"; fig.savefig(out, bbox_inches="tight", facecolor="white"); print("wrote", out)

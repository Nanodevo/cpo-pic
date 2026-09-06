#!/usr/bin/env python3
"""The anticrossing behind the hand-off, for the selected branch (see branch.py).

Isolated-guide index of the silicon against width, the glass guide's value, and the
two supermodes of the coupled pair around the crossing.

Run:  [BRANCH=ey2d] python chain/anticrossing.py  ->  chain/img/anticrossing.png
"""
import pathlib

import matplotlib.pyplot as plt

import figstyle
import numpy as np
from branch import BR

HERE = pathlib.Path(__file__).parent
w_si, n_si = BR.w_pts, BR.n_pts
N_GLASS = BR.n_glass
LAM = 1.55
w_c = BR.coupled[:, 0] * 1e3
upper, lower = BR.coupled[:, 1], BR.coupled[:, 2]
WC = BR.w_cross
XLO, XHI = WC - 13, WC + 22

fig, ax = plt.subplots(figsize=figstyle.size(9.8, 5.4))
sel = (w_si >= XLO) & (w_si <= XHI)
ax.plot(w_si[sel], n_si[sel], ls="--", lw=1.6, color="#888780", label="silicon guide alone")
ax.axhline(N_GLASS, ls="--", lw=1.6, color="#1D9E75", label="glass guide alone")
ax.plot(w_c, upper, "o-", lw=2.4, ms=5, color="#1b6ca8", label="coupled pair: upper mode")
ax.plot(w_c, lower, "o-", lw=2.4, ms=5, color="#6b4fa0", label="coupled pair: lower mode")
i = int(np.argmin(abs(w_c - WC)))
ax.annotate("", xy=(w_c[i], upper[i]), xytext=(w_c[i], lower[i]),
            arrowprops=dict(arrowstyle="<->", color="#c0392b", lw=1.6))
ylo, yhi = 1.497, 1.525
ax.text(w_c[i] + 6, lower[i] - 0.0012, f"gap at the crossing: G = {BR.G:.1e}\nbeat length λ/G = {LAM/BR.G:.0f} µm", color="#c0392b", va="center")
ax.axvline(WC, color="#c0392b", lw=1, ls=":")
ax.text(WC + 1.2, yhi - 0.001, f"phase match, {WC:.0f} nm", color="#c0392b", rotation=90, va="top", ha="left")
ax.set_xlim(XLO, XHI); ax.set_ylim(ylo, yhi)
ax.set_xlabel("silicon width (nm); light enters at the narrow tip on the left")
ax.set_ylabel("effective index")
ax.set_title("Two guides that would cross, and what they do instead", pad=8)
ax.grid(alpha=.22); ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, frameon=False)
out = HERE / "img" / "anticrossing.png"
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("wrote", out)

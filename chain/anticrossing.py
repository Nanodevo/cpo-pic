#!/usr/bin/env python3
"""The anticrossing behind the hand-off, from the run of sim/taper_modes.py.

Isolated-guide indices come from build/taper_modes.csv (silicon alone) and the
glass guide value printed by the run. The coupled-pair supermode indices are
transcribed from the same run's table (tip width, n_eff, split dn).

Run:  python chain/anticrossing.py  ->  chain/img/anticrossing.png
"""
import pathlib

import matplotlib.pyplot as plt

import figstyle
import numpy as np

HERE = pathlib.Path(__file__).parent
sweep = np.loadtxt(HERE.parent / "build" / "taper_modes.csv", delimiter=",", skiprows=1)
w_si, n_si = sweep[:, 0] * 1e3, sweep[:, 1]          # silicon alone
N_GLASS = 1.50522                                     # IOX guide alone, from the run
LAM = 1.55

# coupled pair, from the run: tip (um), n_eff of the upper supermode, split
coupled = np.array([
    [0.200, 1.53425, 1.14e-2], [0.190, 1.52669, 1.49e-2], [0.180, 1.51983, 1.31e-2],
    [0.170, 1.51396, 8.33e-3], [0.160, 1.50957, 4.24e-3], [0.155, 1.50804, 2.79e-3],
    [0.150, 1.50701, 1.82e-3], [0.140, 1.50598, 8.67e-4], [0.130, 1.50555, 4.87e-4],
])
w_c = coupled[:, 0] * 1e3
upper = coupled[:, 1]
lower = coupled[:, 1] - coupled[:, 2]

fig, ax = plt.subplots(figsize=figstyle.size(9.8, 5.4))
sel = (w_si >= 125) & (w_si <= 205)
ax.plot(w_si[sel], n_si[sel], ls="--", lw=1.6, color="#888780", label="silicon guide alone")
ax.axhline(N_GLASS, ls="--", lw=1.6, color="#1D9E75", label="glass guide alone")
ax.plot(w_c, upper, "o-", lw=2.4, ms=5, color="#1b6ca8", label="coupled pair: upper mode")
ax.plot(w_c, lower, "o-", lw=2.4, ms=5, color="#6b4fa0", label="coupled pair: lower mode")
ax.axvspan(125, 150, color="#fdf1e0", zorder=0)
ax.text(137, 1.5245, "below 150 nm the lower\ncurve is the glass\ncontinuum, not a partner\nmode: read with care", color="#8a5a1b", ha="center")
i = np.argmin(abs(w_c - 155))
ax.annotate("", xy=(155, upper[i]), xytext=(155, lower[i]),
            arrowprops=dict(arrowstyle="<->", color="#c0392b", lw=1.6))
ax.text(159, 1.5295, f"gap at 155 nm: Δn = {coupled[i,2]:.1e}\nbeat length λ/Δn = {LAM/coupled[i,2]:.0f} µm", color="#c0392b", va="bottom")
ax.annotate("", xy=(156.2, (upper[i]+lower[i])/2), xytext=(159, 1.5295),
            arrowprops=dict(arrowstyle="-", color="#c0392b", lw=0.9))
ax.axvline(156, color="#c0392b", lw=1, ls=":")
ax.text(154.6, 1.5345, "phase match, 156 nm", color="#c0392b", rotation=90, va="top", ha="center")
ax.set_xlim(125, 205); ax.set_ylim(1.497, 1.536)
ax.set_xlabel("silicon width (nm); light enters at the narrow tip on the left")
ax.set_ylabel("effective index")
ax.set_title("Two guides that would cross, and what they do instead", pad=8)
ax.grid(alpha=.22); ax.legend(loc="lower right")
out = HERE / "img" / "anticrossing.png"
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("wrote", out)

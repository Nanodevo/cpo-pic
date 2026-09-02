#!/usr/bin/env python3
"""Why re-radiation retards the phase, without anything travelling below c.

The incident wave drives the electrons. The electrons radiate their own wave at
the same frequency but lagging the driver by a quarter cycle. Adding a lagging
wave of small amplitude to the original gives a resultant of almost the same
shape whose phase is retarded. Accumulate that through successive layers and the
wave appears to advance more slowly, which is all the refractive index is.

Run:  python chain/phase_delay.py  ->  chain/img/phase-delay.png
"""
import pathlib

import matplotlib.pyplot as plt
import numpy as np

th = np.linspace(0, 4 * np.pi, 900)
inc = np.cos(th)
eps = 0.35
rad = eps * np.sin(th)          # same frequency, lagging by a quarter cycle
tot = inc + rad
shift = np.arctan(eps)          # phase retardation of the resultant

fig, ax = plt.subplots(figsize=(9.6, 4.4))
ax.plot(th, inc, lw=2.0, color="#888780", ls="--", label="incident wave")
ax.plot(th, rad, lw=1.8, color="#8a5a1b",
        label="re-radiated by the electrons (small, lags by ¼ cycle)")
ax.plot(th, tot, lw=2.6, color="#1b6ca8", label="sum: what you actually measure")
ax.annotate("", xy=(shift, 1.06), xytext=(0, 1.0),
            arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.8))
ax.text(shift + 0.12, 1.14, f"phase retarded by {np.degrees(shift):.0f}°",
        color="#c0392b", fontsize=10.5)
ax.axhline(0, color="#d8dee4", lw=1, zorder=0)
ax.set_xlim(0, 4 * np.pi); ax.set_ylim(-1.5, 1.5)
ax.set_xticks([0, np.pi, 2*np.pi, 3*np.pi, 4*np.pi])
ax.set_xticklabels(["0", "π", "2π", "3π", "4π"])
ax.set_xlabel("phase of the wave", fontsize=10.5)
ax.set_ylabel("electric field", fontsize=10.5)
ax.set_title("One thin layer of material: the sum lags the original",
             fontsize=12.5, pad=10)
ax.grid(alpha=.22); ax.legend(fontsize=9.5, loc="lower right")
fig.tight_layout()
out = pathlib.Path(__file__).parent / "img" / "phase-delay.png"
fig.savefig(out, dpi=170, bbox_inches="tight", facecolor="white")
print("wrote", out, "| retardation per layer:", round(np.degrees(shift), 1), "deg")

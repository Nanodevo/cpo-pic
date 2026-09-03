#!/usr/bin/env python3
"""What a beat length is: a distance ALONG the light, not across it.

Two phase-matched guides held at fixed geometry (no taper). Light launched in the
glass sloshes fully into the silicon and back with period L_beat = lambda / dn,
where dn is the gap between the two supermodes. For the coupled pair at 155 nm
from the run of sim/taper_modes.py: dn = 2.79e-3, L_beat = 556 um.

    P_silicon(z) = sin^2(pi z / L_beat),   P_glass(z) = cos^2(pi z / L_beat)

The adhesive thickness (1 um) is the transverse gap between the guides. It sets
how strong the coupling is, and therefore how long L_beat is. It is not compared
with L_beat; it is one of the things that determines it.

Run:  python chain/beat_length.py  ->  chain/img/beat-length.png
"""
import pathlib

import matplotlib.pyplot as plt
import numpy as np

L_BEAT = 1.55 / 2.79e-3          # um
z = np.linspace(0, 1200, 1200)
p_si = np.sin(np.pi * z / L_BEAT) ** 2
p_gl = 1 - p_si

fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(10.5, 6.6), height_ratios=[1, 1.35],
                               gridspec_kw=dict(hspace=0.42))

# --- top: the geometry, two directions labelled ---------------------------
ax0.set_xlim(0, 1200); ax0.set_ylim(0, 10); ax0.axis("off")
ax0.add_patch(plt.Rectangle((0, 1.0), 1200, 2.6, color="#9FE1CB"))          # glass guide
ax0.add_patch(plt.Rectangle((0, 3.6), 1200, 1.0, color="#FAEEDA"))          # adhesive
ax0.add_patch(plt.Rectangle((0, 4.6), 1200, 0.9, color="#378ADD"))          # silicon, fixed 155 nm
ax0.text(8, 2.0, "ion-exchanged guide in the glass", fontsize=10, color="#0F6E56", va="center")
ax0.text(8, 5.05, "silicon guide, held at 155 nm (no taper, for this picture)", fontsize=10, color="#fff", va="center")
ax0.annotate("", xy=(1120, 4.6), xytext=(1120, 3.6), arrowprops=dict(arrowstyle="<->", color="#8a5a1b", lw=1.4))
ax0.text(1132, 4.1, "adhesive, 1 µm\nACROSS the light", fontsize=9.5, color="#8a5a1b", va="center")
ax0.annotate("", xy=(L_BEAT, 7.6), xytext=(0, 7.6), arrowprops=dict(arrowstyle="<->", color="#c0392b", lw=1.6))
ax0.text(L_BEAT / 2, 8.3, f"beat length, {L_BEAT:.0f} µm, ALONG the light", fontsize=10.5, color="#c0392b", ha="center")
ax0.annotate("", xy=(140, 2.3), xytext=(20, 2.3), arrowprops=dict(arrowstyle="->", color="#0F6E56", lw=2))
ax0.text(30, 0.2, "light enters in the glass", fontsize=9.5, color="#0F6E56")
for x, lab in ((L_BEAT / 2, "all in silicon"), (L_BEAT, "all back in glass")):
    ax0.axvline(x, ymin=0.08, ymax=0.62, color="#c0392b", lw=1, ls=":")
    ax0.text(x, 6.3, lab, fontsize=9, color="#c0392b", ha="center")

# --- bottom: the sloshing --------------------------------------------------
ax1.plot(z, p_gl, lw=2.4, color="#1D9E75", label="power in the glass guide")
ax1.plot(z, p_si, lw=2.4, color="#378ADD", label="power in the silicon guide")
for k in (0.5, 1.0, 1.5, 2.0):
    ax1.axvline(k * L_BEAT, color="#c0392b", lw=1, ls=":")
ax1.text(L_BEAT / 2, 1.04, f"{L_BEAT/2:.0f} µm", ha="center", fontsize=9.5, color="#c0392b")
ax1.text(L_BEAT, 1.04, f"{L_BEAT:.0f} µm", ha="center", fontsize=9.5, color="#c0392b")
ax1.set_xlim(0, 1200); ax1.set_ylim(0, 1.12)
ax1.set_xlabel("distance along the guides, z  (µm)", fontsize=10.5)
ax1.set_ylabel("fraction of the power", fontsize=10.5)
ax1.grid(alpha=.22); ax1.legend(fontsize=9.5, loc="center right")
ax1.set_title("Phase-matched and held fixed: the light sloshes between the guides with period L_beat", fontsize=11)

out = pathlib.Path(__file__).parent / "img" / "beat-length.png"
fig.savefig(out, dpi=170, bbox_inches="tight", facecolor="white")
print("wrote", out, f"| L_beat = {L_BEAT:.0f} um, full transfer at {L_BEAT/2:.0f} um")

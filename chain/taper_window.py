#!/usr/bin/env python3
"""What the taper offers against what the light needs, on the same z axis.

Linear taper, 120 nm tip at z = 0 widening to 500 nm at z = 2000 um:
    w(z) = 120 + 0.19 z   (nm, z in um)
The hand-off happens between about 140 and 180 nm of width. Top panel: how much
taper length that window occupies. Bottom panel: the beat length of the coupled
pair at each width, from the run of sim/taper_modes.py, mapped onto z.

Run:  python chain/taper_window.py  ->  chain/img/taper-window.png
"""
import pathlib

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({"font.size": 15})

TIP, END, LEN = 120.0, 500.0, 2000.0
slope = (END - TIP) / LEN                       # nm per um
w = lambda z: TIP + slope * z
zw = lambda wn: (wn - TIP) / slope
W0, W1 = 140.0, 180.0
z0, z1 = zw(W0), zw(W1)

# beat lengths from the run: (width nm, L_beat um)
beat = np.array([[200, 136], [190, 104], [180, 118], [170, 186], [160, 366],
                 [155, 556], [150, 851], [140, 1787]])
zb = zw(beat[:, 0])

fig, (a, b) = plt.subplots(2, 1, figsize=(7.6, 9.0), sharex=True,
                           gridspec_kw=dict(hspace=0.12, height_ratios=[1, 1.2]))
z = np.linspace(0, LEN, 400)
a.plot(z, w(z), lw=2.6, color="#378ADD")
a.axhspan(W0, W1, color="#fdf1e0")
a.axvspan(z0, z1, color="#fdf1e0")
a.annotate("", xy=(z1, 128), xytext=(z0, 128), arrowprops=dict(arrowstyle="<->", color="#8a5a1b", lw=1.6))
a.text(z1 + 25, 128, f"the taper spends {z1 - z0:.0f} µm here", ha="left", va="center", fontsize=15, color="#8a5a1b")
a.text(400, 300, "hand-off window:\n140 to 180 nm wide", fontsize=15, color="#8a5a1b", va="center")
a.set_ylabel("silicon width  (nm)", fontsize=15.5)
a.set_ylim(80, 520); a.grid(alpha=.22)
a.set_title(f"A linear taper: {TIP:.0f} nm tip at z = 0, {END:.0f} nm at z = {LEN:.0f} µm", fontsize=16)

b.semilogy(zb, beat[:, 1], "o-", lw=2.4, ms=6, color="#c0392b")
b.axvspan(z0, z1, color="#fdf1e0")
for k, (zz, (wn, L)) in enumerate(zip(zb, beat)):
    if 140 <= wn <= 180:
        b.annotate(f"{wn:.0f} nm: {L:.0f} µm", xy=(zz, L), xytext=(zz + 140, L),
                   fontsize=16, color="#c0392b", va="center",
                   arrowprops=dict(arrowstyle="-", color="#c0392b", lw=0.7))
b.annotate("", xy=(z1, 25), xytext=(z0, 25), arrowprops=dict(arrowstyle="<->", color="#8a5a1b", lw=1.6))
b.text((z0 + z1) / 2, 15, f"offered: {z1 - z0:.0f} µm", ha="center", fontsize=15.5, color="#8a5a1b")
b.text(470, 2600, "needed: one full slosh\ntakes this long here", fontsize=15, color="#c0392b")
b.set_ylim(10, 6000); b.set_xlim(0, 900)
b.set_xlabel("position along the taper, z  (µm)", fontsize=15.5)
b.set_ylabel("beat length  (µm)", fontsize=15.5)
b.grid(alpha=.22, which="both")
b.set_title("Beat length of the coupled pair along the taper", fontsize=16, pad=14)

out = pathlib.Path(__file__).parent / "img" / "taper-window.png"
fig.savefig(out, dpi=170, bbox_inches="tight", facecolor="white")
print("wrote", out, f"| window {W0:.0f}-{W1:.0f} nm sits at z = {z0:.0f}-{z1:.0f} um, {z1-z0:.0f} um long")

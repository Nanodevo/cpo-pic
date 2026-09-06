#!/usr/bin/env python3
"""What the taper offers against what the light needs, on the same z axis.

Linear taper, 120 nm tip at z = 0 widening to 500 nm at z = 2000 um:
    w(z) = 120 + 0.19 z   (nm, z in um)
The hand-off happens between about 140 and 180 nm of width. Top panel: how much
taper length that window occupies. Bottom panel: the beat length of the coupled
pair at each width, L_b = lambda / sqrt(delta^2 + G^2), the two-mode relation used
by taper_design.py and taper_propagate.py (delta = isolated-silicon n_eff minus
the glass n_eff, G = 2.8e-3 the supermode gap at the crossing), mapped onto z.
An earlier version took the beat lengths from the 'split' column of the coupled
solve, which away from the crossing had tracked the wrong mode pair.

Run:  python chain/taper_window.py  ->  chain/img/taper-window.png
"""
import pathlib

import matplotlib.pyplot as plt

import figstyle
import numpy as np


TIP, END, LEN = 120.0, 500.0, 2000.0
slope = (END - TIP) / LEN                       # nm per um
w = lambda z: TIP + slope * z
zw = lambda wn: (wn - TIP) / slope
W0, W1 = 140.0, 180.0
z0, z1 = zw(W0), zw(W1)

# beat lengths from the two-mode relation, L_b = lambda / sqrt(delta^2 + G^2)
LAMBDA, N_GLASS, G = 1.55, 1.50522, 2.8e-3
sweep = np.array([[0.500,2.44966],[0.450,2.36236],[0.400,2.24035],[0.350,2.07525],[0.300,1.86147],
                  [0.260,1.68548],[0.220,1.55841],[0.200,1.53393],[0.190,1.52624],[0.180,1.51917],
                  [0.170,1.51279],[0.160,1.50724],[0.155,1.50483],[0.150,1.50275],[0.145,1.50101],
                  [0.140,1.49971],[0.130,1.49908],[0.120,1.49908]])[::-1]
delta = lambda wn: np.interp(wn, sweep[:, 0] * 1e3, sweep[:, 1]) - N_GLASS
widths = np.array([200, 190, 180, 170, 160, 155, 150, 145, 140])
beat = np.column_stack([widths, LAMBDA / np.sqrt(delta(widths) ** 2 + G ** 2)])
for wn, L in beat: print(f"   {wn:.0f} nm: beat length {L:.0f} um")
zb = zw(beat[:, 0])

fig, (a, b) = plt.subplots(2, 1, figsize=figstyle.size(7.6, 9.0), sharex=True,
                           gridspec_kw=dict(hspace=0.12, height_ratios=[1, 1.2]))
z = np.linspace(0, LEN, 400)
a.plot(z, w(z), lw=2.6, color="#378ADD")
a.axhspan(W0, W1, color="#fdf1e0")
a.axvspan(z0, z1, color="#fdf1e0")
a.annotate("", xy=(z1, 128), xytext=(z0, 128), arrowprops=dict(arrowstyle="<->", color="#8a5a1b", lw=1.6))
a.text(z1 + 25, 128, f"the taper spends {z1 - z0:.0f} µm here", ha="left", va="center", color="#8a5a1b")
a.text(400, 300, "hand-off window:\n140 to 180 nm wide", color="#8a5a1b", va="center")
a.set_ylabel("silicon width  (nm)")
a.set_ylim(80, 520); a.grid(alpha=.22)
a.set_title(f"A linear taper: {TIP:.0f} nm tip at z = 0, {END:.0f} nm at z = {LEN:.0f} µm")

b.semilogy(zb, beat[:, 1], "o-", lw=2.4, ms=6, color="#c0392b")
b.axvspan(z0, z1, color="#fdf1e0")
ladder = {155: 1000, 160: 760, 150: 580, 145: 440, 140: 335, 170: 255, 180: 160}   # label heights, spaced on the log axis
for zz, (wn, L) in zip(zb, beat):
    if wn in ladder:
        b.annotate(f"{wn:.0f} nm: {L:.0f} µm", xy=(zz, L), xytext=(540, ladder[wn]), color="#c0392b", va="center",
                   arrowprops=dict(arrowstyle="-", color="#c0392b", lw=0.7, shrinkA=0, shrinkB=2))
b.annotate("", xy=(z1, 25), xytext=(z0, 25), arrowprops=dict(arrowstyle="<->", color="#8a5a1b", lw=1.6))
b.text((z0 + z1) / 2, 15, f"offered: {z1 - z0:.0f} µm", ha="center", color="#8a5a1b")
b.text(20, 1200, "needed: one full slosh takes this long here", color="#c0392b")
b.set_ylim(10, 2000); b.set_xlim(0, 900)
b.set_xlabel("position along the taper, z  (µm)")
b.set_ylabel("beat length  (µm)")
b.grid(alpha=.22, which="both")
b.set_title("Beat length of the coupled pair along the taper", pad=14)

out = pathlib.Path(__file__).parent / "img" / "taper-window.png"
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("wrote", out, f"| window {W0:.0f}-{W1:.0f} nm sits at z = {z0:.0f}-{z1:.0f} um, {z1-z0:.0f} um long")

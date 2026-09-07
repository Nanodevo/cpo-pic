#!/usr/bin/env python3
"""One picture for what a ring resonator does, for the reader who is lost.
Top: the ring beside its bus. Middle: the transmission of ONE ring against wavelength, with the
spacing of its dips marked. Bottom: the four-ring bank of the die, ring 1's dips picked out.
Uses the circuit models of circuit_ringbank.py. Output: chain/img/ring-explainer.png"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import figstyle
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
import numpy as np, sax, gdsfactory as gf
import circuit_ringbank as cb

def spectrum(n_rings, wl):
    c = gf.Component(f"explainer_{n_rings}")
    s0 = c << gf.components.straight(length=20.0); prev = s0.ports["o2"]
    for k in range(n_rings):
        r = c << gf.components.ring_single(radius=cb.RADIUS + 0.05 * k, gap=cb.GAP, length_x=cb.LX, length_y=cb.LY); r.connect("o1", prev); prev = r.ports["o2"]
    s1 = c << gf.components.straight(length=20.0); s1.connect("o1", prev)
    c.add_port("in", port=s0.ports["o1"]); c.add_port("out", port=s1.ports["o2"])
    net = cb.to_sax(c.get_netlist(recursive=True)); net = {c.name: net[c.name], **{k: v for k, v in net.items() if k != c.name}}
    f, _ = sax.circuit(netlist=net, models={"straight": cb.straight, "bend_euler": cb.bend_euler, "coupler_ring": cb.coupler_ring})
    S = sax.sdict(f(wl=wl)); return 10 * np.log10(np.abs(np.asarray(S[("in", "out")])) ** 2)

wl = np.linspace(1.540, 1.560, 6001)
T1, T4 = spectrum(1, wl), spectrum(4, wl)
from scipy.signal import find_peaks
d1, _ = find_peaks(-T1, prominence=0.5); d4, _ = find_peaks(-T4, prominence=0.5)
fsr = np.diff(wl[d1] * 1e3)
L = 2 * cb.LX + 2 * cb.LY + 4 * cb.BEND_LEN; fsr_formula = 1.55 ** 2 / (cb.NG * L) * 1e3
print(f"one ring: dips at {np.round(wl[d1]*1e3, 2)} nm, spacing {np.round(fsr, 2)} nm; formula lambda^2/(n_g L) = {fsr_formula:.2f} nm")

fig, (a, b, c) = plt.subplots(3, 1, figsize=figstyle.size(7.6, 11.5), gridspec_kw=dict(height_ratios=[1.1, 1, 1], hspace=0.5))
# --- top: the picture
a.set_xlim(0, 100); a.set_ylim(0, 40); a.axis("off")
a.plot([5, 95], [10, 10], color="#1b6ca8", lw=6, solid_capstyle="butt"); a.text(50, 5.5, "bus waveguide, 500 nm wide", ha="center", va="top", color="#1b6ca8")
a.add_patch(Circle((50, 21.5), 9.5, fc="none", ec="#6b4fa0", lw=6)); a.text(50, 21.5, "ring", ha="center", va="center", color="#6b4fa0"); a.text(61, 26, "round trip\nL = 75.8 µm", ha="left", va="center", color="#6b4fa0", fontsize=10)
a.text(61, 11.6, "200 nm gap between ring and bus", ha="left", va="bottom", fontsize=9, color="#444")
a.add_patch(FancyArrowPatch((6, 10), (22, 10), arrowstyle="->", mutation_scale=18, lw=2, color="#e67e22")); a.text(14, 5.5, "light in, all wavelengths", ha="center", va="top", color="#e67e22", fontsize=10)
a.add_patch(FancyArrowPatch((78, 10), (94, 10), arrowstyle="->", mutation_scale=18, lw=2, color="#e67e22")); a.text(86, 5.5, "light out, minus the\nwavelengths the ring kept", ha="center", va="top", color="#e67e22", fontsize=10)
a.text(20, 31, "at a resonance the round trip holds a\nwhole number of wavelengths: light builds\nup in the ring and is taken out of the bus", fontsize=9.5, color="#333", ha="center", va="center")
a.set_title("What a ring resonator does")
# --- middle: one ring
b.plot(wl * 1e3, T1 - T1.max(), lw=1.6, color="#6b4fa0")
for i in d1: b.plot(wl[i] * 1e3, T1[i] - T1.max(), "v", color="#6b4fa0", ms=7)
if len(d1) >= 2:
    y = 0.25; x0, x1 = wl[d1[0]] * 1e3, wl[d1[1]] * 1e3
    b.annotate("", xy=(x1, y), xytext=(x0, y), arrowprops=dict(arrowstyle="<->", color="#c0392b", lw=1.8))
    b.text((x0 + x1) / 2, y + 0.12, f"spacing between two dips of the same ring:\nthe free spectral range, FSR = {fsr[0]:.2f} nm", ha="center", va="bottom", color="#c0392b", fontsize=10)
b.set_ylim(-1.6, 1.2); b.set_xlim(1540, 1560); b.grid(alpha=.22); b.set_ylabel("transmission  (dB)")
b.set_title("One ring on its bus: a dip at every resonance")
# --- bottom: the four-ring bank
c.plot(wl * 1e3, T4 - T4.max(), lw=1.4, color="#888780")
ring1 = wl[d1] * 1e3
for x in wl[d4] * 1e3:
    col = "#6b4fa0" if np.min(np.abs(ring1 - x)) < 0.05 else "#bbb"
    c.plot(x, T4[np.argmin(abs(wl * 1e3 - x))] - T4.max(), "v", color=col, ms=7)
c.text(1541.2, -1.45, "purple dips: ring 1 (radius 10.00 µm)\ngrey dips: rings 2, 3, 4 (10.05, 10.10, 10.15 µm)", fontsize=9.5, color="#333", va="bottom")
c.set_ylim(-1.6, 0.3); c.set_xlim(1540, 1560); c.grid(alpha=.22); c.set_xlabel("wavelength  (nm)"); c.set_ylabel("transmission  (dB)")
c.set_title("The die's ring bank: four rings, four interleaved sets of dips")
out = pathlib.Path(__file__).parent / "img" / "ring-explainer.png"; fig.savefig(out, bbox_inches="tight", facecolor="white"); print("wrote", out)

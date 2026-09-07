#!/usr/bin/env python3
"""The Mach-Zehnder interferometer from first principles: two waves adding, the phasor picture, and the
output powers against phase difference for perfect and imperfect couplers. -> chain/img/mzi-interference.png"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import figstyle
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import numpy as np
fig = plt.figure(figsize=figstyle.size(7.6, 10.4)); gs = fig.add_gridspec(3, 1, height_ratios=[1, 1, 1.15], hspace=0.5)
# --- A: two waves and their sum for three phase differences
a = fig.add_subplot(gs[0]); x = np.linspace(0, 4 * np.pi, 600)
for k, (dphi, lab) in enumerate(((0, "Δφ = 0: in step, the sum is doubled"), (np.pi / 2, "Δφ = π/2: quarter wave apart, the sum is √2 times one"), (np.pi, "Δφ = π: opposite, the sum is zero"))):
    off = -k * 4.6
    a.plot(x, 0.5 * np.sin(x) + off, color="#1b6ca8", lw=1.3); a.plot(x, 0.5 * np.sin(x + dphi) + off, color="#c0392b", lw=1.3)
    a.plot(x, 0.5 * np.sin(x) + 0.5 * np.sin(x + dphi) + off, color="#333", lw=2.2)
    a.text(4 * np.pi + 0.3, off, lab, va="center", fontsize=9.5)
a.set_xlim(0, 4 * np.pi + 11); a.set_ylim(-11.2, 1.6); a.axis("off")
a.text(0, 1.35, "wave from arm 1", color="#1b6ca8", fontsize=9.5); a.text(5.2, 1.35, "wave from arm 2", color="#c0392b", fontsize=9.5); a.text(10.4, 1.35, "their sum at the output", color="#333", fontsize=9.5)
a.set_title("Two equal waves meeting again: what the phase difference does to their sum")
# --- B: phasors
b = fig.add_subplot(gs[1]); b.set_aspect("equal"); b.set_xlim(-0.4, 10.2); b.set_ylim(-1.9, 1.5); b.axis("off")
for k, dphi in enumerate((0, np.pi / 2, 2 * np.pi / 3, np.pi)):
    cx = k * 2.7
    v1 = np.array([1.0, 0]); v2 = np.array([np.cos(dphi), np.sin(dphi)]); s = v1 + v2
    b.add_patch(FancyArrowPatch((cx, 0), (cx + v1[0], v1[1]), arrowstyle="->", mutation_scale=12, lw=2, color="#1b6ca8"))
    b.add_patch(FancyArrowPatch((cx + v1[0], v1[1]), (cx + s[0], s[1]), arrowstyle="->", mutation_scale=12, lw=2, color="#c0392b"))
    b.add_patch(FancyArrowPatch((cx, 0), (cx + s[0], s[1]), arrowstyle="->", mutation_scale=14, lw=2.6, color="#333"))
    b.text(cx + 1.0, -1.2, f"Δφ = {['0', 'π/2', '2π/3', 'π'][k]}\noutput power = {np.dot(s, s) / 4.0:.2f}", ha="center", va="top", fontsize=9.5)
b.set_title("As arrows: each arm one arrow, the output their sum, power the sum's length squared (over 4)")
# --- C: output powers against phase for perfect and imperfect couplers
c = fig.add_subplot(gs[2]); d = np.linspace(0, 2 * np.pi, 400)
for K, ls, lab in ((0.5, "-", "50:50 couplers"), (0.4, "--", "40:60 couplers")):
    P_cross = 4 * K * (1 - K) * np.cos(d / 2) ** 2; P_bar = (1 - K) ** 2 + K ** 2 - 2 * K * (1 - K) * np.cos(d)
    c.plot(d / np.pi, P_cross, ls=ls, lw=2.2, color="#1b6ca8", label=f"cross port, {lab}"); c.plot(d / np.pi, P_bar, ls=ls, lw=2.2, color="#c0392b", label=f"bar port, {lab}")
c.set_xlabel("phase difference between the arms, Δφ  (units of π)"); c.set_ylabel("fraction of the input power"); c.set_ylim(0, 1.05); c.grid(alpha=.22); c.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=9, frameon=False)
c.set_title("The interferometer's two outputs against Δφ, equation (13)")
out = pathlib.Path(__file__).parent / "img" / "mzi-interference.png"; fig.savefig(out, bbox_inches="tight", facecolor="white"); print("wrote", out)

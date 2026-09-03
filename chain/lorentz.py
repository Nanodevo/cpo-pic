#!/usr/bin/env python3
"""The bound electron as a driven damped oscillator: phase, index, absorption.

Model (Lorentz):   m x'' + m*Gamma*x' + m*w0^2 x = -e E(t)

Everything optical about a transparent material follows from the phase lag of
that oscillator. Below resonance the displacement follows the force, the
re-radiated field ends up a quarter cycle behind the incident field, and the sum
is delayed: that delay is the refractive index. At resonance the lag grows to a
half cycle, the re-radiated field opposes the incident one, and the result is
absorption.

Run:  python chain/lorentz.py  ->  chain/img/lorentz.png
"""
import pathlib

import matplotlib.pyplot as plt

import figstyle
import numpy as np

W0, GAMMA, WP2 = 1.0, 0.10, 0.20        # resonance, damping, plasma term (normalised)
w = np.linspace(0.01, 2.0, 1500)

phase = np.degrees(np.arctan2(GAMMA * w, W0**2 - w**2))     # lag of x behind the force
chi = WP2 / (W0**2 - w**2 - 1j * GAMMA * w)                 # susceptibility
n = np.sqrt(1 + chi)                                        # complex index

fig, ax = plt.subplots(1, 2, figsize=figstyle.size(11.2, 4.3))

ax[0].axvspan(0, 0.72, color="#e6f0e9", zorder=0)
ax[0].plot(w, phase, lw=2.4, color="#1b6ca8")
for y, lab in ((0, "in phase"), (90, "quarter cycle behind"), (180, "half cycle behind")):
    ax[0].axhline(y, color="#c9d4dd", lw=1, zorder=0)
    ax[0].text(1.98, y + 4, lab, ha="right", color="#5c6b7a")
ax[0].axvline(1.0, color="#c0392b", lw=1.2, ls="--")
ax[0].text(1.04, 30, "resonance ω₀", color="#c0392b")
ax[0].text(0.10, 152, "transparent window\nwhere glass is used", color="#2a6b3a")
ax[0].set_xlabel("driving frequency  ω / ω₀")
ax[0].set_ylabel("lag of the electron behind the force  (degrees)")
ax[0].set_title("How far the electron lags")
ax[0].set_ylim(-8, 190); ax[0].set_xlim(0, 2); ax[0].grid(alpha=.22)

ax[1].axvspan(0, 0.72, color="#e6f0e9", zorder=0)
ax[1].plot(w, n.real, lw=2.4, color="#1b6ca8", label="refractive index  n′")
ax[1].axhline(1, color="#c9d4dd", lw=1, zorder=0)
ax[1].set_ylabel("n′", color="#1b6ca8")
ax[1].set_xlabel("driving frequency  ω / ω₀")
ax2 = ax[1].twinx()
ax2.plot(w, n.imag, lw=2.2, color="#c0392b", ls="--", label="absorption  n″")
ax2.set_ylabel("n″  (absorption)", color="#c0392b")
ax[1].axvline(1.0, color="#c0392b", lw=1.2, ls="--")
ax[1].text(0.08, 1.075, "n rises with frequency here:\nnormal dispersion", color="#2a6b3a")
ax[1].set_title("What that lag produces")
ax[1].set_xlim(0, 2); ax[1].grid(alpha=.22)
h1, l1 = ax[1].get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax[1].legend(h1 + h2, l1 + l2, loc="upper right")

fig.suptitle("One driven electron explains the refractive index, dispersion and absorption", y=1.02)
fig.tight_layout()
out = pathlib.Path(__file__).parent / "img" / "lorentz.png"
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("wrote", out)
i = np.argmin(abs(w - 0.3))
print(f"at w/w0=0.3:  lag {phase[i]:.1f} deg,  n' {n.real[i]:.4f},  n'' {n.imag[i]:.2e}")
i = np.argmin(abs(w - 1.0))
print(f"at resonance: lag {phase[i]:.1f} deg,  n' {n.real[i]:.4f},  n'' {n.imag[i]:.3f}")

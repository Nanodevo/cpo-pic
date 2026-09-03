#!/usr/bin/env python3
"""A driven, damped playground swing, solved in steady state.

    m x'' + m*Gamma*x' + (m g / L) x = F0 cos(w t)

Steady state (complex method): x = Re[X e^{iwt}],
    X = (F0/m) / (w0^2 - w^2 + i*Gamma*w),   w0^2 = g/L
    amplitude A = |X|,  lag phi = arg(...) = atan2(Gamma*w, w0^2 - w^2)

Run:  python chain/pendulum.py  ->  chain/img/pendulum.png
"""
import pathlib

import matplotlib.pyplot as plt

import figstyle
import numpy as np

L, m, g, GAMMA, F0 = 2.5, 25.0, 9.81, 0.10, 20.0
w0 = np.sqrt(g / L)
T0 = 2 * np.pi / w0
SMALL_ANGLE_M = L * np.radians(15)          # where sin(theta) ~ theta stops holding

def response(w):
    X = (F0 / m) / (w0**2 - w**2 + 1j * GAMMA * w)
    return abs(X), np.degrees(np.arctan2(GAMMA * w, w0**2 - w**2))

print(f"w0 = {w0:.3f} rad/s, period {T0:.2f} s, Q = w0/Gamma = {w0/GAMMA:.0f}")
print(f"static deflection F0/(m w0^2) = {F0/(m*w0**2):.3f} m")
cases = [(0.1, "ω = 0.1·ω₀"), (1.0, "ω = ω₀"), (10.0, "ω = 10·ω₀")]
for r, lab in cases:
    A, ph = response(r * w0)
    print(f"{lab:12s}  A = {A:8.4f} m   lag = {ph:6.1f} deg   theta_max = {np.degrees(A/L):5.1f} deg")

w = np.logspace(-1.3, 1.3, 1200) * w0
A, ph = response(w)

fig = plt.figure(figsize=figstyle.size(7.6, 10.2))
gs = fig.add_gridspec(2, 3, height_ratios=[1.35, 1], hspace=0.6, wspace=0.28)

ax = fig.add_subplot(gs[0, :])
ax.loglog(w / w0, A, lw=2.4, color="#1b6ca8", label="amplitude A (m)")
ax.axhline(SMALL_ANGLE_M, color="#8a5a1b", ls=":", lw=1.4)
ax.text(1.9, SMALL_ANGLE_M * 1.25, "small-angle model unreliable above here (15°)", color="#8a5a1b")
ax.set_ylabel("amplitude A  (m)", color="#1b6ca8")
ax.set_xlabel("push frequency  ω / ω₀")
ax2 = ax.twinx()
ax2.semilogx(w / w0, ph, lw=2.2, color="#c0392b", ls="--", label="lag φ (degrees)")
ax2.set_ylabel("lag of the swing behind the push  (degrees)", color="#c0392b")
ax2.set_ylim(-10, 190); ax2.set_yticks([0, 90, 180])
for r, lab in cases:
    a, p = response(r * w0)
    ax.plot(r, a, "o", ms=8, color="#1b6ca8", zorder=5)
    ax2.plot(r, p, "o", ms=8, color="#c0392b", zorder=5)
ax.set_title("Steady-state response of the swing", pad=8)
ax.grid(alpha=.22, which="both")
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="upper left")

for k, (r, lab) in enumerate(cases):
    a, p = response(r * w0)
    wk = r * w0
    t = np.linspace(0, 3 * 2 * np.pi / wk, 700)
    push = np.cos(wk * t)
    x = np.cos(wk * t - np.radians(p))
    axk = fig.add_subplot(gs[1, k])
    axk.plot(t, push, lw=1.8, color="#888780", ls="--", label="push")
    axk.plot(t, x, lw=2.4, color="#1b6ca8", label="swing")
    axk.set_title(f"{lab}\n{a:.3g} m, lag {p:.0f}°")
    axk.set_xlabel("time (s)"); axk.set_yticks([])
    axk.grid(alpha=.2)
    if k == 0:
        axk.legend(loc="lower left")
        axk.set_ylabel("normalised")

fig.suptitle(f"Swing: L = {L} m, m = {m:.0f} kg, Γ = {GAMMA} s⁻¹, F₀ = {F0:.0f} N.   "
             f"ω₀ = {w0:.2f} rad/s, period {T0:.2f} s", y=0.985)
out = pathlib.Path(__file__).parent / "img" / "pendulum.png"
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("wrote", out)

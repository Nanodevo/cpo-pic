#!/usr/bin/env python3
"""Bend loss from the conformal transformation, solved and plotted.

The barrier integral, done exactly rather than in the a << x_t limit:

    I(R) = (4/3) * gamma * x_t * (1 - a/x_t)^(3/2),    x_t = R*(n_eff - n2)/n2

Relative leakage is exp(-I). The slowly varying 1/sqrt(R) prefactor is left
out: it changes the absolute loss but not the shape, and the useful engineering
quantity is the ratio between two radii.

Run:  python chain/bend_loss.py  ->  chain/img/bend-loss-curve.png
"""
import math
import pathlib

import matplotlib.pyplot as plt

import figstyle
import numpy as np
from scipy.optimize import brentq
from scipy.special import jv, kv

LAM = 1.55
K0 = 2 * math.pi / LAM


def step_index_mode(n2, dn, V):
    """u, b and n_eff for the fundamental mode of a step-index guide."""
    u = brentq(lambda u: u * jv(1, u) / jv(0, u)
               - math.sqrt(V*V - u*u) * kv(1, math.sqrt(V*V - u*u))
               / kv(0, math.sqrt(V*V - u*u)), 1e-9, V - 1e-9)
    b = 1 - (u / V) ** 2
    return u, b, n2 + b * dn


def case(name, n2, dn, V):
    na = math.sqrt(2 * n2 * dn) if dn < 0.1 else math.sqrt((n2 + dn)**2 - n2**2)
    a = V * LAM / (2 * math.pi * na)
    u, b, n_eff = step_index_mode(n2, dn, V)
    gamma = K0 * math.sqrt(n_eff**2 - n2**2)
    return dict(name=name, n2=n2, dn=dn, a=a, b=b, n_eff=n_eff, gamma=gamma,
                slope=(n_eff - n2) / n2)


def barrier(c, R):
    x_t = c["slope"] * R
    frac = np.clip(1 - c["a"] / x_t, 0, None)
    return (4 / 3) * c["gamma"] * x_t * frac ** 1.5


GLASS = case("IOX glass, dn 0.005", 1.500, 0.005, 2.0)
SIN   = case("silicon nitride, dn 0.55", 1.444, 0.55, 2.0)
SI    = case("silicon, dn 2.04", 1.444, 2.036, 2.0)

for c in (GLASS, SIN, SI):
    print(f"{c['name']:28s} a={c['a']:7.3f} um  b={c['b']:.3f}  "
          f"n_eff={c['n_eff']:.4f}  gamma={c['gamma']:.4f} /um")

print("\nglass, exact vs the a<<x_t limit:")
g = GLASS
for R_mm in (10, 15, 20, 25):
    R = R_mm * 1000
    I = barrier(g, R)
    I_lim = (2/3) * g["gamma"]**3 * R / (K0 * g["n_eff"])**2
    print(f"  R={R_mm:2d} mm  x_t={g['slope']*R:5.1f} um  a/x_t={g['a']/(g['slope']*R):.3f}  "
          f"I={I:6.2f}  I(limit)={I_lim:6.2f}  exp(-I)={math.exp(-I):.2e}")

print("\ndecibels of extra rejection per extra 5 mm of radius (glass):")
for R_mm in (10, 15, 20):
    d = barrier(g, (R_mm+5)*1000) - barrier(g, R_mm*1000)
    print(f"  {R_mm}->{R_mm+5} mm: factor {math.exp(d):.1f}, {10*math.log10(math.exp(d)):.1f} dB")

fig, ax = plt.subplots(figsize=figstyle.size(9, 5))
R = np.logspace(0, 5.2, 900)
for c, col in ((SI, "#1b6ca8"), (SIN, "#6b4fa0"), (GLASS, "#1D9E75")):
    y = np.exp(-barrier(c, R))
    ax.loglog(R, np.clip(y, 1e-18, None), color=col, lw=2.2, label=c["name"])
ax.axhline(1e-4, color="#888", ls=":", lw=1)
ax.text(300, 1.6e-4, "an arbitrary 'low enough' line", color="#5c6b7a")
for x, lab in ((5, "5 µm"), (100, "100 µm"), (15000, "15 mm")):
    ax.axvline(x, color="#d8dee4", lw=1, zorder=0)
    ax.text(x*1.15, 0.35, lab, color="#5c6b7a")
ax.set_xlim(1, 1.6e5); ax.set_ylim(1e-17, 3)
ax.set_xlabel("bend radius (µm)"); ax.set_ylabel("relative leakage, exp(−I)")
ax.set_title("Bend leakage against radius, three platforms, same physics")
ax.grid(alpha=.25, which="both"); ax.legend(loc="lower left")
out = pathlib.Path(__file__).parent / "img" / "bend-loss-curve.png"
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("\nwrote", out)

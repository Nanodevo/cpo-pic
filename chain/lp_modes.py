#!/usr/bin/env python3
"""The first six LP modes of a step-index fiber, solved and plotted.

Each LP_lm mode exists only above its own cutoff V. Ranking those cutoffs
is what "single mode" means: below the LP11 cutoff at V = 2.405 there is
nothing else for the light to be in.

Eigenvalue equation:   u*J_{l+1}(u)/J_l(u) = w*K_{l+1}(w)/K_l(w),  u^2+w^2 = V^2
Field:  E ~ J_l(u r/a) cos(l phi)                 inside the core
        E ~ J_l(u) K_l(w r/a)/K_l(w) cos(l phi)   outside

Run:  python chain/lp_modes.py   ->  chain/img/lp-modes.png
"""
import pathlib

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import brentq
from scipy.special import jn_zeros, jv, kv

V_PLOT = 8.0          # a fat multimode fiber, so every mode below exists
A = 1.0               # core radius, normalised

# (l, m, cutoff V) - cutoff of LP_lm is the m-th zero of J_(l-1)
MODES = [
    (0, 1, 0.000, "LP01"),
    (1, 1, 2.405, "LP11"),
    (2, 1, 3.832, "LP21"),
    (0, 2, 3.832, "LP02"),
    (3, 1, 5.136, "LP31"),
    (1, 2, 5.520, "LP12"),
]


def solve_u(l, m, V):
    """u for LP_lm: lies between its cutoff and the m-th zero of J_l."""
    lo = MODES_CUT[(l, m)] + 1e-6
    hi = min(jn_zeros(l, m)[-1] - 1e-6, V - 1e-9)

    def f(u):
        w = np.sqrt(max(V * V - u * u, 1e-12))
        return u * jv(l + 1, u) / jv(l, u) - w * kv(l + 1, w) / kv(l, w)

    return brentq(f, lo, hi, xtol=1e-12)


MODES_CUT = {(l, m): c for l, m, c, _ in MODES}


def field(l, u, V, n=420, span=2.2):
    w = np.sqrt(V * V - u * u)
    x = np.linspace(-span, span, n)
    X, Y = np.meshgrid(x, x)
    R = np.hypot(X, Y)
    P = np.arctan2(Y, X)
    inside = R <= A
    E = np.where(
        inside,
        jv(l, u * np.clip(R, 0, A) / A),
        jv(l, u) * kv(l, w * np.clip(R, A, None) / A) / kv(l, w),
    )
    return X, Y, E * np.cos(l * P)


fig = plt.figure(figsize=(11, 8.4))
gs = fig.add_gridspec(3, 3, height_ratios=[1, 1, 0.42], hspace=0.42, wspace=0.18)

for i, (l, m, cut, name) in enumerate(MODES):
    ax = fig.add_subplot(gs[i // 3, i % 3])
    u = solve_u(l, m, V_PLOT)
    X, Y, E = field(l, u, V_PLOT)
    ax.imshow((E ** 2) / (E ** 2).max(), extent=[X.min(), X.max(), Y.min(), Y.max()],
              cmap="magma", origin="lower")
    ax.add_patch(plt.Circle((0, 0), A, fill=False, ec="#7fd4ff", lw=1.1, ls="--"))
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(f"{name}   cutoff V = {cut:.3f}" if cut else f"{name}   no cutoff",
                 fontsize=11, pad=6)

ax = fig.add_subplot(gs[2, :])
ax.set_xlim(0, 6.2); ax.set_ylim(0, 1)
ax.get_yaxis().set_visible(False)
for s in ("left", "right", "top"):
    ax.spines[s].set_visible(False)
ax.axvspan(0, 2.405, color="#cfe8dd")
ax.text(0.95, 0.60, "single mode:\nonly LP01 exists here", ha="center", fontsize=10)
LABEL_Y = {"LP11": 0.30, "LP21": 0.30, "LP02": 0.54, "LP31": 0.30, "LP12": 0.54}
for l, m, cut, name in MODES:
    if cut == 0:
        continue
    ax.axvline(cut, color="#444", lw=1)
    ax.text(cut, LABEL_Y[name], f" {name}", fontsize=9.5, va="center")
ax.annotate("SMF-28 at 1550 nm\nV = 2.0", xy=(2.0, 0.06), xytext=(2.0, 0.88),
            ha="center", fontsize=10,
            arrowprops=dict(arrowstyle="->", color="#1b6ca8", lw=1.4))
ax.set_xlabel("V number", fontsize=11)
fig.suptitle("The first six LP modes, and the V at which each one switches on",
             fontsize=13, y=0.975)

out = pathlib.Path(__file__).parent / "img" / "lp-modes.png"
fig.savefig(out, dpi=170, bbox_inches="tight", facecolor="white")
print("wrote", out)
for l, m, cut, name in MODES:
    print(f"{name}: cutoff V {cut:6.3f}   u at V={V_PLOT} -> {solve_u(l, m, V_PLOT):.4f}")

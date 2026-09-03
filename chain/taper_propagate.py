#!/usr/bin/env python3
"""Rung 1: propagate light along the taper with the two-mode coupled equations.

In a frame rotating with the glass guide's propagation constant, with A the
amplitude in the silicon guide and B in the glass guide:

    i dA/dz = k0 * delta(z) * A + kappa * B
    i dB/dz = kappa * A

delta(z) = n_Si(w(z)) - n_glass from the cross-section sweep, kappa from the
supermode gap at the crossing. Start with all the light in the glass and read
|A|^2 at the end of the taper. Exact within the two-mode model; the same model
Landau-Zener approximates.

Run:  python chain/taper_propagate.py  ->  chain/img/taper-propagate.png
"""
import pathlib

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp

import figstyle

K0 = 2 * np.pi / 1.55
N_GLASS = 1.50522
G = 2.8e-3
KAPPA = K0 * G / 2                      # 5.68e-3 rad/um
TIP, END, L_DRAWN = 130.0, 500.0, 2000.0

sweep = np.array([[0.500,2.44966],[0.450,2.36236],[0.400,2.24035],[0.350,2.07525],[0.300,1.86147],
                  [0.260,1.68548],[0.220,1.55841],[0.200,1.53393],[0.190,1.52624],[0.180,1.51917],
                  [0.170,1.51279],[0.160,1.50724],[0.155,1.50483],[0.150,1.50275],[0.145,1.50101],
                  [0.140,1.49971],[0.130,1.49908],[0.120,1.49908]])[::-1]
w_pts, n_pts = sweep[:, 0] * 1e3, sweep[:, 1]
delta_of_w = lambda w: np.interp(w, w_pts, n_pts) - N_GLASS

# shaped profile w(z) for a taper of length L (constant adiabaticity)
_wg = np.linspace(TIP, END, 6000)
_d = delta_of_w(_wg)
_zunit = _d / (2 * K0 * G * np.sqrt(_d * _d + G * G)); _zunit -= _zunit[0]
def w_shaped(z, L):
    return np.interp(z, _zunit * (L / _zunit[-1]), _wg)
def w_linear(z, L):
    return TIP + (END - TIP) * z / L

def propagate(w_of_z, L, kappa=KAPPA, keep_path=False):
    def rhs(z, y):
        d = K0 * delta_of_w(w_of_z(z, L))
        return [-1j * (d * y[0] + kappa * y[1]), -1j * kappa * y[0]]
    sol = solve_ivp(rhs, (0, L), [0j, 1 + 0j], method="DOP853", rtol=1e-9, atol=1e-11,
                    max_step=min(1.0, L / 400), dense_output=keep_path)
    A, B = sol.y[:, -1]
    return (abs(A) ** 2, abs(A) ** 2 + abs(B) ** 2, sol)

for name, prof in (("linear", w_linear), ("shaped", w_shaped)):
    T, norm, _ = propagate(prof, L_DRAWN)
    print(f"{name:7s} 2 mm taper: transferred into the silicon = {T:6.1%}   (power conserved to {abs(norm-1):.1e})")
T841, _, _ = propagate(w_shaped, 841.0)
print(f"shaped  841 um taper: transferred = {T841:6.1%}")
alpha = K0 * abs(np.gradient(delta_of_w(w_linear(np.linspace(0, L_DRAWN, 4000), L_DRAWN)), np.linspace(0, L_DRAWN, 4000)))
i = np.argmin(abs(w_linear(np.linspace(0, L_DRAWN, 4000), L_DRAWN) - 156))
print(f"Landau-Zener for the linear 2 mm taper: transferred = {1 - np.exp(-2*np.pi*KAPPA**2/alpha[i]):.1%}")

# ---- power along z for the two 2 mm profiles -----------------------------
fig, (a, b) = plt.subplots(2, 1, figsize=figstyle.size(7.6, 9.4),
                           gridspec_kw=dict(hspace=0.42))
z = np.linspace(0, L_DRAWN, 3000)
for name, prof, col, ls in (("linear, as drawn", w_linear, "#888780", "--"), ("shaped, same 2 mm", w_shaped, "#1b6ca8", "-")):
    _, _, sol = propagate(prof, L_DRAWN, keep_path=True)
    A = sol.sol(z)[0]
    a.plot(z, abs(A) ** 2, lw=2.4, color=col, ls=ls, label=name)
a.set_xlabel("position along the taper, z  (µm)"); a.set_ylabel("fraction of the power in the silicon")
a.set_ylim(0, 1.05); a.grid(alpha=.22); a.legend(loc="lower right")
a.set_title("Light along the two 2 mm tapers, all of it starting in the glass")

# ---- transmission against taper length ------------------------------------
Ls = np.logspace(np.log10(150), np.log10(6000), 26)
T_lin = np.array([propagate(w_linear, L)[0] for L in Ls])
T_sh = np.array([propagate(w_shaped, L)[0] for L in Ls])
lz = np.array([1 - np.exp(-2*np.pi*KAPPA**2 / (K0 * abs(np.gradient(delta_of_w(w_linear(np.linspace(0,L,4000),L)), np.linspace(0,L,4000)))[np.argmin(abs(w_linear(np.linspace(0,L,4000),L)-156))])) for L in Ls])
b.semilogx(Ls, T_lin, "o-", ms=5, lw=2.2, color="#888780", label="linear taper")
b.semilogx(Ls, lz, ":", lw=1.6, color="#888780", label="Landau-Zener estimate, linear")
b.semilogx(Ls, T_sh, "o-", ms=5, lw=2.4, color="#1b6ca8", label="shaped taper")
b.axvline(L_DRAWN, color="#c0392b", lw=1.2, ls="--"); b.text(L_DRAWN * 1.06, 0.30, "as drawn,\n2 mm", color="#c0392b")
b.set_ylim(0, 1.05); b.set_xlabel("total taper length  (µm)"); b.set_ylabel("transferred into the silicon")
b.grid(alpha=.22, which="both")
from matplotlib.ticker import FixedLocator, FixedFormatter, NullFormatter
b.xaxis.set_major_locator(FixedLocator([200, 500, 1000, 2000, 5000])); b.xaxis.set_major_formatter(FixedFormatter(["200", "500", "1000", "2000", "5000"])); b.xaxis.set_minor_formatter(NullFormatter()); b.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), ncol=1, frameon=False)
b.set_title("How much crosses, against how long the taper is")

out = pathlib.Path(__file__).parent / "img" / "taper-propagate.png"
fig.savefig(out, bbox_inches="tight", facecolor="white"); print("wrote", out)
for L, tl, ts in zip(Ls, T_lin, T_sh):
    if L in Ls[::5]: print(f"   L = {L:6.0f} um   linear {tl:5.1%}   shaped {ts:5.1%}")

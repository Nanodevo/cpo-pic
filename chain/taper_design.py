#!/usr/bin/env python3
"""Reshaping the taper so that it is adiabatic.

Two-mode picture of the glass-to-silicon hand-off. Symbols:
  delta(w)  detuning between the isolated guides, n_Si(w) - n_glass   (index units)
  g         gap between the supermodes at the crossing, 2*kappa/k0      (index units)
  theta     mixing angle, tan(2 theta) = g / delta
  Omega     local beat rate, k0 * sqrt(delta^2 + g^2)                   (rad/um)
The adiabaticity parameter is  eps = |d theta / dz| / Omega.  Transfer follows the
local supermode when eps << 1.  A linear taper spends the same length at every
width; the shaped taper keeps eps constant by going slowly where the gap is
small:  dz = g * d delta / (2 eps k0 (delta^2 + g^2)^(3/2)),  which integrates to
  z(delta) = delta / (2 eps k0 g sqrt(delta^2 + g^2)) + const.

Isolated silicon n_eff(w) transcribed from the run of sim/taper_modes.py; the
glass guide n_eff and the gap from the same run.

Run:  python chain/taper_design.py  ->  chain/img/taper-design.png
"""
import pathlib

import matplotlib.pyplot as plt
import numpy as np

import figstyle

K0 = 2 * np.pi / 1.55                    # rad/um
N_GLASS = 1.50522
G = 2.8e-3                               # supermode gap at the crossing, index units
KAPPA = K0 * G / 2                       # coupling coefficient, rad/um
TIP, END, L = 120.0, 500.0, 2000.0       # nm, nm, um

sweep = np.array([[0.500,2.44966],[0.450,2.36236],[0.400,2.24035],[0.350,2.07525],[0.300,1.86147],
                  [0.260,1.68548],[0.220,1.55841],[0.200,1.53393],[0.190,1.52624],[0.180,1.51917],
                  [0.170,1.51279],[0.160,1.50724],[0.155,1.50483],[0.150,1.50275],[0.145,1.50101],
                  [0.140,1.49971],[0.130,1.49908],[0.120,1.49908]])[::-1]
w_pts, n_pts = sweep[:, 0] * 1e3, sweep[:, 1]
delta = lambda w: np.interp(w, w_pts, n_pts) - N_GLASS
w_cross = np.interp(0.0, n_pts - N_GLASS, w_pts)

# ---- the two profiles ---------------------------------------------------
z_lin = np.linspace(0, L, 2000)
w_lin = TIP + (END - TIP) / L * z_lin

def shaped_z(w, eps):
    d = delta(w)
    return d / (2 * eps * K0 * G * np.sqrt(d * d + G * G))
w_grid = np.linspace(TIP, END, 4000)
span = shaped_z(END, 1.0) - shaped_z(TIP, 1.0)
EPS_SHAPED = span / L                         # choose eps so the shaped taper is also 2 mm
z_shaped = (shaped_z(w_grid, EPS_SHAPED) - shaped_z(TIP, EPS_SHAPED))

# ---- local adiabaticity along each ---------------------------------------
def eps_local(w_of_z, z):
    d = delta(w_of_z)
    dd_dz = np.gradient(d, z)
    return G * np.abs(dd_dz) / (2 * K0 * (d * d + G * G) ** 1.5)
eps_lin = eps_local(w_lin, z_lin)
eps_sh = np.full_like(w_grid, EPS_SHAPED)   # exact by construction: the shaped profile holds eps constant

# ---- Landau-Zener estimate for the linear taper -------------------------
i = np.argmin(abs(w_lin - w_cross))
alpha = K0 * np.gradient(delta(w_lin), z_lin)[i]          # d(Delta beta)/dz at the crossing, rad/um^2
p_stay = np.exp(-2 * np.pi * KAPPA ** 2 / abs(alpha))
print(f"crossing at {w_cross:.0f} nm; kappa = {KAPPA:.2e} rad/um")
print(f"linear 2 mm taper: eps at the crossing = {eps_lin[i]:.2f}, Landau-Zener fraction left in the glass = {p_stay:.0%}")
print(f"shaped 2 mm taper: eps = {EPS_SHAPED:.3f} everywhere; shaped taper at eps = 0.1 would be {span/0.1:.0f} um long")
in_win = (w_grid >= 140) & (w_grid <= 180)
print(f"length spent in the 140-180 nm window: linear {40/((END-TIP)/L):.0f} um, shaped {z_shaped[in_win].max()-z_shaped[in_win].min():.0f} um")

fig, (a, b) = plt.subplots(2, 1, figsize=figstyle.size(7.6, 9.2), sharex=True,
                           gridspec_kw=dict(hspace=0.12, height_ratios=[1, 1.15]))
a.plot(z_lin, w_lin, lw=2.4, color="#888780", ls="--", label="linear taper, as drawn")
a.plot(z_shaped, w_grid, lw=2.6, color="#1b6ca8", label="shaped taper, same 2 mm")
a.axhspan(140, 180, color="#fdf1e0")
a.text(1250, 300, "hand-off window", color="#8a5a1b", va="center")
a.set_ylabel("silicon width  (nm)"); a.set_ylim(100, 520); a.grid(alpha=.22)
a.legend(loc="upper left")
a.set_title("Same length, different shape: spend it where the light needs it")

b.semilogy(z_lin, eps_lin, lw=2.4, color="#888780", ls="--", label="linear")
b.semilogy(z_shaped, eps_sh, lw=2.6, color="#1b6ca8", label="shaped")
b.axhline(0.1, color="#c0392b", ls=":", lw=1.4)
b.text(1650, 0.13, "rule of thumb: keep below 0.1", color="#c0392b", ha="right")
b.set_ylim(3e-3, 5); b.set_ylabel("adiabaticity parameter  ε"); b.set_xlabel("position along the taper, z  (µm)")
b.grid(alpha=.22, which="both"); b.legend(loc="upper right")
b.set_title("How hard each taper is pushing the light, along its length")

out = pathlib.Path(__file__).parent / "img" / "taper-design.png"
fig.savefig(out, bbox_inches="tight", facecolor="white"); print("wrote", out)

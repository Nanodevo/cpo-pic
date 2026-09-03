#!/usr/bin/env python3
"""Why chi^(2) vanishes in a centrosymmetric material.

An electron bound in a potential well V(x) responds linearly only while V is
parabolic. The anharmonic terms of V produce the nonlinear susceptibilities.
If V is an even function, its expansion contains no odd-order corrections to
the restoring force, so the second-order response vanishes identically.

Run:  python chain/anharmonic.py  ->  chain/img/anharmonic.png
"""
import pathlib

import matplotlib.pyplot as plt

import figstyle
import numpy as np

x = np.linspace(-2.5, 2.5, 600)
harm = 0.5 * x**2
sym = 0.5 * x**2 - 0.040 * x**4                 # even: silicon, silica
asym = 0.5 * x**2 - 0.150 * x**3 - 0.020 * x**4  # not even: LiNbO3, GaAs

fig, ax = plt.subplots(1, 2, figsize=figstyle.size(10.5, 4.1), sharey=True)
for a, V, title, sub in (
        (ax[0], sym, "symmetric well, V(−x) = V(x)",
         "silicon, silica, glass:  χ⁽²⁾ = 0,  χ⁽³⁾ ≠ 0"),
        (ax[1], asym, "asymmetric well, V(−x) ≠ V(x)",
         "LiNbO₃, GaAs, quartz:  χ⁽²⁾ ≠ 0")):
    a.plot(x, harm, ls="--", lw=1.4, color="#888780", label="harmonic, ½kx²")
    a.plot(x, V, lw=2.4, color="#1b6ca8", label="real binding potential")
    a.axvline(0, color="#d8dee4", lw=1, zorder=0)
    a.set_title(title, pad=8)
    a.set_xlabel("electron displacement  x")
    a.text(0.5, -0.30, sub, transform=a.transAxes, ha="center", color="#5c6b7a")
    a.set_ylim(-0.4, 3.4); a.grid(alpha=.22)
ax[0].set_ylabel("potential energy  V(x)")
ax[0].legend(loc="upper center")
fig.suptitle("Nonlinearity is the anharmonicity of the electron's binding potential", y=1.02)
fig.tight_layout()
out = pathlib.Path(__file__).parent / "img" / "anharmonic.png"
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("wrote", out)

#!/usr/bin/env python3
"""Export the linear and the shaped taper as GDS, for import into a simulator GUI.

Silicon layer (1, 0). The shaped profile is the constant-adiabaticity curve of
chain/taper_design.py; the linear one is the taper as drawn in chip.py. Both run
from the tip at z = 0 to 500 nm at z = 2000 um, with 20 um of straight 500 nm
waveguide added at the wide end so a port can sit on a uniform section.

Run:  python chain/taper_gds.py  ->  chain/gds/taper_shaped.gds, taper_linear.gds
"""
import pathlib

import gdstk
import numpy as np

K0 = 2 * np.pi / 1.55
N_GLASS = 1.50522
G = 2.8e-3
TIP, END, L, LEAD = 0.130, 0.500, 2000.0, 20.0     # um

sweep = np.array([[0.500,2.44966],[0.450,2.36236],[0.400,2.24035],[0.350,2.07525],[0.300,1.86147],
                  [0.260,1.68548],[0.220,1.55841],[0.200,1.53393],[0.190,1.52624],[0.180,1.51917],
                  [0.170,1.51279],[0.160,1.50724],[0.155,1.50483],[0.150,1.50275],[0.145,1.50101],
                  [0.140,1.49971],[0.130,1.49908],[0.120,1.49908]])[::-1]
w_pts, n_pts = sweep[:, 0], sweep[:, 1]
delta = lambda w: np.interp(w, w_pts, n_pts) - N_GLASS

def shaped_w_of_z(n=800):
    wg = np.linspace(TIP, END, 6000); d = delta(wg)
    zu = d / (2 * K0 * G * np.sqrt(d * d + G * G)); zu -= zu[0]; zu *= L / zu[-1]
    z = np.linspace(0, L, n)
    return z, np.interp(z, zu, wg)

def linear_w_of_z(n=200):
    z = np.linspace(0, L, n); return z, TIP + (END - TIP) * z / L

def polygon(z, w):
    z = np.concatenate([z, [L + LEAD]]); w = np.concatenate([w, [END]])
    top = np.column_stack([z, +w / 2]); bot = np.column_stack([z[::-1], -w[::-1] / 2])
    return gdstk.Polygon(np.vstack([top, bot]).tolist(), layer=1, datatype=0)

out = pathlib.Path(__file__).parent / "gds"
for name, (z, w) in (("shaped", shaped_w_of_z()), ("linear", linear_w_of_z())):
    lib = gdstk.Library(unit=1e-6, precision=1e-9)
    cell = lib.new_cell(f"taper_{name}")
    poly = polygon(z, w); cell.add(poly)
    path = out / f"taper_{name}.gds"; lib.write_gds(str(path))
    (x0, y0), (x1, y1) = poly.bounding_box()
    print(f"{name:7s}: {len(poly.points)} vertices, x {x0:.0f}..{x1:.0f} um, width {2*y0*-1:.3f}..{2*y1:.3f} um -> {path.name}")

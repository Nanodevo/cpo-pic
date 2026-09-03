#!/usr/bin/env python3
"""The full bonded stack as a multi-layer GDS for viewing in KLayout (plan view + 2.5D view).

Layers (layer/datatype), matching the geometry of chain/taper_eme.py:
  1/0 silicon taper   130 -> 500 nm wide, 2000 um + 20 um lead, 220 nm thick, on the adhesive
  2/0 IOX glass guide  6 um wide, 4 um deep, top flush with the glass surface
  3/0 adhesive         1 um bondline over the whole width
  4/0 glass            the substrate (drawn 8 um deep here; 12 um in the simulation)
The z-stack for KLayout's 2.5D viewer is written beside it as stack.lyd25.

Run:  python chain/stack_gds.py  ->  chain/gds/stack_shaped.gds, chain/gds/stack.lyd25
"""
import pathlib
import gdstk
import numpy as np

K0 = 2 * np.pi / 1.55; N_GLASS = 1.50522; G = 2.8e-3
TIP, END, L, LEAD = 0.130, 0.500, 2000.0, 20.0
W_BOX = 16.0                       # simulation box width in x, used for the sheet layers
sweep = np.array([[0.500,2.44966],[0.450,2.36236],[0.400,2.24035],[0.350,2.07525],[0.300,1.86147],
                  [0.260,1.68548],[0.220,1.55841],[0.200,1.53393],[0.190,1.52624],[0.180,1.51917],
                  [0.170,1.51279],[0.160,1.50724],[0.155,1.50483],[0.150,1.50275],[0.145,1.50101],
                  [0.140,1.49971],[0.130,1.49908],[0.120,1.49908]])[::-1]
delta = lambda w: np.interp(w, sweep[:, 0], sweep[:, 1]) - N_GLASS

def shaped_w_of_z(n=800):
    wg = np.linspace(TIP, END, 6000); d = delta(wg)
    zu = d / (2 * K0 * G * np.sqrt(d * d + G * G)); zu -= zu[0]; zu *= L / zu[-1]
    z = np.linspace(0, L, n); return z, np.interp(z, zu, wg)

z, w = shaped_w_of_z()
z = np.concatenate([z, [L + LEAD]]); w = np.concatenate([w, [END]])
top = np.column_stack([z, +w / 2]); bot = np.column_stack([z[::-1], -w[::-1] / 2])
silicon = gdstk.Polygon(np.vstack([top, bot]).tolist(), layer=1, datatype=0)

lib = gdstk.Library(unit=1e-6, precision=1e-9)
cell = lib.new_cell("stack_shaped")
cell.add(gdstk.rectangle((0, -W_BOX / 2), (L + LEAD, W_BOX / 2), layer=4, datatype=0))   # glass
cell.add(gdstk.rectangle((0, -3.0), (L + LEAD, 3.0), layer=2, datatype=0))               # IOX guide
cell.add(gdstk.rectangle((0, -W_BOX / 2), (L + LEAD, W_BOX / 2), layer=3, datatype=0))   # adhesive
cell.add(silicon)
out = pathlib.Path(__file__).parent / "gds"; out.mkdir(exist_ok=True)
lib.write_gds(str(out / "stack_shaped.gds"))
print("wrote", out / "stack_shaped.gds", "layers 1/0 silicon, 2/0 IOX, 3/0 adhesive, 4/0 glass")

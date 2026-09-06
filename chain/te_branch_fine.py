#!/usr/bin/env python3
"""Same as te_branch.py but with a 5 nm mesh on the silicon, so the width is resolved.
Writes chain/eme/te_branch_fine.json."""
import json, pathlib, sys
import numpy as np, tidy3d as td
from tidy3d.plugins.mode import ModeSolver
N_GLASS, N_IOX, N_ADH, N_SI, N_OX = 1.500, 1.512, 1.500, 3.4757, 1.444
BOND, T_SI, IOX_W, IOX_D = 1.0, 0.22, 6.0, 4.0
med = lambda n: td.Medium(permittivity=n * n)
def sim_for(width, with_iox):
    s = [td.Structure(geometry=td.Box(center=(0, -6, 0), size=(td.inf, 12, td.inf)), medium=med(N_GLASS))]
    if with_iox: s.append(td.Structure(geometry=td.Box(center=(0, -2, 0), size=(IOX_W, IOX_D, td.inf)), medium=med(N_IOX)))
    s.append(td.Structure(geometry=td.Box(center=(0, 0.5, 0), size=(td.inf, BOND, td.inf)), medium=med(N_ADH)))
    if width > 0: s.append(td.Structure(geometry=td.Box(center=(0, BOND + T_SI / 2, 0), size=(width, T_SI, td.inf)), medium=med(N_SI)))
    mesh = [td.MeshOverrideStructure(geometry=td.Box(center=(0, BOND + T_SI / 2, 0), size=(1.0, 0.5, td.inf)), dl=(0.005, 0.005, None)),
            td.MeshOverrideStructure(geometry=td.Box(center=(0, -2, 0), size=(8, 6, td.inf)), dl=(0.12, 0.12, None))]
    return td.Simulation(center=(0, -2, 0), size=(16, 12, 2), medium=med(N_OX), structures=s, run_time=1e-12,
                         grid_spec=td.GridSpec.auto(wavelength=1.55, min_steps_per_wvl=12, override_structures=mesh),
                         boundary_spec=td.BoundarySpec.all_sides(boundary=td.PECBoundary()))
def solve(width, with_iox, n):
    ms = ModeSolver(simulation=sim_for(width, with_iox), plane=td.Box(center=(0, -2, 0), size=(16, 12, 0)),
                    mode_spec=td.ModeSpec(num_modes=n, num_pml=(12, 12)), freqs=[td.C_0 / 1.55])
    d = ms.solve(); info = d.modes_info
    return [(float(d.n_eff.isel(f=0, mode_index=m)), float(info["mode area"].isel(f=0, mode_index=m)), float(info["TE (Ex) fraction"].isel(f=0, mode_index=m))) for m in range(n)]
out = {"glass_te": None, "isolated_te": [], "coupled_te": []}
g = solve(0.0, True, 2); out["glass_te"] = max(x[0] for x in g if x[2] > 0.5); print(f"glass TE mode: n_eff {out['glass_te']:.5f}", flush=True)
for w in (0.190, 0.195, 0.200, 0.205, 0.210, 0.215, 0.220, 0.240, 0.260, 0.300, 0.350, 0.400, 0.450, 0.500):
    r = solve(w, False, 3); cand = [x for x in r if x[2] > 0.5 and x[0] > 1.445]
    if cand: ne, area, te = max(cand); out["isolated_te"].append([w, ne, area]); print(f"   isolated TE  w = {w*1e3:.0f} nm : n_eff {ne:.5f}  area {area:6.2f}", flush=True)
    else: print(f"   isolated TE  w = {w*1e3:.0f} nm : not bound", flush=True)
for w in (0.196, 0.199, 0.202, 0.205, 0.208, 0.212):
    r = solve(w, True, 5); te = [[x[0], x[1]] for x in r if x[2] > 0.5 and x[0] > 1.4995]
    out["coupled_te"].append([w, te]); print(f"   coupled TE   w = {w*1e3:.0f} nm : " + "  |  ".join(f"n {n:.5f} area {a:5.1f}" for n, a in te), flush=True)
p = pathlib.Path(__file__).parent / "eme" / "te_branch_fine.json"; p.write_text(json.dumps(out, indent=1)); print("wrote", p, flush=True)

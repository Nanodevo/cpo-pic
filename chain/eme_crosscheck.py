#!/usr/bin/env python3
"""Local (free) cross-check of the rung-2 cross-section with Tidy3D's own mode solver:
where does the silicon-like mode cross the glass mode in THIS 3D model, and how big is
the supermode gap there? Same media, mesh and box as chain/taper_eme.py."""
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
    mesh = [td.MeshOverrideStructure(geometry=td.Box(center=(0, BOND + T_SI / 2, 0), size=(1.2, 0.6, td.inf)), dl=(0.02, 0.02, None)),
            td.MeshOverrideStructure(geometry=td.Box(center=(0, -2, 0), size=(8, 6, td.inf)), dl=(0.12, 0.12, None))]
    return td.Simulation(center=(0, -2, 0), size=(16, 12, 2), medium=med(N_OX), structures=s, run_time=1e-12,
                         grid_spec=td.GridSpec.auto(wavelength=1.55, min_steps_per_wvl=12, override_structures=mesh),
                         boundary_spec=td.BoundarySpec.all_sides(boundary=td.PECBoundary()))
def solve(width, with_iox, n=4):
    ms = ModeSolver(simulation=sim_for(width, with_iox), plane=td.Box(center=(0, -2, 0), size=(16, 12, 0)),
                    mode_spec=td.ModeSpec(num_modes=n, num_pml=(12, 12)), freqs=[td.C_0 / 1.55])
    d = ms.solve(); info = d.modes_info
    out = []
    for m in range(n):
        ne = float(d.n_eff.isel(f=0, mode_index=m)); ke = float(d.k_eff.isel(f=0, mode_index=m))
        area = float(info["mode area"].isel(f=0, mode_index=m)) if "mode area" in info else float("nan")
        te = float(info["TE (Ex) fraction"].isel(f=0, mode_index=m)) if "TE (Ex) fraction" in info else float("nan")
        out.append((ne, ke, area, te))
    return out
print("glass guide alone (no silicon):")
for ne, ke, area, te in solve(0.0, True, 3): print(f"   n_eff {ne:.5f}  loss {ke:.1e}  area {area:6.2f} um^2  TE {te:.2f}")
print("\nisolated silicon strip on the adhesive, oxide above (no IOX guide): the silicon-like mode")
iso = {}
for w in (0.140, 0.150, 0.160, 0.170, 0.180, 0.200, 0.220):
    r = solve(w, False, 2); ne, ke, area, te = r[0]; iso[w] = ne
    print(f"   w = {w*1e3:.0f} nm : n_eff {ne:.5f}  area {area:6.2f} um^2  TE {te:.2f}   {'bound' if ne > 1.5 else 'NOT bound'}")
print("\nboth guides together: the two lowest-order modes (supermodes) and their split")
for w in (0.150, 0.160, 0.170, 0.180):
    r = solve(w, True, 4)
    rows = "  |  ".join(f"n {ne:.5f} area {area:5.1f} TE {te:.2f}" for ne, ke, area, te in r[:3])
    print(f"   w = {w*1e3:.0f} nm : {rows}")

# ---- the branch that matters for the launched light: the E_x ("TE") silicon mode -------
print("\nisolated silicon strip: the E_x-polarized (TE) silicon mode, tracked by TE fraction")
te_iso = {}
for w in (0.180, 0.200, 0.220, 0.240, 0.260, 0.300):
    r = solve(w, False, 3)
    cand = [x for x in r if x[3] > 0.5 and x[0] > 1.445]
    if cand:
        ne, ke, area, te = max(cand); te_iso[w] = ne
        print(f"   w = {w*1e3:.0f} nm : TE-mode n_eff {ne:.5f}  area {area:6.2f} um^2  TE {te:.2f}   {'bound vs adhesive' if ne > 1.5 else 'below the adhesive index'}")
    else:
        print(f"   w = {w*1e3:.0f} nm : no bound TE-polarized silicon mode above the oxide index")
print("\nboth guides together near the TE crossing: modes with TE fraction > 0.5 (E_x), n_eff and area")
for w in (0.190, 0.200, 0.210, 0.220, 0.240):
    r = solve(w, True, 5)
    rows = "  |  ".join(f"n {ne:.5f} area {area:5.1f}" for ne, ke, area, te in r if te > 0.5)
    print(f"   w = {w*1e3:.0f} nm : {rows}")

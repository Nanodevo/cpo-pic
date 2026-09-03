#!/usr/bin/env python3
"""Solve the two port cross-sections of the EME simulation with Tidy3D's local
mode solver, to confirm which mode index is the glass mode at the input and the
silicon mode at the output, and to cross-check n_eff against the femwell results.

Runs locally; spends no credits.

Run:  python chain/eme_ports.py [shaped|linear]
"""
import sys

import numpy as np
import tidy3d as td
from tidy3d.plugins.mode import ModeSolver

sys.argv = sys.argv[:2] if len(sys.argv) > 1 else ["x", "shaped"]
src = open(__file__.replace("eme_ports.py", "taper_eme.py")).read().split("sim = td.EMESimulation(")[0]
exec(src)

base = td.Simulation(center=(0, -2.0, (Z0 + Z1) / 2), size=(16, 12, Z1 - Z0), medium=med(N_OX), structures=structures,
                     grid_spec=td.GridSpec.auto(wavelength=LAM, min_steps_per_wvl=12, override_structures=[mesh_si, mesh_iox]),
                     run_time=1e-12, boundary_spec=td.BoundarySpec.all_sides(boundary=td.PECBoundary()))
for label, zc in (("input port, tip", 0.5), ("output port, 500 nm", L + LEAD - 0.5)):
    ms = ModeSolver(simulation=base, plane=td.Box(center=(0, -2.0, zc), size=(16, 12, 0)),
                    mode_spec=td.ModeSpec(num_modes=6, num_pml=(12, 12)), freqs=[td.C_0 / LAM])
    data = ms.solve()
    neff = np.real(data.n_eff.values[0])
    E2 = sum(abs(data.field_components[c]) ** 2 for c in ("Ex", "Ey", "Ez")).isel(f=0)
    print(f"\n{label}")
    for m in range(6):
        f = float(E2.isel(mode_index=m).sel(y=slice(BOND - 0.3, BOND + T_SI + 0.3)).sum() / E2.isel(mode_index=m).sum())
        print(f"   mode {m}: n_eff = {neff[m]:.5f}   {f:5.1%} of |E|^2 within 0.3 um of the silicon")

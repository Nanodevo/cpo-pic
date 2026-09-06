#!/usr/bin/env python3
"""Waveguide numbers for the circuit model of the ring bank, from the local Tidy3D mode
solver (free): the routing strip is 500 x 220 nm silicon in oxide (BOX below, oxide above),
which is what the die's rings and buses are; the taper region's adhesive stack is not here.
  n_eff(lambda) at 1540/1550/1560 nm  -> effective index and group index n_g = n_eff - lambda dn_eff/dlambda
  two strips 200 nm apart             -> symmetric/antisymmetric supermode split -> coupling per length
Writes chain/eme/ring_params.json"""
import json, pathlib, numpy as np, tidy3d as td
from tidy3d.plugins.mode import ModeSolver
N_SI, N_OX, W, T, GAP = 3.4757, 1.444, 0.5, 0.22, 0.2
med = lambda n: td.Medium(permittivity=n * n)
def sim(strips):
    s = [td.Structure(geometry=td.Box(center=(x, 0, 0), size=(W, T, td.inf)), medium=med(N_SI)) for x in strips]
    mesh = [td.MeshOverrideStructure(geometry=td.Box(center=(0, 0, 0), size=(3.0, 1.0, td.inf)), dl=(0.01, 0.01, None))]
    return td.Simulation(center=(0, 0, 0), size=(6, 4, 2), medium=med(N_OX), structures=s, run_time=1e-12,
                         grid_spec=td.GridSpec.auto(wavelength=1.55, min_steps_per_wvl=12, override_structures=mesh),
                         boundary_spec=td.BoundarySpec.all_sides(boundary=td.PECBoundary()))
def solve(strips, lam, n=2):
    ms = ModeSolver(simulation=sim(strips), plane=td.Box(center=(0, 0, 0), size=(6, 4, 0)),
                    mode_spec=td.ModeSpec(num_modes=n, num_pml=(10, 10)), freqs=[td.C_0 / lam])
    d = ms.solve(); te = d.modes_info["TE (Ex) fraction"].isel(f=0).values
    return [float(d.n_eff.isel(f=0, mode_index=m)) for m in range(n) if te[m] > 0.5]
out = {}
lams = [1.540, 1.550, 1.560]
ne = [solve([0.0], l, 2)[0] for l in lams]
ng = ne[1] - 1.55 * (ne[2] - ne[0]) / 0.02
out.update(n_eff=ne[1], n_g=ng, n_eff_vs_lambda=dict(zip(lams, ne)))
print(f"single strip 500 x 220 nm in oxide: n_eff(1550) = {ne[1]:.4f}, group index n_g = {ng:.3f}")
pair = solve([-(W + GAP) / 2, (W + GAP) / 2], 1.55, 3)
ns, na = max(pair[:2]), min(pair[:2]); kappa = np.pi * (ns - na) / 1.55        # rad/um, coupling per unit length
Lc = np.pi / (2 * kappa)
out.update(n_sym=ns, n_anti=na, kappa_per_um=float(kappa), full_transfer_length_um=float(Lc))
print(f"two strips, {GAP*1e3:.0f} nm gap: symmetric {ns:.5f}, antisymmetric {na:.5f}, split {ns-na:.2e} -> kappa {kappa:.4f} rad/um, full transfer in {Lc:.1f} um")
pathlib.Path(__file__).parent.joinpath("eme", "ring_params.json").write_text(json.dumps(out, indent=1)); print("wrote chain/eme/ring_params.json")

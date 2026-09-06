"""The crossing alone: the die's linear taper from 180 to 240 nm (375 um at 0.16 nm/um), 30 cells, 16 modes,
with a coarse field monitor over the region. Built to see where the glass light goes without paying for
the whole 2 mm. Writes chain/eme/crossing_te3d.json"""

import pathlib
import sys

import numpy as np
import tidy3d as td

PROFILE = "crossing"
LAM = 1.55
K0 = 2 * np.pi / LAM
N_GLASS, N_IOX, N_ADH, N_SI, N_OX = 1.500, 1.512, 1.500, 3.4757, 1.444
from branch import BR
TIP, END, L, LEAD = 0.180, 0.240, 375.0, 10.0   # only the crossing region, at the die's linear slope 0.16 nm/um
BOND, T_SI = 1.0, 0.22
IOX_W, IOX_D = 6.0, 4.0
G = BR.G
NUM_MODES = 16   # was 8: with 8 modes the first run lost 25% of an untouched glass mode to basis truncation across 120 cell interfaces

delta = lambda w: BR.delta(w * 1e3)

def write_for_2_11(sim, path):
    """Write the simulation JSON without the fields tidy3d 2.12 added (min_steps_per_size,
    eme_diagnostics); the Tidy3D hosted notebook runs 2.11.2 and rejects them."""
    import json
    drop = {"min_steps_per_size", "eme_diagnostics"}
    def strip(o):
        if isinstance(o, dict): return {k: strip(v) for k, v in o.items() if k not in drop}
        if isinstance(o, list): return [strip(v) for v in o]
        return o
    d = strip(json.loads(sim.json())); d["version"] = "2.11.2"
    pathlib.Path(path).write_text(json.dumps(d, indent=1))


def profile(n=600):
    z = np.linspace(0, L, n)
    if PROFILE == "linear":
        return z, TIP + (END - TIP) * z / L
    wg = np.linspace(TIP, END, 6000); d = delta(wg)
    zu = d / (2 * K0 * G * np.sqrt(d * d + G * G)); zu -= zu[0]; zu *= L / zu[-1]
    return z, np.interp(z, zu, wg)

z, w = profile()
z = np.concatenate([z, [L + LEAD]]); w = np.concatenate([w, [END]])
verts = np.vstack([np.column_stack([+w / 2, z]), np.column_stack([-w[::-1] / 2, z[::-1]])])   # (x, z)

med = lambda n: td.Medium(permittivity=n * n)
Z0, Z1 = 0.0, L + LEAD
structures = [
    td.Structure(geometry=td.Box(center=(0, -6, (Z0 + Z1) / 2), size=(td.inf, 12, td.inf)), medium=med(N_GLASS), name="glass"),
    td.Structure(geometry=td.Box(center=(0, -IOX_D / 2, (Z0 + Z1) / 2), size=(IOX_W, IOX_D, td.inf)), medium=med(N_IOX), name="iox"),
    td.Structure(geometry=td.Box(center=(0, BOND / 2, (Z0 + Z1) / 2), size=(td.inf, BOND, td.inf)), medium=med(N_ADH), name="adhesive"),
    td.Structure(geometry=td.PolySlab(vertices=verts.tolist(), axis=1, slab_bounds=(BOND, BOND + T_SI)), medium=med(N_SI), name="silicon"),
]
mesh_si = td.MeshOverrideStructure(geometry=td.Box(center=(0, BOND + T_SI / 2, (Z0 + Z1) / 2), size=(1.2, 0.6, td.inf)), dl=(0.02, 0.02, None))
mesh_iox = td.MeshOverrideStructure(geometry=td.Box(center=(0, -IOX_D / 2, (Z0 + Z1) / 2), size=(IOX_W + 2, IOX_D + 2, td.inf)), dl=(0.12, 0.12, None))

sim = td.EMESimulation(
    center=(0, -2.0, (Z0 + Z1) / 2), size=(16, 12, Z1 - Z0),
    medium=med(N_OX), structures=structures,
    grid_spec=td.GridSpec.auto(wavelength=LAM, min_steps_per_wvl=12, override_structures=[mesh_si, mesh_iox]),
    axis=2, freqs=[td.C_0 / LAM],
    eme_grid_spec=td.EMEUniformGrid(num_cells=30, mode_spec=td.EMEModeSpec(num_modes=NUM_MODES, num_pml=(12, 12))),
    boundary_spec=td.BoundarySpec.all_sides(boundary=td.PECBoundary()),
    # a field monitor cannot be combined with a length sweep, so: sweep for the S-matrix curve, field picture on its own
    monitors=[td.EMEFieldMonitor(center=(0, -1.5, (Z0 + Z1) / 2), size=(0, 9, Z1 - Z0), name="side", fields=["Ex", "Ey"], interval_space=(1, 2, 4))],
    sweep_spec=None,
)
out = pathlib.Path(__file__).parent / "eme"; out.mkdir(exist_ok=True)
SUFFIX = "_te3d"
write_for_2_11(sim, str(out / f"{PROFILE}{SUFFIX}.json"))
g = sim.grid.num_cells
print(f"{PROFILE}: validated. cross-section grid {g[0]} x {g[1]} points, {sim.eme_grid_spec.num_cells} EME cells x {sim.eme_grid_spec.mode_spec.num_modes} modes")
print("port modes stored:", sim.store_port_modes, "| sweep:", sim.sweep_spec.scale_factors.tolist() if sim.sweep_spec else None)

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(3, 1, figsize=(7.6, 10.5))
sim.plot(x=0, ax=ax[0]); ax[0].set_title(f"side view along z (x = 0), {PROFILE}"); ax[0].set_xlim(0, 60); ax[0].set_ylim(-8, 4)
sim.plot(y=BOND + T_SI / 2, ax=ax[1]); ax[1].set_title("top view in the silicon plane, first 60 um"); ax[1].set_xlim(0, 60); ax[1].set_ylim(-1, 1)
sim.plot(z=1000, ax=ax[2]); ax[2].set_title("cross-section at z = 1000 um")
fig.tight_layout(); fig.savefig(str(out / f"{PROFILE}{SUFFIX}_geometry.png"), dpi=110, facecolor="white"); print("wrote", out / f"{PROFILE}{SUFFIX}_geometry.png")

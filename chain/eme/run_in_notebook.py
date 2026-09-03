# Cells for the Tidy3D hosted notebook. Upload shaped.json (or linear.json) beside this,
# then run the cells one at a time. Cell 3 is the only one that spends credits.

# ---- cell 1: load and look -------------------------------------------------
import tidy3d as td
from tidy3d import web
sim = td.EMESimulation.from_file("shaped.json")
print(sim.eme_grid_spec.num_cells, "cells,", sim.eme_grid_spec.mode_spec.num_modes, "modes per cell")
print("length sweep:", None if sim.sweep_spec is None else sim.sweep_spec.scale_factors.tolist())
sim.plot(z=1000)   # cross-section: small silicon on the adhesive band, the big glass guide below

# ---- cell 2: upload and ask the price (spends nothing) -------------------
task_id = web.upload(sim, task_name="cpo-pic shaped taper EME")
print("estimated FlexCredits:", web.estimate_cost(task_id))
# STOP HERE. Decide with the number in front of you.

# ---- cell 3: run and download (this spends the credits) ------------------
web.start(task_id)
web.monitor(task_id)
data = web.load(task_id, path="shaped_result.hdf5")

# ---- cell 4: read the answer ---------------------------------------------
import numpy as np
S21 = data.smatrix.S21.isel(f=0, mode_index_in=0, mode_index_out=0)   # glass mode in -> silicon mode out
S11 = data.smatrix.S11.isel(f=0, mode_index_in=0, mode_index_out=0)   # reflected back into the glass mode
scales = [1.0] if sim.sweep_spec is None else sim.sweep_spec.scale_factors.tolist()
for k, s in enumerate(scales):
    t = abs(S21.isel(sweep_index=k).values) ** 2 if "sweep_index" in S21.dims else abs(S21.values) ** 2
    print(f"taper length {2000*s:6.0f} um : transferred into the silicon {float(t):6.1%}")
# Then download shaped_result.hdf5 from the notebook's file browser and put it in chain/eme/.

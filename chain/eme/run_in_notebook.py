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

# ---- cell 5: where did the light go? (run on the loaded `data` of the shaped job) ----
import numpy as np
pm = data.port_modes
for port in ("in", "out"):
    try:
        sub = pm.sel(eme_port_index=0 if port == "in" else 1) if "eme_port_index" in pm.n_eff.dims else pm
        ne = sub.n_eff.isel(f=0).values; te = sub.modes_info["TE (Ex) fraction"].isel(f=0).values if "TE (Ex) fraction" in sub.modes_info else [float("nan")] * len(ne)
        print(f"port {port}: " + ", ".join(f"m{m}: n_eff {float(n):.5f} TE {float(t):.2f}" for m, (n, t) in enumerate(zip(ne, te))))
    except Exception as e:
        print("port modes:", type(e).__name__, e)
S21 = data.smatrix.S21.isel(f=0); S11 = data.smatrix.S11.isel(f=0)
k = list(sim.sweep_spec.scale_factors).index(1.0) if "sweep_index" in S21.dims else None
P21 = abs(S21.isel(sweep_index=k) if k is not None else S21) ** 2
P11 = abs(S11.isel(sweep_index=k) if k is not None else S11) ** 2
print("\n|S21|^2 at the true length: rows = output mode at port 2, columns = input mode at port 1 (first 4 x 4)")
print(np.round(P21.values[:4, :4], 4))
print("power launched in input mode 0 that arrives in ANY port-2 mode:", float(P21.values[:, 0].sum()), " reflected into any port-1 mode:", float(P11.values[:, 0].sum()))
print("power launched in input mode 1 that arrives in ANY port-2 mode:", float(P21.values[:, 1].sum()), " reflected:", float(P11.values[:, 1].sum()))
if k is not None:
    print("\nsweep, input mode 1 (glass TM) -> output mode 1 (silicon TM):")
    for j, s in enumerate(sim.sweep_spec.scale_factors):
        print(f"   taper length {2000*s:6.0f} um : {float(abs(S21.isel(sweep_index=j, mode_index_in=1, mode_index_out=1))**2):6.1%}")

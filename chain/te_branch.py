#!/usr/bin/env python3
"""The horizontally polarized (E_x, "TE") silicon branch in the 3D cross-section of
chain/taper_eme.py, solved locally with Tidy3D's mode solver: the isolated TE silicon
mode against width, and the coupled pair around its crossing with the glass TE mode.
Writes chain/eme/te_branch.json for the design scripts."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import numpy as np
src = open(pathlib.Path(__file__).parent / "eme_crosscheck.py").read()
ns = {}; exec(src.split('print("glass guide alone')[0], ns); solve = ns["solve"]
out = {"glass_te": None, "isolated_te": [], "coupled_te": []}
g = solve(0.0, True, 2); out["glass_te"] = max(x[0] for x in g if x[3] > 0.5)
print(f"glass TE mode: n_eff {out['glass_te']:.5f}")
for w in (0.195, 0.200, 0.205, 0.210, 0.220, 0.240, 0.260, 0.300, 0.350, 0.400, 0.450, 0.500):
    r = solve(w, False, 3); cand = [x for x in r if x[3] > 0.5 and x[0] > 1.445]
    if cand:
        ne, ke, area, te = max(cand); out["isolated_te"].append([w, ne, area]); print(f"   isolated TE  w = {w*1e3:.0f} nm : n_eff {ne:.5f}  area {area:6.2f}")
    else: print(f"   isolated TE  w = {w*1e3:.0f} nm : not bound")
for w in (0.192, 0.196, 0.199, 0.201, 0.203, 0.206, 0.210, 0.215):
    r = solve(w, True, 5); te = [[x[0], x[2]] for x in r if x[3] > 0.5 and x[0] > 1.4995]
    out["coupled_te"].append([w, te]); print(f"   coupled TE   w = {w*1e3:.0f} nm : " + "  |  ".join(f"n {n:.5f} area {a:5.1f}" for n, a in te))
p = pathlib.Path(__file__).parent / "eme" / "te_branch.json"; p.write_text(json.dumps(out, indent=1)); print("wrote", p)

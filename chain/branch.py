"""Which silicon-mode branch the stage-3 design scripts use.

  BRANCH=ey2d   the original 2D femwell sweep of the fundamental silicon mode, which
                below 220 nm is the vertically polarized (E_y) mode; glass n_eff 1.50522,
                gap 2.8e-3, crossing 156 nm. Kept for the record (stage 3 as first written).
  BRANCH=te3d   the horizontally polarized (E_x, TE) branch solved in the 3D cross-section
                of taper_eme.py with Tidy3D's mode solver (te_branch_fine.py): the branch
                the launched glass TE mode actually couples to. Default.

Every script imports BR and reads: w_pts/n_pts (nm, index) of the isolated silicon mode,
n_glass, G (supermode gap at the crossing), tip and end widths (nm), coupled pairs.
"""
import json, os, pathlib
import numpy as np

HERE = pathlib.Path(__file__).parent
NAME = os.environ.get("BRANCH", "te3d")

class Branch:
    def __init__(self, name, label, n_glass, G, tip, end, isolated, coupled):
        self.name, self.label, self.n_glass, self.G, self.tip, self.end = name, label, n_glass, G, tip, end
        iso = np.array(sorted(isolated))                     # [w_um, n_eff]
        w, n = iso[:, 0] * 1e3, iso[:, 1]
        if tip < w[0]:                                       # extend below the narrowest bound point, linearly
            slope = (n[1] - n[0]) / (w[1] - w[0]); w = np.concatenate([[tip], w]); n = np.concatenate([[n[0] + slope * (tip - w[1])], n])
        self.w_pts, self.n_pts = w, n
        self.coupled = np.array(coupled) if coupled else None  # [w_um, upper, lower]
    def delta(self, w_nm):
        return np.interp(w_nm, self.w_pts, self.n_pts) - self.n_glass
    @property
    def w_cross(self):
        return float(np.interp(0.0, self.n_pts - self.n_glass, self.w_pts))

def load(name=NAME):
    if name == "ey2d":
        d = json.loads((HERE / "eme" / "ey_branch_2d.json").read_text())
        return Branch(name, d["label"], d["n_glass"], d["G"], d["tip"], d["end"], d["isolated"], d["coupled"])
    d = json.loads((HERE / "eme" / "te_branch_fine.json").read_text())
    # keep only points bound against the adhesive; below 200 nm the "TE mode" the solver finds is substrate continuum
    pairs = [(w, max(m[0] for m in modes), min(m[0] for m in modes)) for w, modes in d["coupled_te"] if len(modes) >= 2]
    G = min(u - l for _, u, l in pairs)
    return Branch(name, "E_x (TE) branch, 3D cross-section, Tidy3D mode solver, 5 nm mesh", d["glass_te"], G, 180.0, 500.0,
                  [[w, n] for w, n, a in d["isolated_te"] if n > 1.4995], [[w, u, l] for w, u, l in pairs])

BR = load()

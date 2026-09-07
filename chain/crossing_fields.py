#!/usr/bin/env python3
"""The field along the crossing job, transcribed from the notebook's field cell (chain/eme/crossing_runs.json
holds the matrices). Light launched in the glass mode, linear taper 180 -> 240 nm at 0.16 nm/um.
Run 1: mode solver with absorbing layers. Run 2: without. Output: chain/img/crossing-fields.png"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import figstyle
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import numpy as np
# columns: z (um), |E|^2 total relative to the run's maximum, share in the IOX guide, share in the silicon
run1 = np.array([[15.3,.212,.56,.107],[30.8,.232,.50,.133],[46.1,.274,.39,.171],[61.5,.338,.29,.209],[77.0,.423,.21,.245],[92.3,.516,.15,.269],
 [107.8,.645,.10,.299],[123.1,.768,.07,.315],[138.5,.888,.04,.328],[154.0,.976,.03,.337],[169.3,.998,.03,.340],[184.8,.967,.03,.340],
 [200.1,.897,.04,.337],[215.5,.811,.06,.330],[231.0,.027,.44,.176],[246.3,.026,.46,.171],[261.8,.025,.48,.169],[277.1,.024,.49,.167],
 [292.5,.024,.51,.164],[308.0,.022,.56,.147],[323.3,.021,.59,.133],[338.8,.020,.63,.117],[354.1,.019,.68,.097],[369.5,.017,.75,.062]])
run2 = np.array([[15.3,.126,.56,.106],[30.8,.138,.50,.131],[46.1,.166,.39,.172],[61.5,.207,.29,.211],[77.0,.258,.21,.245],[92.3,.312,.15,.269],
 [107.8,.388,.10,.298],[123.1,.464,.07,.316],[138.5,.545,.04,.329],[154.0,.601,.03,.338],[169.3,.607,.03,.340],[184.8,.581,.03,.340],
 [200.1,.534,.05,.335],[215.5,.488,.06,.329],[231.0,.447,.08,.325],[246.3,.423,.10,.321],[261.8,.424,.09,.325],[277.1,.476,.07,.338],
 [292.5,.556,.04,.354],[308.0,.652,.02,.370],[323.3,.691,.01,.378],[338.8,.674,.02,.381],[354.1,.630,.03,.381],[369.5,.651,.03,.402]])
w = lambda z: 180 + 0.16 * z
Z_CROSS = (203.1 - 180) / 0.16
fig, (a, b) = plt.subplots(2, 1, figsize=figstyle.size(7.6, 8.6), sharex=True, gridspec_kw=dict(hspace=0.28))
for run, col, ls, lab in ((run1, "#c0392b", "--", "run 1: absorbing layers in the mode solver"), (run2, "#1b6ca8", "-", "run 2: none, mirrors instead")):
    ref = run[np.argmin(abs(run[:, 0] - 169.3)), 1]
    a.plot(run[:, 0], run[:, 1] / ref, ls=ls, lw=2.2, color=col, marker="o", ms=4, label=lab)
a.axvline(Z_CROSS, color="#8a5a1b", lw=1, ls=":"); a.text(Z_CROSS + 4, 0.06, "crossing, 203 nm", color="#8a5a1b")
a.annotate("run 1 drops 30x between\ntwo samples at 216 nm", xy=(231, 0.03), xytext=(250, 0.55), color="#c0392b", arrowprops=dict(arrowstyle="->", color="#c0392b", lw=0.9))
a.set_ylabel("field energy |E|², relative to z = 169 µm"); a.set_ylim(0, 1.25); a.grid(alpha=.22); a.legend(loc="upper left", fontsize=10)
a.set_title("Light launched in the glass mode, along the crossing region")
b.plot(run2[:, 0], run2[:, 2], "-", lw=2.2, color="#c8698a", marker="o", ms=4, label="share in the ion-exchanged guide")
b.plot(run2[:, 0], run2[:, 3], "-", lw=2.2, color="#1b6ca8", marker="o", ms=4, label="share in the silicon")
b.axvline(Z_CROSS, color="#8a5a1b", lw=1, ls=":")
b.set_xlabel("position along the taper, z  (µm)"); b.set_ylabel("share of |E|² (run 2)"); b.set_ylim(0, 0.65); b.grid(alpha=.22); b.legend(loc="upper right", fontsize=10)
b.set_title("Where the field sits, run 2: out of the glass and into the silicon by 207 nm")
top = a.secondary_xaxis("top", functions=(w, lambda ww: (ww - 180) / 0.16)); top.set_xlabel("silicon width  (nm)")
a.set_xlim(0, 380)
out = pathlib.Path(__file__).parent / "img" / "crossing-fields.png"; fig.savefig(out, bbox_inches="tight", facecolor="white"); print("wrote", out)

#!/usr/bin/env python3
"""Stage 4: the thermo-optic MZI of die channels 16 -> 17, 18 as a circuit.

The cell (chip.switch_cell) is a 1x2 multimode-interference splitter and a 2x2 combiner joined by two
arms; the upper arm carries a heater, the lower arm is 100 um longer, and S-bends spread the two outputs.
The netlist is extracted from the layout; models: straight/bend as in circuit_ringbank.py, the S-bends
as straights of their length, the heater arm as a straight with an extra phase, the MMIs as SAX's ideal
1x2 and 2x2. Outputs: chain/img/switch-phase.png (both outputs against heater phase at 1550 nm) and
chain/img/switch-spectrum.png (both outputs against wavelength at zero heater).
Run:  python chain/circuit_switch.py   (from the repo root, with the repo's venv)
"""
import functools, pathlib, sys
import numpy as np, jax.numpy as jnp, sax
import gdsfactory as gf
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent)); import figstyle
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import circuit_ringbank as cb
import chip

gf.gpdk.PDK.activate()
sw = chip.switch_cell()
ports = {p.name: (round(p.dcenter[0], 1), round(p.dcenter[1], 1)) for p in sw.ports if p.port_type == "optical"}
print("optical ports of the cell:", ports)
rec = sw.get_netlist(recursive=True)
net = cb.to_sax(rec)
for name in net:                                   # drop the heater's electrical ports: no optical role
    net[name]["ports"] = {k: v for k, v in net[name]["ports"].items() if k.startswith("o")}
net = {"switch_cell": net["switch_cell"], **{k: v for k, v in net.items() if k != "switch_cell"}}

PHASE = {"value": 0.0}                             # heater phase, radians, set per sweep point
def straight_heater_metal_undercut(wl=1.55, length=200.0, **_):
    s = cb.straight(wl=wl, length=length)
    return {k: v * jnp.exp(1j * PHASE["value"]) for k, v in s.items()}
@functools.lru_cache(None)
def _bend_s_len(size):
    return float(gf.components.bend_s(size=size).info["length"])
def bend_s(wl=1.55, size=(30.0, 4.375), **_):
    return cb.straight(wl=wl, length=_bend_s_len(tuple(float(v) for v in size)))
def mmi1x2(wl=1.55, **_):
    """SAX's ideal 1x2 (in0 -> out0, out1, equal and in phase) on gdsfactory's o1 (west), o2, o3 (east)."""
    s = sax.sdict(sax.models.mmi1x2(wl=wl)); m = {"in0": "o1", "out0": "o2", "out1": "o3"}
    return {(m[a], m[b]): v for (a, b), v in s.items()}
def mmi2x2(wl=1.55, **_):
    """SAX's ideal 2x2 on gdsfactory's o1, o2 (one side) and o4, o3 (other side)."""
    s = sax.sdict(sax.models.mmi2x2(wl=wl)); m = {"in0": "o1", "in1": "o2", "out0": "o4", "out1": "o3"}
    return {(m[a], m[b]): v for (a, b), v in s.items()}
models = {"straight": cb.straight, "bend_euler": cb.bend_euler, "bend_s": bend_s, "mmi1x2": mmi1x2,
          "mmi2x2": mmi2x2, "straight_heater_metal_undercut": straight_heater_metal_undercut}
circuit, info = sax.circuit(netlist=net, models=models)

def outputs(wl, phase):
    PHASE["value"] = phase
    S = sax.sdict(circuit(wl=wl))
    return np.abs(np.asarray(S[("o1", "o3")])) ** 2, np.abs(np.asarray(S[("o1", "o2")])) ** 2
lab3, lab2 = "o3, upper output (to ch17)", "o2, lower output (to ch18)"

# --- heater phase sweep at 1550 nm
ph = np.linspace(-np.pi, np.pi, 361)
P3 = np.array([outputs(1.55, p)[0] for p in ph]).ravel(); P2 = np.array([outputs(1.55, p)[1] for p in ph]).ravel()
i0 = int(np.argmin(abs(ph)))
print(f"at 1550 nm with the heater off: o3 {P3[i0]:.3f}, o2 {P2[i0]:.3f}, sum {P3[i0]+P2[i0]:.3f}")
for P, n in ((P3, "o3"), (P2, "o2")):
    k = int(np.argmax(P)); print(f"{n} is fullest at a heater phase of {ph[k]/np.pi:+.2f} pi: o3 {P3[k]:.3f}, o2 {P2[k]:.3f}")
fig, ax = plt.subplots(figsize=figstyle.size(7.6, 4.4))
ax.plot(ph / np.pi, P3, lw=2.2, color="#1b6ca8", label=lab3); ax.plot(ph / np.pi, P2, lw=2.2, color="#c0392b", label=lab2)
ax.set_xlabel("heater phase  (units of π)"); ax.set_ylabel("fraction of the input power"); ax.set_ylim(0, 1.05); ax.grid(alpha=.22); ax.legend(loc="upper right", fontsize=9)
ax.set_title("The MZI cell: input at o1, both outputs against the heater phase, 1550 nm")
fig.savefig(HERE / "img" / "switch-phase.png", bbox_inches="tight", facecolor="white"); print("wrote chain/img/switch-phase.png")

# --- wavelength spectrum with the heater off: the 100 um arm imbalance
wl = np.linspace(1.50, 1.60, 4001)
S3, S2 = outputs(wl, 0.0)
from scipy.signal import find_peaks
pk, _ = find_peaks(S2, prominence=0.3); fsr = np.diff(wl[pk] * 1e3)
print(f"with the heater off, o2 peaks: {len(pk)} in 100 nm; spacing {fsr.min():.2f}..{fsr.max():.2f} nm  "
      f"(lambda^2/(n_g dL) with dL = {chip.MZI_DL:.0f} um: {1.55**2/(cb.NG*chip.MZI_DL)*1e3:.2f} nm)")
ratio = S3 / (S3 + S2)
print(f"o3/(o3+o2) swings {ratio.min():.4f}..{ratio.max():.4f}")
fig, ax = plt.subplots(figsize=figstyle.size(7.6, 4.4))
ax.plot(wl * 1e3, S3, lw=1.6, color="#1b6ca8", label=lab3); ax.plot(wl * 1e3, S2, lw=1.6, color="#c0392b", label=lab2)
ax.set_xlabel("wavelength  (nm)"); ax.set_ylabel("fraction of the input power"); ax.set_ylim(0, 1.05); ax.grid(alpha=.22)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=9, frameon=False)
ax.set_title(f"The same cell against wavelength, heater off: the {chip.MZI_DL:.0f} µm arm imbalance")
fig.savefig(HERE / "img" / "switch-spectrum.png", bbox_inches="tight", facecolor="white"); print("wrote chain/img/switch-spectrum.png")

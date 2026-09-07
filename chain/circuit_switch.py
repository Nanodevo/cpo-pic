#!/usr/bin/env python3
"""Stage 4: the 2x2 thermo-optic switch cell of die channels 9 -> 10 as a circuit.

The cell (gdsfactory mzi2x2_2x2_phase_shifter) is two 2x2 multimode-interference couplers joined by
two arms; the upper arm carries a heater, the lower arm is 10 um longer. The netlist is extracted from
the layout; models: straight/bend as in circuit_ringbank.py, the heater arm as a straight with an extra
phase, the MMI as SAX's ideal 2x2. Outputs: chain/img/switch-phase.png (both outputs against heater
phase at 1550 nm) and chain/img/switch-spectrum.png (both outputs against wavelength at zero heater).
Run:  python chain/circuit_switch.py
"""
import pathlib, sys
import numpy as np, jax.numpy as jnp, sax
import gdsfactory as gf
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import figstyle
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import circuit_ringbank as cb

gf.gpdk.PDK.activate()
sw = gf.components.mzi2x2_2x2_phase_shifter()
ports = {p.name: (round(p.dcenter[0], 1), round(p.dcenter[1], 1)) for p in sw.ports if p.name.startswith("o")}
print("optical ports of the cell:", ports)
rec = sw.get_netlist(recursive=True); top_key = max(rec, key=lambda k: len(rec[k]["instances"]))
net = cb.to_sax(rec)
for name in net:                                   # drop the heater's electrical ports: no optical role
    net[name]["ports"] = {k: v for k, v in net[name]["ports"].items() if k.startswith("o")}
net = {top_key: net[top_key], **{k: v for k, v in net.items() if k != top_key}}

PHASE = {"value": 0.0}                             # heater phase, radians, set per sweep point
def straight_heater_metal_undercut(wl=1.55, length=200.0, **_):
    s = cb.straight(wl=wl, length=length)
    return {k: v * jnp.exp(1j * PHASE["value"]) for k, v in s.items()}
def mmi2x2(wl=1.55, **_):
    """SAX's ideal 2x2 (ports in0, in1, out0, out1) renamed to gdsfactory's o1, o2 (west, lower/upper) and
    o4, o3 (east, lower/upper); in0 -> out0 is the same-side path, so out0 is o4."""
    s = sax.sdict(sax.models.mmi2x2(wl=wl)); m = {"in0": "o1", "in1": "o2", "out0": "o4", "out1": "o3"}
    return {(m[a], m[b]): v for (a, b), v in s.items()}
models = {"straight": cb.straight, "bend_euler": cb.bend_euler, "mmi2x2": mmi2x2, "straight_heater_metal_undercut": straight_heater_metal_undercut}
circuit, info = sax.circuit(netlist=net, models=models)

def outputs(wl, phase):
    PHASE["value"] = phase
    S = sax.sdict(circuit(wl=wl))
    return np.abs(np.asarray(S[("o1", "o3")])) ** 2, np.abs(np.asarray(S[("o1", "o4")])) ** 2
same_side = "o4" if abs(ports["o4"][1] - ports["o1"][1]) < abs(ports["o3"][1] - ports["o1"][1]) else "o3"
lab3 = "o3 (bar: same side as the input)" if same_side == "o3" else "o3 (cross: opposite side)"
lab4 = "o4 (bar: same side as the input)" if same_side == "o4" else "o4 (cross: opposite side)"

# --- heater phase sweep at 1550 nm
ph = np.linspace(0, 2 * np.pi, 361)
P3 = np.array([outputs(1.55, p)[0] for p in ph]).ravel(); P4 = np.array([outputs(1.55, p)[1] for p in ph]).ravel()
i_max4 = int(np.argmax(P4)); i_max3 = int(np.argmax(P3))
print(f"at 1550 nm with the heater off: o3 {P3[0]:.3f}, o4 {P4[0]:.3f}")
print(f"o4 is fullest at a heater phase of {ph[i_max4]:.2f} rad ({ph[i_max4]/np.pi:.2f} pi): o3 {P3[i_max4]:.3f}, o4 {P4[i_max4]:.3f}")
print(f"o3 is fullest at a heater phase of {ph[i_max3]:.2f} rad ({ph[i_max3]/np.pi:.2f} pi): o3 {P3[i_max3]:.3f}, o4 {P4[i_max3]:.3f}")
fig, ax = plt.subplots(figsize=figstyle.size(7.6, 4.4))
ax.plot(ph / np.pi, P3, lw=2.2, color="#1b6ca8", label=lab3); ax.plot(ph / np.pi, P4, lw=2.2, color="#c0392b", label=lab4)
ax.set_xlabel("heater phase  (units of π)"); ax.set_ylabel("fraction of the input power"); ax.set_ylim(0, 1.05); ax.grid(alpha=.22); ax.legend(loc="center right")
ax.set_title("The switch cell: input at o1, both outputs against the heater phase, 1550 nm")
fig.savefig(pathlib.Path(__file__).parent / "img" / "switch-phase.png", bbox_inches="tight", facecolor="white"); print("wrote chain/img/switch-phase.png")

# --- wavelength spectrum with the heater off: the 10 um arm imbalance
wl = np.linspace(1.50, 1.60, 2001)
S3, S4 = outputs(wl, 0.0)
from scipy.signal import find_peaks
pk, _ = find_peaks(S4, prominence=0.3); fsr = np.diff(wl[pk] * 1e3)
print(f"with the heater off, o4 peaks at {np.round(wl[pk]*1e3, 1)} nm; spacing {np.round(fsr, 1)} nm  (lambda^2/(n_g dL) with dL = 10 um: {1.55**2/(cb.NG*10)*1e3:.1f} nm)")
fig, ax = plt.subplots(figsize=figstyle.size(7.6, 4.4))
ax.plot(wl * 1e3, S3, lw=2.2, color="#1b6ca8", label=lab3); ax.plot(wl * 1e3, S4, lw=2.2, color="#c0392b", label=lab4)
ax.set_xlabel("wavelength  (nm)"); ax.set_ylabel("fraction of the input power"); ax.set_ylim(0, 1.05); ax.grid(alpha=.22); ax.legend(loc="center right")
ax.set_title("The same cell against wavelength, heater off: the 10 µm arm imbalance")
fig.savefig(pathlib.Path(__file__).parent / "img" / "switch-spectrum.png", bbox_inches="tight", facecolor="white"); print("wrote chain/img/switch-spectrum.png")

#!/usr/bin/env python3
"""Stage 4, rung 1: the ring bank of die channels 7 -> 8 as a circuit of scattering matrices.

Layout -> netlist -> circuit. The channel is rebuilt here exactly as chip.py places it
(four all-pass racetrack rings on one bus, radii staggered by 50 nm), its netlist is
extracted from the layout, and each leaf component gets a compact model:
  straight / bend_euler : phase from n_eff(lambda) with first-order dispersion (group index), loss per cm
  coupler_ring          : a directional coupler; its power coupling comes from the two-strip
                          supermode split of ring_params.py integrated along the racetrack's
                          straight section and the approach of its bends
  edge_coupler          : a 2-port with a fixed loss (placeholder until the EME S-matrix is in)
The circuit solver (SAX) multiplies the matrices along the connections and returns the
transmission spectrum. Output: chain/img/ringbank-spectrum.png and printed numbers.

Run:  python chain/circuit_ringbank.py
"""
import json, pathlib, sys
import numpy as np, jax.numpy as jnp, sax
import gdsfactory as gf
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import figstyle
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent
P = json.loads((HERE / "eme" / "ring_params.json").read_text())
NE, NG, KAPPA, N_OX = P["n_eff"], P["n_g"], P["kappa_per_um"], 1.444
LOSS_DB_CM = 2.5                         # propagation loss of an etched strip guide, a typical value, not measured
TAPER_LOSS_DB = 1.0                      # placeholder for the glass-to-silicon hand-off, per taper
K0 = 2 * np.pi / 1.55
GAMMA = K0 * np.sqrt(NE ** 2 - N_OX ** 2)     # transverse decay rate of the mode outside the core, 1/um
gf.gpdk.PDK.activate()
RADIUS, GAP, LX, LY = 10.0, 0.2, 4.0, 0.6

# ---- the channel as a layout, then its netlist -------------------------------------------
def channel() -> gf.Component:
    c = gf.Component("ringbank_channel")
    t_in = c << gf.components.straight(length=400.0)           # bus from the taper to the first ring
    prev = t_in.ports["o2"]
    for k in range(4):
        r = c << gf.components.ring_single(radius=RADIUS + 0.05 * k, gap=GAP, length_x=LX, length_y=LY)
        r.connect("o1", prev)
        if k < 3:
            s = c << gf.components.straight(length=110.0); s.connect("o1", r.ports["o2"]); prev = s.ports["o2"]
        else:
            prev = r.ports["o2"]
    back = c << gf.components.straight(length=1300.0)          # the loopback route, as a straight of its length
    back.connect("o1", prev)
    c.add_port("in", port=t_in.ports["o1"]); c.add_port("out", port=back.ports["o2"])
    return c

def to_sax(recursive):
    """gdsfactory recursive netlist -> the dict-of-netlists SAX takes, with lengths passed as settings."""
    out = {}
    for name, n in recursive.items():
        inst = {}
        for iname, i in n["instances"].items():
            s = dict(i.get("settings", {})); info = i.get("info", {}) or {}
            if "length" in info: s["length"] = float(info["length"])
            inst[iname] = {"component": i["component"], "settings": s}
        conns = {}
        for net in n.get("nets", []): conns[net["p1"]] = net["p2"]
        for a, b in (n.get("connections") or {}).items(): conns[a] = b
        out[name] = {"instances": inst, "connections": conns, "ports": dict(n["ports"])}
    return out

# ---- compact models ------------------------------------------------------------------------
def neff_of(wl): return NE - (wl - 1.55) * (NG - NE) / 1.55       # first-order dispersion: n_eff(lambda)
def straight(wl=1.55, length=10.0, **_):
    wl = jnp.asarray(wl); phase = 2 * jnp.pi * neff_of(wl) * length / wl
    amp = 10 ** (-LOSS_DB_CM * length * 1e-4 / 20)
    return sax.reciprocal({("o1", "o2"): amp * jnp.exp(1j * phase)})
def bend_euler(wl=1.55, length=15.7, **_):
    return straight(wl=wl, length=length)
BEND_LEN = float(gf.components.bend_euler(radius=RADIUS).info["length"])   # one 90-degree Euler bend of this radius
def coupler_ring(wl=1.55, gap=GAP, radius=RADIUS, length_x=LX, **_):
    """Bus ports o1 (left), o4 (right); ring ports o2 (left), o3 (right). Coupling accumulates along the
    straight section and over the approach of the two bends, whose effective length is sqrt(2 pi R / gamma)."""
    wl = jnp.asarray(wl)
    l_eff = length_x + np.sqrt(2 * np.pi * radius / GAMMA)
    theta = KAPPA * l_eff
    t, k = jnp.cos(theta), 1j * jnp.sin(theta)
    beta = 2 * jnp.pi * neff_of(wl) / wl
    ph_bus = jnp.exp(1j * beta * length_x)                        # the bus straight under the coupler
    ph_ring = jnp.exp(1j * beta * (length_x + 2 * BEND_LEN))       # the ring path through the coupler: straight + two bends
    ph_x = jnp.exp(1j * beta * (length_x + BEND_LEN))              # cross terms: half of each
    amp_ring = 10 ** (-LOSS_DB_CM * (length_x + 2 * BEND_LEN) * 1e-4 / 20)
    return sax.reciprocal({("o1", "o4"): t * ph_bus, ("o2", "o3"): t * ph_ring * amp_ring,
                           ("o1", "o3"): k * ph_x, ("o2", "o4"): k * ph_x})
def edge_coupler(wl=1.55, **_):
    return sax.reciprocal({("o1", "o2"): jnp.full_like(jnp.asarray(wl), 10 ** (-TAPER_LOSS_DB / 20)) + 0j})

def main():
    # ---- solve ----------------------------------------------------------------------------------
    c = channel()
    net = to_sax(c.get_netlist(recursive=True))
    models = {"straight": straight, "bend_euler": bend_euler, "coupler_ring": coupler_ring}
    top = c.name
    net = {top: net[top], **{k: v for k, v in net.items() if k != top}}   # top-level netlist first
    circuit, info = sax.circuit(netlist=net, models=models)
    wl = np.linspace(1.540, 1.560, 4001)
    S = sax.sdict(circuit(wl=wl))
    T = np.abs(np.asarray(S[("in", "out")])) ** 2 * 10 ** (-2 * TAPER_LOSS_DB / 10)
    TdB = 10 * np.log10(T)

    # what the ring is, from the layout itself
    ring_net = c.get_netlist(recursive=True)
    ring_name = next(k for k in ring_net if k.startswith("ring_single"))
    L_ring = 2 * LX + 2 * LY + 4 * BEND_LEN
    theta = KAPPA * (LX + np.sqrt(2 * np.pi * RADIUS / GAMMA))
    print(f"ring: radius {RADIUS} um, racetrack straights {LX} and {LY} um, Euler 90-degree bend length {BEND_LEN:.2f} um")
    print(f"      round-trip length L = {L_ring:.2f} um;  n_eff {NE:.4f}, group index {NG:.3f}")
    print(f"      coupler: theta = {theta:.3f} rad -> power coupling {np.sin(theta)**2:.1%} per pass")
    print(f"      round-trip loss at {LOSS_DB_CM} dB/cm: {LOSS_DB_CM * L_ring * 1e-4:.4f} dB")
    # find the notches
    from scipy.signal import find_peaks
    pk, _ = find_peaks(-TdB, prominence=1.0)
    print(f"resonance notches found between 1540 and 1560 nm: {len(pk)}")
    for i in pk[:12]: print(f"   {wl[i]*1e3:8.3f} nm   depth {TdB[i]:6.1f} dB")

    fig, ax = plt.subplots(figsize=figstyle.size(7.6, 4.4))
    ax.plot(wl * 1e3, TdB, lw=1.4, color="#1b6ca8")
    ax.set_xlabel("wavelength  (nm)"); ax.set_ylabel("transmission ch 7 → ch 8  (dB)")
    ax.set_title("Ring bank of the die, circuit model: four rings, radii 10.00 to 10.15 µm")
    ax.grid(alpha=.22); ax.set_xlim(1540, 1560)
    out = HERE / "img" / "ringbank-spectrum.png"; fig.savefig(out, bbox_inches="tight", facecolor="white"); print("wrote", out)


if __name__ == "__main__":
    main()

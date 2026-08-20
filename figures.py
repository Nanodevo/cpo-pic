#!/usr/bin/env python3
"""Render per-cell zoom figures so the die is readable by humans.

Outputs to docs/: each cell at its own natural scale.
"""

import pathlib

import matplotlib.pyplot as plt

import gdsfactory as gf

import chip  # noqa: F401  (activates PDK, defines cells)
from chip import (RING_GAP, RING_RADIUS, TAPER_LEN, TIP_W, WG_W,
                  edge_coupler, fiducial, spiral_of_length)

DOCS = pathlib.Path(__file__).parent / "docs"
DOCS.mkdir(exist_ok=True)


def save(component: gf.Component, name: str, title: str) -> None:
    plt.figure(figsize=(9, 5))
    component.plot()
    plt.title(title, fontsize=11)
    plt.savefig(DOCS / name, dpi=200, bbox_inches="tight")
    plt.close("all")
    print("wrote", DOCS / name)


# 1) one ring of the WDM bank
save(gf.components.ring_single(radius=RING_RADIUS, gap=RING_GAP),
     "cell_ring.png",
     "One WDM ring: bus below, 10 um ring above, 200 nm gap")

# 2) the 4-ring WDM bank as wired on ch7-8
bank = gf.Component()
prev = None
for k in range(4):
    r = bank << gf.components.ring_single(radius=RING_RADIUS + 0.05 * k,
                                          gap=RING_GAP)
    r.move((140 * k, 0))
    if prev is not None:
        gf.routing.route_single(bank, prev, r.ports["o1"],
                                cross_section="strip")
    prev = r.ports["o2"]
save(bank, "cell_wdm_bank.png",
     "WDM bank: four rings in series, radii 10.00/10.05/10.10/10.15 um")

# 3) the 2x2 thermo-optic switch
save(gf.components.mzi2x2_2x2_phase_shifter(), "cell_switch.png",
     "2x2 MZI switch: two 2x2 splitters, heater metal on the upper arm")

# 4) taper tip region (the full taper is 2 mm x 0.5 um - show the tip)
tip = gf.components.taper(length=30.0, width1=TIP_W, width2=0.32)
save(tip, "cell_taper_tip.png",
     f"Coupler tip, first 30 um of {TAPER_LEN/1000:.0f} mm: "
     f"{TIP_W*1000:.0f} nm tip widening toward {WG_W*1000:.0f} nm")

# 5) fiducial
save(fiducial(), "cell_fiducial.png",
     "Corner fiducial: cross + Vernier combs (10.0 vs 10.5 um pitch)")

# 6) spiral
save(spiral_of_length(5000.0, 8), "cell_spiral.png",
     "0.5 cm cutback spiral (path length converged to 5000 um)")

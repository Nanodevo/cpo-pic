#!/usr/bin/env python3
"""Render per-cell zoom figures so the die is readable by humans.

Outputs to docs/: each cell at its own natural scale.
"""

import pathlib

import matplotlib.pyplot as plt

import gdsfactory as gf

import chip  # noqa: F401  (activates PDK, defines cells)
from chip import (MZI_DL, RING_GAP, RING_RADIUS, RING_STEP, TAPER_LEN, TIP_W,
                  WG_W, fiducial, spiral_of_length, switch_cell)

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
     f"One ring of the bank: bus below, {RING_RADIUS:.0f} um racetrack above, "
     f"{RING_GAP*1e3:.0f} nm gap")

# 2) the 4-ring WDM bank as wired on ch7-8
bank = gf.Component()
prev = None
for k in range(4):
    r = bank << gf.components.ring_single(radius=RING_RADIUS + RING_STEP * k,
                                          gap=RING_GAP)
    r.move((140 * k, 0))
    if prev is not None:
        gf.routing.route_single(bank, prev, r.ports["o1"],
                                cross_section="strip")
    prev = r.ports["o2"]
save(bank, "cell_wdm_bank.png",
     "Ring bank: four rings in series, radii "
     + "/".join(f"{RING_RADIUS + RING_STEP * k:.3f}" for k in range(4)) + " um")

# 3) the 2x2 thermo-optic switch
save(switch_cell(), "cell_switch.png",
     f"2x2 MZI cell: two 2x2 splitters, heater metal on the upper arm, "
     f"lower arm {MZI_DL:.0f} um longer")

# 4) taper tip region, drawn true to the layout: the first 30 um of the real
#    2 mm linear taper (the full taper widens to the routing width only at 2 mm)
TIP_SHOW = 30.0
w_end = TIP_W + (WG_W - TIP_W) * TIP_SHOW / TAPER_LEN
tip = gf.components.taper(length=TIP_SHOW, width1=TIP_W, width2=w_end)
save(tip, "cell_taper_tip.png",
     f"Coupler tip, first {TIP_SHOW:.0f} um of the {TAPER_LEN/1000:.0f} mm taper: "
     f"{TIP_W*1000:.0f} nm widening to {w_end*1000:.0f} nm "
     f"(it reaches {WG_W*1000:.0f} nm only at {TAPER_LEN/1000:.0f} mm)")

# 5) fiducial
save(fiducial(), "cell_fiducial.png",
     "Corner fiducial: cross + Vernier combs (10.0 vs 10.5 um pitch)")

# 6) spiral
save(spiral_of_length(5000.0, 8), "cell_spiral.png",
     "0.5 cm cutback spiral (path length converged to 5000 um)")

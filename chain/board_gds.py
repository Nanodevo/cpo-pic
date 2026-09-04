#!/usr/bin/env python3
"""The whole board: the cpo-pic test die with the glass bridge mated to its west edge,
as one GDS for KLayout (plan view + 2.5D view).

Orientation: the die lies photonics-up; the bridge's thin glass tongue is glued onto
the circuit face over the taper region, its ion-exchanged (IOX) guides facing down
onto the silicon tapers across the adhesive. (The EME cross-section in taper_eme.py
is this same stack drawn glass-down; the physics does not care which way is up.)

Die layers (gdsfactory generic PDK): 1/0 silicon, 47/0 heater, 44/0 via1, 45/0 metal2,
43/0 via2, 49/0 metal3, 99/0 floorplan frame.
Bridge layers (new): 201/0 IOX guides, 202/0 adhesive, 203/0 glass tongue,
204/0 ferrule body, 205/0 fibers.

Run:  python chain/board_gds.py  ->  chain/gds/board.gds
"""
import pathlib
import gdstk
import numpy as np

HERE = pathlib.Path(__file__).parent
die_lib = gdstk.read_gds(str(HERE.parent / "build" / "cpo_pic.gds"))
die = next(c for c in die_lib.cells if c.name == "cpo_pic")

# --- read the taper tips off the die itself (do not trust chip.py's constants blindly)
tips = [p for p in die.get_polygons(layer=1, datatype=0) if p.bounding_box()[0][0] < 15.0]
ys = sorted((p.bounding_box()[0][1] + p.bounding_box()[1][1]) / 2 for p in tips)
x_tip = min(p.bounding_box()[0][0] for p in tips); x_end = max(p.bounding_box()[1][0] for p in tips)
assert len(ys) == 16, f"expected 16 taper tips on the west edge, found {len(ys)}"
pitch = np.diff(ys); print(f"16 tapers found: x {x_tip:.1f}..{x_end:.1f} um, y from {ys[0]:.1f} to {ys[-1]:.1f} um, pitch {pitch.min():.1f}..{pitch.max():.1f} um")

# --- the bridge, in the die's coordinates (x along the light, west edge at x = 0)
IOX_W = 6.0          # um, guide width (taper_eme.py)
TONGUE_X = (-400.0, x_end + 100.0)             # glass tongue: overhangs the die edge, covers the tapers
TONGUE_Y = (ys[0] - 250.0, ys[-1] + 250.0)     # one pitch beyond the outer channels
FERRULE_X = (-1400.0, -400.0)                  # thick block holding the fibers, butt-coupled to the tongue
FIBER_X = (-2400.0, -400.0); FIBER_D = 125.0   # cladding diameter, drawn as a square strip

lib = gdstk.Library(unit=1e-6, precision=1e-9)
lib.add(die, *die.dependencies(True))
bridge = lib.new_cell("glass_bridge")
for y in ys:
    bridge.add(gdstk.rectangle((TONGUE_X[0], y - IOX_W / 2), (TONGUE_X[1], y + IOX_W / 2), layer=201))
    bridge.add(gdstk.rectangle((FIBER_X[0], y - FIBER_D / 2), (FIBER_X[1], y + FIBER_D / 2), layer=205))
bridge.add(gdstk.rectangle((0.0, TONGUE_Y[0]), (TONGUE_X[1], TONGUE_Y[1]), layer=202))          # adhesive: only where tongue meets die
bridge.add(gdstk.rectangle((TONGUE_X[0], TONGUE_Y[0]), (TONGUE_X[1], TONGUE_Y[1]), layer=203))  # glass tongue
bridge.add(gdstk.rectangle((FERRULE_X[0], TONGUE_Y[0]), (FERRULE_X[1], TONGUE_Y[1]), layer=204)) # ferrule body

board = lib.new_cell("board")
board.add(gdstk.Reference(die)); board.add(gdstk.Reference(bridge))
out = HERE / "gds" / "board.gds"; lib.write_gds(str(out))
(x0, y0), (x1, y1) = board.bounding_box()
print(f"wrote {out}: board {x1-x0:.0f} x {y1-y0:.0f} um, cells {len(lib.cells)}")

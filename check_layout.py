#!/usr/bin/env python3
"""Layout sanity check for the die: overlapping shapes and too-close shapes on the
waveguide layer. Run after every build; exits non-zero if anything is found.

Two rules, both on layer 1/0 (silicon):
  OVERLAP   two separate shapes share area (a waveguide drawn across another one)
  MIN GAP   two separate shapes that do not touch come closer than MIN_GAP
            (the ring-to-bus coupling gap, 200 nm by design, is the smallest
            intended spacing on the die; anything below MIN_GAP is a mistake)
Shapes that touch along an edge (port-to-port joins) are allowed.

Usage:  python check_layout.py [build/cpo_pic.gds]
"""
import sys
import pathlib
import gdstk
import numpy as np

MIN_GAP = 0.15      # um
LAYER = (1, 0)

def main(path):
    lib = gdstk.read_gds(str(path))
    def bbox_area(c):
        b = c.bounding_box(); return 0.0 if b is None else (b[1][0] - b[0][0]) * (b[1][1] - b[0][1])
    die = max((c for c in lib.cells if c.name != "$$$CONTEXT_INFO$$$"), key=bbox_area)   # the die: largest footprint
    polys = die.get_polygons(layer=LAYER[0], datatype=LAYER[1])
    boxes = np.array([[*p.bounding_box()[0], *p.bounding_box()[1]] for p in polys])
    overlaps, close = [], []
    for i in range(len(polys)):
        bi = boxes[i]
        cand = np.where(~((boxes[:, 0] > bi[2] + MIN_GAP) | (boxes[:, 2] < bi[0] - MIN_GAP) |
                          (boxes[:, 1] > bi[3] + MIN_GAP) | (boxes[:, 3] < bi[1] - MIN_GAP)))[0]
        for j in cand[cand > i]:
            a = sum(q.area() for q in gdstk.boolean(polys[i], polys[j], "and"))
            if a > 1e-3:
                overlaps.append((a, i, j)); continue
            touching = sum(q.area() for q in gdstk.boolean(polys[i], gdstk.offset(polys[j], 0.002), "and")) > 1e-9
            if not touching and sum(q.area() for q in gdstk.boolean(polys[i], gdstk.offset(polys[j], MIN_GAP), "and")) > 1e-6:
                close.append((i, j))
    def where(i, j):
        bi, bj = boxes[i], boxes[j]
        return f"x {max(bi[0], bj[0]):.1f}..{min(bi[2], bj[2]):.1f}  y {max(bi[1], bj[1]):.1f}..{min(bi[3], bj[3]):.1f} um"
    print(f"{path}: cell '{die.name}', {len(polys)} shapes on layer {LAYER[0]}/{LAYER[1]}")
    for a, i, j in sorted(overlaps, key=lambda h: -h[0]):
        print(f"  OVERLAP {a:9.3f} um^2 at {where(i, j)}")
    for i, j in close:
        print(f"  MIN GAP < {MIN_GAP*1000:.0f} nm at {where(i, j)}")
    print(f"{len(overlaps)} overlaps, {len(close)} min-gap violations -> {'FAIL' if overlaps or close else 'PASS'}")
    return 1 if overlaps or close else 0

if __name__ == "__main__":
    sys.exit(main(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "build/cpo_pic.gds")))

#!/usr/bin/env python3
"""Layout sanity check for the die: overlapping shapes and too-close shapes on the
waveguide layer. Run after every build; exits non-zero if anything is found.

Two rules, both on layer 1/0 (silicon):
  OVERLAP   two separate shapes share area (a waveguide drawn across another one)
  MIN GAP   two separate shapes that do not touch come closer than MIN_GAP
            (the ring-to-bus coupling gap, 300 nm by design, is the smallest
            intended spacing on the die; anything below MIN_GAP is a mistake)
  NEAR      shapes from two DIFFERENT placed cells (a ring and a route, two
            routes) that do not touch come closer than NEAR_GAP: light would
            couple between them. Designed couplers (ring to bus, the MMI
            outputs) sit inside one cell and are not affected. Added in v0.6
            after the ring-bank return passed ring 4 at 346 nm: wider than
            MIN GAP, so the first two rules missed a second coupler.
Shapes that touch along an edge (port-to-port joins) are allowed.

Usage:  python check_layout.py [build/cpo_pic.gds]
"""
import sys
import pathlib
import gdstk
import numpy as np

MIN_GAP = 0.15      # um
NEAR_GAP = 2.0      # um, between different placed cells
LAYER = (1, 0)

def main(path):
    lib = gdstk.read_gds(str(path))
    def bbox_area(c):
        b = c.bounding_box(); return 0.0 if b is None else (b[1][0] - b[0][0]) * (b[1][1] - b[0][1])
    die = max((c for c in lib.cells if c.name != "$$$CONTEXT_INFO$$$"), key=bbox_area)   # the die: largest footprint
    polys, owner = [], []
    for p in die.polygons:
        if (p.layer, p.datatype) == LAYER:
            polys.append(p); owner.append(-1)
    for k, ref in enumerate(die.references):
        for p in ref.get_polygons(layer=LAYER[0], datatype=LAYER[1]):
            polys.append(p); owner.append(k)
    boxes = np.array([[*p.bounding_box()[0], *p.bounding_box()[1]] for p in polys])
    overlaps, close, near = [], [], []
    R = max(MIN_GAP, NEAR_GAP)
    for i in range(len(polys)):
        bi = boxes[i]
        cand = np.where(~((boxes[:, 0] > bi[2] + R) | (boxes[:, 2] < bi[0] - R) |
                          (boxes[:, 1] > bi[3] + R) | (boxes[:, 3] < bi[1] - R)))[0]
        for j in cand[cand > i]:
            a = sum(q.area() for q in gdstk.boolean(polys[i], polys[j], "and"))
            if a > 1e-3:
                overlaps.append((a, i, j)); continue
            touching = sum(q.area() for q in gdstk.boolean(polys[i], gdstk.offset(polys[j], 0.002), "and")) > 1e-9
            if touching:
                continue
            if sum(q.area() for q in gdstk.boolean(polys[i], gdstk.offset(polys[j], MIN_GAP), "and")) > 1e-6:
                close.append((i, j))
            elif owner[i] != owner[j] and sum(q.area() for q in gdstk.boolean(polys[i], gdstk.offset(polys[j], NEAR_GAP), "and")) > 1e-6:
                near.append((i, j))
    def where(i, j):
        bi, bj = boxes[i], boxes[j]
        return f"x {max(bi[0], bj[0]):.1f}..{min(bi[2], bj[2]):.1f}  y {max(bi[1], bj[1]):.1f}..{min(bi[3], bj[3]):.1f} um"
    print(f"{path}: cell '{die.name}', {len(polys)} shapes on layer {LAYER[0]}/{LAYER[1]}")
    for a, i, j in sorted(overlaps, key=lambda h: -h[0]):
        print(f"  OVERLAP {a:9.3f} um^2 at {where(i, j)}")
    for i, j in close:
        print(f"  MIN GAP < {MIN_GAP*1000:.0f} nm at {where(i, j)}")
    for i, j in near:
        print(f"  NEAR < {NEAR_GAP:.1f} um between cells at {where(i, j)}")
    bad = overlaps or close or near
    print(f"{len(overlaps)} overlaps, {len(close)} min-gap, {len(near)} near-between-cells -> {'FAIL' if bad else 'PASS'}")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "build/cpo_pic.gds")))

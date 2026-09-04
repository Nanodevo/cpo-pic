#!/usr/bin/env python3
"""cpo-pic: a passive photonic test die for glass-substrate co-packaged
optics, designed to mate with an ion-exchanged (IOX) glass waveguide
bridge of the kind Corning publishes (Brusberg et al., IMAPS 2022;
OFC 2020-2026).

Interface contract (from the published architecture):
- 16 coupler channels at 250 um pitch on the west edge: one channel
  per fiber of the MPO-16 connector feeding the glass substrate.
- Each coupler is a long linear adiabatic taper (2 mm, routing width
  down to a narrow tip): the evanescent-transfer half of the joint.
  In assembly the die sits face-down on the glass; the taper region
  lies over the IOX guide and the light transfers vertically across
  a ~1 um adhesive bondline.
- Channels are paired odd-in / even-out as loopbacks so a fiber array
  on the glass can grade every interface in transmission (the IMAPS
  test method).

Channel plan (west edge, numbered south to north):
  ch1-ch2    reference loopback (shortest on-chip path)
  ch3-ch4    loopback + 0.5 cm spiral  } cutback pair:
  ch5-ch6    loopback + 2.0 cm spiral  } propagation loss per cm
  ch7-ch8    4-ring WDM bank (staggered radii): the demux skeleton
             of a transceiver engine; per-ring group index and Q
  ch9-ch10   2x2 thermo-optic MZI switch cell (heater metal drawn):
             the switch element of an optical engine, bar/cross path
  ch11-ch12  taper split: 120 nm tip   } coupler DOE vs the
  ch13-ch14  taper split: 180 nm tip   } 150 nm reference pairs
  ch15-ch16  duplicate reference loopback: uniformity statistic

Plus cross + Vernier fiducials in the corners (the marks a vision-based
die bonder reads through a split optic) and human-readable labels.
Generic 220 nm SOI strip-waveguide PDK; the cell parameters, not the
process, are the point - retarget to a foundry PDK by swapping the
cross-section.

Outputs: build/cpo_pic.gds and build/cpo_pic.png
"""

import pathlib

import gdsfactory as gf

gf.gpdk.PDK.activate()

# ---------------------------------------------------------------- geometry
DIE = 5000.0                 # die side, um (5 x 5 mm, like the SiN chips in [8])
PITCH = 250.0                # coupler pitch, um (IMAPS array pitch)
N_CH = 16                    # channels, odd in / even out (MPO-16)
TAPER_LEN = 2000.0           # adiabatic taper length, um (~2 mm per [8])
TIP_W = 0.15                 # taper tip width, um
WG_W = 0.5                   # routing waveguide width, um
EDGE_MARGIN = 10.0           # taper tip setback from die edge, um
X_DUT = EDGE_MARGIN + TAPER_LEN + 300.0   # where devices-under-test start

SPIRAL_SHORT = 5_000.0       # um total path  (0.5 cm)
SPIRAL_LONG = 20_000.0       # um total path  (2.0 cm)
RING_RADIUS = 10.0
RING_GAP = 0.2
MZI_DL = 100.0

ARRAY_SPAN = (N_CH - 1) * PITCH
Y0 = (DIE - ARRAY_SPAN) / 2  # first channel y


def ch_y(ch: int) -> float:
    return Y0 + (ch - 1) * PITCH


@gf.cell
def edge_coupler(tip_w: float = TIP_W) -> gf.Component:
    """Linear adiabatic taper: narrow tip at the west edge -> routing width.

    The evanescent-transfer half of the glass-to-PIC joint: in assembly
    the tip-side length lies over the IOX guide. `tip_w` is the DOE
    factor of the taper-split pairs.
    """
    return gf.components.taper(length=TAPER_LEN, width1=tip_w, width2=WG_W)


def spiral_of_length(target: float, n_loops: int) -> gf.Component:
    """Spiral whose measured path length converges on `target` (um)."""
    straight = max(10.0, (target - 2500.0) / (2 * n_loops))
    c = gf.components.spiral(length=straight, n_loops=n_loops)
    for _ in range(6):
        err = target - c.info["length"]
        if abs(err) < 1.0:
            break
        straight = max(10.0, straight + err / (2 * n_loops))
        c = gf.components.spiral(length=straight, n_loops=n_loops)
    return c


@gf.cell
def vernier(pitch_a: float = 10.0, pitch_b: float = 10.5,
            n: int = 9, bar: tuple[float, float] = (2.0, 20.0)) -> gf.Component:
    """Two facing bar combs at slightly different pitches.

    Reading which bars line up measures residual misalignment to
    (pitch_b - pitch_a) resolution - how [8] verifies placement after
    bonding.
    """
    c = gf.Component()
    w, h = bar
    for i in range(n):
        r = c << gf.components.rectangle(size=(w, h), layer=(1, 0))
        r.move((i * pitch_a, 0))
        r2 = c << gf.components.rectangle(size=(w, h), layer=(1, 0))
        r2.move((i * pitch_b, -h - 5.0))
    return c


@gf.cell
def fiducial() -> gf.Component:
    """Cross + Vernier corner mark (the split-optic targets of Fig. 10)."""
    c = gf.Component()
    c << gf.components.cross(length=60.0, width=4.0, layer=(1, 0))
    v = c << vernier()
    v.move((50.0, -80.0))
    return c


def place_coupler(c: gf.Component, ch: int, tip_w: float = TIP_W):
    t = c << edge_coupler(tip_w=tip_w)
    t.move((EDGE_MARGIN, ch_y(ch)))
    return t


def loop_back(c: gf.Component, from_port, to_taper_port) -> None:
    """Turn an east-facing output around and bring it to the west edge.

    A 180-degree Euler bend attaches directly to the output, then the
    router closes the (now west-facing to east-facing) gap.
    """
    b = c << gf.components.bend_euler(angle=180)
    b.connect("o1", from_port)
    gf.routing.route_single(c, b.ports["o2"], to_taper_port,
                            cross_section="strip")


def label(c: gf.Component, text: str, x: float, y: float,
          size: float = 90.0) -> None:
    t = c << gf.components.text(text=text, size=size, layer=(1, 0))
    t.move((x, y))


@gf.cell
def cpo_pic() -> gf.Component:
    c = gf.Component()

    # die frame (floorplan layer), not filled
    fw = 5.0
    for size, xy in [((DIE, fw), (0, 0)), ((DIE, fw), (0, DIE - fw)),
                     ((fw, DIE), (0, 0)), ((fw, DIE), (DIE - fw, 0))]:
        r = c << gf.components.rectangle(size=size, layer=(99, 0))
        r.move(xy)

    # --- ch1-2 and ch15-16: reference loopbacks
    for ch_in, ch_out, name in [(1, 2, "REF-A"), (15, 16, "REF-B")]:
        t_in = place_coupler(c, ch_in)
        t_out = place_coupler(c, ch_out)
        loop_back(c, t_in.ports["o2"], t_out.ports["o2"])
        label(c, name, 3600, ch_y(ch_in) + 70)

    # --- ch11-12 / ch13-14: coupler DOE, taper tip-width split
    for ch_in, ch_out, tip, name in [(11, 12, 0.12, "TIP 120nm"),
                                     (13, 14, 0.18, "TIP 180nm")]:
        t_in = place_coupler(c, ch_in, tip_w=tip)
        t_out = place_coupler(c, ch_out, tip_w=tip)
        loop_back(c, t_in.ports["o2"], t_out.ports["o2"])
        label(c, name, 3600, ch_y(ch_in) + 70)

    # --- ch3-4 / ch5-6: cutback spirals
    for ch_in, ch_out, target, n_loops, name in [
            (3, 4, SPIRAL_SHORT, 8, "SPIRAL 0.5cm"),
            (5, 6, SPIRAL_LONG, 16, "SPIRAL 2.0cm")]:
        t_in = place_coupler(c, ch_in)
        t_out = place_coupler(c, ch_out)
        # The spiral's two ports sit side by side at one end of the body, both
        # facing outward. Attach it port-to-port: the feed straight ends at
        # X_DUT + 60, the spiral rotates so its ports face the feed and its
        # body lies beyond it, and the return route leaves from o2 (now facing
        # west, 3 um beside the feed) to the output taper. Placing it with a
        # bare move() and routing to o1 sent the feed straight through the arms
        # (v0.3 defect, caught by check_layout.py).
        feed = c << gf.components.straight(
            length=X_DUT + 60 - (EDGE_MARGIN + TAPER_LEN), cross_section="strip")
        feed.connect("o1", t_in.ports["o2"])
        sp = c << spiral_of_length(target, n_loops)
        sp.connect("o1", feed.ports["o2"])
        gf.routing.route_single(c, sp.ports["o2"], t_out.ports["o2"],
                                cross_section="strip")
        label(c, name, 3600, ch_y(ch_in) + 70)

    # --- ch7-8: WDM bank, the demux skeleton of a transceiver engine.
    # Four all-pass rings in series on one bus, radii staggered so each
    # ring notches a different wavelength comb: one transmission scan
    # shows four resonance families (per-ring group index and Q).
    t_in = place_coupler(c, 7)
    t_out = place_coupler(c, 8)
    prev = t_in.ports["o2"]
    for k in range(4):
        ring = c << gf.components.ring_single(radius=RING_RADIUS + 0.05 * k,
                                              gap=RING_GAP)
        ring.move((X_DUT + 120 + 140 * k, ch_y(7)))
        gf.routing.route_single(c, prev, ring.ports["o1"],
                                cross_section="strip")
        prev = ring.ports["o2"]
    loop_back(c, prev, t_out.ports["o2"])
    label(c, "WDM 4-RING", 3600, ch_y(7) + 70)

    # --- ch9-10: 2x2 thermo-optic MZI switch cell, the routing element
    # of an optical engine. Heater metal is drawn; bar path is looped
    # back so the cell is graded passively, cross port left open.
    t_in = place_coupler(c, 9)
    t_out = place_coupler(c, 10)
    sw = c << gf.components.mzi2x2_2x2_phase_shifter()
    sw.move((X_DUT + 200, ch_y(9) + 40))
    gf.routing.route_single(c, t_in.ports["o2"], sw.ports["o1"],
                            cross_section="strip")
    loop_back(c, sw.ports["o4"], t_out.ports["o2"])
    label(c, "TO-SWITCH 2x2", 3600, ch_y(9) + 70)

    # corner fiducials
    for (x, y) in [(200, DIE - 200), (DIE - 300, DIE - 200), (DIE - 300, 350)]:
        f = c << fiducial()
        f.move((x, y))

    # die labels
    label(c, "NANODEVO CPO-PIC v0.4", 300, 260, size=110)
    label(c, "WEST EDGE: 16 TAPERS, 250UM PITCH, TO IOX GLASS (MPO-16)",
          300, 120, size=60)
    return c


if __name__ == "__main__":
    build = pathlib.Path(__file__).parent / "build"
    build.mkdir(exist_ok=True)
    c = cpo_pic()
    gds = build / "cpo_pic.gds"
    c.write_gds(gds)
    print("wrote", gds)
    try:
        c.plot()
        import matplotlib.pyplot as plt
        plt.savefig(build / "cpo_pic.png", dpi=220, bbox_inches="tight")
        print("wrote", build / "cpo_pic.png")
    except Exception as e:
        print("png render skipped:", e)

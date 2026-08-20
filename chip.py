#!/usr/bin/env python3
"""cpo-pic: a passive photonic test die for glass-substrate co-packaged
optics, designed to mate with an ion-exchanged (IOX) glass waveguide
bridge of the kind Corning publishes (Brusberg et al., IMAPS 2022;
OFC 2020-2026).

Interface contract (from the published architecture):
- 12 coupler channels at 250 um pitch on the west edge, matching the
  IOX waveguide arrays on the MPO-16-fed glass substrate.
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
  ch7-ch8    add-drop ring resonator (R=10 um): group index, Q
  ch9-ch10   unbalanced MZI (dL=100 um): FSR sanity check
  ch11-ch12  duplicate reference loopback: uniformity statistic

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
N_CH = 12                    # channels, odd in / even out
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
def edge_coupler() -> gf.Component:
    """Linear adiabatic taper: narrow tip at the west edge -> routing width.

    The evanescent-transfer half of the glass-to-PIC joint: in assembly
    the tip-side length lies over the IOX guide.
    """
    return gf.components.taper(length=TAPER_LEN, width1=TIP_W, width2=WG_W)


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


def place_coupler(c: gf.Component, ch: int):
    t = c << edge_coupler()
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


def label(c: gf.Component, text: str, x: float, y: float) -> None:
    t = c << gf.components.text(text=text, size=25.0, layer=(1, 0))
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

    # --- ch1-2 and ch11-12: reference loopbacks
    for ch_in, ch_out, name in [(1, 2, "REF-A"), (11, 12, "REF-B")]:
        t_in = place_coupler(c, ch_in)
        t_out = place_coupler(c, ch_out)
        loop_back(c, t_in.ports["o2"], t_out.ports["o2"])
        label(c, name, X_DUT + 150, ch_y(ch_in) + 60)

    # --- ch3-4 / ch5-6: cutback spirals
    for ch_in, ch_out, target, n_loops, name in [
            (3, 4, SPIRAL_SHORT, 8, "SPIRAL 0.5cm"),
            (5, 6, SPIRAL_LONG, 16, "SPIRAL 2.0cm")]:
        t_in = place_coupler(c, ch_in)
        t_out = place_coupler(c, ch_out)
        sp = c << spiral_of_length(target, n_loops)
        sp.move((X_DUT + 60, ch_y(ch_in)))
        gf.routing.route_single(c, t_in.ports["o2"], sp.ports["o1"],
                                cross_section="strip")
        loop_back(c, sp.ports["o2"], t_out.ports["o2"])
        label(c, name, X_DUT + 150, ch_y(ch_in) + 130)

    # --- ch7-8: add-drop ring, loopback via the west-facing drop port
    t_in = place_coupler(c, 7)
    t_out = place_coupler(c, 8)
    ring = c << gf.components.ring_double(radius=RING_RADIUS, gap=RING_GAP)
    ring.move((X_DUT + 120, ch_y(7) + 60))
    gf.routing.route_single(c, t_in.ports["o2"], ring.ports["o1"],
                            cross_section="strip")
    gf.routing.route_single(c, ring.ports["o3"], t_out.ports["o2"],
                            cross_section="strip")
    label(c, "RING R10", X_DUT + 150, ch_y(7) + 160)

    # --- ch9-10: unbalanced MZI
    t_in = place_coupler(c, 9)
    t_out = place_coupler(c, 10)
    mzi = c << gf.components.mzi(delta_length=MZI_DL)
    mzi.move((X_DUT + 120, ch_y(9)))
    gf.routing.route_single(c, t_in.ports["o2"], mzi.ports["o1"],
                            cross_section="strip")
    loop_back(c, mzi.ports["o2"], t_out.ports["o2"])
    label(c, "MZI dL100", X_DUT + 150, ch_y(9) + 160)

    # corner fiducials
    for (x, y) in [(200, DIE - 200), (DIE - 300, DIE - 200), (DIE - 300, 350)]:
        f = c << fiducial()
        f.move((x, y))

    # die label
    label(c, "NANODEVO CPO-PIC v0.1  12ch 250um", DIE / 2 - 700, 100)
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

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
  ch7-ch8    4-ring bank, all-pass notch filters with radii staggered
             by 24 nm so the four resonance families sit about a quarter
             of a free spectral range apart; per-ring group index and Q
  ch9-ch10   2x2 thermo-optic MZI cell (heater metal drawn, no pads):
             arms 10 um apart in length so a passive wavelength sweep
             grades it; bar output looped back, open ports terminated
  ch11-ch12  taper split: 120 nm tip   } coupler DOE vs the
  ch13-ch14  taper split: 180 nm tip   } 150 nm reference pairs
  ch15-ch16  duplicate reference loopback: uniformity statistic

Plus cross + Vernier fiducials in the corners (the marks a vision-based
die bonder reads through a split optic), human-readable labels, and a
cladding-open window over the taper region: the evanescent hand-off
needs the silicon to meet the adhesive with no top oxide in between.
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
RING_STEP = 0.024            # radius step between the four rings, um: spaces the
                             # resonance families ~2 nm apart, a quarter of the ~7.8 nm FSR
                             # (v0.4 used 50 nm: rings 1/3 and 2/4 landed ~0.5 nm apart)
RING_GAP = 0.30              # coupling gap, um: 200 nm (v0.4) over-couples, ~1 dB notches
MZI_DL = 10.0                # arm length difference, um: lets a passive sweep grade the cell
RING_CLEAR = 20.0            # straight after the last ring before the bus turns up, um
TERM_LEN = 20.0              # termination taper on unused ports, um
CLAD_OPEN = (60, 0)          # own layer: top-cladding opening over the tapers
                             # (the generic PDK has no such layer)

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
    c.add_port(name=f"ch{ch}", port=t.ports["o1"])   # the die's optical ports: one per channel, at the taper tips
    return t


def loop_back(c: gf.Component, from_port, to_taper_port, clear: float = 0.0) -> None:
    """Bring an east-facing output back to an east-facing taper end further up.

    One route does it: out to the east, a 90-degree bend up, the climb, a
    90-degree bend west and the run back to the taper. `clear` adds a straight
    first, so the turn keeps its distance from the device the output leaves.
    Up to v0.5 a 180-degree bend sat on the output and the router then had to
    turn the light round a second time: an extra U-turn that reached back into
    the cladding window behind the tapers and, after the ring bank, ran 346 nm
    past ring 4, a second coupler nobody designed.
    """
    if clear > 0:
        s = c << gf.components.straight(length=clear, cross_section="strip")
        s.connect("o1", from_port)
        from_port = s.ports["o2"]
    gf.routing.route_single(c, from_port, to_taper_port, cross_section="strip")


def terminate(c: gf.Component, port) -> None:
    """Close an unused optical port with a taper to a narrow tip, so the light
    it carries radiates away instead of reflecting from a blunt waveguide end."""
    t = c << gf.components.taper(length=TERM_LEN, width1=WG_W, width2=TIP_W)
    t.connect("o1", port)


FAN_PITCH = 10.0             # switch port pitch after the fan-out, um
FAN_LEN = 30.0               # length of each fan-out S-bend, um


@gf.cell
def switch_cell() -> gf.Component:
    """The 2x2 thermo-optic MZI as placed on ch9-10, with its arm difference,
    and S-bends that spread its ports from the MMI's 1.24 um to FAN_PITCH.
    Without them a terminator or route attached to one port runs 0.75 um from
    the next one for its whole length: an accidental coupler (v0.5)."""
    c = gf.Component()
    m = c << gf.components.mzi2x2_2x2_phase_shifter(delta_length=MZI_DL)
    for pair in (("o1", "o2"), ("o4", "o3")):
        ps = sorted((m.ports[n] for n in pair), key=lambda q: q.dcenter[1])
        dy = (FAN_PITCH - (ps[1].dcenter[1] - ps[0].dcenter[1])) / 2
        for q, outward in zip(ps, (-1, 1)):          # lower port down, upper port up
            west = abs(q.orientation - 180) < 1        # bend_s mirrors its offset on west-facing ports
            s = c << gf.components.bend_s(size=(FAN_LEN, dy * outward * (-1 if west else 1)),
                                          cross_section="strip")
            s.connect("o1", q)
            assert (s.ports["o2"].dcenter[1] - q.dcenter[1]) * outward > 0
            c.add_port(name=q.name, port=s.ports["o2"])
    c.add_ports([p for p in m.ports if p.port_type != "optical"])
    return c


def label(c: gf.Component, text: str, x: float, y: float,
          size: float = 90.0) -> None:
    t = c << gf.components.text(text=text, size=size, layer=(1, 0))
    t.move((x, y))


@gf.cell
def cpo_pic() -> gf.Component:
    c = gf.Component()

    # cladding-open window over the 16 tapers, from the die edge to the taper ends
    w = c << gf.components.rectangle(
        size=(EDGE_MARGIN + TAPER_LEN, ARRAY_SPAN + 2 * PITCH / 2), layer=CLAD_OPEN)
    w.move((0, Y0 - PITCH / 2))

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

    # --- ch7-8: ring bank. Four all-pass rings in series on one bus, radii
    # staggered so each ring notches a different wavelength comb, about a
    # quarter of a free spectral range from the next: one transmission scan
    # shows four resonance families (per-ring group index and Q).
    t_in = place_coupler(c, 7)
    t_out = place_coupler(c, 8)
    prev = t_in.ports["o2"]
    for k in range(4):
        ring = c << gf.components.ring_single(radius=RING_RADIUS + RING_STEP * k,
                                              gap=RING_GAP)
        ring.move((X_DUT + 120 + 140 * k, ch_y(7)))
        gf.routing.route_single(c, prev, ring.ports["o1"],
                                cross_section="strip")
        prev = ring.ports["o2"]
    loop_back(c, prev, t_out.ports["o2"], clear=RING_CLEAR)
    label(c, "RING BANK 4", 3600, ch_y(7) + 70)

    # --- ch9-10: 2x2 thermo-optic MZI cell. Heater metal is drawn but has no
    # pads on this die; the 10 um arm difference makes the outputs swing with
    # wavelength, so a passive sweep of the looped-back bar port grades the
    # cell. The unused input and the cross output are terminated.
    t_in = place_coupler(c, 9)
    t_out = place_coupler(c, 10)
    sw = c << switch_cell()
    sw.move((X_DUT + 200, 0))
    sw.dmovey(ch_y(9) - sw.ports["o1"].dcenter[1])   # input level with channel 9: a straight feed, no S-jog
    gf.routing.route_single(c, t_in.ports["o2"], sw.ports["o1"],
                            cross_section="strip")
    # the bar port runs straight past the cross port's terminator (the two
    # outputs are only 1.24 um apart) before it turns back
    ext = c << gf.components.straight(length=TERM_LEN + 10.0, cross_section="strip")
    ext.connect("o1", sw.ports["o4"])
    loop_back(c, ext.ports["o2"], t_out.ports["o2"])
    terminate(c, sw.ports["o2"])
    terminate(c, sw.ports["o3"])
    label(c, "TO-SWITCH 2x2", 3600, ch_y(9) + 70)

    # corner fiducials
    for (x, y) in [(200, DIE - 200), (DIE - 300, DIE - 200), (DIE - 300, 350)]:
        f = c << fiducial()
        f.move((x, y))

    # die labels
    label(c, "NANODEVO CPO-PIC v0.6", 300, 260, size=110)
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

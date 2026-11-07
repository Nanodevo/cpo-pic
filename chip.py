#!/usr/bin/env python3
"""cpo-pic: a passive photonic test die for glass-substrate co-packaged
optics, designed to mate with an ion-exchanged (IOX) glass waveguide
bridge of the kind Corning publishes (Brusberg et al., IMAPS 2022;
OFC 2020-2026).

Interface contract (from the published architecture):
- 24 coupler channels at 127 um pitch on the west edge. 127 um is the
  fine pitch of current fiber arrays and V-groove blocks; the glass
  bridge fans a two-row MPO-24 connector (250 um) into this single row.
- Each coupler is a long linear adiabatic taper (2 mm, routing width
  down to a narrow tip): the evanescent-transfer half of the joint.
  In assembly the die sits face-down on the glass; the taper region
  lies over the IOX guide and the light transfers vertically across
  a ~1 um adhesive bondline.
- Channels are paired as loopbacks (in, out) so a fiber array on the
  glass can grade every interface in transmission (the IMAPS test
  method).

Channel plan (west edge, numbered south to north):
  ch1-2      REF-A  reference loopback at the south edge of the array
  ch3-4      loopback + 0.5 cm spiral  }
  ch5-6      loopback + 1.0 cm spiral  } four-point cutback with REF-A:
  ch7-8      loopback + 2.0 cm spiral  } propagation loss per cm
  ch9-10     4-ring bank, 300 nm gap: all-pass notch filters, radii
             staggered by 24 nm so the four resonance families sit about
             a quarter of a free spectral range apart
  ch11       DARK   a taper with no loop: launch into a neighbour, read
             what leaks across = crosstalk floor of the glass interface
  ch12-13    REF-M  reference loopback at the centre of the array
  ch14-15    4-ring bank at the model's critical gap (367 nm): deepest
             notches, compared directly with the 300 nm bank
  ch16-18    MZI, 1x2 splitter in, 2x2 combiner out, arms 100 um apart,
             heater metal drawn (no pads): input ch16, both outputs to
             ch17 and ch18, so nothing on the cell is a dead end
  ch19-20    taper split: 120 nm tip   } coupler DOE vs the
  ch21-22    taper split: 180 nm tip   } 150 nm reference pairs
  ch23-24    REF-B  reference loopback at the north edge: with REF-A and
             REF-M, coupling across the array (roll shows as edge loss)

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
PITCH = 127.0                # coupler pitch, um (fine fiber-array / V-groove pitch; v0.6 used 250)
N_CH = 24                    # channels (MPO-24 fanned into one row by the glass; v0.6 had 16)
TAPER_LEN = 2000.0           # adiabatic taper length, um (~2 mm per [8])
TIP_W = 0.15                 # taper tip width, um
WG_W = 0.5                   # routing waveguide width, um
EDGE_MARGIN = 10.0           # taper tip setback from die edge, um
X_DUT = EDGE_MARGIN + TAPER_LEN + 300.0   # where devices-under-test start

SPIRAL_SHORT = 5_000.0       # um total path  (0.5 cm)
SPIRAL_MID = 10_000.0        # um total path  (1.0 cm)
SPIRAL_LONG = 20_000.0       # um total path  (2.0 cm)
RING_RADIUS = 10.0
RING_STEP = 0.024            # radius step between the four rings, um: spaces the
                             # resonance families ~2 nm apart, a quarter of the ~7.8 nm FSR
                             # (v0.4 used 50 nm: rings 1/3 and 2/4 landed ~0.5 nm apart)
RING_GAP_CRIT = 0.367        # gap where the model's coupling equals the ring loss: deepest notch
RING_GAP = 0.30              # coupling gap, um: 200 nm (v0.4) over-couples, ~1 dB notches
MZI_DL = 100.0               # arm length difference, um: fringes ~5.9 nm apart, ~16 per 100 nm sweep (v0.6: 10 um, <2)
RING_CLEAR = 20.0            # straight after the last ring before the bus turns up, um
LABEL_X = 3600.0             # x of the group labels
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
    """MZI with a 1x2 splitter in and a 2x2 combiner out, arms MZI_DL apart,
    heater metal on one arm. One input, two outputs, all three measured: the
    two outputs are complementary, so their ratio reads the interference
    independently of coupling loss. S-bends spread the outputs from the
    MMI's 1.25 um to FAN_PITCH before anything is attached to them."""
    c = gf.Component()
    # the combiner's arm-side ports are o3/o4 (gdsfactory's mzi1x2_2x2 does the
    # same); with the default o2/o3 the arms land on the wrong ports and overlap
    m = c << gf.components.mzi_phase_shifter(delta_length=MZI_DL,
                                             splitter="mmi1x2", combiner="mmi2x2",
                                             port_e1_combiner="o3", port_e0_combiner="o4")
    c.add_port(name="o1", port=m.ports["o1"])
    outs = sorted((m.ports[n] for n in ("o2", "o3")), key=lambda q: q.dcenter[1])
    dy = (FAN_PITCH - (outs[1].dcenter[1] - outs[0].dcenter[1])) / 2
    for q, outward, name in zip(outs, (-1, 1), ("o2", "o3")):   # o2 = lower output, o3 = upper
        s = c << gf.components.bend_s(size=(FAN_LEN, dy * outward), cross_section="strip")
        s.connect("o1", q)
        assert (s.ports["o2"].dcenter[1] - q.dcenter[1]) * outward > 0
        c.add_port(name=name, port=s.ports["o2"])
    c.add_ports([p for p in m.ports if p.port_type != "optical"])
    return c


def label(c: gf.Component, text: str, x: float, y: float,
          size: float = 60.0) -> None:
    t = c << gf.components.text(text=text, size=size, layer=(1, 0))
    t.move((x, y))


@gf.cell
def cpo_pic() -> gf.Component:
    c = gf.Component()

    # cladding-open window over the 24 tapers, from the die edge to the taper ends
    w = c << gf.components.rectangle(
        size=(EDGE_MARGIN + TAPER_LEN, ARRAY_SPAN + 2 * PITCH / 2), layer=CLAD_OPEN)
    w.move((0, Y0 - PITCH / 2))

    # die frame (floorplan layer), not filled
    fw = 5.0
    for size, xy in [((DIE, fw), (0, 0)), ((DIE, fw), (0, DIE - fw)),
                     ((fw, DIE), (0, 0)), ((fw, DIE), (DIE - fw, 0))]:
        r = c << gf.components.rectangle(size=size, layer=(99, 0))
        r.move(xy)

    def pair(ch_in, ch_out, name, tip=TIP_W):
        t_in = place_coupler(c, ch_in, tip_w=tip)
        t_out = place_coupler(c, ch_out, tip_w=tip)
        label(c, name, LABEL_X, ch_y(ch_in) + 20)
        return t_in, t_out

    # --- reference loopbacks at both edges and the centre of the array
    for ch_in, ch_out, name in [(1, 2, "REF-A"), (12, 13, "REF-M"), (23, 24, "REF-B")]:
        t_in, t_out = pair(ch_in, ch_out, name)
        loop_back(c, t_in.ports["o2"], t_out.ports["o2"])

    # --- coupler DOE: taper tip-width split
    for ch_in, ch_out, tip, name in [(19, 20, 0.12, "TIP 120NM"), (21, 22, 0.18, "TIP 180NM")]:
        t_in, t_out = pair(ch_in, ch_out, name, tip=tip)
        loop_back(c, t_in.ports["o2"], t_out.ports["o2"])

    # --- cutback spirals
    for ch_in, ch_out, target, n_loops, name in [
            (3, 4, SPIRAL_SHORT, 8, "SPIRAL 0.5CM"),
            (5, 6, SPIRAL_MID, 12, "SPIRAL 1.0CM"),
            (7, 8, SPIRAL_LONG, 16, "SPIRAL 2.0CM")]:
        t_in, t_out = pair(ch_in, ch_out, name)
        # The spiral's two ports sit side by side at one end of the body, both
        # facing outward. Attach it port-to-port: the feed straight ends at
        # X_DUT + 60, the spiral rotates so its ports face the feed and its
        # body lies beyond it, and the return route leaves from o2 to the
        # output taper (v0.3 routed the feed through the arms; see README).
        feed = c << gf.components.straight(
            length=X_DUT + 60 - (EDGE_MARGIN + TAPER_LEN), cross_section="strip")
        feed.connect("o1", t_in.ports["o2"])
        sp = c << spiral_of_length(target, n_loops)
        sp.connect("o1", feed.ports["o2"])
        gf.routing.route_single(c, sp.ports["o2"], t_out.ports["o2"],
                                cross_section="strip")

    # --- two ring banks: four all-pass rings in series on one bus, radii
    # staggered so each ring notches a different wavelength comb, about a
    # quarter of a free spectral range from the next. Same rings, two gaps.
    for ch_in, ch_out, gap, name in [(9, 10, RING_GAP, "RINGS 300NM"),
                                     (14, 15, RING_GAP_CRIT, "RINGS 367NM")]:
        t_in, t_out = pair(ch_in, ch_out, name)
        prev = t_in.ports["o2"]
        for k in range(4):
            ring = c << gf.components.ring_single(radius=RING_RADIUS + RING_STEP * k, gap=gap)
            ring.move((X_DUT + 120 + 140 * k, ch_y(ch_in)))
            gf.routing.route_single(c, prev, ring.ports["o1"], cross_section="strip")
            prev = ring.ports["o2"]
        loop_back(c, prev, t_out.ports["o2"], clear=RING_CLEAR)

    # --- dark channel: a taper and nothing else, its wide end terminated
    t = place_coupler(c, 11)
    terminate(c, t.ports["o2"])
    label(c, "DARK", LABEL_X, ch_y(11) + 20)

    # --- MZI on ch16-18: input on ch16, upper output back to ch17 (inner
    # loop), lower output back to ch18 (outer loop, turns further east, so
    # the two returns nest without crossing)
    t_in = place_coupler(c, 16)
    t_a = place_coupler(c, 17)
    t_b = place_coupler(c, 18)
    sw = c << switch_cell()
    sw.move((X_DUT + 200, 0))
    sw.dmovey(ch_y(16) - sw.ports["o1"].dcenter[1])   # input level with ch16: straight feed
    gf.routing.route_single(c, t_in.ports["o2"], sw.ports["o1"], cross_section="strip")
    loop_back(c, sw.ports["o3"], t_a.ports["o2"])
    loop_back(c, sw.ports["o2"], t_b.ports["o2"], clear=40.0)
    label(c, "MZI 1X2-2X2", LABEL_X, ch_y(16) + 20)

    # corner fiducials
    for (x, y) in [(200, DIE - 200), (DIE - 300, DIE - 200), (DIE - 300, 350)]:
        f = c << fiducial()
        f.move((x, y))

    # die labels
    label(c, "NANODEVO CPO-PIC v0.7", 300, 260, size=110)
    label(c, "WEST EDGE: 24 TAPERS, 127UM PITCH, TO IOX GLASS (MPO-24 FAN-IN)",
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

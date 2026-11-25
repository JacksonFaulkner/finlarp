"""The LASER node's nine numbered sections, in the picture-and-panel template (docs/diagram-pages.md).
Section N illustrates heading N of tui/src/screens/diagrams_pages/FIB_LASER.txt, so the menu title,
the text panel and the picture agree. Three beats each, one beat is 8 s.

Run from the repo root (or through bake_queue.py), one section per run:

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_laser_sections.py -- <n>

Writes blender/fiber_laser_section_<n>.blend and assets/fiber_laser_section_<n>.glb. The detailed parts
(EML chip, submount and monitor photodiode, VCSEL, silicon-photonics chip with its Mach-Zehnder
modulator, wafers, lens, ferrules) come from fiber_laser_detail.py; colours from fiber_kit.py.

  1 what happens   driver gets the DSP's symbols; the EML makes light and dims it; a lens puts it in the fibre
  2 the parts      the EML cut open: InP, quantum wells, the DFB grating (one wavelength), the modulator
  3 in order       1 symbol in, 2 steady DFB light, 3 dimmed to a level, 4 lens into the fibre, 5 monitor
  4 three routes   EML, VCSEL and silicon photonics side by side
  5 Mach-Zehnder   light splits into two arms; in phase they add, out of phase they cancel
  6 200G per lane  eight lanes make 1.6T; 200G packs twice the symbols; the eye gets half as wide
  7 the shortage   the InP wafer of EMLs, the CW-laser alternative (still InP), and indium
  8 who makes it   makers tagged on EML chips, VCSEL dies and a silicon-photonics wafer
  9 chokepoints    small InP capacity; every route needs InP; a laser failing inside a CPO package
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, box, ball, tube, label, beat, show, key, P  # noqa: E402
from sand_zooms import start, finish, stream_of  # noqa: E402
from pbr_kit import empty  # noqa: E402
import fiber_kit as K  # noqa: E402
import fiber_laser_detail as D  # noqa: E402
from fiber_laser_detail import frame, camera_path, wire, offsets  # noqa: E402

PAGE = "fiber_laser"
BEATS = 3
PAM4_SEQ = (3, 0, 2, 1, 1, 3, 0, 2)  # as in fiber_laser_overview.py


def setup(name):
    _, root = start(name, beats=BEATS, page=PAGE)
    m = K.materials()
    m.update(D.materials())
    return m, root


def after(b, u):
    """From fraction u of beat b to the end of the section."""
    return [(F(b, u), F(BEATS, 0))]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def pam4_glow(m, parent, at, radii, b, name="lvl"):
    """A glow at `at` stepping through four sizes, one per symbol of PAM4_SEQ, during beat b."""
    for k, r in enumerate(radii):
        g = empty(f"{name}{k}", parent)
        ball(f"{name}{k}_glow", at, r, m["light"], g, 16)
        show(g, [(F(b, i / 8.0), F(b, (i + 1) / 8.0)) for i, s in enumerate(PAM4_SEQ) if s == k])


def lens_fibre(m, root, x_lens, x_fer, x_end, name, r_lens=9.0):
    """A lens in its holder, then a gold sleeve and white ferrule holding the fibre, all cut open on z = 0.
    Returns the lit-core group (hidden until shown)."""
    D.pipe_x(f"{name}_holder", x_lens - 3.0, x_lens + 3.0, r_lens + 3.0, r_lens - 0.5, m["steel"], root)
    o = D.ellipsoid(f"{name}_lens", (x_lens, 0.0, 0.0), 2.8, r_lens, r_lens, m["glass"], root)
    D.cut(o, 0.0)
    box(f"{name}_lens_post", (x_lens - 3.0, -40.0, -10.0), (x_lens + 3.0, -r_lens - 3.0, 0.0), m["post"], root)
    D.pipe_x(f"{name}_sleeve", x_fer - 2.0, x_fer + 24.0, 7.5, 5.0, m["gold"], root)
    D.pipe_x(f"{name}_ferrule", x_fer, x_fer + 24.0, 5.0, 1.4, m["zirconia"], root)
    D.rod(f"{name}_glass", (x_fer, 0.0, 0.0), (x_end, 0.0, 0.0), 1.4, m["clad"], root, True, 24)
    D.pipe_x(f"{name}_coat", x_fer + 24.0, x_end, 4.0, 1.4, m["coating"], root)
    box(f"{name}_fer_post", (x_fer + 4.0, -40.0, -10.0), (x_fer + 20.0, -7.5, 0.0), m["post"], root)
    core = empty(f"{name}_core", root)
    D.rod(f"{name}_core_l", (x_fer, 0.0, 0.0), (x_end, 0.0, 0.0), 0.5, m["light"], core, True, 12, front=0.6)
    return core


# ---- scope helpers (sections 6) ----------------------------------------------------------------------


def scope(m, root, cx, name, w=172.0, h=108.0):
    box(f"{name}_bezel", (cx - w / 2 - 10, -h / 2 - 10, -10.0), (cx + w / 2 + 10, h / 2 + 10, -1.0), m["dark_steel"], root)
    box(f"{name}_screen", (cx - w / 2, -h / 2, -1.0), (cx + w / 2, h / 2, 0.0), m["screen"], root)
    for i in range(-4, 5):
        tube(f"{name}_gv{i}", (cx + w / 9 * i, -h / 2, 0.1), (cx + w / 9 * i, h / 2, 0.1), 0.25, m["grid"], root, 6)
    for i in range(-2, 3):
        tube(f"{name}_gh{i}", (cx - w / 2, h / 4.5 * i, 0.1), (cx + w / 2, h / 4.5 * i, 0.1), 0.25, m["grid"], root, 6)


def trace(m, parent, x0, x1, levels, seq, name, b, u0=0.05, u1=0.85):
    """A PAM4 trace across x0..x1 (one symbol per slot), drawn left to right through beat b."""
    ui = (x1 - x0) / len(seq)
    for k, s in enumerate(seq):
        g = empty(f"{name}{k}", parent)
        xa = x0 + ui * k
        pts = [(xa + 0.2 * ui, levels[s], 1.0), (xa + 0.8 * ui, levels[s], 1.0)]
        if k + 1 < len(seq):
            pts.append((xa + 1.2 * ui, levels[seq[k + 1]], 1.0))
        D.polyline(f"{name}_tr{k}", pts, 0.6, m["light"], g)
        ball(f"{name}_dot{k}", (xa + 0.5 * ui, levels[s], 1.4), 1.6, m["light"], g, 12)
        show(g, [(F(b, u0 + (u1 - u0) * k / len(seq)), F(b + 1, 0))])


def eye(m, parent, xc, w, levels, name):
    """Every move between four levels over two symbol times, centred on xc, `w` wide: three eyes."""

    def ease(x, xa, xb, ya, yb):
        t = min(1.0, max(0.0, (x - xa) / (xb - xa)))
        return ya + (yb - ya) * (0.5 - 0.5 * math.cos(math.pi * t))

    xa, xb, xc0, xd = xc - w / 2, xc - w / 6, xc + w / 6, xc + w / 2
    n = 0
    for a in range(4):
        for b in range(4):
            left = [(xa + (xb - xa) * i / 10, ease(xa + (xb - xa) * i / 10, xa, xb, levels[a], levels[b]), 0.8) for i in range(11)]
            right = [(xc0 + (xd - xc0) * i / 10, ease(xc0 + (xd - xc0) * i / 10, xc0, xd, levels[a], levels[b]), 0.8) for i in range(11)]
            D.polyline(f"{name}_l{n}", left + [(xc0, levels[b], 0.8)], 0.4, m["light"], parent)
            D.polyline(f"{name}_r{n}", right, 0.4, m["light"], parent)
            n += 1
    for k in range(3):
        ym = (levels[k] + levels[k + 1]) / 2
        D.ellipsoid(f"{name}_eye{k}", (xc, ym, 1.2), w / 7.0, (levels[1] - levels[0]) * 0.3, 0.4, m["eye"], parent)


# ---- 1 what happens: a laser turns each symbol into a pulse of light ---------------------------------

S1 = 0.35
PCB1 = -26.0 * S1  # board top, level with the submount's underside


def sec1(m, root):
    cp, lit = D.chip(m, root, (0.0, 0.0, 0.0), S1, name="s1chip")
    sp = D.submount(m, root, (0.0, 0.0, 0.0), S1, name="s1sub")
    box("s1_carrier", (-7.0, -40.0, -14.0), (35.0, PCB1, 0.0), m["post"], root)
    box("s1_pcb", (-112.0, PCB1 - 4.0, -24.0), (-8.0, PCB1, 16.0), m["pcb"], root)
    D.driver_ic(m, root, (-64.0, PCB1, -11.0), (-40.0, PCB1 + 3.0, 11.0), "s1drv")
    ty = PCB1 + 0.25
    for k, z in enumerate((-4.0, 0.0, 4.0)):
        D.polyline(f"s1_dsp{k}", [(-112.0, ty, z), (-65.0, ty, z)], 0.6, m["copper"], root)
    bias_tr = [(-39.0, ty, -3.0), (-9.0, ty, -3.0)]
    data_tr = [(-39.0, ty, -8.0), (-9.0, ty, -8.0)]
    D.polyline("s1_bias_tr", bias_tr, 0.6, m["copper"], root)
    D.polyline("s1_data_tr", data_tr, 0.6, m["copper"], root)
    wb = wire("s1_bias_w", (-9.0, ty, -3.0), cp["dfb_pad"], 4.0, m["gold"], root, 0.3)
    wd = wire("s1_data_w", (-9.0, ty, -8.0), cp["eam_pad"], 7.0, m["gold"], root, 0.3)
    show(lit["dfb"], after(0, 0.6))
    show(lit["eam"], after(0, 0.6))
    fx = cp["front"][0]
    core = lens_fibre(m, root, 50.0, 66.0, 150.0, "s1")
    show(core, after(2, 0.05))
    b1 = empty("s1_beam1", root)
    D.cone("s1_beam_a", (fx, 0, 0), (49.0, 0, 0), 0.3, 7.0, m["beam"], b1, 32, half=True)
    D.cone("s1_beam_b", (51.0, 0, 0), (66.0, 0, 0), 7.0, 0.4, m["beam"], b1, 32, half=True)
    show(b1, after(1, 0.1))
    # beat 0: symbols arrive from the DSP, the driver sends the data on to the chip
    for k, z in enumerate((-4.0, 0.0, 4.0)):
        stream_of(root, f"s1_in{k}", 4, (-112.0, ty + 0.5, z), [(0, 0, 0), (47.0, 0, 0)], 1.1, m["elec"], 0, 0.0 + 0.05 * k, 0.45, 40)
    data = data_tr + wd[1:]
    stream_of(root, "s1_data", 5, data[0], offsets(data), 1.0, m["rf"], 0, 0.35, 0.85, 50)
    stream_of(root, "s1_data1", 6, data[0], offsets(data), 1.0, m["rf"], 1, 0.0, 0.8, 50)
    pam4_glow(m, root, cp["front"], (0.6, 1.2, 1.8, 2.4), 1, "s1_lvl")
    # beat 2: pulses of four brightnesses run down the fibre
    for i, s in enumerate(PAM4_SEQ):
        stream_of(root, f"s1_pulse{i}", 1, (68.0, 0.0, 0.8), [(0, 0, 0), (80.0, 0, 0)], 0.9 + 0.35 * s, m[f"lvl{s}"], 2, 0.05 + 0.09 * i, 0.06 + 0.09 * i, 70)

    label("PAM4 symbols from the DSP", (-84.0, ty, 4.0), root, beat(0))
    label("laser driver IC", (-52.0, PCB1 + 3.0, 0.0), root, beat(0))
    label("data to the modulator", wd[6], root, beat(0))
    label("steady bias to the laser", wb[5], root, beat(0))
    label("DFB laser: steady light", (12.0, 0.0, 0.0), root, beat(1))
    label("modulator dims it: 4 levels", cp["eam_pad"], root, beat(1))
    label("one level per symbol", (fx + 0.5, 2.0, 0.0), root, beat(1))
    label("lens focuses the light", (50.0, 9.0, 0.0), root, beat(2))
    label("into the fibre's core", (68.0, 0.5, 0.0), root, beat(2))
    label("pulses: one per symbol", (120.0, 1.5, 0.0), root, beat(2))

    camera_path(root, [
        frame((-34.0, 2.0, 0.0), 112.0, 0.30, 0.48, pad=1.0),
        frame((18.0, -3.0, 0.0), 48.0, 0.30, 0.28),
        frame((92.0, -2.0, 0.0), 80.0, 0.35, 0.22, pad=1.0),
    ])


# ---- 2 the parts --------------------------------------------------------------------------------


def sec2(m, root):
    cp, lit = D.chip(m, root, name="s2chip")
    sp = D.submount(m, root, name="s2sub")
    show(lit["dfb"], after(1, 0.05))
    show(lit["eam"], after(1, 0.05))
    fg = empty("s2_front", root)
    ball("s2_front_glow", cp["front"], 2.6, m["light"], fg, 16)
    D.cone("s2_front_beam", cp["front"], (cp["front"][0] + 22.0, 0, 0), 1.5, 9.0, m["beam"], fg, 32, 1.4, 1.0, half=True)
    show(fg, beat(2))
    bg = empty("s2_back", root)
    ball("s2_back_glow", cp["back"], 1.4, m["light"], bg, 16)
    D.cone("s2_back_beam", cp["back"], (-8.6, 0, 0), 1.0, 4.0, m["beam_dim"], bg, 24, 1.4, 1.0, half=True)
    show(bg, beat(2))
    show(sp["pd_lit"], beat(2))
    stream_of(root, "s2_run", 5, (2.0, 0.0, 0.8), [(0, 0, 0), (86.0, 0, 0)], 0.9, m["light"], 1, 0.15, 0.75, 50)
    stream_of(root, "s2_out", 5, (91.0, 0.0, 0.8), [(0, 0, 0), (20.0, 0, 0)], 0.9, m["light"], 2, 0.05, 0.8, 30)
    stream_of(root, "s2_bulk", 4, (45.0, -18.0, 0.6), [(0, 0, 0), (0, 14.0, 0)], 0.8, m["elec"], 0, 0.1, 0.8, 50)

    label("INDIUM PHOSPHIDE (InP) chip", cp["cut"], root, beat(0))
    label("EML: laser + modulator, one chip", (58.0, 11.0, -6.0), root, beat(0))
    label("ceramic submount", sp["aln"], root, beat(0))
    label("quantum wells make the light", cp["mqw"], root, beat(1))
    label("DFB grating: locks one WAVELENGTH", cp["grating"], root, beat(1))
    label("ridge keeps it in a stripe", (36.0, 7.5, 0.0), root, beat(1))
    label("DFB LASER section", (28.0, 11.0, -4.0), root, beat(2))
    label("EA modulator section", (74.0, 11.0, -4.0), root, beat(2))
    label("1310 nm out (O-band)", (100.0, 2.0, 0.0), root, beat(2))
    label("monitor photodiode", sp["pd"], root, beat(2))

    camera_path(root, [
        frame((42.0, -7.0, -8.0), 104.0, 0.45, 0.32, pad=1.0),
        frame((28.0, 1.0, 0.0), 46.0, 0.22, 0.30),
        frame((48.0, -4.0, 0.0), 120.0, 0.26, 0.16, pad=1.0),
    ])


# ---- 3 a symbol becomes light, in order ------------------------------------------------------------

S3 = 0.5


def sec3(m, root):
    cp, lit = D.chip(m, root, (0.0, 0.0, 0.0), S3, name="s3chip")
    sp = D.submount(m, root, (0.0, 0.0, 0.0), S3, name="s3sub")
    box("s3_post", (-14.0, -40.0, -24.0), (48.0, -13.0, 0.0), m["post"], root)
    pins = [(14.0, -8.0), (14.0, -20.0), (18.0, -14.0)]
    D.header(m, root, -20.0, -14.0, 44.0, True, pins, "s3hdr")
    for k, (y, z) in enumerate(pins):
        D.pin(f"s3_pin{k}", [(-44.0, y, z), (-6.0, y, z)], m, root, 1.1)
    wb = wire("s3_bias", (-6.0, 14.0, -8.0), cp["dfb_pad"], 4.0, m["gold"], root, 0.35)
    wr = wire("s3_rf", (-6.0, 14.0, -20.0), cp["eam_pad"], 9.0, m["gold"], root, 0.35)
    wm = wire("s3_mon", sp["pd_pad"], (-6.0, 18.0, -14.0), 3.0, m["gold"], root, 0.3)
    show(lit["dfb"], after(0, 0.3))
    show(lit["eam"], after(0, 0.3))
    fx = cp["front"][0]
    core = lens_fibre(m, root, 64.0, 80.0, 150.0, "s3")
    show(core, after(2, 0.1))
    # 1-2: the symbol arrives; bias flows; the DFB makes steady light
    pad = cp["dfb_pad"]
    bias = [(-44.0, 14.0, -8.0), (-6.0, 14.0, -8.0)] + wb[1:] + [(pad[0], cp["top"], 0.8), (pad[0], cp["bottom"] + 1.0, 0.8)]
    for b in range(3):
        stream_of(root, f"s3_bias{b}", 6, bias[0], offsets(bias), 1.0, m["elec"], b, 0.0, 0.7, 80)
    rf = [(-44.0, 14.0, -20.0), (-6.0, 14.0, -20.0)] + wr[1:]
    stream_of(root, "s3_sym", 2, rf[0], offsets(rf), 1.3, m["rf"], 0, 0.05, 0.3, 70)
    steady = empty("s3_steady", root)
    ball("s3_steady_glow", cp["front"], 1.6, m["light"], steady, 16)
    show(steady, span(0, 0.35, 1, 0.0))
    # 3: the modulator dims the light to one of four levels
    stream_of(root, "s3_rf", 6, rf[0], offsets(rf), 1.0, m["rf"], 1, 0.0, 0.7, 70)
    pam4_glow(m, root, cp["front"], (0.8, 1.5, 2.2, 3.0), 1, "s3_lvl")
    # 4: the lens couples the light into the fibre; 5: the monitor keeps the power steady
    bm = empty("s3_beam", root)
    D.cone("s3_beam_a", cp["front"], (63.0, 0, 0), 0.4, 8.0, m["beam"], bm, 32, half=True)
    D.cone("s3_beam_b", (65.0, 0, 0), (80.0, 0, 0), 8.0, 0.4, m["beam"], bm, 32, half=True)
    show(bm, after(2, 0.0))
    bk = empty("s3_back", root)
    D.cone("s3_back_c", cp["back"], (sp["pd_face"][0] + 0.1, 0, 0), 0.3, 1.8, m["beam"], bk, 24, 1.4, 1.0, half=True)
    show(bk, after(2, 0.5))
    show(sp["pd_lit"], after(2, 0.5))
    mon = wm + [(-44.0, 18.0, -14.0)]
    stream_of(root, "s3_mon_s", 5, mon[0], offsets(mon), 0.9, m["elec"], 2, 0.55, 0.9, 50)

    label("1 symbol arrives from the driver", (-10.0, 14.0, -20.0), root, beat(0))
    label("bias current into the DFB", wb[5], root, beat(0))
    label("2 DFB makes steady 1310 nm light", (12.0, 0.0, 0.0), root, [(F(0, 0.35), F(1, 0))])
    label("3 modulator absorbs part of it", cp["eam_pad"], root, beat(1))
    label("one of four brightness levels", (fx + 1.0, 3.0, 0.0), root, beat(1))
    label("data voltage", wr[6], root, beat(1))
    label("4 lens couples it into the fibre", (64.0, 9.0, 0.0), root, span(2, 0.1, 2, 0.55))
    label("fibre core", (95.0, 0.5, 0.0), root, span(2, 0.1, 2, 0.55))
    label("5 monitor photodiode", sp["pd"], root, after(2, 0.6))
    label("keeps the power steady", wm[5], root, after(2, 0.6))

    camera_path(root, [
        frame((10.0, 2.0, 0.0), 62.0, 0.38, 0.32),
        frame((30.0, 0.0, -2.0), 66.0, 0.28, 0.32),
        [(0.16, frame((70.0, 0.0, 0.0), 76.0, 0.30, 0.20)), (0.58, frame((-2.0, -1.0, -4.0), 52.0, 0.35, 0.30))],
    ])


# ---- 4 EML, VCSEL, silicon photonics ---------------------------------------------------------------

E4, V4, P4 = (-115.0, 0.0, 0.0), (-30.0, 0.0, 0.0), (60.0, -2.0, 0.0)
S4E, S4P = 0.4, 0.6


def sec4(m, root):
    box("s4_bench", (-135.0, -22.0, -30.0), (100.0, -18.0, 0.0), m["dark_steel"], root)
    # EML on its submount and carrier
    cp, lit = D.chip(m, root, E4, S4E, name="s4eml")
    D.submount(m, root, E4, S4E, name="s4emls")
    box("s4_eml_carrier", (E4[0] - 9.0, -18.0, -14.0), (E4[0] + 40.0, -26.0 * S4E, 0.0), m["post"], root)
    show(lit["dfb"], after(0, 0.0))
    show(lit["eam"], after(0, 0.0))
    D.cone("s4_eml_beam", cp["front"], (cp["front"][0] + 14.0, 0, 0), 0.3, 4.5, m["beam"], root, 32, 1.4, 1.0, half=True)
    # VCSEL
    vp, vlit, vbeam = D.vcsel(m, root, V4, 1.0, "s4vc")
    box("s4_vc_carrier", (V4[0] - 22.0, -18.0, -22.0), (V4[0] + 22.0, -14.0, 0.0), m["post"], root)
    show(vlit, after(0, 0.0))
    show(vbeam, after(0, 0.0))
    # silicon photonics: InP CW laser, silicon waveguides and modulator, fibre
    pp, paths = D.siph(m, root, P4, S4P, "s4sp")
    box("s4_sp_carrier", (P4[0] - 38.0 * 1.0, -18.0, -26.0), (P4[0] + 31.0, P4[1] - 8.0 * S4P, 0.0), m["post"], root)
    splt = empty("s4_sp_lit", root)
    for n_, pth in paths.items():
        D.polyline(f"s4_sp_lit_{n_}", pth, 0.42, m["light"], splt)
    ball("s4_sp_laser_glow", pp["laser_facet"], 1.0, m["light"], splt, 12)
    show(splt, after(0, 0.0))
    # motion: light along each one in its own beat
    stream_of(root, "s4_eml_s", 5, (E4[0] + 1.0, 0.0, 0.5), [(0, 0, 0), (49.0, 0, 0)], 0.6, m["light"], 0, 0.3, 0.9, 40)
    stream_of(root, "s4_vc_s", 5, (V4[0], 14.0, 0.5), [(0, 0, 0), (0, 25.0, 0)], 0.9, m["light"], 1, 0.05, 0.85, 30)
    for n_ in ("a", "b"):
        pth = paths["in"] + paths[n_][1:] + paths["out"][1:]
        stream_of(root, f"s4_sp_s{n_}", 4, pth[0], offsets(pth), 0.7, m["light"], 2, 0.05, 0.8, 60)

    t0 = span(0, 0.0, 0, 0.32)
    label("EML", (E4[0] + 18.0, 4.4, 0.0), root, t0)
    label("VCSEL", vp["top"], root, t0)
    label("silicon photonics", pp["chip"], root, t0)
    t1 = span(0, 0.38, 1, 0.0)
    label("EML: light leaves the chip's end", (cp["front"][0] + 3.0, 1.5, 0.0), root, t1)
    label("InP: DFB laser + modulator", (E4[0] + 18.0, -4.0, 0.0), root, t1)
    label("single-mode: DR, FR modules", (E4[0] + 30.0, -26.0 * S4E, -2.0), root, t1)
    label("VCSEL: light leaves the top", vp["beam"], root, beat(1))
    label("mirror stacks above and below", vp["dbr_top"], root, beat(1))
    label("oxide aperture shapes the beam", vp["aperture"], root, beat(1))
    label("850 nm, multimode, ~100 m", vp["sub"], root, beat(1))
    label("InP CW laser: steady light", pp["laser"], root, beat(2))
    label("silicon waveguides + modulator", pp["arm_a"], root, beat(2))
    label("grating coupler to the fibre", pp["gc"], root, beat(2))
    label("made in a silicon fab", pp["box"], root, beat(2))

    camera_path(root, [
        [(0.0, frame((-18.0, 12.0, 0.0), 190.0, 0.20, 0.30, pad=1.0)), (0.36, frame((-96.0, -2.0, 0.0), 52.0, 0.32, 0.28))],
        frame((-30.0, 8.0, 0.0), 62.0, 0.35, 0.30),
        frame((50.0, -3.0, -10.0), 64.0, 0.20, 0.62, pad=1.0),
    ])


# ---- 5 how a Mach-Zehnder modulator works -----------------------------------------------------------

AMP, WL = 2.6, 8.0
ARM_X0, ARM_X1 = -18.0, 14.0
OUT_X0, OUT_X1 = 26.0, 40.0


def flat_wave(m, parent, x0, x1, zc, amp, phase, name, y=2.4):
    """A light wave drawn lying on the chip (wiggling in z) along x0..x1."""
    n = int((x1 - x0) / 0.8)
    pts = [(x0 + (x1 - x0) * i / n, y, zc + amp * math.sin(2 * math.pi * (x0 + (x1 - x0) * i / n) / WL + phase)) for i in range(n + 1)]
    if amp < 0.05:
        pts = [(x0, y, zc), (x1, y, zc)]
    D.polyline(name, pts, 0.38, m["light"], parent)


def sec5(m, root):
    pp, paths = D.siph(m, root, (0.0, 0.0, 0.0), 1.0, "s5sp")
    lit = empty("s5_lit", root)
    for n_, pth in paths.items():
        D.polyline(f"s5_lit_{n_}", pth, 0.62, m["stripe_dim"], lit)
    ball("s5_laser_glow", pp["laser_facet"], 1.2, m["light"], lit, 12)
    show(lit, after(0, 0.08))
    for n_ in ("a", "b"):
        pth = paths["in"] + paths[n_][1:]
        stream_of(root, f"s5_split_{n_}", 5, pth[0], offsets(pth), 1.0, m["light"], 0, 0.1, 0.85, 60)
    za, zb, zc = -12.0, -28.0, -20.0
    # beat 1: both arms in step; the output wave is twice as tall
    w1 = empty("s5_inphase", root)
    flat_wave(m, w1, ARM_X0, ARM_X1, za, AMP, 0.0, "s5_wa1")
    flat_wave(m, w1, ARM_X0, ARM_X1, zb, AMP, 0.0, "s5_wb1")
    flat_wave(m, w1, OUT_X0, OUT_X1, zc, 2 * AMP, 0.0, "s5_wo1")
    ball("s5_out_bright", pp["gc"], 2.2, m["light"], w1, 16)
    show(w1, beat(1))
    # beat 2: a voltage slows arm B; the phase shift sets the output: four levels, down to dark
    wa = empty("s5_wa2", root)
    flat_wave(m, wa, ARM_X0, ARM_X1, za, AMP, 0.0, "s5_wa2w")
    show(wa, beat(2))
    for k in range(4):
        g = empty(f"s5_lvl{k}", root)
        a = k / 3.0
        phi = 2 * math.acos(a)
        flat_wave(m, g, ARM_X0, ARM_X1, zb, AMP, phi, f"s5_wb2_{k}")
        flat_wave(m, g, OUT_X0, OUT_X1, zc, 2 * AMP * a, phi / 2, f"s5_wo2_{k}")
        if k:
            ball(f"s5_out_{k}", pp["gc"], 0.7 + 0.5 * k, m["light"], g, 16)
        show(g, [(F(2, i / 8.0), F(2, (i + 1) / 8.0)) for i, s in enumerate(PAM4_SEQ) if s == k])
    sig = empty("s5_sig", root)
    box("s5_sig_lit", (-18.0, 1.4, -21.0), (14.0, 1.7, -19.0), m["rf"], sig)
    show(sig, beat(2))
    stream_of(root, "s5_rf", 5, (-15.0, 2.0, -20.0), [(0, 0, 0), (28.0, 0, 0)], 0.6, m["rf"], 2, 0.0, 0.8, 40)

    label("light in from the CW laser", pp["in"], root, beat(0))
    label("splits into two arms", pp["split"], root, beat(0))
    label("electrodes along each arm", pp["el_g"], root, beat(0))
    label("the halves recombine", pp["join"], root, beat(0))
    label("arm A wave", (0.0, 2.4, za + AMP), root, beat(1))
    label("arm B wave: in step", (0.0, 2.4, zb + AMP), root, beat(1))
    label("in phase: they add, bright", (OUT_X1, 2.4, zc + 2 * AMP), root, beat(1))
    label("voltage slows arm B", (-8.0, 1.7, -20.0), root, beat(2))
    label("out of step: cancel, dark", (OUT_X1, 2.4, zc), root, beat(2))
    label("in between: middle levels", pp["gc"], root, beat(2))

    camera_path(root, [
        frame((-10.0, 0.0, -20.0), 76.0, 0.15, 0.85, pad=1.0),
        frame((13.0, 0.0, -20.0), 74.0, 0.12, 0.95, pad=1.0),
        frame((13.0, 0.0, -20.0), 74.0, 0.12, 0.95, pad=1.0),
    ])


# ---- 6 200G per lane ---------------------------------------------------------------------------------

S6 = 0.25
LANES = [-49.0 + 14.0 * k for k in range(8)]
SC6 = 420.0  # the scope's centre (x)
LV6 = (-36.0, -12.0, 12.0, 36.0)


def sec6(m, root):
    # beat 0: a 1.6T module's eight lanes, one EML each, eight fibres out
    box("s6_sub", (-6.0, -26.0 * S6 - 2.0, -56.0), (30.0, -26.0 * S6, 56.0), m["aln"], root)
    box("s6_carrier", (-10.0, -30.0, -58.0), (36.0, -26.0 * S6 - 2.0, 58.0), m["post"], root)
    box("s6_vgroove", (40.0, -30.0, -58.0), (62.0, -2.0, 58.0), m["si"], root)
    lanes = empty("s6_lanes", root)
    for k, z in enumerate(LANES):
        cp, _ = D.chip(m, root, (0.0, 0.0, z), S6, full=True, name=f"s6c{k}")
        D.cone(f"s6_beam{k}", (cp["front"][0], 0, z), (40.0, 0, z), 0.3, 3.0, m["beam"], lanes, 24)
        tube(f"s6_fib{k}", (40.0, 0.0, z), (120.0, 0.0, z), 2.0, m["clad"], root, 16)
        tube(f"s6_core{k}", (40.0, 0.0, z), (120.0, 0.0, z), 0.6, m["light"], lanes, 8)
        stream_of(root, f"s6_s{k}", 3, (24.0, 0.0, z), [(0, 0, 0), (94.0, 0, 0)], 0.9, m["light"], 0, 0.03 * k, 0.6 + 0.03 * k, 50)
    show(lanes, beat(0))
    # beats 1-2: the scope, 100G above and 200G below; then the two eyes
    scope(m, root, SC6, "s6sc")
    top = tuple(24.0 + 7.0 * k for k in range(4))
    bot = tuple(-45.0 + 7.0 * k for k in range(4))
    seq8 = (3, 0, 2, 1, 1, 3, 0, 2)
    seq16 = (3, 0, 2, 1, 1, 3, 0, 2, 2, 1, 3, 0, 1, 2, 0, 3)
    trace(m, root, SC6 - 80.0, SC6 + 80.0, top, seq8, "s6_t100", 1)
    trace(m, root, SC6 - 80.0, SC6 + 80.0, bot, seq16, "s6_t200", 1)
    eyes = empty("s6_eyes", root)
    eye(m, eyes, SC6 - 30.0, 100.0, LV6, "s6_e100")
    eye(m, eyes, SC6 + 55.0, 50.0, LV6, "s6_e200")
    show(eyes, after(2, 0.0))
    sweep = empty("s6_sweep", root)
    tube("s6_sweep_l", (SC6 - 80.0, -54.0, 0.5), (SC6 - 80.0, 54.0, 0.5), 0.5, m["elec"], sweep, 8)
    key(sweep, F(1, 0.05), "location", P(0, 0, 0), linear=True)
    key(sweep, F(1, 0.85), "location", P(160.0, 0, 0), linear=True)
    show(sweep, span(1, 0.05, 1, 0.9))
    pulse = empty("s6_pulse", root)
    for k in range(3):
        ball(f"s6_read{k}", (SC6 + 55.0, (LV6[k] + LV6[k + 1]) / 2, 1.8), 1.2, m["elec"], pulse, 12)
    for i in range(5):
        key(pulse, F(2, i / 4.0) if i < 4 else F(3, 0) - 1, "location", P(0, 0, 0.6 * (i % 2)))
    show(pulse, after(2, 0.1))

    label("1.6T module: 8 lanes x 200G", (12.0, 2.75, LANES[7]), root, beat(0))
    label("one EML per lane", (12.0, 2.75, LANES[4]), root, beat(0))
    label("8 fibres out", (110.0, 2.0, LANES[6]), root, beat(0))
    label("100G lane", (SC6 - 80.0 + 10.0, top[3], 1.4), root, beat(1))
    label("200G lane: 2x the symbols", (SC6 - 80.0 + 5.0, bot[3], 1.4), root, beat(1))
    label("same time window", (SC6 + 60.0, 52.0, 0.5), root, beat(1))
    label("100G eye", (SC6 - 30.0, LV6[3], 0.8), root, beat(2))
    label("200G eye: half as wide", (SC6 + 55.0, LV6[3], 0.8), root, beat(2))
    label("needs ~2x the bandwidth", (SC6 + 55.0, (LV6[1] + LV6[2]) / 2, 1.8), root, beat(2))

    camera_path(root, [
        frame((50.0, 0.0, 0.0), 128.0, 0.25, 0.85, pad=1.0),
        frame((SC6 - 6.0, 0.0, 0.0), 178.0, 0.10, 0.06, pad=1.0),
        frame((SC6 + 4.0, 0.0, 0.0), 172.0, 0.12, 0.05, pad=1.0),
    ])


# ---- 7 the laser shortage ------------------------------------------------------------------------------

SP7 = (260.0, 0.0, 0.0)
IN7 = 520.0


def sec7(m, root):
    # beat 0: an InP wafer of EML dies, and one finished EML on a tray
    centres = D.wafer(m, root, (0.0, 0.0, 0.0), 45.0, m["wafer_inp"], (6.0, 3.0), "s7w")
    hot = empty("s7_hot", root)
    for i, c in enumerate(centres[:: max(1, len(centres) // 18)]):
        box(f"s7_hot{i}", (c[0] - 2.7, c[1], c[2] - 1.2), (c[0] + 2.7, c[1] + 0.6, c[2] + 1.2), m["hot"], hot)
    for i in range(7):
        key(hot, F(0, i / 6.0) if i < 6 else F(3, 0) - 1, "location", P(0, 0.4 * (i % 2), 0))
    box("s7_tray", (58.0, -3.0, -16.0), (98.0, 0.0, 16.0), m["tray"], root)
    D.chip(m, root, (64.0, 6.0, 0.0), 0.3, full=True, name="s7eml")
    # beat 1: the alternative: CW laser + silicon modulator; the laser is still InP
    pp, paths = D.siph(m, root, SP7, 0.7, "s7sp")
    box("s7_sp_carrier", (SP7[0] - 45.0, -16.0, -30.0), (SP7[0] + 37.0, -8.0 * 0.7, 0.0), m["post"], root)
    halo = empty("s7_halo", root)
    box("s7_halo_b", (SP7[0] - 62.0 * 0.7 - 1.5, -2.5, -26.0 * 0.7 - 1.5), (SP7[0] - 50.0 * 0.7 + 1.5, 5.0, -14.0 * 0.7 + 1.5), m["halo"], halo)
    show(halo, after(1, 0.1))
    lt = empty("s7_sp_lit", root)
    for n_, pth in paths.items():
        D.polyline(f"s7_lit_{n_}", pth, 0.45, m["light"], lt)
    show(lt, after(1, 0.0))
    # beat 2: indium: an ingot and the share of world supply (one report: ~70 % China)
    ing = K.bevel(box("s7_ingot", (IN7 - 30.0, 0.0, -10.0), (IN7 + 10.0, 10.0, 10.0), m["indium"], root), 2.0)
    box("s7_ingot_base", (IN7 - 36.0, -3.0, -16.0), (IN7 + 16.0, 0.0, 16.0), m["tray"], root)
    pie = (IN7 + 60.0, 0.0, 0.0)
    cn = empty("s7_pie_cn_lift", root)
    D.wedge("s7_pie_cn", pie, 30.0, 6.0, 0.0, 2 * math.pi * 0.7, m["pie_cn"], cn)
    for i in range(5):
        key(cn, F(2, i / 4.0) if i < 4 else F(3, 0) - 1, "location", P(0, 2.0 * (i % 2), 0))
    D.wedge("s7_pie_rest", pie, 30.0, 4.0, 2 * math.pi * 0.7, 2 * math.pi, m["pie_rest"], root)
    del ing
    # the InP crystal grown with that indium (plus phosphorus), and wafers sliced off it
    D.rod("s7_boule", (IN7 - 30.0, 9.0, -34.0), (IN7 + 2.0, 9.0, -34.0), 9.0, m["wafer_inp"], root, False, 48)
    D.cone("s7_boule_tip", (IN7 - 30.0, 9.0, -34.0), (IN7 - 38.0, 9.0, -34.0), 9.0, 2.0, m["wafer_inp"], root, 48)
    for k in range(4):
        x = IN7 + 6.0 + 3.0 * k
        D.rod(f"s7_slice{k}", (x, 9.0, -34.0), (x + 0.8, 9.0, -34.0), 9.0, m["wafer_inp"], root, False, 48)
    box("s7_boule_base", (IN7 - 40.0, -3.0, -46.0), (IN7 + 22.0, 0.0, -22.0), m["tray"], root)

    label("InP wafer of EML dies", (-30.0, 0.3, 25.0), root, beat(0))
    label("EML capacity locked up", (0.0, 0.6, 0.0), root, beat(0))
    label("lead times beyond 2027", (78.0, 3.3, 0.0), root, beat(0))
    label("alternative: CW laser + silicon", pp["chip"], root, beat(1))
    label("the CW laser is still InP", (SP7[0] - 56.0 * 0.7, 5.0, -20.0 * 0.7), root, beat(1))
    label("silicon modulator", pp["arm_a"], root, beat(1))
    label("indium: the In in InP", (IN7 - 10.0, 10.0, 0.0), root, beat(2))
    label("China: ~70% (one report)", (pie[0] - 4.0, 6.0, -16.0), root, beat(2))
    label("InP crystal, sliced into wafers", (IN7 - 14.0, 18.0, -34.0), root, beat(2))
    label("rest of the world", (pie[0] + 12.0, 4.0, 16.0), root, beat(2))

    camera_path(root, [
        frame((36.0, 0.0, 0.0), 136.0, 0.18, 0.80, pad=1.0),
        frame((SP7[0] - 4.0, 4.0, -10.0), 76.0, 0.22, 0.62),
        frame((IN7 + 28.0, 2.0, 0.0), 124.0, 0.20, 0.62, pad=1.0),
    ])


# ---- 8 who makes it --------------------------------------------------------------------------------------

EML_MAKERS = ("Lumentum (LITE)", "Coherent (COHR)", "Mitsubishi Electric", "Sumitomo", "Broadcom (AVGO)")
VC8, SW8 = 320.0, 640.0


def vcsel_die(m, root, x, name):
    box(f"{name}_die", (x - 16.0, -3.0, -8.0), (x + 16.0, 0.0, 8.0), m["gaas"], root)
    for k in range(4):
        cx = x - 10.5 + 7.0 * k
        tube(f"{name}_mesa{k}", (cx, 0.0, 0.0), (cx, 2.0, 0.0), 2.4, m["dbr_a"], root, 24)
        D.pipe_y(f"{name}_ring{k}", 2.0, 2.4, 2.4, 1.0, m["gold"], root, cx=cx, half=False, verts=24)
        tube(f"{name}_ap{k}", (cx, 2.0, 0.0), (cx, 2.5, 0.0), 1.0, m["stripe"], root, 16)
        D.cone(f"{name}_beam{k}", (cx, 2.5, 0.0), (cx, 12.0, 0.0), 1.0, 2.6, m["beam"], root, 16)
        box(f"{name}_pad{k}", (cx - 2.0, 0.0, 3.5), (cx + 2.0, 0.3, 6.5), m["gold"], root)


def sec8(m, root):
    # beat 0: a tray of EML chips, one per maker
    box("s8_tray", (-80.0, -4.0, -36.0), (80.0, 0.0, 36.0), m["tray"], root)
    spots = ((-50.0, -16.0), (0.0, -16.0), (50.0, -16.0), (-25.0, 18.0), (25.0, 18.0))
    for i, (name, (x, z)) in enumerate(zip(EML_MAKERS, spots)):
        box(f"s8_pocket{i}", (x - 23.0, -0.2, z - 12.0), (x + 23.0, 0.05, z + 12.0), m["dark_steel"], root)
        cp, lit = D.chip(m, root, (x - 18.0, 8.0, z), 0.4, full=True, name=f"s8eml{i}")
        show(lit["dfb"], [(F(0, 0.1 + 0.15 * i), F(1, 0))])
        label(name, (x - 4.0, cp["top"], z - 2.0), root, beat(0))
    # beat 1: VCSEL array dies
    for i, x in enumerate((VC8 - 40.0, VC8, VC8 + 40.0)):
        vcsel_die(m, root, x, f"s8vc{i}")
    for i, name in enumerate(("Coherent", "Broadcom", "Lumentum")):
        label(name, (VC8 - 40.0 + 40.0 * i, 0.0, 8.0), root, beat(1))
    label("VCSEL arrays: light out the top", (VC8 + 3.5, 2.5, 0.0), root, beat(1))
    stream_of(root, "s8_vc_s", 4, (VC8 - 3.5, 2.5, 0.0), [(0, 0, 0), (0, 14.0, 0)], 0.8, m["light"], 1, 0.05, 0.85, 30)
    # beat 2: a silicon-photonics wafer
    D.wafer(m, root, (SW8, 0.0, 0.0), 75.0, m["wafer_si"], (12.0, 9.0), "s8sw", pad=m["si_wg"])
    label("silicon-photonics wafer", (SW8 - 50.0, 0.3, 40.0), root, beat(2))
    label("design: Intel, Cisco, Broadcom, Marvell", (SW8, 0.3, 0.0), root, beat(2))
    label("foundries: TSMC, GlobalFoundries, Tower (TSEM)", (SW8 + 30.0, 0.3, -40.0), root, beat(2))

    camera_path(root, [
        frame((0.0, 0.0, 0.0), 150.0, 0.12, 0.78, pad=1.0),
        frame((VC8 + 2.0, 5.0, 0.0), 98.0, 0.15, 0.55, pad=1.0),
        frame((SW8, 0.0, 0.0), 168.0, 0.12, 0.88, pad=1.0),
    ])


# ---- 9 chokepoints and risks ----------------------------------------------------------------------------

R9 = 420.0  # the two routes
C9 = 820.0  # the CPO package


def sec9(m, root):
    # beat 0: a small InP wafer laid on a 300 mm silicon wafer
    D.wafer(m, root, (0.0, 0.0, 0.0), 150.0, m["wafer_si"], (24.0, 20.0), "s9si")
    D.wafer(m, root, (40.0, 3.0, 40.0), 45.0, m["wafer_inp"], (6.0, 3.0), "s9inp")
    gp = empty("s9_inp_glow", root, P(40.0, 0.0, 40.0))  # a glowing rim round the InP wafer, pulsing
    D.pipe_y("s9_inp_ring", 1.5, 3.6, 47.5, 45.2, m["hot"], gp, cx=0.0, half=False, verts=96)
    for i in range(7):
        key(gp, F(0, i / 6.0) if i < 6 else F(3, 0) - 1, "scale", (1.0, 1.0, 1.0 + 0.5 * (i % 2)))
    # beat 1: both single-mode routes; their InP parts glow
    cp, lit = D.chip(m, root, (R9, 0.0, 0.0), 0.4, name="s9eml")
    D.submount(m, root, (R9, 0.0, 0.0), 0.4, name="s9emls", pd=False)
    show(lit["dfb"], after(1, 0.0))
    show(lit["eam"], after(1, 0.0))
    halo = empty("s9_halo", root)
    box("s9_halo_eml", (R9 - 1.5, -8.6, -10.0), (R9 + 37.5, 5.4, 0.5), m["halo"], halo)
    pp, paths = D.siph(m, root, (R9 + 110.0, 0.0, 0.0), 0.6, "s9sp")
    box("s9_halo_cw", (R9 + 110.0 - 62.0 * 0.6 - 1.5, -1.5, -26.0 * 0.6 - 1.5), (R9 + 110.0 - 50.0 * 0.6 + 1.5, 4.0, -14.0 * 0.6 + 1.5), m["halo"], halo)
    show(halo, after(1, 0.15))
    box("s9_bench", (R9 - 12.0, -14.0, -26.0), (R9 + 145.0, -10.4, 0.0), m["dark_steel"], root)
    box("s9_sp_carrier", (R9 + 110.0 - 38.0, -10.4, -26.0), (R9 + 110.0 + 31.0, -4.8, 0.0), m["post"], root)
    box("s9_eml_carrier", (R9 - 8.0, -10.4, -12.0), (R9 + 38.0, -26.0 * 0.4, 0.0), m["post"], root)
    # beat 2: a CPO package; one of its lasers fails
    box("s9_sub", (C9 - 62.0, -4.0, -62.0), (C9 + 62.0, 0.0, 62.0), m["substrate"], root)
    box("s9_asic", (C9 - 24.0, 0.0, -24.0), (C9 + 24.0, 4.0, 24.0), m["die"], root)
    oes = [(C9 - 44.0, -16.0, "x"), (C9 - 44.0, 16.0, "x"), (C9 + 44.0, -16.0, "x"), (C9 + 44.0, 16.0, "x"),
           (C9 - 16.0, -44.0, "z"), (C9 + 16.0, -44.0, "z"), (C9 - 16.0, 44.0, "z"), (C9 + 16.0, 44.0, "z")]
    fail_i = 7
    for i, (x, z, ax) in enumerate(oes):
        hx, hz = (6.0, 9.0) if ax == "x" else (9.0, 6.0)
        box(f"s9_oe{i}", (x - hx, 0.0, z - hz), (x + hx, 3.0, z + hz), m["oe"], root)
        box(f"s9_las{i}", (x - 2.0, 3.0, z - 2.0), (x + 2.0, 5.0, z + 2.0), m["inp"], root)
        g = empty(f"s9_las{i}_on", root)
        ball(f"s9_las{i}_glow", (x, 5.2, z), 1.4, m["light"], g, 12)
        dx, dz = (1.0 if x > C9 else -1.0, 0.0) if ax == "x" else (0.0, 1.0 if z > 0 else -1.0)
        for f in (-1, 1):
            o = (x + dx * hx + (f * 3.0 if ax == "z" else 0.0), 1.5, z + dz * hz + (f * 3.0 if ax == "x" else 0.0))
            tube(f"s9_fib{i}_{f}", o, (o[0] + dx * 30.0, 1.5, o[2] + dz * 30.0), 0.9, m["clad"], root, 12)
            # light pulses leave down every fibre; the failed engine's stop when its laser dies
            u1 = 0.42 if i == fail_i else 0.95
            stream_of(root, f"s9_puls{i}_{f}", 5, (o[0], 2.6, o[2]), [(0, 0, 0), (dx * 30.0, 0, dz * 30.0)],
                      0.8, m["light"], 2, 0.0, u1, 40)
        if i == fail_i:
            show(g, span(0, 0.0, 2, 0.45))
            bad = empty("s9_fail", root)
            ball("s9_fail_b", (x, 5.2, z), 2.6, m["fail"], bad, 16)
            ball("s9_fail_halo", (x, 5.2, z), 6.0, m["fail_halo"], bad, 20)
            show(bad, after(2, 0.45))
        else:
            show(g, after(0, 0.0))

    label("300 mm silicon wafer", (-110.0, 0.3, -40.0), root, beat(0))
    label("InP wafer: far smaller", (40.0, 3.3, 40.0), root, beat(0))
    label("EML capacity: small, slow to add", (70.0, 3.3, 70.0), root, beat(0))
    label("EML: InP", (R9 + 18.0, 5.0, -2.0), root, beat(1))
    label("CW laser for silicon: InP too", (R9 + 110.0 - 56.0 * 0.6, 4.0, -20.0 * 0.6), root, beat(1))
    label("every route needs InP lasers", (R9 + 60.0, -12.0, 0.0), root, beat(1))
    label("switch ASIC", (C9, 4.0, 0.0), root, beat(2))
    label("optical engines with lasers", (C9 - 44.0, 3.0, 16.0), root, beat(2))
    label("its fibres go dark", (oes[fail_i][0], 1.5, oes[fail_i][1] + 24.0), root, after(2, 0.5))
    label("a laser fails inside", (oes[fail_i][0], 6.0, oes[fail_i][1]), root, after(2, 0.45))

    camera_path(root, [
        frame((10.0, 0.0, 10.0), 300.0, 0.15, 0.80, pad=1.0),
        frame((R9 + 62.0, -2.0, -8.0), 136.0, 0.12, 0.50, pad=1.0),
        frame((C9 + 4.0, 0.0, 14.0), 168.0, 0.25, 0.80, pad=1.0),
    ])


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}


def build(n):
    m, root = setup(f"section_{n}")
    SECTIONS[n](m, root)
    finish(f"section_{n}", page=PAGE)


if __name__ == "__main__":
    build(int(sys.argv[sys.argv.index("--") + 1]))

"""The five zoom-ins (a-e) of the PAM4 DSP overview. Each is its own three-beat scene built from the
detailed cut-away parts in fiber_dsp_detail.py, with the camera framed per beat and tags pinned to
the parts (the old version froze the overview's frames instead).

  a  lid and fins        the lid on the package; it lifts, leaving the paste; up, its fins and plate
  b  the die             the die face down under the raised lid; its floor plan, face up; on its bumps
  c  PAM4 ladder         a scope's four Gray-coded levels: the top level, the bottom, a middle one
  d  electrical data in  a host lane's differential pair; symbols ride it; they climb into the die
  e  heat off the fins   the die and lid hot; heat rises off the fins; cool air through the gaps

Run one zoom per Blender process (the scene resets on each start):

    blender -b --factory-startup --python tools/pbr3d/blender/fiber_dsp_zooms.py -- a

Writes assets/fiber_dsp_zoom_<letter>.glb. The captions are in
tui/src/screens/diagrams_nodes/fiber/dsp/zooms.rs.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, P, ball, box, key, label, tube  # noqa: E402
from sand_zooms import start, finish, stream_of  # noqa: E402
from pbr_kit import empty  # noqa: E402
import fiber_dsp_detail as D  # noqa: E402
from fiber_dsp_detail import (  # noqa: E402
    BEOL_Y1, BOARD_Y1, DIE, DIE_Y0, DIE_Y1, FIN_Y1, LID_Y1, TIM_Y1, frame, glide, lbox,
)
import fiber_dsp_sections as S  # noqa: E402
from fiber_dsp_sections import (  # noqa: E402
    IN_BALL_X, IN_BUMP_X, IN_X1, LEVELS, SCOPE_X0, SCOPE_X1, group, span, tags,
)

PAGE = "fiber_dsp"
BEATS = 3
SCALE = 4.0
LID_UP = 9.0


def zoom_a(m, root):
    """a lid and fins: the lid on; it lifts off; up, with its fins on the plate."""
    D.board(m, root)
    G = D.package(m, root, quad=False)
    lid = G["lid"]
    key(lid, F(1, 0.10), "location", P(0, 0, 0))
    key(lid, F(1, 0.45), "location", P(0, LID_UP, 0))
    for k, z in enumerate((-1.1, -5.5, -9.9)):
        D.run(root, f"air{k}", [(18.0, LID_UP + 2.4, z), (-18.0, LID_UP + 2.4, z)], 4, 0.4, m["air"], 2,
              0.05 + 0.05 * k, 0.6 + 0.05 * k, 60)
    tags(root, [
        (0, "metal lid, cut open", (10, -0.55, 0)),
        (0, "fins on the lid", (-6, FIN_Y1, 8)),
        (0, "skirt on a sealant bead", (13.5, -3.0, 0)),
        (1, "lid lifts off", (10, LID_UP - 0.55, 0)),
        (1, "paste stays on the die", (5, TIM_Y1 - 0.15, 0)),
        (2, "fins stand on the plate", (-4, LID_Y1 + LID_UP + 4.0, -6.6)),
        (2, "plate spreads the heat", (10, LID_UP - 0.55, 0)),
    ])
    return [
        frame((-14, -7.5, -12), (14, FIN_Y1, 12), 0.60, 0.35),
        frame((-2, -5, -4), (14, FIN_Y1 + LID_UP, 12), 0.65, 0.25, fill=0.92),
        frame((-14, LID_Y1 + LID_UP - 2, -12), (14, FIN_Y1 + LID_UP, 12), 0.75, 0.30, fill=0.95),
    ]


PLAN_X = 40.0


def zoom_b(m, root):
    """b the die: face down in the package under the raised lid; its floor plan face up beside it;
    then a close look at it sitting on its bumps."""
    D.board(m, root, x1=52.0)
    G = D.package(m, root, quad=False)
    G["lid"].location = P(0, LID_UP, 0)
    S.die_glow(m, group("die_on", G["die"], span(0, 1)), "lit_rx")
    pe = empty("plan_at", root)
    pe.location = P(PLAN_X, BOARD_Y1 + 1.6, 0)
    S.die_plan(m, pe)
    lit = group("plan_lit", pe, span(1, 2))
    S.glow("p_tx", -5.2, -6.4, 5.2, -0.6, m["lit_tx"], lit)
    S.glow("p_rx", -5.2, 0.6, 5.2, 6.4, m["lit_rx"], lit)
    for k in range(3):
        z = -5.0 + 1.6 * k
        D.run(pe, f"ptx{k}", [(-7.0, 0.7, z), (7.0, 0.7, z)], 3, 0.35, m["path"], 1, 0.05 + 0.04 * k, 0.6, 70)
        D.run(pe, f"prx{k}", [(7.0, 0.7, -z), (-7.0, 0.7, -z)], 3, 0.35, m["noise"], 1, 0.08 + 0.04 * k, 0.65, 70)
    for k, x in enumerate((1.8, 4.2, 6.6)):
        D.run(root, f"bump{k}", [(x, -3.9, 0.35), (x, DIE_Y0 + 0.1, 0.35)], 2, 0.22, m["path"], 2,
              0.05 + 0.1 * k, 0.6 + 0.1 * k, 30)
    px, py = PLAN_X, BOARD_Y1 + 1.6
    tags(root, [
        (0, "the die, face down", (4, -2.2, 0)),
        (0, "its circuits: the metal stack", (2, -2.95, 0)),
        (0, "lid raised above", (8, LID_UP - 0.5, 0)),
        (1, "SerDes lanes down both edges", (px - 6.6, py + 0.3, 5.0)),
        (1, "transmit: PAM4 + FEC encode", (px, py + 0.3, -3.5)),
        (1, "receive: equaliser + FEC decode", (px, py + 0.3, 3.5)),
        (2, "C4 bumps under the die", (3.0, -3.5, 0)),
        (2, "underfill round them", (7.5, -3.5, 0)),
        (2, "substrate: copper + vias", (7.5, -4.9, 0)),
    ])
    return [
        frame((-2, -6, -2), (14, -1, 13), 0.65, 0.35, fill=0.95),
        frame((px - 9, py - 1.6, -8), (px + 9, py + 0.4, 8), 0.25, 0.95),
        frame((0, -7.2, 0), (12, -1.5, 1), 0.45, 0.32, fill=0.95),
    ]


def zoom_c(m, root):
    """c PAM4 ladder: four Gray-coded levels on a scope; each beat lights one level and a dot runs
    along it: the top (10), the bottom (00), a middle one (11)."""
    S.scope(m, root, SCOPE_X0, SCOPE_X1)
    for name, y in LEVELS.items():
        tube(f"rung_{name}", (SCOPE_X0 + 0.5, y, -0.9), (SCOPE_X1 - 0.5, y, -0.9), 0.22, m["rung"], root, 10)
    for b, name in enumerate(("10", "00", "11")):
        y = LEVELS[name]
        g = group(f"lit{b}", root, span(b, b + 1))
        tube(f"glow{b}", (SCOPE_X0 + 0.5, y, -0.9), (SCOPE_X1 - 0.5, y, -0.9), 0.45, m["hl"], g, 12)
        D.run(root, f"dot{b}", [(SCOPE_X0 + 1, y, -0.3), (SCOPE_X1 - 1, y, -0.3)], 3, 0.7, m["path"], b,
              0.02, 0.5, 90)
    x = SCOPE_X0 + 1
    tags(root, [
        (0, "top level: 10", (x, LEVELS["10"], -0.9)),
        (0, "Gray code: next levels differ by 1 bit", (x + 16, LEVELS["11"], -0.9)),
        (1, "bottom level: 00", (x, LEVELS["00"], -0.9)),
        (1, "lowest voltage", (x + 16, LEVELS["00"], -0.9)),
        (2, "middle level: 11", (x, LEVELS["11"], -0.9)),
        (2, "levels 1/3 as far apart as NRZ's", (x + 16, (LEVELS["01"] + LEVELS["11"]) / 2, -0.9)),
    ])
    return [
        frame((SCOPE_X0 - 1, 3, -1), (SCOPE_X1 + 1, 14, 0), 0.15, 0.20, fill=0.95),
        frame((SCOPE_X0 - 1, -3.8, -1), (SCOPE_X1 + 1, 8, 0), 0.15, 0.05, fill=0.95),
        frame((SCOPE_X0 - 1, -3.8, -1), (SCOPE_X1 + 1, 14.3, 0), 0.10, 0.10, fill=0.98),
    ]


def zoom_d(m, root):
    """d electrical data in: the host lane as a differential pair on the board; blurred symbols ride
    it; they climb the ball, via and bump into the die."""
    S.tx_path(m, root)
    y = BOARD_Y1
    pair = [(IN_X1, y + 0.4, 0.3), (IN_BALL_X + 0.3, y + 0.4, 0.3)]
    pair_n = [(IN_X1, y + 0.4, 1.3), (IN_BALL_X + 1.3, y + 0.4, 1.3)]
    for b in (1, 2):
        D.run(root, f"p{b}", pair, 5, 0.42, m["noise"], b, 0.0, 0.5, 70)
        D.run(root, f"n{b}", pair_n, 5, 0.42, m["noise"], b, 0.03, 0.53, 70)
    up = [(IN_BALL_X, y + 0.4, 0.4), (IN_BALL_X, -4.1, 0.4), (IN_BUMP_X, -4.1, 0.4), (IN_BUMP_X, -2.9, 0.4)]
    D.run(root, "up", up, 5, 0.35, m["path"], 2, 0.2, 0.8, 50)
    lit = group("in_lit", root, span(2, 3))
    S.overlay("lit_via", (IN_BALL_X - 0.3, -5.9, 0.28), (IN_BALL_X + 0.3, -3.9, 0.34), m, lit)
    S.overlay("lit_sub", (IN_BUMP_X, -4.22, 0.02), (IN_BALL_X, -4.06, 0.08), m, lit)
    lbox("die_lit", (DIE[0] - 0.08, DIE_Y0 - 0.02, DIE[1] - 0.08), (DIE[2] + 0.08, BEOL_Y1, DIE[3] + 0.08),
         m["path"], lit, None, 0.08)
    tags(root, [
        (0, "host lane: a differential pair", (30, y + 0.2, 1.0)),
        (0, "host lane enters here", (IN_X1, y + 0.2, 0.3)),
        (0, "BGA ball under the package", (IN_BALL_X, -6.45, 0.4)),
        (1, "blurred PAM4 symbols", (26, y + 0.6, 0.3)),
        (1, "equal and opposite", (24, y + 0.6, 1.3)),
        (2, "up a via", (IN_BALL_X, -5.0, 0.3)),
        (2, "into the die by a bump", (IN_BUMP_X, -3.5, 0.3)),
    ])
    return [
        frame((-2, -10, -2), (IN_X1 + 1, LID_Y1, 3), 0.45, 0.40, fill=0.95),
        frame((10, -8, -1), (IN_X1 + 1, -5, 3), 0.40, 0.35, fill=0.95),
        frame((0, -7.5, 0), (15, -1.5, 1), 0.35, 0.18, fill=0.95),
    ]


def zoom_e(m, root):
    """e heat off the fins: the die, paste, lid and fins glow; heat rises; air runs through the gaps."""
    D.board(m, root)
    G = D.package(m, root, quad=False)
    del G
    o = 0.05
    dx0, dz0, dx1, dz1 = DIE
    hot = empty("hot", root)
    lbox("hot_die", (dx0 - o, DIE_Y0 - o, dz0 - o), (dx1 + o, DIE_Y1 + o, dz1 + o), m["heat"], hot, None, o)
    lbox("hot_tim", (dx0 + 0.15, DIE_Y1, dz0 + 0.15), (dx1 - 0.15, TIM_Y1 + o, dz1 - 0.15), m["heat"], hot, None, o)
    lx0, lz0, lx1, lz1 = D.LID
    lbox("hot_plate", (lx0 - o, TIM_Y1, lz0 - o), (lx1 + o, LID_Y1 + o, lz1 + o), m["heat"], hot, None, o)
    for k, z in enumerate(D.FIN_ZS):
        lbox(f"hot_fin{k}", (lx0 + 0.55, LID_Y1, z - D.FIN_T / 2 - o), (lx1 - 0.55, FIN_Y1 + o, z + D.FIN_T / 2 + o),
             m["heat"], hot, None, o)
    spots = ((-9.0, -6.6), (-4.0, -2.2), (3.0, -4.4), (8.0, -8.8), (-6.0, 4.4), (-2.0, 8.8))
    for b, (n, rise) in enumerate(((1, 5.0), (3, 9.0), (3, 14.0))):
        for k, (dx, dz) in enumerate(spots):
            stream_of(root, f"puff{b}_{k}", n, (dx, FIN_Y1 + 0.3, dz), [(0, 0, 0), (dx * 0.2, rise, dz * 0.1)], 0.8,
                      m["heat"], b, 0.03 + 0.05 * k, 0.55 + 0.05 * k, 70)
    for k, z in enumerate((-1.1, -3.3, -5.5, -7.7, -9.9)):
        D.run(root, f"air{k}", [(18.0, 2.4, z), (-18.0, 2.4, z)], 3, 0.4, m["air"], 2, 0.05 + 0.04 * k, 0.6, 60)
    tags(root, [
        (0, "heat made in the die", (5, -2.95, 0)),
        (0, "through paste into the lid", (6, TIM_Y1 - 0.1, 0)),
        (0, "heat off the fins", (-6, FIN_Y1, 6.6)),
        (1, "heat rising", (0, FIN_Y1 + 7, 0)),
        (1, "fins: more surface", (-10, FIN_Y1, 6.6)),
        (2, "air carries it away", (14, 2.4, -5.5)),
        (2, "into the air above", (0, FIN_Y1 + 12, 0)),
    ])
    return [
        frame((-14, -7.5, -12), (14, FIN_Y1 + 3, 12), 0.55, 0.35, fill=0.95),
        frame((-14, -4, -12), (14, FIN_Y1 + 10, 12), 0.55, 0.30, fill=0.95),
        frame((-16, -4, -12), (18, FIN_Y1 + 15, 12), 0.80, 0.25, fill=0.95),
    ]


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}


def build(letter):
    name = f"zoom_{letter}"
    _, root = start(name, beats=BEATS, page=PAGE)
    m = D.materials()
    poses = ZOOMS[letter](m, root)
    glide(root, poses)
    root.scale = (SCALE, SCALE, SCALE)
    return name


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in ZOOMS:
        raise SystemExit("usage: blender -b --python fiber_dsp_zooms.py -- <a|b|c|d|e>")
    finish(build(argv[0]), page=PAGE)

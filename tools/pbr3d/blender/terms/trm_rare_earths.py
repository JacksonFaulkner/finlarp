"""TRM_RARE_EARTHS: the Terms-tab overview for rare earth magnets, built with the kit_supply parts.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_rare_earths.py

Writes assets/term_TRM_RARE_EARTHS.glb. Captions live in specs/terms/TRM_RARE_EARTHS.json (same beat count).

A fan row and a motor cut-away sit in a plant yard; the bench holds a sintered NdFeB magnet cut open
to a slice of grains, each grain a magnetic domain drawn as an arrow. A field aligns them, and the
process line (ore, tanks, magnet press) runs beads of material from mine to magnet.

Beats:
  0 motors    magnet rotors in fans and robot joints, spinning
  1 grains    a cut slice of NdFeB: each grain a tiny magnet, domains pointing every which way
  2 align     in a strong field the domains line up and add their pull
  3 process   ore to tanks to a magnet press, material beads flowing through the pipes
  4 supply    China does most of the chain; export limits and lead times reach the motors
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_supply as K  # noqa: E402
from term_common import F, bx, empty, show, spin  # noqa: E402
from power_vrm_detail import frame, run  # noqa: E402

SLUG = "TRM_RARE_EARTHS"
BEATS = [
    ("Rare earth magnets turn the fans and motors in AI racks",
     "Rare earths are 17 metallic elements, neodymium and dysprosium among them. Their permanent magnets spin the "
     "cooling fans in servers, the drives in storage, and the motors in robots and vehicles. Neodymium-iron-boron "
     "(NdFeB) is the strongest common type, so a small magnet gives a lot of turning force."),
    ("Inside a magnet: grains, each one a tiny magnetic domain",
     "A sintered NdFeB magnet is packed with fine grains, and each grain acts as a small magnet with its own north "
     "and south pole. Left alone, the grains point every which way and their fields cancel out. The alloy keeps "
     "the order it is given, which is why these magnets stay strong at room temperature."),
    ("Pressed in a field, the grains line up and lock in",
     "During manufacturing the powder is pressed in a strong magnetic field, so the grains turn to point the same "
     "way. Sintering then locks that order in place. A grain pointing the wrong way adds nothing to the field, so "
     "alignment decides how strong the finished magnet is."),
    ("Mined, separated and pressed into magnets in a chain of steps",
     "Ore is mined, then the rare earths are separated from one another and refined into metal and alloy. The "
     "alloy is milled to powder, pressed in a field and sintered into a magnet. Each separation step is hard "
     "chemistry, which is why so few plants can do it."),
    ("China handles most of the chain, so export limits reach the motors",
     "China does most of the mining, nearly all separation and most magnet making, and it has put export controls "
     "on rare earths. Magnet supply sets the cost and lead time of motors and actuators in data center and factory "
     "equipment. Related: MP Materials (MP), Lynas Rare Earths (LYC.AX), Neo Performance Materials (NEO.TO)."),
]

# the cut-open magnet on the bench (x 150..248)
BX0, BX1 = 160.0, 236.0
BY0, BY1 = 0.5, 36.0
BZ = -20.0
NX, NY = 6, 5

# the plant yard, behind the bench
MOTORS = [(-60.0, 0.0, -100.0), (-20.0, 0.0, -100.0), (20.0, 0.0, -100.0)]
ROCK = (-130.0, 0.0, -40.0)
TANKS = [(-95.0, 0.0, -40.0), (-60.0, 0.0, -40.0)]
PRESS = (-30.0, 8.0, -40.0)
PIPES = [
    [(-118.0, 6.0, -40.0), (-105.0, 8.0, -40.0)],
    [(-85.0, 8.0, -40.0), (-70.0, 8.0, -40.0)],
    [(-50.0, 8.0, -40.0), (-35.0, 8.0, -40.0)],
]


def block(m, root):
    """A cut slice of the magnet: NX x NY grains, each a box with a domain arrow. Returns the random
    and the aligned arrow groups (shown in turn)."""
    g = empty("nd_block", root)
    bx("nd_frame", (BX0 - 3.0, 0.0, BZ - 4.0), (BX1 + 3.0, BY1 + 2.0, BZ - 2.6), m["sup_ndfeb"], g)
    gw, gh = (BX1 - BX0) / NX, (BY1 - BY0) / NY
    rand, aligned = [], []
    for i in range(NX):
        for j in range(NY):
            c = (BX0 + gw * (i + 0.5), BY0 + gh * (j + 0.5), BZ)
            bx(f"grain{i}_{j}", (c[0] - gw / 2 + 0.4, c[1] - gh / 2 + 0.4, BZ - 1.5),
               (c[0] + gw / 2 - 0.4, c[1] + gh / 2 - 0.4, BZ + 1.5), m["sup_ndfeb"], g)
            th = 2.4 * (i * NY + j)
            rx, ry = math.cos(th), math.sin(th)
            n = math.hypot(rx, ry)
            rand.append((c, (rx / n, ry / n, 0.0)))
            aligned.append((c, (0.0, 1.0, 0.0)))
    rand_g = K.arrows(m, root, "dom_rand", rand, gw * 0.6, "sup_arrow_dn")
    align_g = K.arrows(m, root, "dom_align", aligned, gw * 0.6, "sup_arrow_up")
    return rand_g, align_g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    bx("bench", (140.0, -3.0, -50.0), (250.0, 0.0, 10.0), m["sup_steel"], root)
    bx("yard", (-170.0, -3.0, -130.0), (90.0, 0.0, -20.0), m["sup_steel"], root)

    # beat 0: motors in the yard
    rotors, motor_pts = [], []
    for k, c in enumerate(MOTORS):
        _, rot, pts = K.motor(m, root, f"fan{k}", c, 14.0, 22.0, poles=8)
        rotors.append(rot)
        motor_pts.append(pts)
    spin(rotors[0], [0], turns=1.0)
    spin(rotors[1], [0], turns=-1.0)
    spin(rotors[2], [0], turns=1.0)

    # the rock, tanks and press for beat 3
    K.rock_pile(m, root, "ore", ROCK, 14.0)
    tank_pts = []
    for k, c in enumerate(TANKS):
        _, pts = K.tank(m, root, f"tank{k}", c, 10.0, 24.0)
        tank_pts.append(pts)
    K.magnet(m, root, "press", PRESS, (10.0, 10.0, 10.0), "n")
    for k, p in enumerate(PIPES):
        K.pipe(m, root, f"pipe{k}", p, 1.6, "sup_steel")

    # the block on the bench: grains, then domains
    nd_g = empty("nd_holder", root)
    rand_g, align_g = block(m, nd_g)
    show(nd_g, [(F(1, 0), F(5, 0))])
    show(rand_g, [(F(1, 0), F(2, 0))])
    show(align_g, [(F(2, 0.1), F(5, 0))])
    field = K.ring(m, root, "field", (199.0, 18.0, BZ), 110.0, 0.25, "field", "y", 36)
    show(field, [(F(2, 0.2), F(3, 0))])

    # beat 3: beads through the process line
    for k, p in enumerate(PIPES):
        run(root, f"flow{k}", p, 3, 1.0, m["sup_flow"], [3], 0.0, 0.7, 40)

    # beat 4: the motors turn again
    spin(rotors[0], [4], turns=1.0)
    spin(rotors[1], [4], turns=-1.0)

    tags = {
        0: [("fan rotor: magnets in a ring", motor_pts[0]["top"]), ("robot and drive motors", motor_pts[1]["top"]),
            ("NdFeB: strongest common type", motor_pts[2]["top"])],
        1: [("grain: a tiny magnet", (BX0 + 5.0, BY0 + 6.0, BZ)), ("arrows: magnetic domains", (BX1 - 5.0, BY1, BZ)),
            ("neodymium-iron-boron", (199.0, BY1 + 3.0, BZ))],
        2: [("pressed in a field", (199.0, 18.0, BZ + 40.0)), ("domains line up", (199.0, 18.0, BZ)),
            ("alignment sets strength", (BX1 + 2.0, BY0 + 6.0, BZ))],
        3: [("ore: mined rare earths", (ROCK[0], 14.0, ROCK[2])), ("separated, refined", tank_pts[0]["top"]),
            ("pressed into magnets", PRESS)],
        4: [("China does most of it", PRESS), ("MP, LYC, NEO", tank_pts[1]["top"]),
            ("export limits reach motors", motor_pts[0]["top"])],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-20.0, 15.0, -90.0), 230.0, 0.30, 0.30),
        frame((199.0, 18.0, BZ), 110.0, 0.25, 0.20),
        frame((199.0, 18.0, BZ), 70.0, 0.10, 0.10),
        frame((-80.0, 10.0, -40.0), 190.0, 0.30, 0.40),
        frame((-60.0, 20.0, -60.0), 260.0, 0.25, 0.45),
    ], root)


if __name__ == "__main__":
    build()

"""TRM_TUNNEL_OXIDE: a flash cell cut open on the bench with its few-nanometre oxide drawn thick,
electrons tunnelling through it both ways, and traps piling up in it as it wears.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_tunnel_oxide.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_nand as K  # noqa: E402
from term_common import F, show  # noqa: E402
from power_vrm_detail import frame, run, wire  # noqa: E402

SLUG = "TRM_TUNNEL_OXIDE"
BEATS = [
    ("Every flash cell has a glass film a few nm thick",
     "Inside each NAND or NOR cell, a sheet of silicon dioxide separates the channel from the charge store. It is "
     "about 7 to 10 nm thick, a few dozen atoms. All data in flash depends on this layer."),
    ("It sits between the channel and the floating gate",
     "Below it is the silicon channel between source and drain; above it is the floating gate that holds the bit. "
     "At normal voltages it is a near-perfect insulator, so stored electrons stay for ten years or more."),
    ("High voltage: electrons tunnel straight through",
     "Put about 20 V across the film and the barrier bends thin enough for electrons to tunnel through quantum "
     "mechanically (Fowler-Nordheim tunnelling). Program sends them up; erase reverses the field to pull them back."),
    ("Each cycle leaves damage: traps build up",
     "Electrons forced through the oxide break bonds and leave charge traps behind. Traps shift thresholds and open "
     "leak paths, so retention drops. This is the main reason a cell survives only thousands of cycles."),
    ("Thinner is faster but leakier",
     "Thinning the oxide lowers write voltage but lets charge leak; that limit helped push NAND from shrinking cells "
     "to stacking them in 3D. Oxide deposition and etch: Applied Materials (AMAT), Lam Research (LRCX); users: Micron "
     "(MU), Samsung (005930.KS)."),
]

X0, X1 = 152.0, 246.0
Z0 = -40.0
CX, CZ = (X0 + X1) / 2, -20.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.prep(m)
    ctx = K.context(m, root)
    cell = K.cell_fg(m, root, "cell", X0, X1, Z0)
    C.magnify(m, root, ctx["pkg"], (X0 - 2.0, 14.0, CZ))
    chan, fg, tox = cell["chan"], cell["fg"], cell["tox"]
    # the oxide itself blinks to call it out in beat 1
    ring = K.traps(m, root, "callout", [(tox[0] + dx, tox[1], -0.6) for dx in range(-20, 21, 5)], 0.5)
    show(ring, [(F(0, 0.4), F(1, 1.0))])
    stored = K.electrons(m, root, "stored", [(fg[0] - 12.0 + 3.0 * k, fg[1], -1.5) for k in range(9)], 9, 1.0)
    show(stored, [(F(1, 0.0), F(2, 0.0)), (F(2, 0.5), F(4, 1.0))])
    # beat 2: tunnelling up then back down, several lanes across the oxide
    for i, dx in enumerate((-10.0, 0.0, 10.0)):
        up = K.tunnel_path((chan[0] + dx, chan[1], -1.5), (fg[0] + dx, fg[1], -1.5), bend=1.5)
        run(root, f"up{i}", up, 2, 0.8, m["nand_e"], 2, 0.05 + 0.05 * i, 0.5, 25)
        run(root, f"dn{i}", list(reversed(up)), 2, 0.8, m["nand_e"], 2, 0.55, 0.95, 25)
        run(root, f"wear{i}", up, 2, 0.8, m["nand_e"], 3, 0.05, 0.9, 25)
    # beat 3: traps accumulate in the oxide, a few at a time
    for k in range(4):
        tr = K.traps(m, root, f"trap{k}", [(tox[0] - 18.0 + 11.0 * k + 3.0 * j, tox[1], -0.8) for j in range(2)], 0.6)
        show(tr, [(F(3, 0.15 + 0.18 * k), F(4, 1.0))])
    # beat 4: a leak path, stored electrons draining down
    run(root, "leak", K.tunnel_path((fg[0] + 12.0, fg[1], -1.5), (chan[0] + 12.0, chan[1], -1.5), bend=0.5),
        3, 0.7, m["nand_e"], 4, 0.1, 0.9, 40)

    C.tags(root, {
        0: [("flash package on the board", ctx["pkg"]), ("one cell, drawn huge", (CX, 25.0, CZ))],
        1: [("tunnel oxide, ~7-10 nm", tox), ("floating gate above", fg), ("channel below", (cell["src"][0] + 8.0, chan[1], CZ)),
            ("control gate", cell["cg"])],
        2: [("~20 V bends the barrier", cell["cg"]), ("Fowler-Nordheim tunnelling", tox)],
        3: [("traps left in the oxide", tox), ("thresholds drift", fg), ("thousands of cycles max", cell["sub"])],
        4: [("leak path through thin oxide", (fg[0] + 12.0, tox[1], -1.5)), ("AMAT, LRCX, MU, 005930.KS", cell["sub"])],
    })
    C.done(SLUG, BEATS, [
        frame((-40.0, 20.0, -60.0), 540.0, 0.30, 0.45, pad=1.0),
        frame((CX, 12.0, CZ), 110.0, 0.25, 0.22),
        frame((CX, 10.0, CZ), 70.0, 0.20, 0.15),
        frame((CX, 10.0, CZ), 70.0, 0.35, 0.18),
        frame((CX, 12.0, CZ), 100.0, 0.30, 0.25),
    ], root)


if __name__ == "__main__":
    build()

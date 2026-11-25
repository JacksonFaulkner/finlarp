"""TRM_NOR_FLASH: a NOR boot chip beside the GPU board's controller, then two floating-gate cells
cut open side by side, each wired straight to its own bit line so any byte reads at random.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_nor_flash.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_nand as K  # noqa: E402
from term_common import F, show  # noqa: E402
from power_vrm_detail import frame, run, wire  # noqa: E402

SLUG = "TRM_NOR_FLASH"
BEATS = [
    ("NOR flash holds the firmware every board boots from",
     "A small 8-pin NOR chip sits on every server, GPU board, SSD and switch. At power-on the processor reads its boot "
     "code and firmware from it. It keeps that code with the power off and rarely gets rewritten."),
    ("Cells sit in parallel, each with its own contact",
     "Cut open, each cell is a floating-gate transistor like NAND's. The difference is wiring: every NOR cell's drain "
     "has its own contact to the bit line, so the cells sit in parallel instead of in a series string."),
    ("Random reads: any byte, straight off the bit line",
     "Because each cell connects directly, the chip can read any address in tens of nanoseconds. Code can execute "
     "straight from it (execute-in-place), which is why it stores boot code rather than bulk data."),
    ("Write by hot electrons, erase by tunnelling",
     "Programming drives a strong drain current so fast hot electrons jump over the oxide onto the floating gate. "
     "Erase pulls them off by tunnelling, a sector at once. Writes are slow, but reads stay fast and reliable."),
    ("The trade: reliable and direct, but low density",
     "The per-cell contacts take space, so NOR is roughly 10x less dense than NAND and tops out near 2 Gb per chip. "
     "That fits firmware, not datasets. Makers: Winbond (2344.TW), Macronix (2337.TW), GigaDevice (603986.SS), "
     "Infineon (IFX.DE)."),
]

Z0 = -40.0
CZ = -20.0
CELLS = [(152.0, 196.0), (202.0, 246.0)]
BLY = 34.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.prep(m)
    ctx = K.context(m, root)
    cells = [K.cell_fg(m, root, f"cell{i}", a, b, Z0) for i, (a, b) in enumerate(CELLS)]
    C.magnify(m, root, ctx["pkg"], (150.0, 14.0, CZ))
    # bit line across the top, a contact plug down to each drain
    wire("bitline", [(150.0, BLY, -1.0), (248.0, BLY, -1.0)], 1.0, m["copper"], root)
    for i, c in enumerate(cells):
        d = c["drn"]
        wire(f"plug{i}", [(d[0], BLY, -1.0), (d[0], d[1], -1.0)], 0.8, m["copper"], root)
    # beat 2: reads land on either cell at random, down its own plug
    for i, c in enumerate(cells):
        d = c["drn"]
        run(root, f"read{i}", [(150.0 if i == 0 else 248.0, BLY, -1.0), (d[0], BLY, -1.0), (d[0], d[1], -1.0), (c["src"][0], c["chan"][1], -1.0)],
            3, 0.8, m["nand_e"], 2, 0.05 + 0.25 * i, 0.9, 30)
    # beat 3: hot electrons hop near the drain; erase tunnels them back down
    c = cells[1]
    run(root, "hot", K.tunnel_path((c["drn"][0] - 4.0, c["chan"][1], -1.5), (c["fg"][0] + 6.0, c["fg"][1], -1.5), bend=3.0),
        4, 0.8, m["nand_e"], 3, 0.05, 0.45, 30)
    run(root, "erase", K.tunnel_path((c["fg"][0], c["fg"][1], -1.5), (c["chan"][0], c["chan"][1], -1.5), bend=-3.0),
        4, 0.8, m["nand_e"], 3, 0.55, 0.95, 30)
    stored = K.electrons(m, root, "stored", [(c["fg"][0] - 8.0 + 3.0 * k, c["fg"][1], -1.5) for k in range(6)], 6, 1.0)
    show(stored, [(F(1, 0.2), F(3, 0.5)), (F(4, 0.0), F(4, 1.0))])

    a, b = cells
    C.tags(root, {
        0: [("NOR boot chip on the board", ctx["pkg"]), ("CPU reads firmware at power-on", (-130.0, 8.0, -80.0)),
            ("two cells, cut open", (200.0, 28.0, CZ))],
        1: [("floating gate, like NAND", a["fg"]), ("own contact per drain", (a["drn"][0], 26.0, -1.0)),
            ("bit line", (160.0, BLY + 1.0, -1.0)), ("cells in parallel", b["cg"])],
        2: [("any address, ~tens of ns", (172.0, BLY + 1.0, -1.0)), ("execute code in place", b["cg"])],
        3: [("hot electrons jump the oxide", b["fg"]), ("erase: tunnel out per sector", b["tox"])],
        4: [("~10x less dense than NAND", a["cg"]), ("2344.TW, 2337.TW, 603986.SS", b["sub"])],
    })
    C.done(SLUG, BEATS, [
        frame((-40.0, 20.0, -60.0), 540.0, 0.30, 0.45, pad=1.0),
        frame((199.0, 18.0, CZ), 125.0, 0.25, 0.22),
        frame((199.0, 20.0, CZ), 120.0, 0.15, 0.30),
        frame((224.0, 14.0, CZ), 75.0, 0.30, 0.22),
        frame((199.0, 18.0, CZ), 125.0, 0.40, 0.30),
    ], root)


if __name__ == "__main__":
    build()

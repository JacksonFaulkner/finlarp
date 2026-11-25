"""TRM_ROM on the shared GPU board: a small boot ROM chip beside the package, its mask-ROM array cut
open huge on the bench (word lines, bit lines, a transistor only where the mask put one), and a row of
PROM fuses, some blown.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_rom.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, mat, show  # noqa: E402
from power_vrm_detail import frame, run  # noqa: E402

SLUG = "TRM_ROM"
BEATS = [
    ("ROM holds code that must be there the moment power comes on",
     "When a board powers up, the processor needs instructions before anything else works. A small read-only memory "
     "holds that first boot code or fixed microcode, and it keeps its contents with the power off."),
    ("In a mask ROM, the bits are drawn into the chip itself",
     "A mask ROM is a grid of word lines and bit lines. At each crossing the factory's photomask either places a "
     "transistor or leaves it out: present means 0, absent means 1. The data is fixed when the wafer is made."),
    ("Reading: raise one word line, sense every bit line",
     "To read a row, the decoder raises one word line. Where a transistor sits, it pulls its precharged bit line low; "
     "where none sits, the line stays high. Sense amplifiers turn the pattern into a byte in a few nanoseconds."),
    ("PROM: blank fuses, blown once by the user",
     "A programmable ROM ships with every fuse intact. A programmer drives high current through chosen fuses to burn "
     "them open, writing the data once. After that it cannot be changed, like a mask ROM made in the field."),
    ("Mostly replaced by flash; makers Macronix, Winbond, Micron",
     "Because code needs fixing after shipping, most new boards keep boot code in SPI NOR flash or EEPROM instead, and "
     "true mask ROM survives inside chips for tiny fixed boot loaders. Macronix (2337.TW), Winbond (2344.TW) and "
     "Micron (MU) make the small NOR and ROM parts."),
]

ROM = (190.0, 0.0, -150.0)
X0, X1, Z0 = 158.0, 242.0, -64.0
ROWS, COLS = 6, 8
TY = 4.0
PATTERN = [[(r * 5 + c * 3 + r * c) % 3 != 0 for c in range(COLS)] for r in range(ROWS)]
READ_ROW = 2


def mats(m):
    m["wl"] = mat("rom_wl", (0.50, 0.28, 0.36), rough=0.4)
    m["wl_on"] = mat("rom_wl_on", (1.0, 0.45, 0.62), emit=(1.0, 0.40, 0.60), strength=4.5)
    m["bl"] = mat("rom_bl", (0.78, 0.80, 0.84), metal=0.9, rough=0.3)
    m["tr"] = mat("rom_tr", (0.20, 0.30, 0.55), metal=0.3, rough=0.4)
    m["hi"] = mat("rom_hi", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=3.0)
    m["fuse"] = mat("rom_fuse", (0.85, 0.82, 0.70), metal=0.9, rough=0.3)


def cx(c):
    return X0 + 12.0 + c * (X1 - X0 - 24.0) / (COLS - 1)


def rz(r):
    return Z0 + 10.0 + r * 7.0


def array(m, root):
    g = empty("arr", root)
    C.xsec(m, g, "arr_sub", X0, X1, Z0, [(-2.0, 1.0, "si"), (1.0, 1.6, "oxide")])
    for c in range(COLS):
        bx(f"bl{c}", (cx(c) - 0.8, TY + 1.2, Z0 + 4.0), (cx(c) + 0.8, TY + 1.8, -4.0), m["bl"], g)
        bx(f"sa{c}", (cx(c) - 3.0, 1.6, -6.0), (cx(c) + 3.0, 3.6, -1.0), m["substrate"], g)
    wl_on = None
    for r in range(ROWS):
        bx(f"wl{r}", (X0 + 4.0, 1.6, rz(r) - 1.0), (X1 - 4.0, 2.4, rz(r) + 1.0), m["wl"], g)
        for c in range(COLS):
            if PATTERN[r][c]:
                bx(f"tr{r}{c}", (cx(c) - 1.8, 2.4, rz(r) - 1.8), (cx(c) + 1.8, TY + 1.2, rz(r) + 1.8), m["tr"], g)
        if r == READ_ROW:
            wl_on = empty("wl_on", g)
            bx("wl_on_b", (X0 + 4.0, 2.4, rz(r) - 1.6), (X1 - 4.0, 3.4, rz(r) + 1.6), m["wl_on"], wl_on)
    bx("dec", (X0 - 4.0, 1.6, Z0 + 4.0), (X0 + 3.0, 5.0, -8.0), m["substrate"], g)
    # sense output: lit where the line stays high (no transistor in the read row)
    hi = empty("hi", g)
    for c in range(COLS):
        if not PATTERN[READ_ROW][c]:
            bx(f"hi{c}", (cx(c) - 2.0, 3.6, -5.0), (cx(c) + 2.0, 4.0, -2.0), m["hi"], hi)
    return wl_on, hi


def fuses(m, root):
    """A row of PROM fuses behind the array: thin links, some blown open."""
    g = empty("fuses", root)
    z = Z0 - 22.0
    bx("fz_sub", (X0, -1.0, z - 8.0), (X1, 1.0, z + 8.0), m["si"], g)
    blown = []
    for k in range(10):
        x = X0 + 8.0 + k * 8.5
        bx(f"fz_pa{k}", (x - 3.0, 1.0, z - 6.0), (x + 3.0, 1.6, z - 3.0), m["alum"], g)
        bx(f"fz_pb{k}", (x - 3.0, 1.0, z + 3.0), (x + 3.0, 1.6, z + 6.0), m["alum"], g)
        if k % 3 == 1:
            intact = empty(f"fz_i{k}", g)
            bx(f"fz_l{k}", (x - 0.4, 1.0, z - 3.0), (x + 0.4, 1.4, z + 3.0), m["fuse"], intact)
            show(intact, [(F(0, 0), F(3, 0.5))])
            pop = empty(f"fz_pop{k}", g)
            bx(f"fz_pop{k}_b", (x - 1.2, 1.0, z - 1.2), (x + 1.2, 2.4, z + 1.2), m["warn"], pop)
            show(pop, [(F(3, 0.45), F(3, 0.6))])
            bx(f"fz_s1{k}", (x - 0.4, 1.0, z - 3.0), (x + 0.4, 1.4, z - 1.2), m["fuse"], g)
            bx(f"fz_s2{k}", (x - 0.4, 1.0, z + 1.2), (x + 0.4, 1.4, z + 3.0), m["fuse"], g)
            blown.append((x, 1.6, z))
        else:
            bx(f"fz_l{k}", (x - 0.4, 1.0, z - 3.0), (x + 0.4, 1.4, z + 3.0), m["fuse"], g)
    return (X0 + 40.0, 1.6, z), blown


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    b = C.base(m, root)
    pk = b["pk"]
    rtop = C.chip(m, root, "rom", ROM, 10.0, 6.0, 1.4, pins=4)
    spi = [(ROM[0] - 6.0, 0.0, ROM[2]), (145.0, 0.0, ROM[2]), (145.0, 0.0, -60.0), (60.0, 0.0, -60.0)]
    for k, dz in enumerate((-1.5, 0.0, 1.5)):
        C.trace(m, root, f"t_spi{k}", [(p[0], 0.0, p[2] + dz) for p in spi], 0.4)
    wl_on, hi = array(m, root)
    fz, blown = fuses(m, root)
    C.magnify(m, root, rtop, (X0 + 10.0, 8.0, -10.0), r=4.0)

    # beat 0: boot code streams from the ROM into the package, die wakes
    run(root, "boot", [(p[0], 1.0, p[2]) for p in spi], 12, 0.9, m["sig"], 0, 0.1, 0.8, 50)
    show(b["die_glow"], [(F(0, 0.6), F(1, 0))])
    # beat 2: read row lights, low lines drain, high lines lit at the sense amps
    show(wl_on, [(F(2, 0.1), F(3, 0))])
    show(hi, [(F(2, 0.4), F(3, 0)), (F(4, 0.0), F(5, 0))])
    for c in range(COLS):
        if PATTERN[READ_ROW][c]:
            run(root, f"pull{c}", [(cx(c), TY + 2.2, -5.0), (cx(c), TY + 2.2, rz(READ_ROW))], 3, 0.6, m["e_blue"], 2, 0.15, 0.6, 25)
    # beat 3: programmer current pulses into the fuses chosen
    for k, p in enumerate(blown):
        run(root, f"burn{k}", [(p[0], 6.0, p[2] - 10.0), (p[0], 1.8, p[2] - 4.0), (p[0], 1.8, p[2])], 4, 0.6, m["h_amber"], 3, 0.0, 0.4, 20)

    C.tags(root, {
        0: [("boot ROM chip", rtop), ("first code into the processor", (145.0, 1.0, -110.0)), ("GPU / CPU package", pk["top"])],
        1: [("word lines (rows)", (X0 + 6.0, 2.4, rz(0))), ("bit lines (columns)", (cx(COLS - 1), TY + 1.8, Z0 + 6.0)),
            ("transistor = 0, none = 1", (cx(1), TY + 1.2, rz(3)))],
        2: [("decoder raises one row", (X0, 5.0, rz(READ_ROW))), ("transistor pulls line low", (cx(0), TY + 2.0, rz(READ_ROW))),
            ("sense amps read a byte", (cx(4), 4.0, -3.0))],
        3: [("PROM fuses", fz), ("blown open once", blown[0]), ("cannot be changed", blown[-1])],
        4: [("now mostly SPI NOR flash", rtop), ("Macronix 2337.TW", (cx(2), TY, rz(4))), ("Winbond 2344.TW, MU", (cx(6), TY, rz(4)))],
    })
    ac = ((X0 + X1) / 2, TY, Z0 / 2)
    C.done(SLUG, BEATS, [
        frame((90.0, 0.0, -110.0), 260.0, 0.30, 0.75, pad=1.0),
        frame(ac, 100.0, 0.20, 0.70),
        frame(ac, 95.0, -0.15, 0.60),
        frame(((X0 + X1) / 2, 2.0, Z0 - 22.0), 95.0, 0.15, 0.80),
        frame((150.0, 0.0, -90.0), 200.0, 0.25, 0.70, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()

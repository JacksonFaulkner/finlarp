"""TRM_STORAGE_CONTROLLER: the SSD stick again, with its controller die lifted onto the bench as
a floor plan: PCIe PHY, CPU cores running the FTL, DRAM controller, LDPC ECC engine and eight
flash-channel PHYs. Commands are translated, data is error-corrected, and writes spread out.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_storage_controller.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_nand as K  # noqa: E402
from term_common import show  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink  # noqa: E402
from sand_overview import empty  # noqa: E402
import trm_ssd as S  # noqa: E402  (the drive builder, shared with TRM_SSD)

SLUG = "TRM_STORAGE_CONTROLLER"
BEATS = [
    ("The controller is the processor inside every SSD",
     "Between the server's PCIe link and the NAND packages sits one chip: the controller. It turns simple host "
     "commands like 'read block 7' into the exact die, plane and page operations flash needs."),
    ("Opened up: PHYs, CPU cores, ECC and channel engines",
     "The die holds a PCIe/NVMe front end, several Arm-class CPU cores, a DRAM controller, an error-correction engine "
     "and 8 to 16 flash-channel PHYs round the edge. Data-center controllers are built on 7 to 12 nm logic."),
    ("The FTL maps every logical block to a physical page",
     "Flash cannot overwrite in place, so the flash translation layer writes new data to a fresh page and updates "
     "a map. The map, about 1 GB of DRAM per TB of flash, lives in the DRAM cache beside the controller."),
    ("LDPC error correction cleans every read",
     "Cells storing 3 or 4 bits drift, so raw reads come back with errors. The LDPC engine fixes them on the fly "
     "using parity stored with each page; stronger ECC lets makers use denser, cheaper NAND."),
    ("Wear leveling spreads writes; that sets endurance",
     "Each block survives a few thousand erase cycles, so the controller rotates writes across all blocks and "
     "moves cold data. Merchant controllers: Marvell (MRVL), Silicon Motion (SIMO), Phison (8299.TWO); "
     "Samsung (005930.KS) builds its own."),
]

BX0, BX1 = 152.0, 246.0
Z0, Z1 = -70.0, -4.0
BCX, BCZ = (BX0 + BX1) / 2, (Z0 + Z1) / 2
Y = 4.0  # die top on the bench


def block(m, g, name, x0, x1, z0, z1, mt, h=1.2):
    bx(name, (x0, Y, z0), (x1, Y + h, z1), m[mt], g)
    return ((x0 + x1) / 2, Y + h, (z0 + z1) / 2)


def die(m, root):
    """The controller die floor plan on a package substrate."""
    g = empty("cdie", root)
    bx("cd_sub", (BX0 - 4.0, 0.0, Z0 - 4.0), (BX1 + 4.0, 2.0, Z1 + 2.0), m["substrate"], g)
    bx("cd_si", (BX0, 2.0, Z0), (BX1, Y, Z1), m["silicon"], g)
    b = {}
    b["pcie"] = block(m, g, "cd_pcie", BX0 + 2.0, BX0 + 14.0, Z0 + 4.0, Z1 - 4.0, "gold", 0.8)
    b["cpu"] = [block(m, g, f"cd_cpu{k}", BX0 + 20.0 + 13.0 * k, BX0 + 31.0 + 13.0 * k, Z0 + 4.0, Z0 + 20.0, "die")
                for k in range(4)]
    b["sram"] = block(m, g, "cd_sram", BX0 + 20.0, BX0 + 70.0, Z0 + 24.0, Z0 + 34.0, "grid", 0.8)
    b["ecc"] = block(m, g, "cd_ecc", BX0 + 20.0, BX0 + 52.0, Z0 + 38.0, Z1 - 4.0, "plane12", 1.0)
    b["dram"] = block(m, g, "cd_dram", BX0 + 56.0, BX0 + 74.0, Z0 + 38.0, Z1 - 4.0, "plane08", 1.0)
    b["ch"] = [block(m, g, f"cd_ch{k}", BX1 - 14.0, BX1 - 2.0, Z0 + 2.0 + 8.0 * k, Z0 + 8.0 + 8.0 * k, "copper", 0.8)
               for k in range(8)]
    return b


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.prep(m)
    d = S.drive(m, root)
    b = die(m, root)
    C.magnify(m, root, d["ctrl"], (BX0 - 2.0, 10.0, BCZ))

    up = lambda p, dy=1.5: (p[0], p[1] + dy, p[2])  # noqa: E731
    # beat 0: traffic in over PCIe and out to the flash
    for k in range(2):
        run(root, f"in{k}", d["lanes"][k + 1], 3, 1.4, m["sig"], 0, 0.1 + 0.1 * k, 0.8, 40)
        run(root, f"out{k}", d["chans"][k * 2], 3, 1.4, m["e_blue"], 0, 0.2 + 0.1 * k, 0.8, 50)
    # beat 1: a command walks the die: PCIe -> core -> each channel PHY
    for k, ch in enumerate(b["ch"]):
        run(root, f"walk{k}", [up(b["pcie"]), up(b["cpu"][k % 4]), up(ch)], 2, 0.9, m["sig"], 1, 0.05 + 0.08 * k, 0.8, 40)
    rise(root, "cpu_heat", up(b["cpu"][1], 0.5), 6, 0.7, m["h_amber"], [1, 2], 0.0, 0.85, 14.0, 40, (22.0, 6.0))
    # beat 2: FTL lookup: core <-> DRAM controller <-> the DRAM chip on the board
    for k in range(4):
        run(root, f"ftl{k}", [up(b["cpu"][k]), up(b["sram"]), up(b["dram"])], 2, 0.9, m["e_blue"], 2, 0.05 + 0.1 * k, 0.8, 40)
    run(root, "map", [(S.DRAM[0], 3.0, S.DRAM[2]), (S.CTRL[0], 4.0, S.CTRL[2])], 3, 1.2, m["bit"], 2, 0.1, 0.8, 30)
    # beat 3: raw data with errors (red) comes in from the channels, ECC turns it green
    for k in (1, 3, 5, 7):
        run(root, f"raw{k}", [up(b["ch"][k]), up(b["ecc"])], 3, 0.9, m["warn"], 3, 0.05 + 0.05 * k, 0.7, 36)
    run(root, "clean", [up(b["ecc"]), up(b["sram"]), up(b["pcie"])], 5, 0.9, m["sig"], 3, 0.2, 0.9, 40)
    ecc_glow = empty("ecc_glow", root)
    bx("ecc_g", (BX0 + 22.0, Y + 1.0, Z0 + 40.0), (BX0 + 50.0, Y + 1.3, Z1 - 6.0), m["chan"], ecc_glow)
    show(ecc_glow, [])
    blink(ecc_glow, 3, [1, 3, 5, 7], n=8, on=0.7)
    # beat 4: wear leveling: small block cells on each NAND top light in rotation
    for k, t in enumerate(d["nand"]):
        for j in range(6):
            cell = empty(f"wl{k}_{j}", root)
            x = t[0] - 15.0 + 6.0 * j
            bx(f"wl{k}_{j}b", (x, t[1], -66.0), (x + 4.0, t[1] + 0.4, -58.0), m["sig"], cell)
            show(cell, [])
            blink(cell, 4, [(j + 2 * k) % 12], n=12, on=0.9)
        run(root, f"wr{k}", d["chans"][k], 2, 1.2, m["e_blue"], 4, 0.05 + 0.05 * k, 0.8, 50)

    C.tags(root, {
        0: [("storage controller", (S.CTRL[0], 3.0, S.CTRL[2])), ("host side: PCIe x4", (-230.0, 0.0, -50.0)),
            ("flash side: NAND channels", d["nand"][1]), ("its die, opened on the bench", (BCX, 6.0, BCZ))],
        1: [("PCIe / NVMe PHY", b["pcie"]), ("Arm CPU cores", b["cpu"][1]), ("ECC engine", b["ecc"]),
            ("8 flash-channel PHYs", b["ch"][4])],
        2: [("FTL runs on the cores", b["cpu"][2]), ("DRAM controller", b["dram"]), ("on-die SRAM buffers", b["sram"])],
        3: [("raw reads carry bit errors", b["ch"][5]), ("LDPC fixes them on the fly", b["ecc"]),
            ("clean data out to the host", b["pcie"])],
        4: [("writes rotate across blocks", d["nand"][1]), ("few thousand erases per block", d["nand"][3]),
            ("MRVL, SIMO, 8299.TWO", (S.CTRL[0], 3.0, S.CTRL[2])), ("in-house: 005930.KS", (S.DRAM[0], 1.6, S.DRAM[2]))],
    })
    C.done(SLUG, BEATS, [
        frame((-20.0, 10.0, -46.0), 380.0, 0.20, 0.45, pad=1.0),
        frame((BCX, Y, BCZ), 110.0, 0.20, 0.70),
        frame((BCX - 10.0, Y, BCZ), 100.0, 0.25, 0.65),
        frame((BCX, Y, BCZ), 110.0, 0.30, 0.65),
        frame((-40.0, 0.0, -46.0), 300.0, 0.15, 0.60, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()

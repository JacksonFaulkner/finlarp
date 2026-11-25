"""TRM_EEPROM: a small serial EEPROM on a board, then one byte's cell pair cut open: a select
transistor and a floating-gate cell, written and erased on its own, byte by byte.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_eeprom.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_nand as K  # noqa: E402
from term_common import F, show  # noqa: E402
from power_vrm_detail import frame, run, wire  # noqa: E402

SLUG = "TRM_EEPROM"
BEATS = [
    ("EEPROM: a tiny chip that remembers settings",
     "Small serial EEPROMs, often a few kilobits, sit on boards, DIMMs, sensors and cars. They hold configuration, "
     "serial numbers and calibration that must survive power-off and change now and then."),
    ("Each bit is a select transistor plus a floating gate",
     "Cut open, an EEPROM bit is two transistors. The floating-gate cell stores charge like flash; the select "
     "transistor beside it isolates that cell, so one byte can be changed without touching its neighbours."),
    ("Write: electrons tunnel onto one byte's gates",
     "The select transistor opens a single byte, and a high voltage pulls electrons through a thin tunnel oxide "
     "onto the floating gate. Only that byte changes; there is no block erase as in flash."),
    ("Erase electrically, byte by byte, no UV lamp",
     "Reversing the field tunnels the charge back off. Older EPROMs needed a UV lamp through a quartz window to "
     "erase; EEPROM does it with voltage in milliseconds, for about a million cycles."),
    ("Flexible but big: the extra transistor costs density",
     "Two transistors per bit makes EEPROM far less dense than flash, so it stays at kilobits to a few megabits for "
     "config data. Makers: Microchip (MCHP), STMicroelectronics (STM), Infineon (IFX.DE)."),
]

Z0 = -40.0
CZ = -20.0
SEL = (152.0, 186.0)
FGC = (192.0, 246.0)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.prep(m)
    ctx = K.context(m, root)
    sel = K.cell_ctf(m, root, "sel", SEL[0], SEL[1], Z0)
    cell = K.cell_fg(m, root, "cell", FGC[0], FGC[1], Z0)
    C.magnify(m, root, ctx["pkg"], (150.0, 14.0, CZ))
    chan, fg = cell["chan"], cell["fg"]
    # select line opens: its gate blinks while the byte is addressed
    lamp = K.traps(m, root, "sel_on", [(sel["cg_top"][0] + dx, sel["cg_top"][1] + 0.6, -1.0) for dx in (-6, 0, 6)], 0.8)
    show(lamp, [(F(1, 0.4), F(4, 1.0))])
    # bit line current through the select transistor into the cell
    wire("bitline", [(150.0, 34.0, -1.0), (sel["chan"][0] - 12.0, 34.0, -1.0), (sel["chan"][0] - 12.0, sel["chan"][1], -1.0)],
         0.9, m["copper"], root)
    run(root, "bl", [(150.0, 34.0, -1.0), (sel["chan"][0] - 12.0, 34.0, -1.0), (sel["chan"][0] - 12.0, sel["chan"][1], -1.0),
                     (chan[0], chan[1], -1.0)], 4, 0.8, m["nand_e"], 1, 0.4, 0.95, 35)
    path = K.tunnel_path((chan[0], chan[1], -1.5), (fg[0], fg[1], -1.5), bend=3.0)
    run(root, "prog", path, 4, 0.8, m["nand_e"], 2, 0.1, 0.6, 35)
    run(root, "erase", list(reversed(path)), 4, 0.8, m["nand_e"], 3, 0.1, 0.6, 35)
    stored = K.electrons(m, root, "stored", [(fg[0] - 9.0 + 3.0 * k, fg[1], -1.5) for k in range(7)], 7, 1.0)
    show(stored, [(F(2, 0.55), F(3, 0.5))])

    C.tags(root, {
        0: [("serial EEPROM, a few kbit", ctx["pkg"]), ("one bit, cut open", (200.0, 28.0, CZ))],
        1: [("select transistor", sel["cg_top"]), ("floating-gate cell", cell["cg"]), ("bit line", (160.0, 35.0, -1.0))],
        2: [("only this byte opened", sel["cg_top"]), ("electrons tunnel onto the gate", fg)],
        3: [("erase by voltage, not UV", fg), ("~1M cycles, ms per byte", cell["sub"])],
        4: [("2 transistors per bit", sel["cg_top"]), ("MCHP, STM, IFX.DE", cell["sub"])],
    })
    C.done(SLUG, BEATS, [
        frame((-40.0, 20.0, -60.0), 540.0, 0.30, 0.45, pad=1.0),
        frame((199.0, 18.0, CZ), 125.0, 0.25, 0.22),
        frame((219.0, 14.0, CZ), 80.0, 0.30, 0.22),
        frame((219.0, 14.0, CZ), 80.0, 0.15, 0.25),
        frame((199.0, 18.0, CZ), 125.0, 0.40, 0.30),
    ], root)


if __name__ == "__main__":
    build()

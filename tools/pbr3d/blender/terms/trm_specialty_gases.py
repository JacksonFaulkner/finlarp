"""TRM_SPECIALTY_GASES: the Terms-tab overview for fab specialty gases, built with the kit_supply parts.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_specialty_gases.py

Writes assets/term_TRM_SPECIALTY_GASES.glb. Captions live in specs/terms/TRM_SPECIALTY_GASES.json.

A fab sub-floor: a gas cabinet of cylinders feeds purifiers and a valve box, and lines run up to a
process chamber cut open to its wafer. Gas molecules land as a film, then a plasma etches, then NF3
cleans the chamber walls.

Beats:
  0 cabinet   cylinders of NF3, WF6, silane in a vented cabinet, gas flowing out
  1 deposit   WF6 and silane meet over the wafer; tungsten lands as a film
  2 etch      a plasma of etch gas cuts patterns into the film
  3 clean     NF3 plasma strips buildup off the chamber walls
  4 supply    few plants, ppb purity; LIN, APD, ENTG
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import kit_supply as K  # noqa: E402
import sand_overview as O  # noqa: E402
from term_common import F, bx, empty, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink, mat  # noqa: E402

SLUG = "TRM_SPECIALTY_GASES"
BEATS = [
    ("Specialty gases arrive in cylinders and feed the fab's tools",
     "Fabs use dozens of high-purity process gases: nitrogen trifluoride (NF3), tungsten hexafluoride (WF6), "
     "silane, and fluorocarbon etch gases. They come in steel cylinders or bulk trailers, sit in vented gas "
     "cabinets, and pass through purifiers and valve boxes before reaching a tool. Many are toxic or burn in air, "
     "so every line is double-walled and watched by sensors."),
    ("In deposition, gas molecules react and land as a thin film",
     "In chemical vapor deposition, WF6 and a reducing gas meet over a hot wafer and leave a layer of tungsten a "
     "few nanometers at a time. Silane does the same for silicon and oxide films. Each layer of a chip's wiring "
     "and insulation starts as gas flowing into a chamber like this."),
    ("In etch, a plasma of fluorine gases cuts the pattern",
     "Etch tools turn fluorocarbon or chlorine gases into a glowing plasma. Ions strike the wafer and carve away "
     "the film wherever the mask leaves it open, down into deep trenches and holes. 3D NAND and gate-all-around "
     "logic need many more etch steps, so they burn more gas per wafer."),
    ("NF3 plasma scrubs the chamber walls between runs",
     "Film builds up on chamber walls too, and flakes would land on wafers as defects. Fabs run NF3 through a "
     "remote plasma source between batches; the fluorine eats the buildup and leaves as exhaust. NF3 is one of "
     "the largest-volume specialty gases, and exhaust is burned in abatement units because it warms the climate."),
    ("Few plants, strict purity: a bad lot can scrap wafers",
     "Purity is held to parts per billion, and a contaminated cylinder can ruin every wafer it touches. Only a "
     "handful of plants make each gas, some tied to one region (neon from Ukraine was a 2022 scare). Demand grows "
     "with deposition and etch steps per wafer. Related: Linde (LIN), Air Products (APD), Entegris (ENTG)."),
]

CAB = (-120.0, 0.0, -40.0)
PUR = (-70.0, 0.0, -40.0)
VMB = (-35.0, 0.0, -40.0)
CH = (60.0, 0.0, -40.0)   # chamber base centre
CW, CHH, CD = 60.0, 40.0, 46.0
WY = 16.0                 # wafer height
GAS_COLORS = ["sup_flow", "sup_he", "sg_violet"]


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.materials(m)
    m["sg_violet"] = mat("sg_violet", (0.7, 0.4, 1.0), emit=(0.65, 0.35, 1.0), strength=2.5)
    m["sg_plasma"] = mat("sg_plasma", (0.6, 0.4, 1.0), emit=(0.6, 0.35, 1.0), strength=0.8)
    m["sg_pink"] = mat("sg_pink", (1.0, 0.45, 0.7), emit=(1.0, 0.4, 0.7), strength=0.8)
    m["sg_wafer"] = mat("sg_wafer", (0.35, 0.38, 0.48), metal=0.8, rough=0.15)
    m["sg_film"] = mat("sg_film", (0.7, 0.72, 0.76), metal=0.9, rough=0.25)
    m["sg_dep"] = mat("sg_dep", (0.6, 0.6, 0.55), metal=0.3, rough=0.8)

    bx("floor", (-160.0, -3.0, -90.0), (120.0, 0.0, 10.0), m["sup_steel"], root)

    # gas cabinet: back + sides, front open, six cylinders
    bx("cab_back", (CAB[0] - 24, 0, CAB[2] - 14), (CAB[0] + 24, 50, CAB[2] - 12), m["white"], root)
    bx("cab_l", (CAB[0] - 24, 0, CAB[2] - 14), (CAB[0] - 22, 50, CAB[2] + 12), m["white"], root)
    bx("cab_r", (CAB[0] + 22, 0, CAB[2] - 14), (CAB[0] + 24, 50, CAB[2] + 12), m["white"], root)
    bx("cab_top", (CAB[0] - 24, 50, CAB[2] - 14), (CAB[0] + 24, 52, CAB[2] + 12), m["white"], root)
    bx("cab_duct", (CAB[0] - 4, 52, CAB[2] - 8), (CAB[0] + 4, 62, CAB[2] + 0), m["sup_steel"], root)
    tops = []
    lines = []
    for k in range(3):
        x = CAB[0] - 14 + k * 14
        O.disc(f"cyl{k}", (x, 19.0, CAB[2]), 5.0, 38.0, m["sup_gas"], root)
        O.ball(f"cyl{k}_dome", (x, 38.0, CAB[2]), 5.0, m["sup_gas"], root)
        O.disc(f"cyl{k}_band", (x, 30.0, CAB[2]), 5.2, 2.5, m[GAS_COLORS[k]], root)
        bx(f"cyl{k}_valve", (x - 1.2, 43, CAB[2] - 1.2), (x + 1.2, 46, CAB[2] + 1.2), m["sup_coil"], root)
        tops.append((x, 46.0, CAB[2]))
        p = [(x, 46, CAB[2]), (x, 48, CAB[2] + 6), (CAB[0] + 30, 48, CAB[2] + 6 - k * 3),
             (PUR[0] - 8, 30 - k * 6, CAB[2] + 6 - k * 3)]
        K.pipe(m, root, f"cab_line{k}", p, 0.8)
        lines.append(p)
    # purifiers and the valve box
    for k in range(3):
        O.disc(f"pur{k}", (PUR[0] - 4 + k * 4, 18, PUR[2] + 6 - k * 3), 1.8, 36, m["sup_steel"], root)
    bx("vmb", (VMB[0] - 10, 0, VMB[2] - 12), (VMB[0] + 10, 34, VMB[2] + 12), m["sup_steel"], root)
    vleds = empty("vmb_leds", root)
    for k in range(6):
        bx(f"vled{k}", (VMB[0] - 7 + k * 2.6, 26, VMB[2] + 12), (VMB[0] - 5.6 + k * 2.6, 28, VMB[2] + 12.4),
           m["sup_he"], vleds)
    to_vmb = []
    to_ch = []
    for k in range(3):
        a = [(PUR[0] - 4 + k * 4, 36, PUR[2] + 6 - k * 3), (PUR[0] - 4 + k * 4, 40, PUR[2] + 6 - k * 3),
             (VMB[0], 40, VMB[2] + 6 - k * 3), (VMB[0], 34, VMB[2] + 6 - k * 3)]
        b = [(VMB[0] + 10, 20 + k * 4, VMB[2] - 3 + k * 3), (20, 20 + k * 4, VMB[2] - 3 + k * 3),
             (30, CHH + 6, CH[2] - 3 + k * 3), (CH[0], CHH + 6, CH[2] - 3 + k * 3)]
        K.pipe(m, root, f"pur_line{k}", a, 0.8)
        K.pipe(m, root, f"ch_line{k}", b, 0.8)
        to_vmb.append(a)
        to_ch.append(b)

    # the process chamber, front cut away
    x0, x1 = CH[0] - CW / 2, CH[0] + CW / 2
    z0, z1 = CH[2] - CD / 2, CH[2] + CD / 2
    bx("ch_back", (x0, 0, z0), (x1, CHH, z0 + 2), m["sup_steel"], root)
    bx("ch_l", (x0, 0, z0), (x0 + 2, CHH, z1), m["sup_steel"], root)
    bx("ch_r", (x1 - 2, 0, z0), (x1, CHH, z1), m["sup_steel"], root)
    bx("ch_lid", (x0, CHH, z0), (x1, CHH + 3, z1), m["sup_steel"], root)
    bx("ch_floor", (x0, 0, z0), (x1, 3, z1), m["sup_pkg"], root)
    bx("showerhead", (CH[0] - 20, CHH - 4, CH[2] - 16), (CH[0] + 20, CHH - 2, CH[2] + 16), m["sup_coil"], root)
    O.disc("chuck", (CH[0], WY / 2, CH[2]), 18.0, WY - 1.0, m["sup_gas"], root)
    O.disc("wafer", (CH[0], WY + 0.3, CH[2]), 16.0, 0.6, m["sg_wafer"], root)
    film = O.disc("film", (CH[0], WY + 0.9, CH[2]), 15.5, 0.6, m["sg_film"], root)
    show(film, [(F(1, 0.5), F(5, 0))])
    # etched trenches cut into the film
    trench = empty("trenches", root)
    for k in range(7):
        x = CH[0] - 10.5 + k * 3.5
        bx(f"trench{k}", (x - 0.6, WY + 0.6, CH[2] - 10), (x + 0.6, WY + 1.35, CH[2] + 10), m["sup_pkg"], trench)
    show(trench, [(F(2, 0.5), F(5, 0))])
    # wall buildup, scrubbed off in beat 3
    dep = empty("wall_dep", root)
    bx("dep_back", (x0 + 2, 4, z0 + 2), (x1 - 2, CHH - 6, z0 + 2.8), m["sg_dep"], dep)
    bx("dep_l", (x0 + 2, 4, z0 + 2), (x0 + 2.8, CHH - 6, z1), m["sg_dep"], dep)
    bx("dep_r", (x1 - 2.8, 4, z0 + 2), (x1 - 2, CHH - 6, z1), m["sg_dep"], dep)
    show(dep, [(F(2, 0.6), F(3, 0.1))])
    # plasmas
    etch_pl = O.disc("etch_plasma", (CH[0], WY + 12, CH[2]), 13.0, 3.0, m["sg_plasma"], root)
    show(etch_pl, [(F(2, 0.15), F(2, 0.9))])
    clean_pl = empty("clean_pl", root)
    bx("clean_plasma", (x0 + 4, 5, z0 + 4), (x1 - 4, CHH - 6, z0 + 5), m["sg_pink"], clean_pl)
    show(clean_pl, [(F(3, 0.1), F(3, 0.95))])
    # abatement on the exhaust
    bx("abate", (x1 + 10, 0, CH[2] - 8), (x1 + 24, 30, CH[2] + 8), m["white"], root)
    exh = [(x1, 6, CH[2]), (x1 + 10, 6, CH[2])]
    K.pipe(m, root, "exhaust", exh, 1.2)

    # flows
    for k in range(3):
        mk = m[GAS_COLORS[k]]
        run(root, f"cab_flow{k}", lines[k], 3, 1.1, mk, [0, 4], 0.05 * k, 0.8, 30)
        run(root, f"pur_flow{k}", to_vmb[k], 3, 1.1, mk, [0, 4], 0.2, 0.9, 25)
        run(root, f"ch_flow{k}", to_ch[k], 3, 1.1, mk, [0, 1, 2, 3], 0.1, 0.9, 30)
    for b in (0, 4):
        blink(vleds, b, [0, 2, 4, 6], n=8, on=0.5)
    # deposition: molecules fall from the showerhead and stick
    for k in range(8):
        x = CH[0] - 14 + k * 4
        dz = (k % 3 - 1) * 6
        run(root, f"dep_drop{k}", [(x, CHH - 5, CH[2] + dz), (x, WY + 1.2, CH[2] + dz)], 3, 1.5,
            m["sup_flow" if k % 2 else "sup_he"], [1], 0.05 * (k % 4), 0.95, 20)
    # etch ions striking
    for k in range(6):
        x = CH[0] - 9 + k * 3.5
        run(root, f"ion{k}", [(x, WY + 14, CH[2]), (x, WY + 1.0, CH[2])], 3, 0.6, m["sg_violet"], [2],
            0.15 + 0.03 * k, 0.9, 12)
    # clean: NF3 in, fluorine out the exhaust
    run(root, "clean_out", [(x1 - 4, 8, CH[2]), (x1 + 10, 6, CH[2])], 6, 1.0, m["sg_pink"], [3], 0.2, 0.9, 18)
    rise(root, "abate_heat", (x1 + 17, 30, CH[2]), 6, 0.9, m["sup_hot"], [3], h=18.0)

    tags = {
        0: [("NF3, WF6, silane", tops[1]), ("vented gas cabinet", (CAB[0], 62.0, CAB[2])),
            ("purifiers", (PUR[0], 40.0, PUR[2])), ("valve box to tools", (VMB[0], 34.0, VMB[2]))],
        1: [("WF6 + reducer meet", (CH[0], CHH - 3, CH[2])), ("tungsten film lands", (CH[0] + 12, WY + 1, CH[2] + 8)),
            ("nm per pass", (CH[0] - 14, WY, CH[2] + 12))],
        2: [("fluorine plasma", (CH[0], WY + 15, CH[2])), ("ions cut trenches", (CH[0] + 10, WY + 1, CH[2] + 10)),
            ("more etch for 3D NAND", (x1, CHH, CH[2]))],
        3: [("buildup on walls", (x0 + 4, 30.0, z0 + 3)), ("NF3 plasma scrubs it", (CH[0], 25.0, CH[2])),
            ("abatement burns exhaust", (x1 + 17, 30.0, CH[2]))],
        4: [("ppb purity", tops[0]), ("few plants per gas", (CAB[0], 62.0, CAB[2])),
            ("LIN, APD, ENTG", (VMB[0], 34.0, VMB[2]))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-90.0, 25.0, -40.0), 110.0, 0.30, 0.25),
        frame((CH[0], 22.0, CH[2]), 70.0, 0.20, 0.30),
        frame((CH[0], 20.0, CH[2]), 85.0, 0.20, 0.35),
        frame((CH[0] + 10, 20.0, CH[2]), 90.0, 0.35, 0.25),
        frame((-30.0, 25.0, -40.0), 230.0, 0.25, 0.35),
    ], root)


if __name__ == "__main__":
    build()

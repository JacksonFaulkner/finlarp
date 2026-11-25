"""TRM_NPU: a phone opened up on the bench, its logic board and application processor, and the
SoC die drawn huge beside it: CPU cores, GPU, NPU and caches. The NPU's grid of multiply-accumulate
cells lights up as weights and activations stream through; a request that would go to a far-off
cloud rack is answered locally instead.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_npu.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from power_vrm_detail import frame, run, blink, rise  # noqa: E402

SLUG = "TRM_NPU"
BEATS = [
    ("Inside a phone or laptop, one chip runs everything",
     "Open a phone and most of the logic board is one application processor (SoC) with its memory stacked on or beside "
     "it, plus modem, power and camera chips. That one SoC holds the CPU, the graphics, the image processor and, since "
     "about 2017, a neural processing unit."),
    ("The SoC is a set of blocks; the NPU is one of them",
     "On the die the CPU cores, GPU, caches, memory controllers and NPU sit side by side. The NPU takes a fair slice of "
     "area but runs only one kind of work: the matrix math of neural networks. Apple calls it the Neural Engine; "
     "Qualcomm the Hexagon NPU; Intel and AMD put one in every AI PC chip."),
    ("Inside the NPU: a grid of multiply-accumulate cells",
     "A neural network is mostly multiplying big matrices. The NPU lays out thousands of small multiply-accumulate (MAC) "
     "cells in a grid, feeds weights in from one side and activations from the other, and keeps both in local SRAM so "
     "they rarely travel to DRAM. Low-precision INT8 or INT4 math keeps each cell tiny and frugal."),
    ("It answers on the device instead of in the cloud",
     "Because the NPU does that math at a few watts, speech recognition, photo processing, translation and small "
     "language models can run on the device: faster, offline and private, with no round trip to a data-centre GPU. The "
     "CPU or GPU could do it too, but at several times the energy."),
    ("TOPS on the spec sheet sell AI PCs and phones",
     "NPUs are rated in TOPS (trillions of operations per second): about 40-50 TOPS is the bar for a Copilot+ PC, and "
     "phone NPUs are in the same range. That rating drives device upgrade cycles more than data-centre spend. Makers: "
     "Qualcomm (QCOM), Apple (AAPL), Intel (INTC), AMD (AMD), MediaTek; Arm (ARM) licenses NPU designs."),
]

# the giant die
GX0, GX1, GZ0 = 70.0, 200.0, -90.0
TY = 6.0
NPU = (140.0, 196.0, GZ0 + 6.0, -6.0)  # x0, x1, z0, z1
SOC = (0.0, 0.0, -80.0)


def mats(m):
    for k, c in (("cpu", (0.30, 0.42, 0.62)), ("gpu", (0.22, 0.48, 0.40)), ("npu", (0.50, 0.30, 0.52)),
                 ("isp", (0.58, 0.48, 0.22)), ("sram", (0.32, 0.30, 0.40)), ("glass", (0.05, 0.06, 0.08)),
                 ("frame", (0.55, 0.57, 0.60)), ("cloud", (0.30, 0.32, 0.36))):
        m[k] = mat(f"npu_{k}", c, metal=0.45, rough=0.35)
    m["mac_g"] = mat("npu_mac_g", (0.95, 0.50, 1.0), emit=(0.90, 0.45, 1.0), strength=1.8)
    m["cpu_g"] = mat("npu_cpu_g", (0.35, 0.65, 1.0), emit=(0.30, 0.60, 1.0), strength=1.4)
    m["batt"] = mat("npu_batt", (0.20, 0.22, 0.26), metal=0.2, rough=0.6)


def phone(m, root):
    """A phone lying flat, back off, front edge cut open: frame, battery, logic board with chips."""
    g = empty("phone", root)
    x0, x1, z0, z1 = -40.0, 40.0, -160.0, 0.0
    bx("ph_glass", (x0, 0.0, z0), (x1, 1.2, z1), m["glass"], g)
    bx("ph_disp", (x0 + 1.0, 1.2, z0 + 1.0), (x1 - 1.0, 2.2, z1), m["screen"], g)
    for s in (-1, 1):
        bx(f"ph_side{s}", ((x0 if s < 0 else x1 - 2.0), 0.0, z0), ((x0 + 2.0 if s < 0 else x1), 9.0, z1), m["frame"], g)
    bx("ph_top", (x0, 0.0, z0), (x1, 9.0, z0 + 2.0), m["frame"], g)
    bx("ph_batt", (x0 + 4.0, 2.2, z0 + 50.0), (x1 - 4.0, 7.0, z1 - 4.0), m["batt"], g)
    # logic board at the top of the phone
    bx("ph_pcb", (x0 + 3.0, 2.2, z0 + 3.0), (x1 - 3.0, 3.4, z0 + 46.0), m["mask"], g)
    soc = (0.0, 3.4, z0 + 24.0)
    bx("ph_soc", (soc[0] - 9.0, 3.4, soc[2] - 9.0), (soc[0] + 9.0, 5.0, soc[2] + 9.0), m["substrate"], g)
    bx("ph_dram", (soc[0] - 8.0, 5.0, soc[2] - 8.0), (soc[0] + 8.0, 7.0, soc[2] + 8.0), m["mold"], g)  # PoP memory
    for k, (cx, cz, w) in enumerate(((-24.0, z0 + 12.0, 8.0), (24.0, z0 + 14.0, 9.0), (-24.0, z0 + 34.0, 7.0), (22.0, z0 + 34.0, 6.0))):
        bx(f"ph_ic{k}", (cx - w / 2, 3.4, cz - w / 2), (cx + w / 2, 4.6, cz + w / 2), m["mold"], g)
    for i in range(10):
        D.mlcc(m, g, f"ph_c{i}", (-14.0 + 3.0 * i, 3.4, z0 + 40.0), 1.6, 0.8, 0.8)
    bx("ph_cam", (-30.0, 3.4, z0 + 4.0), (-20.0, 8.0, z0 + 14.0), m["dark"], g)
    return {"soc": (soc[0], 7.0, soc[2]), "batt": (0.0, 7.0, -60.0), "cam": (-25.0, 8.0, z0 + 9.0), "board": (24.0, 4.6, z0 + 14.0)}


def giant(m, root):
    g = empty("gsoc", root)
    bx("g_sub", (GX0, 0.0, GZ0), (GX1, 3.0, 0.0), m["substrate"], g)
    for k, y in enumerate((0.8, 1.8)):
        bx(f"g_subcu{k}", (GX0, y, GZ0), (GX1, y + 0.3, 0.15), m["copper"], g)
    bx("g_die", (GX0 + 2.0, 3.0, GZ0 + 2.0), (GX1 - 2.0, TY, 0.0), m["die"], g)
    for k in range(4):
        y = 4.6 + 0.3 * k
        bx(f"g_bm{k}", (GX0 + 2.0, y, -0.4), (GX1 - 2.0, y + 0.12, 0.1), m["copper"], g)
    pts = {}
    cpu_g = empty("cpu_g", root)
    for i in range(2):  # 2 big + 6 little cores
        for j in range(4):
            big = i == 0 and j < 2
            x0, z0 = GX0 + 6.0 + 14.0 * i, GZ0 + 6.0 + 10.0 * j
            w = 12.0 if big else 9.0
            bx(f"g_cpu{i}{j}", (x0, TY, z0), (x0 + w, TY + (2.0 if big else 1.4), z0 + 8.0), m["cpu"], g)
            bx(f"g_cpug{i}{j}", (x0 + 0.5, TY + (2.0 if big else 1.4), z0 + 0.5), (x0 + w - 0.5, TY + 2.3, z0 + 7.5), m["cpu_g"], cpu_g)
    show(cpu_g, [])
    pts["cpu"] = (GX0 + 18.0, TY + 2.0, GZ0 + 20.0)
    bx("g_l3", (GX0 + 6.0, TY, GZ0 + 48.0), (GX0 + 32.0, TY + 1.0, GZ0 + 58.0), m["sram"], g)
    pts["l3"] = (GX0 + 19.0, TY + 1.0, GZ0 + 53.0)
    # GPU: shader cores
    for i in range(3):
        for j in range(4):
            x0, z0 = GX0 + 38.0 + 10.0 * i, GZ0 + 6.0 + 12.0 * j
            bx(f"g_gpu{i}{j}", (x0, TY, z0), (x0 + 8.5, TY + 1.6, z0 + 10.0), m["gpu"], g)
    pts["gpu"] = (GX0 + 53.0, TY + 1.6, GZ0 + 30.0)
    bx("g_isp", (GX0 + 6.0, TY, GZ0 + 62.0), (GX0 + 32.0, TY + 1.2, -6.0), m["isp"], g)
    pts["isp"] = (GX0 + 19.0, TY + 1.2, -12.0)
    bx("g_mc", (GX0 + 38.0, TY, GZ0 + 62.0), (GX0 + 66.0, TY + 1.2, -6.0), m["sram"], g)
    pts["mc"] = (GX0 + 52.0, TY + 1.2, -12.0)
    # NPU: SRAM banks on two sides, a 10 x 8 MAC grid
    nx0, nx1, nz0, nz1 = NPU
    bx("g_npu", (nx0, TY, nz0), (nx1, TY + 0.8, nz1), m["npu"], g)
    bx("g_wsram", (nx0 + 2.0, TY + 0.8, nz0 + 2.0), (nx1 - 2.0, TY + 2.4, nz0 + 10.0), m["sram"], g)
    bx("g_asram", (nx0 + 2.0, TY + 0.8, nz0 + 12.0), (nx0 + 10.0, TY + 2.4, nz1 - 2.0), m["sram"], g)
    cols = []
    cells = []
    cx0, cz0 = nx0 + 13.0, nz0 + 13.0
    sx, sz = (nx1 - 2.0 - cx0) / 10, (nz1 - 2.0 - cz0) / 8
    for i in range(10):
        cg = empty(f"mac_col{i}", root)
        for j in range(8):
            x, z = cx0 + sx * i, cz0 + sz * j
            cells.append(bx(f"g_mac{i}{j}", (x + 0.4, TY + 0.8, z + 0.4), (x + sx - 0.4, TY + 2.0, z + sz - 0.4), m["npu"], g))
            bx(f"g_macg{i}{j}", (x + 0.8, TY + 2.0, z + 0.8), (x + sx - 0.8, TY + 2.3, z + sz - 0.8), m["mac_g"], cg)
        show(cg, [])
        cols.append(cg)
    D.join(cells, "g_macs")
    pts.update(npu=((nx0 + nx1) / 2, TY + 2.3, (nz0 + nz1) / 2), wsram=((nx0 + nx1) / 2, TY + 2.4, nz0 + 6.0),
               asram=(nx0 + 6.0, TY + 2.4, -20.0), grid=(cx0 + sx * 5, TY + 2.3, cz0 + sz * 4))
    geo = dict(cx0=cx0, cz0=cz0, sx=sx, sz=sz)
    return cpu_g, cols, pts, geo


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    ph = phone(m, root)
    cpu_g, cols, gp, geo = giant(m, root)
    C.magnify(m, root, ph["soc"], (GX0, 8.0, -45.0), r=4.0)
    # a cloud rack far back right
    cl = empty("cloud", root)
    rx, rz = 250.0, -260.0
    bx("rack", (rx - 15.0, 0.0, rz - 15.0), (rx + 15.0, 80.0, rz + 15.0), m["cloud"], cl)
    for k in range(8):
        bx(f"rack_s{k}", (rx - 13.0, 6.0 + 9.0 * k, rz + 15.0), (rx + 13.0, 12.0 + 9.0 * k, rz + 15.4), m["dark"], cl)
        bx(f"rack_l{k}", (rx + 9.0, 8.0 + 9.0 * k, rz + 15.4), (rx + 11.0, 9.0 + 9.0 * k, rz + 15.6), m["sig"], cl)

    # beat 1: CPU cores tick
    show(cpu_g, [(F(1, 0.2), F(2, 0))])
    blink(cpu_g, 3, [0, 1], n=8, on=0.5)
    # beat 2-4: the MAC grid lights column by column as data sweeps across
    for i, cg in enumerate(cols):
        iv = []
        for b in (2, 3, 4):
            for rep in range(3):
                a = 0.08 + rep * 0.3 + 0.02 * i
                iv.append((F(b, a), F(b, a + 0.12)))
        show(cg, iv)
    y = TY + 3.0
    for j in range(4):  # activations stream in from the left SRAM along rows
        z = geo["cz0"] + geo["sz"] * (2 * j + 0.5)
        run(root, f"act{j}", [(NPU[0] + 6.0, y, z), (NPU[1] - 2.0, y, z)], 4, 0.6, m["e_blue"], [2, 3], 0.05 * j, 0.85, 30)
    for i in range(5):  # weights stream down from the top SRAM along columns
        x = geo["cx0"] + geo["sx"] * (2 * i + 0.5)
        run(root, f"wt{i}", [(x, y + 0.5, NPU[2] + 6.0), (x, y + 0.5, NPU[3])], 4, 0.6, m["h_amber"], [2, 3], 0.05 * i, 0.85, 30)
    # beat 3: the request stays local; the cloud path is drawn dim and unused
    D.polyline("cloud_link", [(30.0, 12.0, -140.0), (140.0, 60.0, -220.0), (rx - 15.0, 60.0, rz)], 0.3, m["dim_glow"], root)
    run(root, "local", [ph["cam"], (0.0, 10.0, -140.0), ph["soc"]], 6, 1.0, m["sig"], 3, 0.0, 0.6, 30)
    run(root, "local_ans", [ph["soc"], (0.0, 10.0, -60.0), (0.0, 4.0, -20.0)], 6, 1.0, m["sig"], 3, 0.3, 0.9, 30)
    rise(root, "soc_heat", (0.0, 7.5, ph["soc"][2]), 3, 0.5, m["heat"], 3, 0.1, 0.9, 10.0, 40, (4.0, 4.0))
    C.tags(root, {
        0: [("application processor (SoC)", ph["soc"]), ("battery", ph["batt"]), ("camera", ph["cam"]),
            ("modem, power chips", ph["board"])],
        1: [("CPU cores", gp["cpu"]), ("GPU", gp["gpu"]), ("NPU", gp["npu"]), ("image processor", gp["isp"]), ("cache", gp["l3"])],
        2: [("weights from SRAM", gp["wsram"]), ("activations in", gp["asram"]), ("MAC grid: INT8 / INT4", gp["grid"])],
        3: [("answered on the phone", ph["soc"]), ("no trip to the cloud", (rx, 82.0, rz)), ("a few watts", gp["npu"])],
        4: [("40-50 TOPS", gp["grid"]), ("QCOM, AAPL, INTC, AMD, ARM", gp["cpu"])],
    })
    bc = ((GX0 + GX1) / 2, TY, GZ0 / 2)
    C.done(SLUG, BEATS, [
        frame((0.0, 4.0, -80.0), 180.0, 0.30, 0.70, pad=1.0),
        frame(bc, 140.0, 0.20, 0.75),
        frame(((NPU[0] + NPU[1]) / 2, TY, (NPU[2] + NPU[3]) / 2), 75.0, 0.15, 0.80),
        frame((110.0, 20.0, -150.0), 420.0, 0.30, 0.55, pad=1.0),
        frame(bc, 140.0, -0.15, 0.55),
    ], root)


if __name__ == "__main__":
    build()

"""TRM_EDGE_AI: inference on the device instead of the data center. A car on a road with a
windshield camera and a pedestrian ahead; its edge SoC drawn ~large on a stand beside the road,
lid off (CPU cluster, GPU, NPU MAC array, LPDDR, ISP); far down the road a small data-center
building with racks that the cloud round trip has to reach.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_edge_ai.py

Beats:
  0 device   the car sees a pedestrian; the camera feeds the computer in the car
  1 soc      the SoC opened: NPU, CPU, GPU, memory, image processor
  2 local    local loop (fast) vs cloud round trip (slow, far away)
  3 budget   a few watts: heat rising, TOPS per watt
  4 market   phones, PCs, cameras, robots; who sells the chips
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, mat, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_EDGE_AI"
BEATS = [
    ("Edge AI runs the model on the device itself",
     "A car's camera sees a pedestrian and the car must brake within a fraction of a second. Edge AI means the neural "
     "network runs on a chip inside the car (or phone, camera, PC, robot) rather than in a data center. The camera "
     "frames go a few centimetres to the computer, not hundreds of kilometres."),
    ("Inside the chip: an NPU next to the CPU and GPU",
     "An edge system-on-chip packs CPU cores for control, a GPU for graphics and some AI, an image signal processor "
     "for the camera, and a neural processing unit (NPU): a big array of multiply-accumulate units built for "
     "inference at low power. LPDDR memory sits right beside it on the package."),
    ("Local answers in milliseconds; the cloud adds a round trip",
     "On the device, a frame goes camera -> NPU -> brake decision in tens of milliseconds, with no network needed. "
     "Sending it to a data center adds radio and network hops both ways and can stall when coverage drops. Edge "
     "inference also saves bandwidth and keeps data private."),
    ("The limit is power and heat: TOPS per watt",
     "A phone chip has a few watts to spend and a car computer tens of watts, against hundreds to over a thousand "
     "for one data-center GPU. So edge chips are rated in TOPS (trillion operations per second) per watt, run smaller "
     "or quantized models (8-bit or 4-bit), and are limited by memory capacity and bandwidth."),
    ("Edge chips ship in phones, PCs, cars, cameras and robots",
     "Every new phone and 'AI PC' has an NPU, cars carry driver-assist SoCs, and cameras and robots run vision "
     "models locally. Related: Qualcomm (QCOM) in phones, PCs and cars, Ambarella (AMBA) in vision SoCs, NXP (NXPI) "
     "in cars and industry, Intel (INTC) in AI PCs; also Apple, MediaTek and NVIDIA's Jetson/DRIVE."),
]

CAR = (-150.0, 0.0, -30.0)  # car rear-left base corner x, ground y, centre z
PED = (-20.0, 0.0, -30.0)
SOC = (20.0, 110.0, -150.0, -80.0)  # x0, x1, z0, z1 of the big chip on its stand
SY = 14.0  # stand height
DC = (300.0, -60.0)  # data-center x, z


def mats(m):
    m["paint"] = mat("edge_paint", (0.70, 0.12, 0.10), metal=0.6, rough=0.3)
    m["glass"] = mat("edge_glass", (0.25, 0.35, 0.45), metal=0.2, rough=0.1)
    m["road"] = mat("edge_road", (0.18, 0.18, 0.20), rough=0.9)
    m["line"] = mat("edge_line", (0.90, 0.88, 0.70), rough=0.6)
    m["skin"] = mat("edge_ped", (0.85, 0.65, 0.20), rough=0.6)
    m["npu_on"] = mat("edge_npu", (0.45, 1.0, 0.55), emit=(0.40, 1.0, 0.50), strength=3.0)
    m["cpu_on"] = mat("edge_cpu", (0.35, 0.75, 1.0), emit=(0.30, 0.70, 1.0), strength=3.0)
    m["box"] = mat("edge_box", (1.0, 0.85, 0.2), emit=(1.0, 0.80, 0.15), strength=3.0)


def car(m, root):
    x, y, z = CAR
    g = empty("car", root)
    bx("car_body", (x, 4.0, z - 16.0), (x + 70.0, 16.0, z + 16.0), m["paint"], g)
    bx("car_cab", (x + 14.0, 16.0, z - 14.0), (x + 50.0, 28.0, z + 14.0), m["glass"], g)
    bx("car_roof", (x + 18.0, 28.0, z - 13.0), (x + 46.0, 29.0, z + 13.0), m["paint"], g)
    for wx in (x + 12.0, x + 56.0):
        for wz in (z - 16.0, z + 16.0):
            D.tube(f"car_w{wx:.0f}{wz:.0f}", (wx, 6.0, wz - 2.5), (wx, 6.0, wz + 2.5), 6.0, m["rubber"], g, 20)
    for lz in (z - 11.0, z + 11.0):
        bx(f"car_hl{lz:.0f}", (x + 70.0, 10.0, lz - 3.0), (x + 70.4, 13.0, lz + 3.0), m["bit"], g)
    cam = (x + 50.0, 26.0, z)
    bx("car_cam", (cam[0] - 2.0, cam[1] - 2.0, z - 2.0), (cam[0] + 1.0, cam[1] + 1.0, z + 2.0), m["plastic"], g)
    ecu = (x + 6.0, 16.5, z)
    bx("car_ecu", (x + 2.0, 16.0, z - 6.0), (x + 12.0, 19.0, z + 6.0), m["alu"], g)
    return {"cam": cam, "ecu": ecu, "car": (x + 35.0, 29.0, z), "wheel": (x + 56.0, 0.0, z + 18.0)}


def pedestrian(m, root):
    x, y, z = PED
    g = empty("ped", root)
    for s in (-1, 1):
        bx(f"ped_leg{s}", (x - 1.5, 0.0, z + s * 2.0 - 1.0), (x + 1.5, 10.0, z + s * 2.0 + 1.0), m["dark"], g)
    bx("ped_torso", (x - 2.5, 10.0, z - 3.5), (x + 2.5, 20.0, z + 3.5), m["skin"], g)
    D.tube("ped_head", (x, 20.5, z), (x, 24.5, z), 2.2, m["ceramic"], g, 16)
    box = empty("ped_box", root)
    pts = [(x - 6.0, 0.5, z), (x - 6.0, 28.0, z), (x + 6.0, 28.0, z), (x + 6.0, 0.5, z), (x - 6.0, 0.5, z)]
    D.polyline("ped_bb", [(p[0], p[1], z - 8.0) for p in pts], 0.35, m["box"], box)
    show(box, [(F(0, 0.5), F(1, 0)), (F(2, 0.3), F(3, 0))])
    return {"ped": (x, 28.0, z - 8.0)}


def soc(m, root):
    x0, x1, z0, z1 = SOC
    g = empty("soc", root)
    bx("st_post", ((x0 + x1) / 2 - 4.0, 0.0, (z0 + z1) / 2 - 4.0), ((x0 + x1) / 2 + 4.0, SY, (z0 + z1) / 2 + 4.0), m["dark"], g)
    bx("st_pcb", (x0 - 8.0, SY, z0 - 8.0), (x1 + 8.0, SY + 1.6, z1 + 8.0), m["mask"], g)
    y = SY + 1.6
    bx("soc_sub", (x0, y, z0), (x1, y + 2.0, z1), m["substrate"], g)
    y += 2.0
    bx("soc_die", (x0 + 4.0, y, z0 + 4.0), (x1 - 30.0, y + 1.2, z1 - 4.0), m["die"], g)
    yt = y + 1.2
    # LPDDR stacks beside the die
    for k, (za, zb) in enumerate(((z0 + 4.0, z0 + 33.0), (z0 + 37.0, z1 - 4.0))):
        for L in range(4):
            bx(f"lp{k}_{L}", (x1 - 26.0, y + 1.6 * L, za), (x1 - 4.0, y + 1.6 * L + 1.3, zb), m["hbm_dram"], g)
            bx(f"lp{k}_{L}m", (x1 - 26.0, y + 1.6 * L + 1.3, za), (x1 - 4.0, y + 1.6 * (L + 1), zb), m["mold"], g)
    # NPU MAC array: 8 x 6 cells, left half of the die
    npu = [empty(f"npu{k}", root) for k in range(4)]
    for i in range(8):
        for j in range(6):
            cx, cz = x0 + 8.0 + 4.4 * i, z0 + 8.0 + 4.4 * j
            bx(f"mac{i}{j}", (cx, yt, cz), (cx + 3.6, yt + 1.0, cz + 3.6), m["si"], g)
            bx(f"macg{i}{j}", (cx + 0.3, yt + 1.0, cz + 0.3), (cx + 3.3, yt + 1.15, cz + 3.3), m["npu_on"], npu[(i + j) % 4])
    # CPU cluster: 4 cores with cache, GPU block, ISP
    cpu = empty("cpu_g", root)
    for k in range(4):
        cx = x0 + 47.0 + 5.5 * (k % 2)
        cz = z0 + 8.0 + 6.0 * (k // 2)
        bx(f"cpu{k}", (cx, yt, cz), (cx + 4.6, yt + 1.4, cz + 5.0), m["fet"], g)
        bx(f"cpug{k}", (cx + 0.4, yt + 1.4, cz + 0.4), (cx + 4.2, yt + 1.55, cz + 4.6), m["cpu_on"], cpu)
    bx("l3", (x0 + 47.0, yt, z0 + 21.0), (x0 + 57.5, yt + 0.8, z0 + 26.0), m["cold"], g)
    bx("gpu_blk", (x0 + 47.0, yt, z0 + 30.0), (x0 + 57.5, yt + 1.4, z0 + 46.0), m["driver"], g)
    bx("isp_blk", (x0 + 8.0, yt, z0 + 36.0), (x0 + 40.0, yt + 1.2, z1 - 6.0), m["cell"] if "cell" in m else m["gan"], g)
    for k in npu + [cpu]:
        show(k, [])
    return npu, cpu, {
        "npu": (x0 + 25.0, yt + 1.2, z0 + 20.0), "cpu": (x0 + 52.0, yt + 1.6, z0 + 14.0),
        "gpu": (x0 + 52.0, yt + 1.4, z0 + 40.0), "isp": (x0 + 24.0, yt + 1.2, z1 - 8.0),
        "lp": (x1 - 15.0, y + 6.4, z1 - 10.0), "soc": ((x0 + x1) / 2, yt, (z0 + z1) / 2), "yt": yt}


def datacenter(m, root):
    x, z = DC
    g = empty("dc", root)
    bx("dc_bld", (x - 40.0, 0.0, z - 50.0), (x + 40.0, 40.0, z + 20.0), m["grid"], g)
    bx("dc_roof", (x - 42.0, 40.0, z - 52.0), (x + 42.0, 42.0, z + 22.0), m["dark"], g)
    leds = empty("dc_leds", root)
    for k in range(6):  # racks seen through an open front wall
        rx = x - 34.0 + 12.0 * k
        bx(f"dc_r{k}", (rx, 0.0, z + 10.0), (rx + 9.0, 34.0, z + 20.5), m["dark"], g)
        for s in range(6):
            bx(f"dc_l{k}{s}", (rx + 2.0, 4.0 + 5.0 * s, z + 20.5), (rx + 7.0, 5.0 + 5.0 * s, z + 21.0), m["sig"], leds)
    tower = empty("tw", root)
    bx("tw_mast", (-60.0, 0.0, -142.0), (-56.0, 70.0, -138.0), m["steel"], tower)
    for k in range(3):
        bx(f"tw_ant{k}", (-62.0 + 4.0 * k, 60.0, -140.0), (-60.5 + 4.0 * k, 70.0, -137.5), m["white"], tower)
    blink(leds, 2, [0, 2, 4, 6], n=8, on=0.6)
    return {"dc": (x, 42.0, z), "tw": (-58.0, 70.0, -140.0)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("ground", (-220.0, -3.0, -200.0), (360.0, -1.0, 40.0), m["grass"] if "grass" in m else m["mask"], root)
    bx("road", (-220.0, -1.0, -55.0), (360.0, 0.0, -5.0), m["road"], root)
    for k in range(14):
        xa = -215.0 + 40.0 * k
        bx(f"dash{k}", (xa, 0.0, -31.0), (xa + 18.0, 0.1, -29.0), m["line"], root)
    cp = car(m, root)
    pp = pedestrian(m, root)
    npu, cpu, sp = soc(m, root)
    dp = datacenter(m, root)
    C.magnify(m, root, cp["ecu"], (SOC[0] - 4.0, sp["yt"], -115.0), r=5.0)

    # beat 0: light from the pedestrian to the camera, frames to the computer
    run(root, "img", [pp["ped"], cp["cam"]], 6, 0.8, m["bit"], [0, 2], 0.1, 0.8, 20)
    run(root, "frm", [cp["cam"], (cp["cam"][0] - 20.0, 30.0, CAR[2]), cp["ecu"]], 6, 0.9, m["e_blue"], [0, 2], 0.2, 0.9, 20)
    # beat 1: the NPU array lights in waves, the CPU ticks
    for k, g in enumerate(npu):
        show(g, [(F(1, 0.1 + 0.05 * k), F(4, 0))])
    blink(cpu, 1, [0, 1, 2, 3, 4, 5, 6, 7], n=8, on=0.4)
    run(root, "isp_npu", [sp["isp"], sp["npu"]], 5, 0.7, m["e_blue"], 1, 0.0, 0.8, 18)
    run(root, "mem", [sp["lp"], sp["npu"]], 5, 0.7, m["v12"], 1, 0.1, 0.9, 22)
    # beat 2: local loop (short, quick, repeats) vs cloud round trip (long, slow)
    run(root, "cloud", [cp["car"], dp["tw"], (120.0, 80.0, -120.0), dp["dc"], (150.0, 70.0, -110.0), dp["tw"], cp["car"]],
        3, 1.4, m["warn"], 2, 0.0, 0.25, 140)
    brake = empty("brake", root)
    for lz in (CAR[2] - 12.0, CAR[2] + 12.0):
        bx(f"brk{lz:.0f}", (CAR[0] - 0.4, 10.0, lz - 3.0), (CAR[0], 13.0, lz + 3.0), m["warn"], brake)
    show(brake, [(F(2, 0.2), F(3, 0))])
    # beat 3: heat off the chip
    rise(root, "soc_heat", (sp["soc"][0], sp["yt"] + 1.0, sp["soc"][2]), 7, 1.0, m["heat"], 3, 0.0, 0.85, 26.0, 55, (25.0, 18.0))

    C.tags(root, {
        0: [("camera sees a pedestrian", pp["ped"]), ("windshield camera", cp["cam"]), ("computer in the car", cp["ecu"]),
            ("its SoC, enlarged", sp["soc"])],
        1: [("NPU: MAC array", sp["npu"]), ("CPU cores", sp["cpu"]), ("GPU", sp["gpu"]),
            ("image signal processor", sp["isp"]), ("LPDDR memory", sp["lp"])],
        2: [("on-device: ~10s of ms", cp["car"]), ("cloud: network both ways", dp["tw"]), ("data center far away", dp["dc"])],
        3: [("a few W phone, ~10s W car", sp["soc"]), ("rated in TOPS per watt", sp["npu"]), ("8-bit / 4-bit models", sp["lp"])],
        4: [("phones, AI PCs, cars, cameras", cp["car"]), ("QCOM, AMBA, NXPI, INTC", sp["soc"])],
    })
    sc = ((SOC[0] + SOC[1]) / 2, sp["yt"], (SOC[2] + SOC[3]) / 2)
    C.done(SLUG, BEATS, [
        frame((-70.0, 15.0, -30.0), 200.0, 0.40, 0.30),
        frame(sc, 100.0, 0.20, 0.80),
        frame((80.0, 30.0, -70.0), 460.0, 0.10, 0.35, pad=1.0),
        frame(sc, 110.0, 0.40, 0.45),
        frame((-20.0, 15.0, -40.0), 270.0, -0.35, 0.35),
    ], root)


if __name__ == "__main__":
    build()

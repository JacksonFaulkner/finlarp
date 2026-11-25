"""TRM_NEUROMORPHIC_COMPUTING: the Terms-tab overview for neuromorphic computing.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_neuromorphic_computing.py

Writes assets/term_TRM_NEUROMORPHIC_COMPUTING.glb. Captions in specs/terms/TRM_NEUROMORPHIC_COMPUTING.json.

Beats:
  0 bottleneck  a processor and a separate memory chip, data shuttling (and heating) between them
  1 cores       the neuromorphic die cut open: a mesh of cores, each with its own synapse memory + neurons
  2 spikes      event-driven: only cores that receive a spike wake up and fire along the mesh
  3 edge        an event camera feeds sparse spikes; milliwatts instead of watts
  4 reality     next to a GPU rack: promising at the edge, small commercial footprint
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
from sand_overview import F, empty, show  # noqa: E402
from power_vrm_detail import blink, bx, frame, polyline, rise, run  # noqa: E402

import term_common as C  # noqa: E402
import kit_photonics as K  # noqa: E402

SLUG = "TRM_NEUROMORPHIC_COMPUTING"
BEATS = [
    ("Ordinary chips spend most energy moving data",
     "In a CPU or GPU, the weights of a neural network sit in memory chips separate from the compute units, and every "
     "step hauls them across the bus. Moving a number from DRAM can cost 100x more energy than the arithmetic done on "
     "it. This split, the von Neumann bottleneck, is what neuromorphic chips try to remove."),
    ("A neuromorphic chip is a mesh of tiny cores, each with its own memory",
     "The die is tiled with many small cores. Each core holds its own synapse memory (the weights) right next to a "
     "group of digital neurons, so data barely moves. Intel's Loihi 2 has 128 such cores and about a million neurons; "
     "the cores talk over an on-chip mesh network."),
    ("Neurons fire spikes, and only busy cores wake up",
     "Each neuron adds up incoming spikes and fires its own spike when a threshold is crossed. A spike is a small "
     "packet routed across the mesh to the neurons it connects to. Cores with no incoming spikes stay idle, so "
     "power tracks activity instead of clock speed."),
    ("Best fit: sparse sensor data at the edge",
     "Event cameras and other sensors send a signal only when something changes, which suits spiking chips well. "
     "Gesture, keyword or anomaly detection can run in milliwatts on a battery device, where a GPU would need watts. "
     "BrainChip's Akida is sold as licensable IP and small chips for this."),
    ("Promising, but GPUs still carry almost all AI",
     "Spiking networks are hard to train and lack the software stack that CUDA gives GPUs, so neuromorphic chips remain "
     "mostly research and niche edge parts. Data-centre AI still runs on GPUs and accelerators. Related: Intel (INTC, "
     "Loihi), BrainChip (BRCHF), NVIDIA (NVDA), Qualcomm (QCOM)."),
]

N = 6           # mesh is N x N cores
PITCH = 16.0
CX, CZ = 0.0, 0.0
CY = 6.0        # top of the die


def core_c(i, j):
    return (CX + (i - (N - 1) / 2) * PITCH, CY, CZ + (j - (N - 1) / 2) * PITCH)


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)

    # ---- beat 0: von Neumann pair at the left, x -190..-90 ----
    vn = empty("vn", root)
    bx("vn_board", (-195.0, -1.6, -30.0), (-85.0, 0.0, 30.0), m["ph_pcb"], vn)
    bx("cpu", (-185.0, 0.0, -14.0), (-157.0, 5.0, 14.0), m["ph_dsp"], vn)
    bx("cpu_lid", (-182.0, 5.0, -11.0), (-160.0, 6.0, 11.0), m["steel"], vn)
    for k in range(4):
        bx(f"dram{k}", (-112.0, 0.0, -24.0 + 12.5 * k), (-92.0, 4.0, -15.0 + 12.5 * k), m["ph_dsp"], vn)
    for k in range(8):
        z = -12.0 + 3.4 * k
        polyline(f"bus{k}", [(-157.0, 1.0, z * 0.6), (-112.0, 1.0, z * 1.4)], 0.35, m["ph_gold"], vn)
    show(vn, [(F(0, 0), F(1, 0))])
    for k in range(8):
        z = -12.0 + 3.4 * k
        p = [(-157.0, 2.0, z * 0.6), (-112.0, 2.0, z * 1.4)]
        run(root, f"busf{k}", p if k % 2 else p[::-1], 3, 0.9, m["h_amber"], [0], 0.02 * k, 0.75, 22)
    rise(root, "vnheat", (-135.0, 2.0, 0.0), 12, 0.8, m["warn"], [0], spread=(18.0, 10.0), h=26.0)

    # ---- beats 1-4: the neuromorphic die ----
    chip = empty("chip", root)
    bx("pkg", (-62.0, -1.0, -62.0), (62.0, 2.0, 62.0), m["pcb_blue"], chip)
    bx("die", (-52.0, 2.0, -52.0), (52.0, CY - 1.0, 52.0), m["si"], chip)
    for k in range(12):  # bumps peeking out around the die
        for s in (-1, 1):
            bx(f"bmp{k}{s}", (-50.0 + 9 * k, 1.0, s * 57.0 - 1), (-48.0 + 9 * k, 2.4, s * 57.0 + 1), m["tin"], chip)
    neurons = {}
    for i in range(N):
        for j in range(N):
            x, y, z = core_c(i, j)
            bx(f"c{i}{j}", (x - 6.6, y - 1.0, z - 6.6), (x + 6.6, y, z + 6.6), m["ph_front"], chip)
            # synapse SRAM: a 4x4 bit grid on the left half
            for a in range(3):
                for b in range(4):
                    bx(f"s{i}{j}{a}{b}", (x - 6.0 + 1.9 * a, y, z - 5.6 + 2.9 * b), (x - 4.5 + 1.9 * a, y + 0.6, z - 3.4 + 2.9 * b),
                       m["ph_ln"], chip)
            # neuron block on the right
            bx(f"n{i}{j}", (x + 0.6, y, z - 5.4), (x + 6.0, y + 1.4, z + 5.4), m["ph_dsp"], chip)
            hot = empty(f"nh{i}{j}", chip)
            bx(f"nhb{i}{j}", (x + 1.2, y + 1.4, z - 4.6), (x + 5.4, y + 2.0, z + 4.6), m["ph_c4"], hot)
            neurons[(i, j)] = hot
    # mesh routers between cores
    for i in range(N):
        for j in range(N):
            x, y, z = core_c(i, j)
            if i < N - 1:
                polyline(f"mx{i}{j}", [(x + 6.6, y - 0.4, z + 6.0), (x + PITCH - 6.6, y - 0.4, z + 6.0)], 0.35, m["ph_gold"], chip)
            if j < N - 1:
                polyline(f"mz{i}{j}", [(x + 6.0, y - 0.4, z + 6.6), (x + 6.0, y - 0.4, z + PITCH - 6.6)], 0.35, m["ph_gold"], chip)
    show(chip, [(F(1, 0), F(5, 0))])

    # beat 1: every neuron block lights once in a slow sweep (to show the tiling)
    # beats 2-3: sparse firing only
    sparse = [(1, 1), (2, 1), (2, 2), (3, 2), (3, 3), (4, 4), (1, 4), (0, 2)]
    for (i, j), hot in neurons.items():
        iv = [(F(1, 0.1 + 0.12 * ((i + j) % 6)), F(1, 0.22 + 0.12 * ((i + j) % 6)))]
        if (i, j) in sparse:
            k = sparse.index((i, j))
            for b in (2, 3):
                u = 0.1 + 0.1 * k
                iv.append((F(b, u), F(b, u + 0.07)))
        show(hot, iv)
    # spike packets hop along the chain of sparse cores
    for b in (2, 3):
        for k in range(len(sparse) - 1):
            a, c = core_c(*sparse[k]), core_c(*sparse[k + 1])
            p = [(a[0] + 6.0, CY + 1.5, a[2] + 6.0), (c[0] + 6.0, CY + 1.5, a[2] + 6.0), (c[0] + 6.0, CY + 1.5, c[2] + 6.0)]
            run(root, f"sp{b}_{k}", p, 1, 1.1, m["ph_amber"], [b], 0.1 + 0.1 * k + 0.07, 0.2, 10)

    # ---- beat 3: event camera at the right ----
    cam = empty("cam", root)
    bx("cam_body", (110.0, 0.0, -12.0), (136.0, 20.0, 12.0), m["ph_case"], cam)
    bx("cam_lens", (102.0, 6.0, -6.0), (110.0, 14.0, 6.0), m["quartz_c"], cam)
    bx("cam_ring", (104.0, 5.0, -7.0), (106.0, 15.0, 7.0), m["steel"], cam)
    bx("cam_sens", (132.0, 4.0, -8.0), (134.0, 16.0, 8.0), m["si"], cam)
    pix = []
    for a in range(4):
        for b in range(4):
            e = empty(f"px{a}{b}", cam)
            bx(f"pxb{a}{b}", (131.6, 5.0 + 2.8 * a, -7.0 + 3.6 * b), (132.0, 7.0 + 2.8 * a, -4.6 + 3.6 * b), m["ph_c4"], e)
            pix.append(e)
    for k, e in enumerate(pix):
        if k in (2, 5, 6, 11):
            blink(e, 3, [k % 8], n=8, on=0.8)
        else:
            show(e, [])
    polyline("cam_cable", [(110.0, 2.0, 0.0), (80.0, 3.0, 0.0), (62.0, 3.0, 0.0)], 0.6, m["rubber"], cam)
    # a battery: milliwatts
    bx("bat", (70.0, 0.0, 30.0), (96.0, 10.0, 44.0), m["steel"], cam)
    bx("bat_cap", (96.0, 3.0, 34.0), (98.0, 7.0, 40.0), m["copper"] if "copper" in m else m["steel"], cam)
    bx("bat_lvl", (72.0, 10.0, 32.0), (80.0, 10.6, 42.0), C.mat("t_batlvl", (0.35, 1.0, 0.55), emit=(0.35, 1.0, 0.55), strength=1.5), cam)
    show(cam, [(F(3, 0), F(5, 0))])
    run(root, "evt", [(110.0, 4.0, 0.0), (80.0, 5.0, 0.0), (62.0, 5.0, 0.0), (core_c(1, 1)[0], CY + 2, core_c(1, 1)[2])],
        4, 1.0, m["ph_amber"], [3], 0.0, 0.8, 30)

    # ---- beat 4: a GPU rack behind for scale ----
    rack = empty("rack", root)
    bx("rk", (-150.0, 0.0, -150.0), (-90.0, 120.0, -110.0), m["ph_case"], rack)
    for k in range(14):
        bx(f"rk_s{k}", (-147.0, 4.0 + 8.2 * k, -110.0), (-93.0, 10.0 + 8.2 * k, -109.4), m["ph_front"], rack)
        bx(f"rk_l{k}", (-100.0, 6.0 + 8.2 * k, -109.4), (-97.0, 8.0 + 8.2 * k, -109.0), m["ph_green"], rack)
    show(rack, [(F(4, 0), F(5, 0))])
    rise(root, "rkheat", (-120.0, 120.0, -130.0), 12, 1.0, m["h_amber"], [4], spread=(22.0, 14.0), h=30.0)

    C.tags(root, {
        0: [("processor", (-171.0, 10.0, 0.0)), ("separate memory (DRAM)", (-102.0, 8.0, 18.0)),
            ("weights cross the bus", (-135.0, 6.0, -10.0)), ("moving data costs ~100x", (-135.0, 30.0, 0.0))],
        1: [("core: synapse memory", (core_c(0, 0)[0] - 4.0, CY + 2.0, core_c(0, 0)[2])),
            ("neurons next to memory", (core_c(1, 0)[0] + 3.0, CY + 2.0, core_c(1, 0)[2])),
            ("on-chip mesh network", (core_c(0, 1)[0] + 6.0, CY, core_c(0, 1)[2] + 8.0))],
        2: [("spike = small packet", (core_c(2, 2)[0] + 6.0, CY + 4.0, core_c(2, 2)[2] + 6.0)),
            ("only busy cores wake", (core_c(3, 3)[0] + 4.0, CY + 4.0, core_c(3, 3)[2])),
            ("idle cores: ~no power", (core_c(5, 5)[0], CY + 2.0, core_c(5, 5)[2]))],
        3: [("event camera", (120.0, 24.0, 0.0)), ("only changes are sent", (132.0, 18.0, 0.0)),
            ("milliwatts on a battery", (83.0, 14.0, 37.0))],
        4: [("GPU rack: ~100+ kW", (-120.0, 125.0, -110.0)), ("neuromorphic: edge niche", (0.0, 14.0, 50.0)),
            ("INTC Loihi, BRCHF Akida", (120.0, 24.0, 0.0))],
    })
    C.done(SLUG, BEATS, [
        frame((-140.0, 3.0, 0.0), 110.0, 0.20, 0.65),
        [(0.0, frame((0.0, CY, 0.0), 130.0, 0.15, 0.80)), (0.55, frame((-30.0, CY, -30.0), 60.0, 0.30, 0.75))],
        frame((5.0, CY, 0.0), 110.0, -0.15, 0.85),
        frame((50.0, CY, 5.0), 200.0, -0.30, 0.65),
        frame((-20.0, 40.0, -50.0), 300.0, 0.35, 0.35, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()

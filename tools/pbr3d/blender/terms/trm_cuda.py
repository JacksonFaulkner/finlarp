"""TRM_CUDA on the MLCC base board: the GPU die blown up on the bench as a grid of streaming
multiprocessors (each a field of small cores plus a tensor-core block), HBM stacks beside it, and
behind it the CUDA software stack as a tower of slabs (framework, libraries, runtime, driver).

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_cuda.py

Beats:
  0 board    the GPU on the board: where CUDA code runs
  1 grid     a kernel launch: the host sends a grid of thread blocks, blocks land on SMs
  2 matmul   HBM streams tiles in, tensor cores blink through a matrix multiply
  3 stack    the tower: a PyTorch call falls through cuDNN/cuBLAS, the runtime, the driver
  4 moat     every layer is tuned for NVIDIA; code and skills stay on CUDA
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, mat, show  # noqa: E402
from power_vrm_detail import frame, run, rise, blink  # noqa: E402

SLUG = "TRM_CUDA"
BEATS = [
    ("CUDA is how code reaches the thousands of cores in this GPU",
     "The GPU package in the middle of this board holds one or two big dies with tens of thousands of simple cores. "
     "A CPU can't drive them one by one. CUDA is NVIDIA's platform for doing it: a C++ dialect and compiler (nvcc), a "
     "runtime and driver, and a large set of tuned libraries."),
    ("A kernel launch spreads a grid of thread blocks over the SMs",
     "The die is tiled into streaming multiprocessors (SMs), about 130-150 on a data-center GPU. A CUDA program "
     "launches a kernel as a grid of thread blocks; the hardware hands each block to a free SM, and each SM runs "
     "its threads 32 at a time (a warp) in lockstep. Millions of threads can be in flight at once."),
    ("AI is mostly matrix multiplies, fed from HBM into tensor cores",
     "Training and inference are dominated by multiplying big matrices. Tiles of the matrices stream in from the HBM "
     "stacks beside the die into each SM's shared memory, and tensor cores multiply small blocks in one step. "
     "Libraries like cuBLAS and cuDNN pick the tile sizes and memory moves that keep these units busy."),
    ("Frameworks sit on a deep stack of NVIDIA software",
     "A line of PyTorch becomes a call into cuDNN or cuBLAS (or a kernel compiled by Triton or nvcc), then into the "
     "CUDA runtime, then the driver, which schedules work on the GPU. NCCL adds multi-GPU communication and TensorRT "
     "optimizes inference. Each layer has had nearly two decades of tuning on NVIDIA chips."),
    ("That stack is the moat rivals have to cross",
     "Models, kernels, tools and millions of developers' habits are built on CUDA first, so switching chips means "
     "porting and re-tuning software, not just buying hardware. AMD answers with ROCm and HIP, Intel with oneAPI, and "
     "compilers like Triton try to stay hardware-neutral. Related: NVIDIA (NVDA), AMD (AMD), Intel (INTC)."),
]

# the giant die on the bench
GX0, GX1 = 166.0, 236.0
GZ0, GZ1 = -64.0, -4.0
GY = 4.0  # top of the die slab
NX, NZ = 5, 4  # SM grid
# the software tower behind the die
TX0, TX1, TZ0, TZ1 = 162.0, 240.0, -150.0, -100.0
LAYERS = [("PyTorch / JAX", "cuda_fw"), ("cuDNN cuBLAS NCCL", "cuda_lib"), ("CUDA runtime", "cuda_rt"),
          ("driver", "cuda_drv")]
SLAB = 9.0


def mats(m):
    m["cuda_fw"] = mat("cuda_fw", (0.85, 0.40, 0.20), metal=0.2, rough=0.4)
    m["cuda_lib"] = mat("cuda_lib", (0.45, 0.70, 0.20), metal=0.2, rough=0.4)
    m["cuda_rt"] = mat("cuda_rt", (0.25, 0.50, 0.75), metal=0.2, rough=0.4)
    m["cuda_drv"] = mat("cuda_drv", (0.45, 0.40, 0.60), metal=0.2, rough=0.4)
    m["core_off"] = mat("cuda_core", (0.30, 0.32, 0.38), metal=0.6, rough=0.35)
    m["core_on"] = mat("cuda_core_on", (0.45, 1.0, 0.45), emit=(0.40, 1.0, 0.40), strength=3.0)
    m["tc_on"] = mat("cuda_tc_on", (1.0, 0.75, 0.25), emit=(1.0, 0.70, 0.20), strength=3.0)
    m["blk"] = mat("cuda_blk", (0.35, 0.80, 1.0), emit=(0.30, 0.75, 1.0), strength=2.5)


def giant(m, root):
    """The die as a grid of SMs. Returns points, per-SM core glow groups, tensor-core glows."""
    g = empty("gdie", root)
    bx("g_sub", (GX0 - 18.0, 0.4, GZ0 - 6.0), (GX1 + 18.0, 2.0, GZ1 + 4.0), m["substrate"], g)
    bx("g_die", (GX0, 2.0, GZ0), (GX1, GY, GZ1), m["die"], g)
    # HBM stacks, cut open on the front pair: 8 DRAM layers on a base die
    hbm = {}
    for side, (xa, xb) in (("l", (GX0 - 16.0, GX0 - 3.0)), ("r", (GX1 + 3.0, GX1 + 16.0))):
        for j, (za, zb) in enumerate(((GZ0, GZ0 + 27.0), (GZ0 + 33.0, GZ1))):
            bx(f"hbm_{side}{j}_base", (xa, 2.0, za), (xb, 3.4, zb), m["silicon"], g)
            for k in range(8):
                y = 3.4 + 1.3 * k
                bx(f"hbm_{side}{j}_{k}", (xa, y, za), (xb, y + 1.0, zb), m["hbm_dram"], g)
                bx(f"hbm_{side}{j}_{k}g", (xa, y + 1.0, za), (xb, y + 1.3, zb), m["hbm"], g)
            hbm[(side, j)] = ((xa + xb) / 2, 14.0, (za + zb) / 2)
    sw, sd = (GX1 - GX0) / NX, (GZ1 - GZ0) / NZ
    cores, tcs, sm_c = [], [], []
    for i in range(NX):
        for j in range(NZ):
            x0, z0 = GX0 + sw * i + 0.8, GZ0 + sd * j + 0.8
            x1, z1 = x0 + sw - 1.6, z0 + sd - 1.6
            bx(f"sm{i}_{j}", (x0, GY, z0), (x1, GY + 0.6, z1), m["dark"], g)
            # 4 x 3 cores on the left part, tensor-core block on the right, L1/shared strip at back
            cg = empty(f"smg{i}_{j}", root)
            cw = (x1 - x0) * 0.62 / 4
            cd = (z1 - z0 - 2.6) / 3
            offs, ons = [], []
            for a in range(4):
                for b in range(3):
                    lo = (x0 + 0.4 + cw * a, GY + 0.6, z0 + 2.4 + cd * b)
                    hi = (x0 + cw * (a + 1) - 0.2, GY + 1.4, z0 + 2.4 + cd * (b + 1) - 0.4)
                    offs.append(bx(f"c{i}{j}{a}{b}", lo, hi, m["core_off"], g))
                    ons.append(bx(f"cg{i}{j}{a}{b}", (lo[0], hi[1], lo[2]), (hi[0], hi[1] + 0.12, hi[2]), m["core_on"], cg))
            D.join(offs, f"cores{i}_{j}")
            D.join(ons, f"coreg{i}_{j}")
            tx0 = x0 + (x1 - x0) * 0.66
            bx(f"tc{i}_{j}", (tx0, GY + 0.6, z0 + 2.4), (x1 - 0.4, GY + 2.0, z1 - 0.4), m["si"], g)
            tg = empty(f"tcg{i}_{j}", root)
            bx(f"tcgb{i}_{j}", (tx0 + 0.3, GY + 2.0, z0 + 2.7), (x1 - 0.7, GY + 2.15, z1 - 0.7), m["tc_on"], tg)
            bx(f"l1_{i}_{j}", (x0 + 0.4, GY + 0.6, z0 + 0.4), (x1 - 0.4, GY + 1.0, z0 + 2.0), m["cold"], g)
            show(cg, [])
            show(tg, [])
            cores.append(cg)
            tcs.append(tg)
            sm_c.append(((x0 + x1) / 2, GY + 2.0, (z0 + z1) / 2))
    pts = {"die": ((GX0 + GX1) / 2, GY + 2.0, (GZ0 + GZ1) / 2), "sm": sm_c[NZ * 2 + 3], "tc": sm_c[NZ * 4 + 3],
           "hbm": hbm[("l", 1)], "hbm_r": hbm[("r", 1)], "l1": (GX0 + sw * 0.5, GY + 1.0, GZ1 - 3.0)}
    return pts, cores, tcs, sm_c


def tower(m, root):
    """The software stack: slabs on a GPU block, each with a front cut showing its code lines."""
    g = empty("tower", root)
    bx("tw_gpu", (TX0, 0.4, TZ0), (TX1, 8.0, TZ1), m["die"], g)
    for k in range(10):
        x = TX0 + 4.0 + 7.4 * k
        bx(f"tw_fin{k}", (x, 8.0, TZ0 + 2.0), (x + 1.0, 10.0, TZ1 - 2.0), m["alu"], g)
    tops = []
    for k, (_, mt) in enumerate(reversed(LAYERS)):
        y0 = 10.0 + k * (SLAB + 3.0)
        inset = 2.0 * k
        bx(f"tw_l{k}", (TX0 + inset, y0, TZ0 + inset), (TX1 - inset, y0 + SLAB, TZ1 - inset * 0.5), m[mt], g)
        # code lines engraved on the front face
        for r in range(3):
            w = 20.0 + 14.0 * ((r + k) % 3)
            bx(f"tw_c{k}{r}", (TX0 + inset + 4.0, y0 + 2.0 + 2.4 * r, TZ1 - inset * 0.5),
               (TX0 + inset + 4.0 + w, y0 + 3.0 + 2.4 * r, TZ1 - inset * 0.5 + 0.3), m["ink"], g)
        tops.append((TX1 - inset - 6.0, y0 + SLAB * 0.5, TZ1 - inset * 0.5))
    tops.reverse()  # top layer first, like LAYERS
    glow = empty("tw_glow", root)
    for k in range(len(LAYERS)):
        y0 = 10.0 + k * (SLAB + 3.0)
        inset = 2.0 * k
        bx(f"tw_e{k}", (TX0 + inset - 0.3, y0 + SLAB, TZ0 + inset - 0.3), (TX1 - inset + 0.3, y0 + SLAB + 0.4, TZ1 - inset * 0.5 + 0.3), m["blk"], glow)
    show(glow, [])
    top_y = 10.0 + len(LAYERS) * (SLAB + 3.0)
    return tops, glow, top_y


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    b = C.base(m, root)
    pk = b["pk"]
    gp, cores, tcs, sm_c = giant(m, root)
    tops, tglow, top_y = tower(m, root)
    C.magnify(m, root, pk["top"], (GX0 - 18.0, 10.0, -30.0), r=8.0)

    # beat 0: the die on the board glows, heat rises
    show(b["die_glow"], [(F(0, 0.3), F(1, 0)), (F(2, 0), F(3, 0))])
    rise(root, "pk_heat", (0.0, D.DIE_Y[1] + 1.0, -16.0), 6, 1.0, m["heat"], 0, 0.3, 0.9, 30.0, 60, (14.0, 10.0))

    # beat 1: thread blocks drop from the host (above) onto SMs, one after another; SMs light up
    host = ((GX0 + GX1) / 2, 46.0, 16.0)
    for k, c in enumerate(sm_c):
        u = 0.05 + 0.6 * k / len(sm_c)
        run(root, f"blk{k}", [host, (c[0], c[1] + 12.0, c[2]), (c[0], c[1] + 0.5, c[2])], 1, 1.4, m["blk"], 1, u, u, 26)
        show(cores[k], [(F(1, u + 0.06), F(2, 0))])
    bx("host", (host[0] - 12.0, host[1], host[2] - 6.0), (host[0] + 12.0, host[1] + 5.0, host[2] + 6.0), m["fet"], root)

    # beat 2: HBM feeds tiles in, tensor cores blink in waves, cores stay on
    for k, (c, cg, tg) in enumerate(zip(sm_c, cores, tcs)):
        show(cg, [(F(1, 0.06 + 0.6 * k / len(sm_c)), F(2, 0)), (F(2, 0), F(3, 0)), (F(4, 0.3), F(5, 0))])
        blink(tg, 2, [(k % 4), (k % 4) + 4], n=8, on=0.55)
    for side in ("l", "r"):
        for j in range(2):
            hx = GX0 - 9.5 if side == "l" else GX1 + 9.5
            z = -50.0 if j == 0 else -18.0
            dx = 1.0 if side == "l" else -1.0
            for r in range(3):
                zz = z + (r - 1) * 6.0
                run(root, f"hbm_{side}{j}{r}", [(hx, 15.0, zz), (hx + dx * 10.0, GY + 4.0, zz), ((GX0 + GX1) / 2 - dx * 10.0, GY + 3.0, zz)],
                    5, 0.8, m["v12"], 2, 0.0 + 0.1 * r, 0.8, 30)

    # beat 3: a call falls down the tower to the GPU, then work comes back up as results
    cx = TX1 - 10.0
    path = [(cx, top_y + 14.0, TZ1 + 2.0)] + [(cx, t[1], TZ1 + 2.0) for t in tops] + [(cx, 6.0, TZ1 + 2.0)]
    run(root, "call", path, 8, 1.2, m["blk"], [3, 4], 0.0, 0.7, 50)
    run(root, "to_die", [(TX0 + 30.0, 4.0, TZ1), (TX0 + 30.0, 8.0, GZ0 - 8.0), (GX0 + 20.0, GY + 2.0, GZ0 + 6.0)], 6, 0.9, m["blk"], 3, 0.3, 0.9, 30)
    show(tglow, [(F(3, 0.1), F(5, 0))])
    for k, tg in enumerate(tcs):
        blink(tg, 4, [k % 8], n=8, on=0.8)

    C.tags(root, {
        0: [("GPU package: CUDA runs here", pk["top"]), ("die, ~40x, on the bench", gp["die"]),
            ("HBM stacks", gp["hbm"])],
        1: [("host CPU launches a kernel", host), ("thread blocks -> SMs", gp["sm"]),
            ("~140 SMs, 32-thread warps", (GX1, GY + 2.0, GZ1))],
        2: [("HBM streams matrix tiles", gp["hbm"]), ("tensor cores: block matmul", gp["tc"]),
            ("shared memory / L1", gp["l1"])],
        3: [(LAYERS[k][0], tops[k]) for k in range(len(LAYERS))],
        4: [("tuned for NVIDIA since 2007", tops[1]), ("rivals: ROCm, oneAPI, Triton", (TX0 + 10.0, top_y + 4.0, TZ1)),
            ("NVDA, AMD, INTC", gp["die"])],
    })
    tc = ((TX0 + TX1) / 2, top_y / 2, (TZ0 + TZ1) / 2)
    C.done(SLUG, BEATS, [
        frame((20.0, 0.0, -80.0), 380.0, 0.30, 0.65, pad=1.0),
        frame(((GX0 + GX1) / 2, 20.0, -34.0), 100.0, 0.25, 0.55),
        frame(((GX0 + GX1) / 2, 6.0, -34.0), 90.0, 0.15, 0.85),
        frame(tc, 100.0, 0.35, 0.25),
        frame(((TX0 + TX1) / 2, 18.0, -75.0), 150.0, 0.45, 0.45),
    ], root)


if __name__ == "__main__":
    build()

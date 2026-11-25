"""TRM_NVLINK: the Terms-tab overview for NVLink, built at the POWER pages' level of detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_nvlink.py

Writes assets/term_TRM_NVLINK.glb. Captions live in specs/terms/TRM_NVLINK.json (same beat count).

An 8-GPU HGX node with its lid off (net_server_detail): two NVSwitch chips between the GPU rows, a
copper NVLink trace bundle from every GPU to both. GPU-to-GPU traffic goes through the NVSwitch on
the baseboard; the same transfer over PCIe has to cross the host board and the CPUs. Bars on the
left compare the two. Then an NVL72 rack: 18 compute trays and 9 NVSwitch trays tied by a copper
cable spine at the back, so all 72 GPUs share one NVLink domain.

Beats:
  0 node      eight GPUs, two NVSwitch chips, NVLink traces on the baseboard
  1 path      GPU to GPU through NVSwitch (many fast beads) vs through PCIe and the CPUs (few, slow)
  2 numbers   bars: NVLink 1.8 TB/s per GPU vs PCIe Gen5 x16 128 GB/s
  3 rack      NVL72: compute trays to switch trays over the copper spine
  4 fusion    NVLink Fusion / UALink: a third-party chip in a tray joins the domain
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import bx, empty, show, mat  # noqa: E402
from sand_overview import F  # noqa: E402
from power_vrm_detail import frame, run, blink, polyline, present, join  # noqa: E402
import net_server_detail as S  # noqa: E402

SLUG = "TRM_NVLINK"
BEATS = [
    ("NVLink wires GPUs straight to each other, not through PCIe",
     "Inside an 8-GPU server the GPUs sit on one baseboard with two NVSwitch chips between them. Every GPU has a bundle "
     "of NVLink lanes running to each switch, separate from the PCIe lanes that go to the CPU and network cards. NVLink "
     "is Nvidia's own link, built only for moving data between accelerators."),
    ("GPU to GPU goes through the NVSwitch in one hop",
     "When one GPU reads another's memory, the data crosses the baseboard into an NVSwitch and straight out to the other "
     "GPU. Over PCIe the same transfer would drop to the host board, through a PCIe switch, often across both CPUs and "
     "back. Fewer hops and wider links mean lower latency and far more bandwidth."),
    ("About 14x the bandwidth of a PCIe slot",
     "A Blackwell GPU has 18 NVLink 5 links, 1.8 TB/s in total. A PCIe Gen5 x16 slot moves about 128 GB/s. That gap is why "
     "large models split across GPUs (tensor and expert parallelism) run inside the NVLink domain, where GPUs swap "
     "activations every layer."),
    ("NVL72: 72 GPUs in one rack act as one big accelerator",
     "In a GB200 NVL72 rack, 18 compute trays (4 GPUs each) connect to 9 NVSwitch trays through a spine of about 5,000 "
     "copper cables at the back of the rack. Every GPU reaches every other GPU at full NVLink speed, so 72 GPUs share "
     "one memory domain. Copper works because the runs are under a couple of metres."),
    ("NVLink Fusion opens the fabric; UALink is the open rival",
     "NVLink Fusion licenses NVLink chiplets so other companies' CPUs and custom accelerators can join an Nvidia rack. "
     "UALink is an open standard from AMD and others for the same scale-up job. Retimers, cables and switch silicon "
     "for these links are a growing market. Related: Nvidia (NVDA), Astera Labs (ALAB), Marvell (MRVL), AMD (AMD)."),
]

RX0 = 560.0  # NVL72 rack, left edge (x); 150 wide, front z = 0, back z = -170
RW = 150.0
TRAY_H, TRAY_Y0 = 12.0, 30.0
BAR_X, BAR_Z = -400.0, -150.0


def mats(m):
    m["rack"] = mat("nvl_rack", (0.18, 0.19, 0.22), metal=0.7, rough=0.45)
    m["tray"] = mat("nvl_tray", (0.34, 0.36, 0.40), metal=0.8, rough=0.4)
    m["swtray"] = mat("nvl_swtray", (0.14, 0.30, 0.26), metal=0.6, rough=0.4)
    m["bar_n"] = mat("nvl_bar_n", (0.20, 0.55, 0.28), metal=0.2, rough=0.5)
    m["bar_p"] = mat("nvl_bar_p", (0.60, 0.42, 0.14), metal=0.2, rough=0.5)
    m["cap_n"] = mat("nvl_cap_n", (0.40, 1.0, 0.45), emit=(0.30, 1.0, 0.40), strength=2.0)
    m["cap_p"] = mat("nvl_cap_p", (1.0, 0.75, 0.25), emit=(1.0, 0.68, 0.18), strength=2.0)
    m["fus"] = mat("nvl_fus", (0.30, 0.55, 1.0), emit=(0.25, 0.50, 1.0), strength=0.8)


def tray_y(i):
    return TRAY_Y0 + i * (TRAY_H + 2.0)


def nvl72(m, root):
    """The rack: posts, 10 compute trays, 9 switch trays, 8 compute trays (bottom up), and the copper
    cable spine at the back. Returns group, the tray kinds and spine x positions."""
    g = empty("rack", root)
    x0, x1 = RX0, RX0 + RW
    top = tray_y(27) + 10.0
    posts = [bx(f"post{i}", (x, 0.0, z), (x + 6.0, top, z + 6.0), m["rack"], g)
             for i, (x, z) in enumerate([(x0 - 6, -6), (x1, -6), (x0 - 6, -176), (x1, -176)])]
    posts += [bx("rk_top", (x0 - 6, top, -176), (x1 + 6, top + 6, 0), m["rack"], g),
              bx("rk_base", (x0 - 6, -4, -176), (x1 + 6, 0, 0), m["rack"], g)]
    join(posts, "rack_frame")
    kinds = ["c"] * 8 + ["s"] * 9 + ["c"] * 10
    body, fronts = [], []
    for i, k in enumerate(kinds):
        y = tray_y(i)
        body.append(bx(f"tr{i}", (x0, y, -165.0), (x1, y + TRAY_H, 0.0), m["tray" if k == "c" else "swtray"], g))
        if k == "c":  # four GPU tiles on the front face
            for j in range(4):
                xx = x0 + 14.0 + 32.0 * j
                fronts.append(bx(f"tr{i}_g{j}", (xx, y + 3.0, 0.0), (xx + 22.0, y + TRAY_H - 3.0, 1.0), m["die"], g))
        else:
            for j in range(2):
                xx = x0 + 24.0 + 62.0 * j
                fronts.append(bx(f"tr{i}_s{j}", (xx, y + 3.0, 0.0), (xx + 38.0, y + TRAY_H - 3.0, 1.0), m["sw_die"], g))
    join(body, "trays")
    join(fronts, "fronts")
    spine_x = [x0 + 18.0 + 23.0 * j for j in range(6)]
    cab = []
    for j, sx in enumerate(spine_x):
        cab.append(polyline(f"sp{j}", [(sx, tray_y(0), -172.0), (sx, tray_y(26) + TRAY_H, -172.0)], 2.2, m["copper"], g))
    join(cab, "spine")
    stubs = []
    for i in range(27):
        y = tray_y(i) + TRAY_H / 2
        for j, sx in enumerate(spine_x):
            stubs.append(bx(f"st{i}_{j}", (sx - 1.0, y - 0.8, -172.0), (sx + 1.0, y + 0.8, -165.0), m["copper"], g))
    join(stubs, "stubs")
    return g, kinds, spine_x


def bars(m, root):
    g = empty("bars", root)
    sc = 0.11
    out = {}
    for k, (name, val, mt, cap) in enumerate((("nv", 1800.0, "bar_n", "cap_n"), ("pc", 128.0, "bar_p", "cap_p"))):
        x = BAR_X + 70.0 * k
        h = val * sc
        bx(f"bar_{name}", (x, 0.0, BAR_Z - 20.0), (x + 40.0, h, BAR_Z + 20.0), m[mt], g)
        bx(f"bar_{name}_c", (x - 1.0, h, BAR_Z - 21.0), (x + 41.0, h + 3.0, BAR_Z + 21.0), m[cap], g)
        out[name] = (x + 20.0, h + 3.0, BAR_Z + 20.0)
    bx("bar_floor", (BAR_X - 20.0, -3.0, BAR_Z - 40.0), (BAR_X + 130.0, 0.0, BAR_Z + 40.0), m["floor"], g)
    return g, out


def build():
    m, root = C.setup(SLUG, len(BEATS))
    m.update(S.materials())
    mats(m)
    s = S.scene(m, root, cut=False, rails=False, out=False)
    for k in ("leaf", "fe", "out"):
        if k in s:
            present(s[k], [])
    rack, kinds, spine_x = nvl72(m, root)
    bar_g, bt = bars(m, root)
    present(rack, [(F(3, 0.0), F(5, 0))])
    present(bar_g, [(F(2, 0.0), F(3, 0))])

    # beat 0: every NVLink bundle carries a trickle; dies warm
    for k in range(8):
        for sw in (0, 1):
            e = [(p[0], 6.0, p[2]) for p in S.nvl_edge(k, sw)]
            run(root, f"tr{k}{sw}", [(S.gpu_xz(k)[0], 10.0, S.gpu_xz(k)[1])] + e, 2, 2.0, m["nvl"], 0, 0.2 + 0.05 * sw, 0.8, 40)
    for gl in s["glow"]:
        show(gl, [(F(0, 0.0), F(3, 0))])

    # beat 1: GPU0 -> GPU7 through NVSwitch (dense) vs GPU0 -> GPU3 via PCIe and both CPUs (sparse, slow)
    run(root, "nvl_a", [(p[0], p[1] + 4.0, p[2]) for p in S.nvl_path(0, 7, 0)], 16, 4.0, m["nvl"], 1, 0.05, 0.75, 45)
    run(root, "nvl_b", [(p[0], p[1] + 4.0, p[2]) for p in S.nvl_path(3, 4, 1)], 16, 4.0, m["nvl"], 1, 0.1, 0.8, 45)
    pa = S.pcie_path(0)[:8]
    pb = S.pcie_path(3)[:8]
    slow = ([(p[0], p[1] + 4.0, p[2]) for p in pa] + [(p[0], p[1] + 6.0, p[2]) for p in reversed(S.cpu_path(0))]
            + [(p[0], p[1] + 6.0, p[2]) for p in S.cpu_path(3)] + [(p[0], p[1] + 4.0, p[2]) for p in reversed(pb)])
    run(root, "pcie_slow", slow, 4, 4.0, m["pcie"], 1, 0.05, 0.5, 110)

    # beat 2: bars, a stream into the NVLink bar
    run(root, "bar_n_in", [(bt["nv"][0], 2.0, BAR_Z + 24.0), (bt["nv"][0], bt["nv"][1] - 2.0, BAR_Z + 24.0)], 12, 2.4, m["nvl"], 2, 0.0, 0.8, 30)
    run(root, "bar_p_in", [(bt["pc"][0], 2.0, BAR_Z + 24.0), (bt["pc"][0], bt["pc"][1] + 4.0, BAR_Z + 24.0)], 2, 2.4, m["pcie"], 2, 0.0, 0.8, 30)

    # beats 3-4: compute tray -> spine -> switch tray, both directions
    for i, src in enumerate((2, 6, 20, 24)):
        dst = 9 + (i * 2) % 9
        sx = spine_x[i % len(spine_x)]
        ys, yd = tray_y(src) + TRAY_H / 2, tray_y(dst) + TRAY_H / 2
        path = [(RX0 + 30.0 + 25.0 * i, ys, 2.0), (RX0 + 30.0 + 25.0 * i, ys, -150.0), (sx, ys, -175.0), (sx, yd, -175.0),
                (RX0 + RW / 2, yd, -150.0), (RX0 + RW / 2, yd, 2.0)]
        run(root, f"sp{i}", path, 8, 2.4, m["nvl"], [3, 4], 0.05 + 0.04 * i, 0.8, 50)
    # tray LEDs blink
    leds = empty("rk_leds", root)
    ledg = []
    for i, k in enumerate(kinds):
        lg = empty(f"rl{i}", leds)
        bx(f"rlm{i}", (RX0 + RW - 8.0, tray_y(i) + 4.0, 0.0), (RX0 + RW - 4.0, tray_y(i) + 8.0, 1.6), m["led"], lg)
        ledg.append(lg)
        blink(lg, 3, [i % 8, (i * 3 + 1) % 8], n=8, on=0.6)
    # beat 4: a third-party accelerator (blue) in one tray, joined through a Fusion chiplet
    fus = empty("fusion", root)
    yf = tray_y(22)
    bx("fus_chip", (RX0 + 14.0, yf + 2.5, -0.5), (RX0 + 68.0, yf + TRAY_H - 2.5, 2.0), m["fus"], fus)
    present(fus, [(F(4, 0.1), F(5, 0))])
    run(root, "fus_run", [(RX0 + 40.0, yf + 6.0, 3.0), (RX0 + 40.0, yf + 6.0, -150.0), (spine_x[1], yf + 6.0, -175.0),
                          (spine_x[1], tray_y(13) + 6.0, -175.0), (RX0 + RW / 2, tray_y(13) + 6.0, 3.0)], 8, 2.6, m["fe"], 4, 0.2, 0.85, 50)

    sw0, sw1 = s["sw"]
    C.tags(root, {
        0: [("GPU module (die + HBM)", s["gpu"][1]["top"]), ("NVSwitch chip", sw0["top"]),
            ("NVLink traces to both switches", (0.0, 6.0, -340.0)), ("PCIe + host board", (0.0, 20.0, -150.0))],
        1: [("NVLink: GPU to switch to GPU", sw1["top"]), ("PCIe: down, across CPUs, back", s["cpu"][0]["top"]),
            ("one hop, wide link", sw0["top"])],
        2: [("NVLink 5: 1.8 TB/s per GPU", bt["nv"]), ("PCIe Gen5 x16: 128 GB/s", bt["pc"])],
        3: [("18 compute trays, 4 GPUs each", (RX0 + RW / 2, tray_y(23), 2.0)), ("9 NVSwitch trays", (RX0 + RW / 2, tray_y(12), 2.0)),
            ("copper spine, ~5,000 cables", (spine_x[3], tray_y(20), -175.0)), ("72 GPUs, one domain", (RX0 + RW / 2, tray_y(27) + 14.0, -80.0))],
        4: [("third-party chip via Fusion", (RX0 + 40.0, yf + TRAY_H, 2.0)), ("UALink: open alternative", (RX0 + RW / 2, tray_y(5), 2.0)),
            ("NVDA  ALAB  MRVL  AMD", (RX0 + RW / 2, tray_y(27) + 14.0, -80.0))],
    })
    rc = (RX0 + RW / 2, tray_y(13), -85.0)
    C.done(SLUG, BEATS, [
        frame((-20.0, 30.0, -300.0), 640.0, 0.25, 0.70),
        frame((0.0, 20.0, -330.0), 470.0, 0.15, 0.85),
        [(0.16, frame((-320.0, 80.0, -200.0), 360.0, 0.35, 0.30))],
        frame(rc, 470.0, 2.55, 0.20),
        frame((RX0 + RW / 2, tray_y(18), -60.0), 300.0, 0.40, 0.18),
    ], root)


if __name__ == "__main__":
    build()

"""The SERVER page's overview (NETWORK+COOL tab), in the picture-and-panel template
(docs/diagram-pages.md).

Run from the repo root:

    blender -b --factory-startup --python tools/pbr3d/blender/net_server_overview.py

Writes blender/net_server_overview.blend and assets/net_server_overview.glb. One beat is 8 s.

One 8-GPU node with its lid off (net_server_detail.py): the HGX baseboard at the back with eight
GPUs under cold plates and two NVSwitch chips, the host board at the front with two CPUs, four PCIe
switches and ten cards (eight NICs, two DPUs), coolant headers at the rear, and cables up to the
leaf switch above.

Beats (match the eight beats in diagrams_nodes/netcool/server/overview.rs):
  0 the node     the whole server: GPU baseboard, host board, NICs
  1 GPUs         eight GPUs under cold plates; the front-left plate cut open
  2 NVLink       green beads GPU to NVSwitch to GPU, all to all
  3 PCIe         amber beads GPU to PCIe switch to its NIC; the CPUs on the same switches
  4 to the leaf  magenta packets out of each NIC, up the cables to the leaf; port LEDs
  5 DPUs         cyan traffic from the two DPUs to the front-end switch; CPU memory
  6 cooling      blue coolant in, orange out, heat lifting off the dies
  7 all at once  every path inside the node running (leaf hidden)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import net_server_detail as D  # noqa: E402
from net_server_detail import frame, camera_path, run, rise, blink  # noqa: E402

PAGE = "net_server"
NAME = "overview"
BEATS = 8

NVL_PAIRS = [(k, (k + d) % 8, (k + d) % 2) for d in (3, 5, 1) for k in range(8)]


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def nvlink(m, root, beats, pairs=NVL_PAIRS, n=2, u0=0.0, u1=0.85, size=3.0, life=70, tag="nvl"):
    for i, (a, b, sw) in enumerate(pairs):
        run(root, f"{tag}{i}", D.nvl_path(a, b, sw), n, size, m["nvl"], beats, u0 + 0.02 * (i % 8), u1, life)


def pcie(m, root, beats, ks=range(8), n=3, u0=0.0, u1=0.8, size=3.0, life=90, tag="pc"):
    for k in ks:
        run(root, f"{tag}{k}", D.pcie_path(k), n, size, m["pcie"], beats, u0 + 0.015 * k, u1, life)


def cpu_links(m, root, beats, n=2, tag="cp"):
    for c in range(4):
        run(root, f"{tag}{c}", D.cpu_path(c), n, 1.8, m["mem"], beats, 0.05 + 0.03 * c, 0.85, 40)


def packets(m, root, beats, ns=range(8), n=4, u0=0.0, u1=0.85, size=3.2, life=60, tag="pk", rails=False):
    for i in ns:
        nx = D.NIC_X[i]
        run(root, f"{tag}{i}", [(nx, 8.0, -32.0), (nx, 12.8, 6.0)] + D.cable_path(nx, D.leaf_x(i)), n, size, m["pkt"], beats,
            u0 + 0.02 * i, u1, life)


def frontend(m, root, s, beats, n=4, tag="fe"):
    for i in range(2):
        for j in range(2):
            px = s["dpu"][i]["ports"][j][0]
            run(root, f"{tag}{i}{j}", [(px, 8.0, -32.0), (px, 12.8, 6.0)] + D.fe_path(px, 2 * i + j), n, 2.2, m["fe"], beats,
                0.05 + 0.05 * (2 * i + j), 0.85, 60)


def coolant(m, root, beats, ks=range(8), n=3, tag="cl", u0=0.0, u1=0.8):
    for k in ks:
        p = D.coolant_path(k)
        run(root, f"{tag}s{k}", p[:5], n, 2.4, m["cold"], beats, u0 + 0.02 * k, u1, 70)
        run(root, f"{tag}r{k}", p[4:], n, 2.4, m["warm"], beats, u0 + 0.15 + 0.02 * k, min(u1 + 0.1, 0.95), 60)
    run(root, f"{tag}rs", D.rack_supply_path(), 4, 3.2, m["cold"], beats, u0, u1, 60)
    run(root, f"{tag}rr", D.rack_return_path(), 4, 3.2, m["warm"], beats, u0 + 0.1, u1, 60)


def heat(m, root, s, b, ks=range(8), n=3, tag="ht"):
    for k in ks:
        rise(root, f"{tag}{k}", s["gpu"][k]["top"], n, 1.4, m["heat"], b, 0.05 + 0.03 * k, 0.85, 50.0, 70, (18.0, 18.0))


def leds(s, beats, leaf=True):
    for i, lg in enumerate(s["leds"]):
        blink(lg, beats[0], [j for j in range(16) if (j + i) % 3 != 0], 16, 0.5)
    if leaf:
        for i, lg in enumerate(s["leaf_leds"]):
            blink(lg, beats[0], [j for j in range(16) if (j + 2 * i) % 4 != 1], 16, 0.5)


def glow(s, iv):
    for g in s["glow"]:
        show(g, iv)


def build():
    m, root = start(NAME, beats=BEATS, page=PAGE)
    m.update(D.materials())
    s = D.scene(m, root)
    D.present(s["rails"], [])
    D.present(s["leaf"], span(4, 0.0, 6, 0.0))
    D.present(s["fe"], span(5, 0.0, 6, 0.0) + span(7, 0.0, 8, 0.0))

    nvlink(m, root, [2, 7])
    pcie(m, root, [3, 7])
    cpu_links(m, root, [3, 5, 7])
    packets(m, root, [4])
    leds(s, [4])
    frontend(m, root, s, [5, 7])
    coolant(m, root, [6, 7])
    heat(m, root, s, 6)
    glow(s, span(1, 0.3, 2, 0.0) + span(6, 0.0, 8, 0.0))

    g0, g4 = s["gpu"][0], s["gpu"][5]
    tags = {
        0: [("GPU baseboard: 8 GPUs", s["gpu"][6]["top"]), ("host board: CPUs, PCIe", s["cpu"][1]["top"]),
            ("NICs at the front", s["nic"][7]["cage"]), ("cards at the front edge", s["dpu"][1]["cage"])],
        1: [("cold plate cut open", g0["fins"]), ("GPU dies + HBM", g0["die"]), ("8 GPUs, 2 rows of 4", g4["top"])],
        2: [("NVSwitch chips", s["sw"][1]["top"]), ("NVLink: 1.8 TB/s per GPU", s["gpu"][1]["top"]),
            ("all-to-all inside the node", s["gpu"][6]["top"])],
        3: [("PCIe switch", s["psw"][1]["top"]), ("GPU to its own NIC", s["nic"][2]["chip"]), ("CPU hosts the switches", s["cpu"][0]["top"])],
        4: [("8 NICs: one per GPU", s["nic"][1]["cage"]), ("400-800 Gb/s each", s["nic"][6]["cage"]),
            ("to the leaf switch", (0.0, D.LEAF[2], 65.0))],
        5: [("2 DPUs: front end + storage", s["dpu"][0]["chip"]), ("front-end switch", (D.FE[0] + 40.0, D.FE[3], 55.0)),
            ("CPU + DDR5", s["cpu"][1]["dimm"])],
        6: [("supply header", (-120.0, D.SUP_Y, D.HDR_Z)), ("return to rack manifold", (40.0, 160.0, -630.0)),
            ("~1 kW per GPU into water", g4["top"])],
        7: [("~14 kW node", s["gpu"][2]["top"]), ("NVLink inside", s["sw"][0]["top"]), ("network out", s["nic"][5]["cage"])],
    }
    for i, items in tags.items():
        for text, pos in items:
            label(text, pos, root, beat(i))

    camera_path(root, [
        frame((0.0, 40.0, -290.0), 640.0, 0.30, 0.70, pad=1.0),
        frame((-60.0, 10.0, -360.0), 300.0, 0.25, 0.55),
        frame((0.0, 0.0, -395.0), 380.0, 0.05, 1.05, pad=1.0),
        frame((-20.0, 0.0, -220.0), 420.0, 0.20, 0.85, pad=1.0),
        frame((0.0, 90.0, -10.0), 420.0, 0.35, 0.30, pad=1.0),
        frame((110.0, 50.0, -60.0), 360.0, 0.55, 0.40, pad=1.0),
        frame((0.0, 30.0, -470.0), 480.0, 0.60, 0.50, pad=1.0),
        frame((0.0, 50.0, -290.0), 680.0, -0.30, 0.65, pad=1.0),
    ])
    return root


if __name__ == "__main__":
    build()
    finish(NAME, page=PAGE)

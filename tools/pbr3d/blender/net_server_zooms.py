"""Zoom-ins (a-e) for the SERVER page: the overview's node (net_server_detail.scene) with its own
camera, beads and tags, three beats each (diagrams_nodes/netcool/server/zooms.rs):

  a GPU + cold plate   the cut-open plate: dies and HBM, coolant through the fins, heat out
  b NVSwitch           two switch chips, every GPU wired to both, all-to-all traffic
  c PCIe switches      GPU, NIC and NVMe on one switch; the CPU above; GPUDirect RDMA
  d NICs and DPUs      the front edge: ConnectX cards, OSFP cages, the BlueField DPUs
  e out to the leaf    one cable per NIC; rail-optimised: NIC k of every server to rail k

Run one zoom per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/net_server_zooms.py -- a

Writes assets/net_server_zoom_<letter>.glb (and blender/net_server_zoom_<letter>.blend).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import net_server_detail as D  # noqa: E402
from net_server_detail import frame, camera_path, run, rise, blink  # noqa: E402
import net_server_overview as OV  # noqa: E402

PAGE = "net_server"
BEATS = 3


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def hide_out(s, leaf=False, fe=False, rails=False):
    D.present(s["leaf"], span(0, 0.0, 3, 0.0) if leaf else [])
    D.present(s["fe"], span(0, 0.0, 3, 0.0) if fe else [])
    D.present(s["rails"], span(0, 0.0, 3, 0.0) if rails else [])


def zoom_a(m, root, s):
    hide_out(s)
    g = s["gpu"][0]
    gx, gz = D.gpu_xz(0)
    OV.glow(s, span(0, 0.2, 3, 0.0))
    p = D.coolant_path(0)
    run(root, "a_in", p[:3], 4, 2.4, m["cold"], [1, 2], 0.0, 0.8, 50)
    for j in range(3):
        zz = gz - 4.0 - 6.0 * j
        run(root, f"a_fin{j}", [(gx - 28.0, 18.0, zz), (gx + 28.0, 18.0, zz)], 4, 1.8, m["cold"], 1, 0.05 + 0.04 * j, 0.85, 50)
        run(root, f"a_fw{j}", [(gx - 28.0, 18.0, zz), (gx + 28.0, 18.0, zz)], 4, 1.8, m["warm"], 2, 0.05 + 0.04 * j, 0.85, 50)
    run(root, "a_out", p[5:], 4, 2.4, m["warm"], 2, 0.1, 0.85, 60)
    rise(root, "a_heat", g["die"], 6, 1.2, m["heat"], 0, 0.1, 0.85, 22.0, 60, (14.0, 0.0))
    tags(root, [
        [("two GPU dies", g["die"]), ("HBM stacks beside", g["hbm"]), ("~1 kW per GPU", g["sub"])],
        [("copper cold plate", g["fins"]), ("microchannel fins", (gx + 20.0, 18.0, gz)), ("coolant in", g["in"])],
        [("warm coolant out", g["out"]), ("to the return rail", (gx + 28.0, D.RET_Y, gz - 60.0))],
    ])
    camera_path(root, [frame((gx, 10.0, gz), 110.0, 0.20, 0.30), frame((gx, 14.0, gz), 90.0, 0.10, 0.25),
                       frame((gx + 10.0, 24.0, gz - 30.0), 140.0, 0.35, 0.45)])


def zoom_b(m, root, s):
    hide_out(s)
    OV.nvlink(m, root, [0], pairs=[(0, 5, 0), (5, 0, 1)], n=4, size=3.0)
    OV.nvlink(m, root, [1], pairs=[(k, (k + 4) % 8, k % 2) for k in range(8)], n=2, size=3.0)
    OV.nvlink(m, root, [2], n=2, size=3.0)
    tags(root, [
        [("NVLink traces", (-40.0, 4.6, -350.0)), ("GPU to switch to GPU", s["gpu"][0]["top"])],
        [("NVSwitch chip", s["sw"][0]["top"]), ("every GPU wired to both", s["gpu"][2]["top"])],
        [("1.8 TB/s per GPU", s["gpu"][1]["top"]), ("14.4 TB/s total", s["sw"][1]["top"])],
    ])
    camera_path(root, [frame((-110.0, 0.0, -395.0), 260.0, 0.10, 0.95), frame((0.0, 0.0, -395.0), 160.0, 0.20, 0.60),
                       frame((0.0, 0.0, -395.0), 380.0, 0.0, 1.10, pad=1.0)])


def zoom_c(m, root, s):
    hide_out(s)
    OV.pcie(m, root, [0], ks=[1, 5], n=4)
    OV.cpu_links(m, root, [1], n=4)
    for c in range(4):
        run(root, f"c_nv{c}", [(D.PX[c], 7.0, D.PZ), (D.PX[c] + 25.0, 6.6, D.PZ)], 3, 1.8, m["mem"], 1, 0.3, 0.85, 20)
    OV.pcie(m, root, [2], n=3)
    tags(root, [
        [("GPU", s["gpu"][1]["top"]), ("PCIe switch", s["psw"][1]["top"]), ("its NIC", s["nic"][2]["chip"])],
        [("CPU: root of the tree", s["cpu"][0]["top"]), ("NVMe on the switch", s["psw"][1]["nvme"])],
        [("GPUDirect RDMA: GPU to NIC", s["psw"][2]["top"]), ("skips CPU memory", s["cpu"][1]["top"])],
    ])
    camera_path(root, [frame((-60.0, 0.0, -220.0), 200.0, 0.15, 0.80), frame((-110.0, 0.0, -150.0), 200.0, 0.30, 0.70),
                       frame((0.0, 0.0, -170.0), 440.0, 0.10, 0.95, pad=1.0)])


def zoom_d(m, root, s):
    hide_out(s, fe=True)
    OV.packets(m, root, [0, 1], ns=[2, 3, 4, 5], n=4)
    OV.frontend(m, root, s, [2])
    OV.leds(s, [1], leaf=False)
    tags(root, [
        [("ConnectX NIC", s["nic"][3]["chip"]), ("OSFP cage", s["nic"][2]["cage"])],
        [("port LEDs", s["nic"][4]["cage"]), ("transceiver in the cage", (D.NIC_X[5], 17.0, 14.0))],
        [("BlueField-3 DPU", s["dpu"][0]["chip"]), ("2 ports each", s["dpu"][1]["cage"]), ("front-end switch", (D.FE[0] + 40.0, D.FE[3], 55.0))],
    ])
    camera_path(root, [frame((-50.0, 10.0, -25.0), 130.0, 0.20, 0.45), frame((40.0, 12.0, -10.0), 140.0, 0.30, 0.30),
                       frame((140.0, 50.0, 0.0), 300.0, 0.45, 0.30, pad=1.0)])


def zoom_e(m, root, s):
    D.present(s["leaf"], span(0, 0.0, 2, 0.0))
    D.present(s["rails"], span(2, 0.0, 3, 0.0))
    D.present(s["fe"], [])
    OV.packets(m, root, [0, 1, 2], n=4)
    OV.leds(s, [1])
    tags(root, [
        [("one cable per NIC", (D.NIC_X[2], 60.0, 60.0)), ("transceivers", s["nic"][5]["cage"])],
        [("leaf switch above", (0.0, D.LEAF[3], 65.0)), ("400-800 Gb/s a port", (D.NIC_X[6], 60.0, 60.0))],
        [("rail-optimised: 8 rail switches", (0.0, D.LEAF[3], 65.0)), ("NIC k of every server to rail k", (-660.0, 30.0, 0.0))],
    ])
    camera_path(root, [frame((0.0, 60.0, 0.0), 300.0, 0.35, 0.25, pad=1.0), frame((0.0, 120.0, 30.0), 480.0, 0.25, 0.25, pad=1.0),
                       frame((0.0, 150.0, -150.0), 1400.0, 0.0, 0.30, pad=1.0)])


ZOOMS = {"a": zoom_a, "b": zoom_b, "c": zoom_c, "d": zoom_d, "e": zoom_e}


def run_zoom(letter):
    name = f"zoom_{letter}"
    m, root = start(name, beats=BEATS, page=PAGE)
    m.update(D.materials())
    s = D.scene(m, root)
    ZOOMS[letter](m, root, s)
    finish(name, page=PAGE)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) != 1 or argv[0] not in ZOOMS:
        raise SystemExit("usage: blender -b --python net_server_zooms.py -- <a|b|c|d|e>")
    run_zoom(argv[0])

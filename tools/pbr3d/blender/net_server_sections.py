"""The SERVER page's nine numbered sections, in the picture-and-panel template
(docs/diagram-pages.md). Section N illustrates heading N of
tui/src/screens/diagrams_pages/NET_SERVER.txt (the tenth, Sources, is text only). Three beats each,
one beat is 8 s.

Run one section per Blender process:

    blender -b --factory-startup --python tools/pbr3d/blender/net_server_sections.py -- <n>

Writes blender/net_server_section_<n>.blend and assets/net_server_section_<n>.glb. The node comes
from net_server_detail.py; close-ups (a GPU module and a NIC three times larger) are built above
the node at BY.

  1 what happens   GPU to GPU over NVLink inside; out through a NIC; up to the leaf
  2 the parts      baseboard and NVSwitch; host board, CPUs, PCIe switches; NICs and DPUs
  3 a packet       HBM to PCIe switch, to the NIC, through the cage, up the cable
  4 NVLink         one GPU's links; both switches; every pair at once
  5 PCIe + CPU     the switch tree; the CPU's DDR5; GPUDirect RDMA past the CPU
  6 NICs and DPU   a NIC three times larger; its cage and transceiver; the DPUs to the front end
  7 cooling        a cold plate three times larger, cut open; the rails; out to the rack manifold
  8 who makes it   makers tagged on the GPUs, switches, NICs, CPUs, cooling
  9 chokepoints    800 G per GPU; PCIe and NIC count; heat per node
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, label, beat, show  # noqa: E402
from sand_zooms import start, finish  # noqa: E402
import net_server_detail as D  # noqa: E402
from net_server_detail import frame, camera_path, run, rise, empty  # noqa: E402
import net_server_overview as OV  # noqa: E402

PAGE = "net_server"
BEATS = 3
BY = 320.0

V_ALL = frame((0.0, 30.0, -290.0), 640.0, 0.30, 0.70, pad=1.0)
V_GPU = frame((0.0, 0.0, -395.0), 380.0, 0.05, 1.05, pad=1.0)
V_HOST = frame((0.0, 0.0, -150.0), 440.0, 0.10, 0.95, pad=1.0)
V_FRONT = frame((0.0, 70.0, 0.0), 440.0, 0.30, 0.30, pad=1.0)
V_COOL = frame((0.0, 30.0, -470.0), 480.0, 0.60, 0.50, pad=1.0)
V_BENCH = frame((0.0, BY + 30.0, 0.0), 300.0, 0.25, 0.30, pad=1.0)


def span(b0, u0, b1, u1):
    return [(F(b0, u0), F(b1, u1))]


def tags(root, per_beat):
    for i, items in enumerate(per_beat):
        for text, pos in items:
            label(text, pos, root, beat(i))


def node(m, root, leaf=(), fe=()):
    s = D.scene(m, root)
    D.present(s["rails"], [])
    D.present(s["leaf"], [iv for b in leaf for iv in beat(b)])
    D.present(s["fe"], [iv for b in fe for iv in beat(b)])
    return s


def sec1(m, root):
    s = node(m, root, leaf=(2,))
    OV.nvlink(m, root, [0], n=2, size=3.0)
    OV.pcie(m, root, [1], n=3)
    OV.packets(m, root, [2])
    OV.leds(s, [2])
    tags(root, [
        [("GPU to GPU: NVLink", s["gpu"][1]["top"]), ("through NVSwitch", s["sw"][0]["top"])],
        [("off the node: PCIe to a NIC", s["psw"][1]["top"]), ("one NIC per GPU", s["nic"][2]["chip"])],
        [("up to the leaf", (0.0, D.LEAF[2], 65.0)), ("400-800 Gb/s per GPU", s["nic"][6]["cage"])],
    ])
    camera_path(root, [V_GPU, V_HOST, V_FRONT])


def sec2(m, root):
    s = node(m, root)
    OV.glow(s, beat(0))
    tags(root, [
        [("HGX baseboard", s["gpu"][6]["top"]), ("8 GPUs", s["gpu"][1]["top"]), ("2 NVSwitch chips", s["sw"][1]["top"])],
        [("2 CPUs + DDR5", s["cpu"][0]["top"]), ("4 PCIe switches", s["psw"][2]["top"]), ("MCIO cables", (D.PX[1], 20.0, -221.0))],
        [("8 ConnectX NICs", s["nic"][1]["cage"]), ("2 BlueField DPUs", s["dpu"][0]["chip"]), ("coolant headers", (-120.0, D.SUP_Y, D.HDR_Z))],
    ])
    camera_path(root, [V_GPU, V_HOST, V_ALL])


def sec3(m, root):
    s = node(m, root, leaf=(2,))
    k = 1
    p = D.pcie_path(k)
    OV.glow(s, beat(0))
    run(root, "s3_hbm", [s["gpu"][k]["hbm"], s["gpu"][k]["die"]] + p[1:5], 5, 3.0, m["pcie"], 0, 0.0, 0.85, 80)
    run(root, "s3_sw", p[3:], 5, 3.0, m["pcie"], 1, 0.0, 0.85, 80)
    OV.packets(m, root, [2], ns=[2], n=6, size=3.4)
    tags(root, [
        [("data leaves HBM", s["gpu"][k]["hbm"]), ("over the baseboard", (D.GX[1] + 30.0, 5.0, -250.0))],
        [("PCIe switch", s["psw"][1]["top"]), ("into the NIC", s["nic"][2]["chip"]), ("out the cage", s["nic"][2]["cage"])],
        [("transceiver: light", (D.NIC_X[2], 17.0, 14.0)), ("leaf port", (D.leaf_x(2), D.LEAF[2], 65.0))],
    ])
    camera_path(root, [frame((-55.0, 0.0, -280.0), 200.0, 0.15, 0.85), frame((-80.0, 0.0, -130.0), 240.0, 0.25, 0.70),
                       frame((-60.0, 90.0, 20.0), 300.0, 0.30, 0.25, pad=1.0)])


def sec4(m, root):
    s = node(m, root)
    OV.nvlink(m, root, [0], pairs=[(0, b, b % 2) for b in range(1, 8)], n=2, size=3.0)
    OV.nvlink(m, root, [1], pairs=[(k, (k + 2) % 8, 0) for k in range(8)] + [(k, (k + 6) % 8, 1) for k in range(8)], n=2, size=3.0)
    OV.nvlink(m, root, [2], n=2, size=3.0)
    tags(root, [
        [("one GPU: 18 links", s["gpu"][0]["top"]), ("1.8 TB/s", s["gpu"][1]["top"])],
        [("left NVSwitch", s["sw"][0]["top"]), ("right NVSwitch", s["sw"][1]["top"])],
        [("every pair at full speed", s["gpu"][6]["top"]), ("14.4 TB/s total", s["sw"][1]["top"])],
    ])
    camera_path(root, [V_GPU, frame((0.0, 0.0, -395.0), 200.0, 0.15, 0.70), V_GPU])


def sec5(m, root):
    s = node(m, root)
    OV.pcie(m, root, [0], n=3)
    OV.cpu_links(m, root, [0, 1], n=3)
    for i, cx in enumerate(D.CPUX):
        for sd in (-1, 1):
            for j in range(2):
                x = cx + sd * (50.0 + 20.0 * j)
                run(root, f"s5_dd{i}{sd}{j}", [(x, 30.0, D.CPUZ - 50.0), (cx + sd * 30.0, 10.0, D.CPUZ)], 3, 1.8, m["mem"], 1, 0.05 + 0.1 * j, 0.85, 30)
    OV.pcie(m, root, [2], ks=[0, 2, 5, 7], n=4)
    tags(root, [
        [("4 PCIe Gen5 switches", s["psw"][0]["top"]), ("2 GPUs + 2 NICs each", s["psw"][2]["top"])],
        [("CPU: the host", s["cpu"][0]["top"]), ("DDR5: ~2 TB", s["cpu"][1]["dimm"])],
        [("GPUDirect RDMA", s["psw"][1]["top"]), ("GPU memory straight to NIC", s["nic"][6]["chip"])],
    ])
    camera_path(root, [V_HOST, frame((0.0, 10.0, -112.0), 340.0, 0.10, 0.70, pad=1.0), V_HOST])


def sec6(m, root):
    s = node(m, root, fe=(2,))
    g = empty("s6_bench", root)
    _, leds, pts = D.nic(m, g, "bnic", 0.0, y0=BY, s=3.0, z0=-56.0, z1=-6.0)
    D.present(g, span(0, 0.0, 2, 0.0))
    run(root, "s6_in", [(0.0, BY + 18.0, -150.0), (0.0, BY + 26.0, -100.0), pts["ports"][0]], 6, 3.0, m["pcie"], 0, 0.0, 0.8, 60)
    run(root, "s6_out", [pts["ports"][0], (0.0, BY + 38.0, 80.0), (0.0, BY + 38.0, 160.0)], 6, 3.4, m["pkt"], 1, 0.0, 0.85, 50)
    D.blink(leds[0], 1, range(16), 16, 0.5)
    OV.frontend(m, root, s, [2])
    tags(root, [
        [("ConnectX chip", pts["chip"]), ("PCIe in", (0.0, BY + 22.0, -120.0))],
        [("OSFP cage", pts["cage"]), ("400G (CX-7) / 800G (CX-8)", (0.0, BY + 38.0, 120.0))],
        [("BlueField-3 DPUs", s["dpu"][0]["chip"]), ("front end + storage", (D.FE[0] + 40.0, D.FE[3], 55.0))],
    ])
    camera_path(root, [frame((0.0, BY + 20.0, -100.0), 220.0, 0.30, 0.40, pad=1.0), frame((0.0, BY + 30.0, 20.0), 260.0, 0.45, 0.25, pad=1.0),
                       frame((140.0, 50.0, 0.0), 300.0, 0.45, 0.30, pad=1.0)])


def sec7(m, root):
    s = node(m, root)
    g = empty("s7_bench", root)
    _, glow, pts = D.gpu(m, g, "bgpu", 0.0, 0.0, y0=BY, s=3.0, cut_open=True)
    D.present(g, beat(0))
    show(glow, beat(0))
    for j in range(4):
        zz = -10.0 - 20.0 * j
        run(root, f"s7_f{j}", [(-84.0, BY + 54.0, zz), (84.0, BY + 54.0, zz)], 4, 3.0, m["cold"], 0, 0.04 * j, 0.6, 60)
        run(root, f"s7_w{j}", [(-20.0, BY + 54.0, zz), (84.0, BY + 54.0, zz)], 3, 3.0, m["warm"], 0, 0.3 + 0.04 * j, 0.9, 40)
    rise(root, "s7_h", pts["die"], 6, 2.4, m["heat"], 0, 0.05, 0.8, 40.0, 60, (30.0, 0.0))
    OV.coolant(m, root, [1, 2])
    OV.heat(m, root, s, 1)
    OV.glow(s, span(1, 0.0, 3, 0.0))
    tags(root, [
        [("coolant through microchannels", pts["fins"]), ("die heat into copper", pts["die"])],
        [("supply rail to every plate", (D.GX[0] - 28.0, D.SUP_Y, -400.0)), ("return rail", (D.GX[3] + 28.0, D.RET_Y, -400.0))],
        [("quick disconnects", (40.0, D.RET_Y, -615.0)), ("rack manifold", (-40.0, 160.0, -620.0))],
    ])
    camera_path(root, [frame((0.0, BY + 30.0, 0.0), 300.0, 0.25, 0.30, pad=1.0), V_COOL, frame((0.0, 60.0, -600.0), 320.0, 0.70, 0.30, pad=1.0)])


def sec8(m, root):
    s = node(m, root)
    tags(root, [
        [("GPUs + NVSwitch: NVIDIA", s["gpu"][1]["top"]), ("HBM: SK hynix, Micron, Samsung", s["gpu"][6]["top"])],
        [("PCIe switches: Broadcom, Astera", s["psw"][1]["top"]), ("CPUs: Intel, AMD", s["cpu"][1]["top"]), ("NICs + DPUs: NVIDIA", s["nic"][6]["cage"])],
        [("servers: SMCI, Dell, HPE, Foxconn", s["gpu"][2]["top"]), ("cold plates: Vertiv, CoolIT, Boyd", (-120.0, D.SUP_Y, D.HDR_Z))],
    ])
    camera_path(root, [V_GPU, V_HOST, V_ALL])


def sec9(m, root):
    s = node(m, root, leaf=(0,))
    OV.packets(m, root, [0], n=6)
    OV.pcie(m, root, [1], n=5)
    OV.glow(s, beat(2))
    OV.heat(m, root, s, 2)
    OV.coolant(m, root, [2])
    tags(root, [
        [("800 Gb/s per GPU and rising", s["nic"][5]["cage"]), ("optics per port", (D.NIC_X[2], 17.0, 14.0))],
        [("PCIe lanes are shared", s["psw"][2]["top"]), ("one NIC per GPU", s["nic"][1]["chip"])],
        [("~14 kW in one chassis", s["gpu"][1]["top"]), ("liquid is no longer optional", (-120.0, D.SUP_Y, D.HDR_Z))],
    ])
    camera_path(root, [V_FRONT, V_HOST, V_COOL])


SECTIONS = {1: sec1, 2: sec2, 3: sec3, 4: sec4, 5: sec5, 6: sec6, 7: sec7, 8: sec8, 9: sec9}


def build(n):
    m, root = start(f"section_{n}", beats=BEATS, page=PAGE)
    m.update(D.materials())
    SECTIONS[n](m, root)
    finish(f"section_{n}", page=PAGE)


if __name__ == "__main__":
    build(int(sys.argv[sys.argv.index("--") + 1]))

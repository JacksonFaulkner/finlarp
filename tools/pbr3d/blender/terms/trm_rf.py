"""TRM_RF on the MLCC base board. AI boards carry no radios, so the bench holds a phone's RF
front-end module, shield off: PA, LNA, switch, BAW filters, antenna; then one BAW resonator, cut.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_rf.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show  # noqa: E402
from power_vrm_detail import frame, run  # noqa: E402

SLUG = "TRM_RF"
BEATS = [
    ("RF chips sit between the antenna and the modem",
     "This GPU board has no radio: RF (radio-frequency) chips live in phones, base stations, Wi-Fi gear and satellites. "
     "Beside the board is a phone's RF front-end module, the block between antenna and modem, drawn large with its "
     "shield lifted off."),
    ("Inside: amplifiers, a switch and a row of filters",
     "On a small laminate sit a power amplifier (PA, often gallium arsenide) to transmit, a low-noise amplifier (LNA) to "
     "receive, an antenna switch to pick the band, and acoustic filters (BAW/SAW) that pass only one band each. A 5G phone "
     "needs dozens of bands, so it carries many filters."),
    ("Transmit: the PA boosts the signal out through a filter",
     "The transceiver's weak signal enters the PA, leaves a few hundred milliwatts strong, passes the band's filter so it "
     "does not spill into neighbours, then the switch routes it to the antenna, which radiates it."),
    ("Receive: a faint signal, cleaned and amplified",
     "Incoming signals can be a billionth of a milliwatt. The switch sends them through the right filter to the LNA, "
     "which lifts them while adding as little noise as possible before the transceiver digitizes them."),
    ("A BAW filter: a vibrating sliver of crystal",
     "Each filter is built from bulk acoustic wave (BAW) resonators: a thin piezoelectric film (aluminium nitride) between "
     "metal electrodes, over a mirror stack. It rings mechanically at one GHz frequency, so only that band passes. Revenue "
     "tracks handset cycles and band counts. Makers: Qorvo (QRVO), Skyworks (SWKS), Broadcom (AVGO), Qualcomm (QCOM), Murata."),
]

MX0, MX1, MZ0, MZ1 = 160.0, 240.0, -110.0, -45.0
Y0 = 0.6
# the giant BAW at the front
BX0, BX1, BZ0 = 168.0, 232.0, -26.0


def module(m, root):
    g = empty("fem", root)
    bx("fem_lam", (MX0, Y0, MZ0), (MX1, Y0 + 3.0, MZ1), m["pcb_blue"], g)
    for k in range(3):
        bx(f"fem_cu{k}", (MX0, Y0 + 0.7 + 0.8 * k, MZ0), (MX1, Y0 + 0.9 + 0.8 * k, MZ1 + 0.05), m["copper"], g)
    # shield can, lifted and floating above the back half
    bx("fem_can", (MX0 - 1.0, 0.0, MZ0 - 72.0), (MX1 + 1.0, 1.0, MZ0 - 6.0), m["steel"], g)
    for k, (za, zb) in enumerate(((MZ0 - 72.0, MZ0 - 70.0), (MZ0 - 8.0, MZ0 - 6.0))):
        bx(f"fem_can_w{k}", (MX0 - 1.0, 1.0, za), (MX1 + 1.0, 4.0, zb), m["steel"], g)
    y = Y0 + 3.0
    parts = {
        "pa": (MX0 + 6.0, MZ0 + 30.0, MX0 + 26.0, MZ0 + 50.0, "gan"),
        "lna": (MX0 + 6.0, MZ0 + 8.0, MX0 + 20.0, MZ0 + 22.0, "si"),
        "sw": (MX0 + 50.0, MZ0 + 22.0, MX0 + 62.0, MZ0 + 38.0, "si"),
        "trx": (MX0 - 30.0, MZ0 + 18.0, MX0 - 10.0, MZ0 + 42.0, "mold"),
    }
    cen = {}
    for k, (a, b_, c, d, mt) in parts.items():
        yy = 0.0 if k == "trx" else y
        bx(f"p_{k}", (a, yy, b_), (c, yy + 2.0, d), m[mt], g)
        cen[k] = ((a + c) / 2, yy + 2.0, (b_ + d) / 2)
    # PA's HBT fingers
    for i in range(8):
        x = MX0 + 8.0 + 2.2 * i
        bx(f"pa_f{i}", (x, y + 2.0, MZ0 + 33.0), (x + 1.0, y + 2.4, MZ0 + 47.0), m["gold"], g)
    # filters: 2 rows of 3
    filt = []
    for i in range(3):
        for j in range(2):
            a, b_ = MX0 + 30.0 + 0.0 * i, MZ0 + 6.0 + 18.0 * i + 0.0 * j
            x0 = MX0 + 30.0 + 8.0 * j
            bx(f"f{i}{j}", (x0, y, b_), (x0 + 7.0, y + 1.6, b_ + 12.0), m["aln"], g)
            for r in range(3):
                bx(f"f{i}{j}r{r}", (x0 + 1.0, y + 1.6, b_ + 1.0 + 3.6 * r), (x0 + 6.0, y + 1.9, b_ + 3.6 + 3.6 * r), m["moly"], g)
            filt.append((x0 + 3.5, y + 1.9, b_ + 6.0))
    for k in ("pa", "lna", "sw"):
        a, b_, c, d, _ = parts[k]
        for i in range(4):
            z = b_ + (d - b_) * (i + 0.5) / 4
            D.wire(f"bw_{k}{i}", D.arc((c, y + 2.0, z), (c + 3.0, y, z), 1.5, 5), 0.15, m["gold"], g, 6)
    # antenna: an inverted-F copper strip standing at the module's right end
    ant = [(MX1 - 6.0, y, MZ0 + 30.0), (MX1 - 6.0, y + 16.0, MZ0 + 30.0), (MX1 - 6.0, y + 16.0, MZ1 - 4.0)]
    D.polyline("ant", ant, 0.8, m["copper"], g)
    bx("ant_short", (MX1 - 6.8, y, MZ0 + 22.0), (MX1 - 5.2, y + 16.0, MZ0 + 23.6), m["copper"], g)
    cen["ant"] = (MX1 - 6.0, y + 16.0, (MZ0 + MZ1) / 2)
    cen["filt"] = filt
    # traces
    tr = lambda pts: [(p[0], y + 0.3, p[2]) for p in pts]  # noqa: E731
    paths = {
        "tx": tr([(MX0 - 10.0, 0, MZ0 + 36.0), (MX0 + 6.0, 0, MZ0 + 40.0), (MX0 + 26.0, 0, MZ0 + 40.0), filt[4],
                  (MX0 + 56.0, 0, MZ0 + 30.0), (MX1 - 6.0, 0, MZ0 + 30.0)]) + [ant[1], ant[2]],
        "rx": [ant[2], ant[1]] + tr([(MX1 - 6.0, 0, MZ0 + 30.0), (MX0 + 56.0, 0, MZ0 + 30.0), filt[1],
                                     (MX0 + 20.0, 0, MZ0 + 15.0), (MX0 + 6.0, 0, MZ0 + 15.0), (MX0 - 10.0, 0, MZ0 + 24.0)]),
    }
    return cen, paths


def baw(m, root):
    """One BAW resonator, cut: Bragg mirror (alternating W / SiO2), Mo bottom electrode, AlN film,
    Mo top electrode. The film group vibrates."""
    g = empty("baw", root)
    bx("baw_si", (BX0, Y0, BZ0), (BX1, Y0 + 6.0, 0.0), m["si"], g)
    y = Y0 + 6.0
    for k in range(6):
        bx(f"bragg{k}", (BX0, y, BZ0), (BX1, y + 1.5, 0.0), m["moly" if k % 2 else "oxide"], g)
        y += 1.5
    bx("baw_mo_b", (BX0 + 6.0, y, BZ0 + 3.0), (BX1 - 6.0, y + 1.2, 0.0), m["moly"], g)
    film = empty("baw_film", root)
    bx("baw_aln", (BX0 + 4.0, y + 1.2, BZ0 + 2.0), (BX1 - 4.0, y + 7.0, 0.0), m["aln"], film)
    bx("baw_mo_t", (BX0 + 10.0, y + 7.0, BZ0 + 5.0), (BX1 - 10.0, y + 8.2, 0.0), m["moly"], film)
    acoust = empty("baw_wave", film)
    for k in range(5):
        x = BX0 + 14.0 + k * 9.0
        bx(f"aw{k}", (x, y + 1.6, -0.1), (x + 1.0, y + 6.6, 0.15), m["rf"], acoust)
    show(acoust, [])
    return film, acoust, {"aln": (BX0 + 20.0, y + 4.0, 0.0), "top": ((BX0 + BX1) / 2, y + 8.2, 0.0),
                          "bragg": (BX1 - 8.0, Y0 + 10.0, 0.0), "res": ((BX0 + BX1) / 2, y + 8.0, BZ0 / 2)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    b = C.base(m, root)
    cen, paths = module(m, root)
    film, acoust, bp = baw(m, root)
    run(root, "tx", paths["tx"], 8, 0.9, m["rf"], 2, 0.0, 0.6, 70)
    for r in C.rings(m, root, "txw", cen["ant"], [2], n=4, r0=3.0, r1=45.0, mt="rf"):
        pass
    run(root, "rx", paths["rx"], 8, 0.5, m["sig"], 3, 0.0, 0.6, 70)
    for r in C.rings(m, root, "rxw", cen["ant"], [3], n=3, r0=45.0, r1=3.0, mt="sig"):
        pass
    C.wiggle(film, [4], amp=(0.0, 0.35, 0.0), period=4)
    show(acoust, [(F(4, 0.1), F(5, 0))])

    C.tags(root, {
        0: [("GPU board: no radio here", b["pk"]["top"]), ("phone RF front-end", (200.0, 6.0, -78.0)), ("its shield can, set aside", (200.0, 2.0, MZ0 - 40.0))],
        1: [("power amplifier (GaAs)", cen["pa"]), ("low-noise amplifier", cen["lna"]), ("antenna switch", cen["sw"]),
            ("BAW filters, one per band", cen["filt"][2]), ("antenna", cen["ant"])],
        2: [("PA boosts the signal", cen["pa"]), ("filter keeps it in band", cen["filt"][4]), ("radiated", cen["ant"])],
        3: [("faint signal in", cen["ant"]), ("LNA lifts it, low noise", cen["lna"])],
        4: [("AlN film rings at GHz", bp["aln"]), ("Mo electrodes", bp["top"]), ("acoustic mirror", bp["bragg"]),
            ("QRVO, SWKS, AVGO, QCOM", bp["res"])],
    })
    mc = ((MX0 + MX1) / 2, 6.0, (MZ0 + MZ1) / 2)
    C.done(SLUG, BEATS, [
        frame((100.0, 5.0, -90.0), 340.0, 0.40, 0.60, pad=1.0),
        frame(mc, 120.0, 0.25, 0.75),
        frame(mc, 120.0, 0.35, 0.60),
        frame(mc, 120.0, 0.15, 0.60),
        frame(((BX0 + BX1) / 2, 15.0, -6.0), 85.0, 0.15, 0.12),
    ], root)


if __name__ == "__main__":
    build()

"""Detailed close-up rig for the PLANAR sections (chip_planar.py sec1-sec10).

device() builds one planar MOSFET as a cut-away block, big enough to fill the left pane: the
silicon body (p-type for an NMOS, an n-well for a PMOS), shallow-trench-isolation oxide at both
ends, deep source/drain wells with shallow extensions under the gate edge, the gate dielectric
(SiON, or an IL plus HfO2), the gate (polysilicon or metal) with nitride spacers, nickel-silicide
caps and two tungsten contacts. Options give the FD-SOI version (a thin film on buried oxide),
SiGe source/drain for the PMOS and a tensile nitride liner for the NMOS.

Also: carrier streams for the on-current and the four leakage paths, depletion regions, arrows,
and a cut SOI wafer. Units are schematic millimetres, Y up, the cut face at z = 0 with the
camera on +z. A drawn gate half-length of 110 stands for a ~30-45 nm-class gate, 300 for a long
(~0.25 um-class) one; films are drawn thicker than life.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import F, box, cut, disc, empty, label, mat, show  # noqa: E402
from chip_gate_stack_detail import arc, arrow, electrons, group, part, span, track  # noqa: E402

W = 900.0  # the block's half-width
DZ = 700.0  # how far it runs back from the cut face
BOT = -470.0
STI = 170.0  # isolation width at each end
GATE_H = 280.0
ZD = 30.0  # carrier streams run this far in front of the cut face


def mats(m):
    m["p_sub"] = mat("pl_sub", (0.66, 0.56, 0.40), rough=0.75)
    m["p_nwell"] = mat("pl_nwell", (0.55, 0.62, 0.48), rough=0.75)
    m["p_nplus"] = mat("pl_nplus", (0.36, 0.53, 0.92), rough=0.55)
    m["p_pplus"] = mat("pl_pplus", (0.92, 0.50, 0.55), rough=0.55)
    m["p_sige"] = mat("pl_sige", (0.95, 0.62, 0.28), rough=0.5)
    m["p_sti"] = mat("pl_sti", (0.86, 0.90, 0.97), rough=0.4)
    m["p_sion"] = mat("pl_sion", (0.92, 0.94, 1.0), rough=0.35)
    m["p_il"] = mat("pl_il", (0.78, 0.82, 0.88), rough=0.5)
    m["p_hfo2"] = mat("pl_hfo2", (0.98, 0.84, 0.25), rough=0.35)
    m["p_poly"] = mat("pl_poly", (0.55, 0.36, 0.22), rough=0.65)
    m["p_metal"] = mat("pl_metal", (0.58, 0.60, 0.68), metal=0.85, rough=0.3)
    m["p_spacer"] = mat("pl_spacer", (0.36, 0.62, 0.58), rough=0.5)
    m["p_silicide"] = mat("pl_silicide", (0.28, 0.28, 0.32), metal=0.7, rough=0.4)
    m["p_w"] = mat("pl_w", (0.62, 0.64, 0.70), metal=0.9, rough=0.28)
    m["p_liner"] = mat("pl_liner", (0.30, 0.85, 0.55), emit=(0.25, 0.80, 0.50), strength=0.6, alpha=0.75)
    m["p_box"] = mat("pl_box", (0.80, 0.88, 1.0), emit=(0.70, 0.82, 1.0), strength=0.25)
    m["p_film"] = mat("pl_film", (0.82, 0.76, 0.62), rough=0.6)
    m["p_dep"] = mat("pl_dep", (1.0, 0.45, 0.30), emit=(1.0, 0.40, 0.25), strength=0.9, alpha=0.38)
    m["p_reach"] = mat("pl_reach", (1.0, 0.30, 0.30), emit=(1.0, 0.25, 0.25), strength=0.7, alpha=0.28)
    m["p_bias"] = mat("pl_bias", (0.75, 0.55, 1.0), emit=(0.70, 0.50, 1.0), strength=1.2, alpha=0.45)
    m["p_on"] = mat("pl_on", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=2.2)
    m["p_sub_leak"] = mat("pl_sub_leak", (1.0, 0.35, 0.30), emit=(1.0, 0.30, 0.25), strength=2.2)
    m["p_tun"] = mat("pl_tun", (1.0, 0.50, 0.85), emit=(1.0, 0.45, 0.80), strength=2.2)
    m["p_gidl"] = mat("pl_gidl", (1.0, 0.75, 0.25), emit=(1.0, 0.70, 0.20), strength=2.2)
    m["p_punch"] = mat("pl_punch", (1.0, 0.20, 0.45), emit=(1.0, 0.15, 0.40), strength=2.2)
    m["p_chan"] = mat("pl_chan", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=2.0, alpha=0.8)
    m["p_field"] = mat("pl_field", (1.0, 0.72, 0.35), emit=(1.0, 0.65, 0.25), strength=3.0)
    m["p_push"] = mat("pl_push", (1.0, 0.55, 0.25), emit=(1.0, 0.50, 0.20), strength=3.0)
    m["p_pull"] = mat("pl_pull", (0.35, 1.0, 0.60), emit=(0.30, 1.0, 0.55), strength=3.0)
    m["p_hl"] = mat("pl_hl", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=1.0, alpha=0.25)
    m["p_wafer"] = mat("pl_wafer", (0.55, 0.58, 0.66), metal=0.8, rough=0.25)
    m["p_bar"] = mat("pl_bar", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=2.5)
    m["p_trk_on"] = mat("pl_trk_on", (0.40, 0.95, 1.0), emit=(0.40, 0.95, 1.0), strength=0.8, alpha=0.30)
    m["p_trk_leak"] = mat("pl_trk_leak", (1.0, 0.40, 0.35), emit=(1.0, 0.35, 0.30), strength=0.8, alpha=0.30)


def device(parent, m, cx=0.0, lg=110.0, kind="n", gate="poly", diel="sion", soi=False, sige=False,
           liner=False, ivs=None, pre="dev", contacts=True):
    """One planar transistor centred on cx (see the module docstring). Returns a dict of
    reference points: gate top, dielectric top, source/drain inner edges, junction depth."""
    g = group(pre, parent, ivs)
    sub = m["p_nwell"] if kind == "p" else m["p_sub"]
    sd = m["p_sige"] if sige else (m["p_pplus"] if kind == "p" else m["p_nplus"])
    x0, x1 = cx - W, cx + W
    film = -70.0
    if soi:
        box(f"{pre}_handle", (x0, BOT, -DZ), (x1, -150.0, 0.0), sub, g)
        box(f"{pre}_box", (x0, -150.0, -DZ), (x1, film, 0.0), m["p_box"], g)
        box(f"{pre}_film", (x0 + STI, film, -DZ), (x1 - STI, 0.0, 0.0), m["p_film"], g)
        sti_bot, sd_bot, ext_bot, sd_top = film, film, film, 46.0
    else:
        box(f"{pre}_sub", (x0, BOT, -DZ), (x1, 0.0, 0.0), sub, g)
        sti_bot, sd_bot, ext_bot, sd_top = -300.0, -170.0, -55.0, 40.0 if sige else 2.0
    for s in (-1, 1):
        a, b = cx + s * (W - STI), cx + s * W
        box(f"{pre}_sti{s}", (min(a, b), sti_bot, -DZ), (max(a, b), 4.0, 3.0), m["p_sti"], g)
        a, b = cx + s * (lg + 70.0), cx + s * (W - STI)
        box(f"{pre}_sd{s}", (min(a, b), sd_bot, -DZ), (max(a, b), sd_top, 2.0), sd, g)
        if not soi:
            a2 = cx + s * (lg - 22.0)
            box(f"{pre}_ext{s}", (min(a2, a), ext_bot, -DZ), (max(a2, a), 2.0, 2.0), sd, g)
        a, b = cx + s * (lg + 90.0), cx + s * (W - STI - 20.0)
        box(f"{pre}_sil{s}", (min(a, b), sd_top, -DZ), (max(a, b), sd_top + 16.0, 3.0), m["p_silicide"], g)
    # gate dielectric, gate, spacers, gate silicide
    zb = -DZ + 60.0
    if diel == "hk":
        box(f"{pre}_il", (cx - lg, 0.0, zb), (cx + lg, 8.0, 3.0), m["p_il"], g)
        box(f"{pre}_hk", (cx - lg, 8.0, zb), (cx + lg, 34.0, 3.0), m["p_hfo2"], g)
        tox = 34.0
    else:
        tox = 12.0
        box(f"{pre}_ox", (cx - lg, 0.0, zb), (cx + lg, tox, 3.0), m["p_sion"], g)
    top = tox + GATE_H
    box(f"{pre}_gate", (cx - lg, tox, zb), (cx + lg, top, 3.0), m["p_poly"] if gate == "poly" else m["p_metal"], g)
    for s in (-1, 1):
        a, b = cx + s * lg, cx + s * (lg + 70.0)
        box(f"{pre}_spacer{s}", (min(a, b), 2.0, zb), (max(a, b), top, 3.0), m["p_spacer"], g)
    if gate == "poly":
        box(f"{pre}_gsil", (cx - lg, top, zb), (cx + lg, top + 16.0, 3.0), m["p_silicide"], g)
    if liner:
        lg_ = group(f"{pre}_liner", g, liner if isinstance(liner, list) else None)
        for s in (-1, 1):
            a, b = cx + s * (lg + 70.0), cx + s * (W - STI)
            box(f"{pre}_ln_sd{s}", (min(a, b), sd_top + 16.0, zb), (max(a, b), sd_top + 34.0, 5.0), m["p_liner"], lg_)
            a, b = cx + s * (lg + 70.0), cx + s * (lg + 88.0)
            box(f"{pre}_ln_w{s}", (min(a, b), sd_top + 34.0, zb), (max(a, b), top + 34.0, 5.0), m["p_liner"], lg_)
        box(f"{pre}_ln_top", (cx - lg - 70.0, top + 16.0, zb), (cx + lg + 70.0, top + 34.0, 5.0), m["p_liner"], lg_)
    if contacts:
        from sand_overview import tube
        for s in (-1, 1):
            x = cx + s * (lg + 70.0 + (W - STI - lg - 70.0) / 2)
            tube(f"{pre}_ct{s}", (x, sd_top + 16.0, -200.0), (x, top + 240.0, -200.0), 34.0, m["p_w"], g, 12)
        tube(f"{pre}_ctg", (cx, top + 16.0, -420.0), (cx, top + 240.0, -420.0), 30.0, m["p_w"], g, 12)
    return {"top": top, "tox": tox, "sd_in": lg + 70.0 if soi else lg - 22.0, "jd": sd_bot, "cx": cx,
            "lg": lg, "sd_top": sd_top, "film": film}


def stream(root, m, name, pts, n, b, u0=0.08, u1=0.80, life=60, key="p_sub_leak", size=16.0):
    return electrons(root, m, name, pts, n, b, u0, u1, life, key, size)


def ride(root, m, name, pts, n, b, key, trk, ivs=None, u0=0.05, u1=0.85, life=70, size=16.0):
    """Beads riding a faint segmented track along `pts` (the track shows for `ivs`, default beat b)."""
    track(root, name + "_trk", pts, size * 0.32, m[trk], ivs or span(b, b + 1))
    return electrons(root, m, name, pts, n, b, u0, u1, life, key, size)


def paths(d):
    """The on-current and the four leak paths of device `d`, as point lists in front of the cut."""
    cx, lg, tox = d["cx"], d["lg"], d["tox"]
    x = lg + 120.0
    return {
        "on": arc((cx - x, -12.0, ZD), (cx + x, -12.0, ZD), -4.0, 8),
        "sub": arc((cx + x, -18.0, ZD), (cx - x, -18.0, ZD), -10.0, 8),
        "tun": [[(cx + f * lg, -10.0, ZD), (cx + f * lg, tox + 90.0, ZD)] for f in (-0.5, 0.0, 0.5)],
        "gidl": arc((cx + lg + 30.0, -10.0, ZD), (cx + lg + 160.0, -420.0, ZD), -40.0, 8),
        "punch": arc((cx + lg + 60.0, -120.0, ZD), (cx - lg - 60.0, -120.0, ZD), -130.0, 10),
    }


def on_current(root, m, d, b, name="on", n=10, u0=0.05, u1=0.85):
    cx, x = d["cx"], d["lg"] + 120.0
    return stream(root, m, name, [(cx - x, -12.0, ZD), (cx + x, -12.0, ZD)], n, b, u0, u1, 70, "p_on")


def leak_sub(root, m, d, b, name="sub", n=6):
    cx, x = d["cx"], d["lg"] + 120.0
    return stream(root, m, name, [(cx + x, -16.0, ZD), (cx - x, -16.0, ZD)], n, b, 0.08, 0.85, 90, "p_sub_leak")


def leak_tunnel(root, m, d, b, name="tun", n=3, u1=0.85):
    cx = d["cx"]
    for k, dx in enumerate((-0.5, 0.0, 0.5)):
        stream(root, m, f"{name}{k}", [(cx + dx * d["lg"], -10.0, ZD), (cx + dx * d["lg"], d["tox"] + 90.0, ZD)],
               n, b, 0.02 + 0.04 * k, u1, 45, "p_tun", 13.0)


def leak_gidl(root, m, d, b, name="gidl", n=5):
    cx, x = d["cx"], d["lg"] + 40.0
    return stream(root, m, name, [(cx + x, -10.0, ZD), (cx + x + 40.0, -200.0, ZD), (cx + x + 60.0, -400.0, ZD)],
                  n, b, 0.08, 0.85, 70, "p_gidl")


def leak_punch(root, m, d, b, name="punch", n=8, depth=-210.0):
    cx, x = d["cx"], d["lg"] + 60.0
    return stream(root, m, name, [(cx + x, -120.0, ZD), (cx + 0.4 * x, depth, ZD), (cx - 0.4 * x, depth, ZD),
                                  (cx - x, -120.0, ZD)], n, b, 0.08, 0.85, 90, "p_punch")


def depletion(parent, m, d, reach, ivs, pre="dep"):
    """The depletion region round each source/drain junction, reaching `reach` into the body."""
    g = group(pre, parent, ivs)
    cx, sx, jd = d["cx"], d["sd_in"], d["jd"]
    for s in (-1, 1):
        a, b = cx + s * (sx - reach), cx + s * sx
        box(f"{pre}_side{s}", (min(a, b), jd - reach, -DZ + 80.0), (max(a, b), 0.0, 8.0), m["p_dep"], g)
        a, b = cx + s * sx, cx + s * (W - STI)
        box(f"{pre}_bot{s}", (min(a, b), jd - reach, -DZ + 80.0), (max(a, b), jd, 8.0), m["p_dep"], g)
    return g


def field_arrows(parent, m, d, ivs, pre="fld", depth=-60.0):
    g = group(pre, parent, ivs)
    cx = d["cx"]
    for k, f in enumerate((-0.6, 0.0, 0.6)):
        x = cx + f * d["lg"]
        arrow(f"{pre}{k}", (x, d["top"] - 40.0, ZD), (x, depth, ZD), 6.0, m["p_field"], g)
    return g


def soi_wafer(parent, m, ivs, pre="wafer", c=(0.0, 0.0, 0.0), r=700.0):
    """A 300 mm SOI wafer, cut in half to show its three layers (drawn thick): the handle wafer,
    the buried oxide and the thin top silicon film."""
    g = group(pre, parent, ivs)
    x, y, z = c
    o = disc(f"{pre}_handle", (x, y - 70.0, z), r, 140.0, m["p_wafer"], g)
    cut(o, z)
    o = disc(f"{pre}_box", (x, y + 15.0, z), r, 30.0, m["p_box"], g)
    cut(o, z + 2.0)
    o = disc(f"{pre}_top", (x, y + 42.0, z), r, 24.0, m["p_film"], g)
    cut(o, z + 4.0)
    return g


def wafer_stack(parent, m, n, ivs_each, pre="ws", c=(0.0, 0.0, 0.0), r=520.0):
    """Bare wafers stacked one above the next; wafer k shows during ivs_each[k]."""
    g = group(pre, parent)
    x, y, z = c
    for k in range(n):
        wg = group(f"{pre}{k}", g, ivs_each[k])
        disc(f"{pre}{k}_d", (x, y + k * 46.0, z), r, 30.0, m["p_wafer"], wg)
    return g


__all__ = ["mats", "device", "stream", "on_current", "leak_sub", "leak_tunnel", "leak_gidl", "leak_punch",
           "depletion", "field_arrows", "ride", "paths", "arc", "track", "soi_wafer", "wafer_stack", "arrow", "group", "part", "span", "label",
           "box", "empty", "show", "F", "W", "DZ", "BOT", "STI", "ZD"]

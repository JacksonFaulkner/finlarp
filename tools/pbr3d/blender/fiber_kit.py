"""Shared station geometry for the FIBER tab (PAM4 DSP, LASER, OPTICAL FIBER, PHOTODIODE, TRANSCEIVER, CPO).

Every fiber page builds its picture from these builders, so one station looks the same on every page.
Units mm, Y up, camera on +z. Each builder takes the material dict from `materials()` and a parent empty.
Built from the references in scratchpad/refs (SFP/X2 photos, Nortel module, pluggable vs NPO vs CPO,
CPO evolution ladder): a flip-chip DSP package, TO-can lasers and photodiodes, a glass fibre with
ferrules, a finned pluggable module in a cage, and a CPO package with the optical engine beside the ASIC.

Stations and their centres (x, mm). The host board runs under all six.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sand_overview import box, tube, ball  # noqa: E402
from pbr_kit import empty, mat  # noqa: E402

DSP_X, LASER_X, PD_X, MOD_X, CPO_X = 0.0, 40.0, 122.0, 172.0, 236.0
FIBRE_Y = -5.0          # height of the fibre's axis
FIBRE_X0 = LASER_X + 12  # where the fibre starts (leaves the laser)
FIBRE_X1 = PD_X - 10.0   # where it ends (at the photodiode)


def bevel(o, w=0.6):
    """Round a housing's hard edges so it reads as a part, not a box."""
    if o is None:
        return o
    mod = o.modifiers.new("bevel", "BEVEL")
    mod.width = w
    mod.segments = 2
    mod.limit_method = "ANGLE"
    return o


def part(name, lo, hi, m, parent, w=0.6):
    """A bevelled box. `w` is the bevel width (0 for flat slabs)."""
    return bevel(box(name, lo, hi, m, parent), w)


def materials():
    return {
        "board": mat("fib_board", (0.10, 0.34, 0.20), rough=0.7),
        "copper": mat("fib_copper", (0.80, 0.50, 0.30), metal=0.9, rough=0.3),
        "substrate": mat("fib_substrate", (0.42, 0.27, 0.15), rough=0.8),
        "die": mat("fib_die", (0.16, 0.18, 0.22), metal=0.3, rough=0.4),
        "steel": mat("fib_steel", (0.62, 0.65, 0.70), metal=0.8, rough=0.35),
        "dark_steel": mat("fib_dark_steel", (0.25, 0.27, 0.30), metal=0.7, rough=0.45),
        "gold": mat("fib_gold", (0.85, 0.70, 0.30), metal=0.9, rough=0.3),
        "oe": mat("fib_oe", (0.20, 0.40, 0.70), metal=0.4, rough=0.35),
        "glass": mat("fib_glass", (0.60, 0.80, 0.90), rough=0.1, alpha=0.2),
        "cladding": mat("fib_cladding", (0.70, 0.85, 0.95), rough=0.2, alpha=0.35),
        "light": mat("fib_light", (1.0, 0.35, 0.20), emit=(1.0, 0.35, 0.20), strength=8.0),
        "elec": mat("fib_elec", (0.30, 0.90, 1.00), emit=(0.20, 0.90, 1.00), strength=8.0),
        "cage": mat("fib_cage", (0.45, 0.48, 0.52), metal=0.6, rough=0.5, alpha=0.3),
    }


def board(m, parent):
    return part("board", (-30.0, -10.0, -30.0), (270.0, -7.0, 30.0), m["board"], parent, w=0.0)


def dsp(m, parent):
    """PAM4 DSP: flip-chip package (substrate, die, finned steel lid) on the board."""
    g = empty("dsp", parent)
    part("dsp_substrate", (DSP_X - 18, -7.0, -14.0), (DSP_X + 18, -5.5, 14.0), m["substrate"], g, 0.5)
    part("dsp_die", (DSP_X - 8, -5.5, -7.0), (DSP_X + 8, -4.0, 7.0), m["die"], g, 0.3)
    part("dsp_lid", (DSP_X - 12, -4.0, -11.0), (DSP_X + 12, -1.0, 11.0), m["steel"], g, 1.0)
    for k in range(-4, 5):
        z = 2.2 * k
        part(f"dsp_fin_{k}", (DSP_X - 11, -1.0, z - 0.4), (DSP_X + 11, 3.0, z + 0.4), m["steel"], g, 0.2)
    return g


def trace(m, parent):
    """Electrical trace from the DSP edge to the module cage, routed at z = -9 clear of the laser and PD."""
    return part("trace_elec", (DSP_X + 14.0, -7.0, -9.8), (MOD_X - 26.0, -6.6, -8.2), m["copper"], parent, 0.0)


def laser(m, parent):
    """LASER: a TO-can with a glass window and a chip inside."""
    g = empty("laser", parent)
    tube("laser_can", (LASER_X - 6.0, -4.0, 0.0), (LASER_X + 3.0, -4.0, 0.0), 4.5, m["steel"], g, 24)
    tube("laser_window", (LASER_X + 3.0, -4.0, 0.0), (LASER_X + 4.0, -4.0, 0.0), 3.2, m["glass"], g, 24)
    part("laser_chip", (LASER_X - 4.0, -6.0, -2.0), (LASER_X + 1.0, -3.0, 2.0), m["die"], g, 0.2)
    return g


def fibre(m, parent, core_parent=None):
    """OPTICAL FIBER: cladding and glass as one run, gold ferrules at both ends. The lit core is
    built into `core_parent` if given, so a page can switch it on and off."""
    g = empty("fibre", parent)
    tube("fibre_cladding", (FIBRE_X0, FIBRE_Y, 0.0), (FIBRE_X1, FIBRE_Y, 0.0), 2.6, m["cladding"], g, 24)
    tube("fibre_glass", (FIBRE_X0, FIBRE_Y, 0.0), (FIBRE_X1, FIBRE_Y, 0.0), 2.0, m["glass"], g, 24)
    core = core_parent if core_parent is not None else empty("fibre_core", parent)
    tube("fibre_core_l", (FIBRE_X0, FIBRE_Y, 0.0), (FIBRE_X1, FIBRE_Y, 0.0), 0.7, m["light"], core, 12)
    tube("ferrule_l", (LASER_X + 9, FIBRE_Y, 0.0), (LASER_X + 16, FIBRE_Y, 0.0), 1.6, m["gold"], g, 16)
    tube("ferrule_r", (PD_X - 16.0, FIBRE_Y, 0.0), (PD_X - 9.0, FIBRE_Y, 0.0), 1.6, m["gold"], g, 16)
    return g


def photodiode(m, parent):
    """PHOTODIODE: a TO-can with a window and a chip inside."""
    g = empty("photodiode", parent)
    tube("pd_can", (PD_X - 3.0, -4.0, 0.0), (PD_X + 6.0, -4.0, 0.0), 4.5, m["steel"], g, 24)
    tube("pd_window", (PD_X - 3.0, -4.0, 0.0), (PD_X - 4.0, -4.0, 0.0), 3.2, m["glass"], g, 24)
    part("pd_chip", (PD_X - 1.0, -6.0, -2.0), (PD_X + 4.0, -3.0, 2.0), m["die"], g, 0.2)
    return g


def module(m, parent):
    """TRANSCEIVER: a finned pluggable housing in a cage at the board edge, with a gold card edge."""
    g = empty("module", parent)
    part("module_cage", (MOD_X - 26.0, -7.0, -12.0), (MOD_X + 26.0, 0.0, 12.0), m["cage"], g, 0.4)
    part("module_housing", (MOD_X - 24.0, -6.0, -10.0), (MOD_X + 24.0, 8.0, 10.0), m["dark_steel"], g, 1.0)
    for k in range(-5, 6):
        z = 2.0 * k
        part(f"module_fin_{k}", (MOD_X - 22.0, 8.0, z - 0.45), (MOD_X + 22.0, 13.0, z + 0.45), m["steel"], g, 0.15)
    for k in range(-4, 5):
        x = MOD_X + 3.2 * k
        part(f"module_pin_{k}", (x - 0.8, -7.0, -10.0), (x + 0.8, -6.0, -8.5), m["gold"], g, 0.1)
    return g


def cpo(m, parent):
    """CPO: ASIC and optical engine on one substrate, four fibre ports at the edge, passive connector."""
    g = empty("cpo", parent)
    part("cpo_substrate", (CPO_X - 24.0, -7.0, -15.0), (CPO_X + 24.0, -5.5, 15.0), m["substrate"], g, 0.5)
    part("cpo_asic", (CPO_X - 16.0, -5.5, -10.0), (CPO_X + 4.0, -1.5, 10.0), m["die"], g, 0.8)
    part("cpo_oe", (CPO_X + 8.0, -5.5, -8.0), (CPO_X + 22.0, -2.5, 8.0), m["oe"], g, 0.6)
    for z in (-6.0, -2.0, 2.0, 6.0):
        tube(f"cpo_fibre_{z}", (CPO_X + 22.0, -4.0, z), (CPO_X + 30.0, -4.0, z), 1.0, m["glass"], g, 12)
    part("cpo_connector", (CPO_X + 30.0, -7.0, -9.0), (CPO_X + 36.0, -1.0, 9.0), m["dark_steel"], g, 0.6)
    return g


def link_stations(m, root):
    """The whole link on its board: every station in place, used by the tab overview and the
    overview of any page that shows the whole link."""
    board(m, root)
    trace(m, root)
    dsp(m, root)
    laser(m, root)
    fibre(m, root)
    photodiode(m, root)
    module(m, root)
    cpo(m, root)
    return root

"""TRM_CHIPS_ACT: the Terms-tab overview for the US CHIPS and Science Act.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_chips_act.py

Centre: a cut-open US fab (cleanroom bay with a row of litho/etch tools, sub-fab, exhaust stacks)
under construction. Left: a federal treasury of gold coin stacks that pays grants into the fab in
three milestone tranches. Right: a cost wall comparing a US fab and an Asian fab; the grant and
the 25% tax credit shrink the US bar. Back: a China fab with a capped expansion (red guard rail).

Beats:
  0 law       the 2022 act: ~$39B grants + 25% credit
  1 build     a fab goes up; grants pay at milestones
  2 cost      US fabs cost more; subsidy closes the gap
  3 strings   guardrails cap advanced China expansion
  4 who       recipients: INTC, TSM, Samsung, MU, GFS
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from term_common import D, F, bx, empty, show, mat  # noqa: E402
from power_vrm_detail import frame, run, blink, rise, present  # noqa: E402
import kit_ledger as K  # noqa: E402

SLUG = "TRM_CHIPS_ACT"
BEATS = [
    ("The CHIPS Act pays to build chip fabs in the US",
     "The CHIPS and Science Act of 2022 set aside about $39 billion in direct manufacturing grants, plus a 25% "
     "investment tax credit on fab equipment and buildings. The goal is to bring leading-edge and mature chip "
     "production back onshore after decades of it moving to Taiwan, Korea and China."),
    ("Grants are paid out in milestones, not up front",
     "A company signs a preliminary award, then receives the money in tranches as it hits construction and "
     "production milestones. A fab takes three to five years to build, so a delayed fab also delays its grant cash."),
    ("The subsidy narrows the US cost gap",
     "Building and running a fab in the US costs roughly 30-50% more than in Taiwan, mostly from labor, permits "
     "and construction. The grant plus the tax credit cuts the net cost of a US fab enough to make the project pencil out."),
    ("The money comes with strings",
     "Recipients agree to guardrails: for ten years they cannot materially expand advanced chip capacity in China "
     "or other countries of concern. Some awards also carry conditions on stock buybacks, childcare and profit sharing above plan."),
    ("The big awards went to a handful of chipmakers",
     "Intel, TSMC Arizona, Samsung Texas, Micron Idaho/New York and GlobalFoundries got the largest grants. "
     "For investors it lowers capex net of subsidy and shows up as reduced property cost or grant income. "
     "Related: Intel (INTC), Micron (MU), TSMC (TSM), GlobalFoundries (GFS), Texas Instruments (TXN)."),
]

FX = 40.0  # fab centre x


def mats(m):
    m["floor"] = mat("ca_floor", (0.16, 0.17, 0.19), rough=0.85)
    m["wall"] = mat("ca_wall", (0.78, 0.80, 0.82), rough=0.6)
    m["roof"] = mat("ca_roof", (0.45, 0.48, 0.52), metal=0.4, rough=0.5)
    m["clean"] = mat("ca_clean", (0.92, 0.94, 0.97), rough=0.3)
    m["tool"] = mat("ca_tool", (0.62, 0.66, 0.72), metal=0.6, rough=0.35)
    m["tool_hot"] = mat("ca_tool_hot", (0.30, 0.65, 1.0), emit=(0.30, 0.65, 1.0), strength=3.5)
    m["subfab"] = mat("ca_subfab", (0.30, 0.32, 0.36), metal=0.5, rough=0.5)
    m["bar_us"] = mat("ca_bar_us", (0.25, 0.45, 0.80), rough=0.6)
    m["bar_as"] = mat("ca_bar_as", (0.55, 0.58, 0.62), rough=0.6)
    m["bar_sub"] = mat("ca_bar_sub", (0.85, 0.68, 0.25), metal=0.6, rough=0.3)
    m["red"] = mat("ca_red", (0.80, 0.15, 0.12), rough=0.5)
    m["flag_r"] = mat("ca_flag_r", (0.75, 0.12, 0.15), rough=0.6)
    m["flag_w"] = mat("ca_flag_w", (0.92, 0.92, 0.92), rough=0.6)
    m["flag_b"] = mat("ca_flag_b", (0.12, 0.18, 0.45), rough=0.6)
    m["crane"] = mat("ca_crane", (0.95, 0.70, 0.10), metal=0.3, rough=0.5)
    m["steam"] = mat("ca_steam", (0.90, 0.92, 0.95), rough=0.9, alpha=0.5)


def fab(m, parent, name, cx, cz, s=1.0, cut=True):
    """A fab building centred (cx, cz), s = scale. With cut, the front wall and half the roof are
    open so the cleanroom bay and its tool row show. Returns (group, tool glows)."""
    g = empty(name, parent)
    w, d, h = 70.0 * s, 44.0 * s, 26.0 * s
    x0, x1, z0, z1 = cx - w / 2, cx + w / 2, cz - d / 2, cz + d / 2
    bx(f"{name}_slab", (x0 - 4 * s, 0.0, z0 - 4 * s), (x1 + 4 * s, 1.5 * s, z1 + 4 * s), m["subfab"], g)
    # sub-fab (pumps, abatement) level
    bx(f"{name}_sub", (x0, 1.5 * s, z0), (x1, 8.0 * s, z1), m["subfab"], g)
    for k in range(6):
        px = x0 + (k + 0.5) * w / 6
        bx(f"{name}_pump{k}", (px - 2 * s, 2 * s, z1 - 8 * s), (px + 2 * s, 7 * s, z1 - 4 * s), m["tool"], g)
    # cleanroom floor + back and side walls
    bx(f"{name}_cr", (x0, 8.0 * s, z0), (x1, 9.0 * s, z1), m["clean"], g)
    bx(f"{name}_wb", (x0, 8.0 * s, z0), (x1, h, z0 + 1.5 * s), m["wall"], g)
    bx(f"{name}_wl", (x0, 8.0 * s, z0), (x0 + 1.5 * s, h, z1), m["wall"], g)
    bx(f"{name}_wr", (x1 - 1.5 * s, 8.0 * s, z0), (x1, h, z1), m["wall"], g)
    if cut:
        bx(f"{name}_roof", (x0, h, z0), (x1, h + 2 * s, cz - 4 * s), m["roof"], g)
        bx(f"{name}_wf", (x0, 1.5 * s, z1 - 1.0 * s), (x1, 8.0 * s, z1), m["wall"], g)
    else:
        bx(f"{name}_roof", (x0, h, z0), (x1, h + 2 * s, z1), m["roof"], g)
        bx(f"{name}_wf", (x0, 1.5 * s, z1 - 1.5 * s), (x1, h, z1), m["wall"], g)
    # tool row: litho/etch/dep tools with glowing status windows
    glows = []
    for k in range(5):
        tx = x0 + (k + 0.7) * w / 5.6
        bx(f"{name}_tool{k}", (tx - 4.5 * s, 9.0 * s, cz - 8 * s), (tx + 4.5 * s, 19.0 * s, cz + 6 * s), m["tool"], g)
        glows.append(bx(f"{name}_win{k}", (tx - 2.5 * s, 13.0 * s, cz + 6 * s), (tx + 2.5 * s, 16.0 * s, cz + 6.6 * s),
                        m["tool_hot"], g))
    # overhead wafer track (AMHS)
    bx(f"{name}_amhs", (x0 + 2 * s, 22.0 * s, cz + 9 * s), (x1 - 2 * s, 23.0 * s, cz + 10 * s), m["tool"], g)
    # exhaust stacks
    for k in range(3):
        sx = x0 + 10 * s + k * 8 * s
        bx(f"{name}_stack{k}", (sx - 2 * s, h, z0 + 2 * s), (sx + 2 * s, h + 16 * s, z0 + 6 * s), m["roof"], g)
    return g, glows


def flag(m, parent, name, x, y, z, s=1.0):
    g = empty(name, parent)
    bx(f"{name}_pole", (x - 0.5, 0.0, z - 0.5), (x + 0.5, y, z + 0.5), m["steel"], g)
    for k in range(5):
        mt = m["flag_r"] if k % 2 == 0 else m["flag_w"]
        bx(f"{name}_s{k}", (x + 0.5, y - 2.0 * s * (k + 1), z - 0.2), (x + 14 * s, y - 2.0 * s * k, z + 0.2), mt, g)
    bx(f"{name}_c", (x + 0.5, y - 6.0 * s, z - 0.3), (x + 6.0 * s, y, z + 0.3), m["flag_b"], g)
    return g


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.ldg_materials(m)
    mats(m)
    bx("floor", (-240.0, -4.0, -200.0), (260.0, -2.0, 120.0), m["floor"], root)

    # the US fab, rising in beat 1 (a crane beside it) and running from beat 2
    us, glows = fab(m, root, "us_fab", FX, 0.0, 1.2)
    flag(m, root, "us_flag", FX - 50.0, 50.0, 30.0)
    crane = empty("crane", root)
    bx("crane_mast", (FX + 48.0, 0.0, -6.0), (FX + 52.0, 70.0, -2.0), m["crane"], crane)
    bx("crane_jib", (FX - 10.0, 66.0, -6.0), (FX + 70.0, 70.0, -2.0), m["crane"], crane)
    D.polyline("crane_cable", [(FX + 10.0, 66.0, -4.0), (FX + 10.0, 40.0, -4.0)], 0.4, m["steel"], crane)
    present(crane, [(F(0, 0), F(2, 0))])
    present(us, [(F(0, 0), F(5, 0))])
    for k, gl in enumerate(glows):
        blink(gl, 2, [k % 4, (k + 2) % 8], n=8, on=0.6)
    for b in (3, 4):
        for k, gl in enumerate(glows):
            blink(gl, b, [k, k + 3], n=8, on=0.7)
    rise(root, "stack_heat", (FX - 26.0, 52.0, -20.0), 8, 2.0, m["steam"], [2, 3], h=24.0, spread=(14.0, 3.0))

    fx = empty("fx", root)
    present(fx, [(F(0, 0), F(5, 0))])

    # treasury (left): coin stacks, paying three milestone tranches into the fab
    K.coin_row(m, root, "treasury", -210.0, -10.0, 16.0, [26, 30, 22, 28, 24], r=6.5, h=2.0)
    bx("treasury_plinth", (-222.0, 0.0, -24.0), (-130.0, 2.0, 4.0), m["subfab"], root)
    path = [(-160.0, 30.0, -10.0), (-90.0, 50.0, -10.0), (FX - 45.0, 40.0, 10.0), (FX - 30.0, 20.0, 20.0)]
    show(K.pipe(m, root, "grant_pipe", path[:3], "steel", 1.8), [(F(0, 0), F(5, 0))])
    run(root, "grant0", path, 14, 3.2, m["ldg_gold_b"], [0], 0.2, 0.8, 50)
    for k in range(3):  # milestone tranches in beat 1
        run(root, f"tranche{k}", path, 6, 3.2, m["ldg_gold_b"], [1], 0.05 + 0.3 * k, 0.15 + 0.3 * k, 40)
    # milestone gates on the fab's front: three steps lighting up in turn
    for k in range(3):
        gate = empty(f"mileg{k}", fx)
        bx(f"mile{k}", (FX - 30.0 + 24.0 * k, 0.0, 34.0), (FX - 22.0 + 24.0 * k, 4.0 + 3.0 * k, 40.0),
                  m["ldg_gold_b"], gate)
        present(gate, [(F(1, 0.1 + 0.3 * k), F(2, 0))])

    # cost wall (right): US fab vs Asian fab, the subsidy slice cuts the US bar in beat 2
    RX = 200.0
    K.ledger_bar(m, root, "cost_as", RX + 30.0, 10.0, 18.0, {0: 60.0}, "bar_as")
    K.ledger_bar(m, root, "cost_us", RX - 10.0, 10.0, 18.0, {0: 88.0, 2: 62.0}, "bar_us")
    sub = K.ledger_bar(m, root, "cost_sub", RX - 10.0, 34.0, 18.0, {2: 26.0}, "bar_sub")
    show(sub, [(F(2, 0.1), F(5, 0))])
    K.coin_stack(m, root, "credit", (RX - 40.0, 0.0, 30.0), 14, r=6.0, h=2.0)
    bx("cost_plinth", (RX - 32.0, -1.0, -4.0), (RX + 48.0, 0.0, 46.0), m["subfab"], root)

    # China (back): a fab with a red guardrail; the expansion block is blocked in beat 3
    cn, cglows = fab(m, root, "cn_fab", -40.0, -140.0, 0.8, cut=False)
    present(cn, [(F(0, 0), F(5, 0))])
    ext = empty("cn_expand_g", fx)
    bx("cn_expand", (-12.0, 0.0, -160.0), (30.0, 20.0, -120.0), m["ldg_glass"], ext)
    present(ext, [(F(3, 0), F(5, 0))])
    for k in range(9):
        bx(f"rail{k}", (-16.0 + 6.0 * k, 0.0, -112.0), (-14.0 + 6.0 * k, 14.0, -110.0), m["red"], root)
    bx("rail_top", (-16.0, 12.0, -112.0), (34.0, 14.0, -110.0), m["red"], root)
    xa = empty("cn_x_g", fx)
    bx("cn_x", (-6.0, 22.0, -118.0), (22.0, 26.0, -116.0), m["ldg_red_b"], xa)
    present(xa, [(F(3, 0.1 + 0.2 * k), F(3, 0.22 + 0.2 * k)) for k in range(4)])
    run(root, "cn_try", [(-60.0, 10.0, -100.0), (-20.0, 10.0, -105.0), (-14.0, 10.0, -108.0)], 6, 2.5,
        m["ldg_red_b"], [3], 0.1, 0.8, 30)

    # recipients (beat 4): four more fabs behind the US one, each fed by gold beads
    names = [("INTC", -150.0), ("TSM", -90.0), ("MU", 120.0), ("GFS", 180.0)]
    for k, (nm, x) in enumerate(names):
        g, gl = fab(m, root, f"rec_{nm}", x, -80.0, 0.5, cut=False)
        present(g, [(F(4, 0.05 * k), F(5, 0))])
        run(root, f"rec_feed_{nm}", [(-160.0, 30.0, -10.0), (-100.0, 50.0, -60.0), (x, 30.0, -80.0)], 6, 2.6,
            m["ldg_gold_b"], [4], 0.1 + 0.05 * k, 0.8, 40)

    C.tags(root, {
        0: [("~$39B grants + 25% tax credit", (-170.0, 64.0, -10.0)), ("US fab", (FX, 46.0, 0.0)),
            ("CHIPS and Science Act, 2022", (-80.0, 70.0, -10.0))],
        1: [("tranches paid at milestones", (FX - 6.0, 18.0, 40.0)), ("fab build: 3-5 years", (FX + 50.0, 76.0, -4.0)),
            ("treasury", (-180.0, 60.0, -10.0))],
        2: [("net US cost after subsidy", (RX - 10.0, 66.0, 10.0)), ("Asia fab cost", (RX + 30.0, 68.0, 10.0)),
            ("grant + credit: ~26 off", (RX - 10.0, 30.0, 34.0))],
        3: [("no big China expansion, 10 yrs", (0.0, 34.0, -118.0)), ("guardrail", (10.0, 16.0, -110.0))],
        4: [("INTC", (-150.0, 26.0, -80.0)), ("TSM Arizona", (-90.0, 26.0, -80.0)), ("MU", (120.0, 26.0, -80.0)),
            ("GFS", (180.0, 26.0, -80.0))],
    })
    C.done(SLUG, BEATS, [
        frame((-60.0, 30.0, -10.0), 330.0, 0.25, 0.40, pad=1.0),
        frame((FX - 20.0, 25.0, 15.0), 190.0, 0.30, 0.35),
        frame((RX + 5.0, 40.0, 20.0), 130.0, -0.30, 0.25),
        frame((-10.0, 15.0, -135.0), 140.0, -0.15, 0.75),
        frame((40.0, 20.0, -50.0), 420.0, 0.05, 0.40, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()

"""TRM_SPINE_LEAF: the Terms-tab overview for spine-leaf networks, at the POWER pages' detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_spine_leaf.py

Writes assets/term_TRM_SPINE_LEAF.glb and specs/terms/TRM_SPINE_LEAF.json.

A row of eight GPU racks, each topped by its leaf switch; four spine switches in a spine rack
behind; yellow fibre from every leaf to every spine. A third tier (super-spines) appears last.

Beats:
  0 layout   every rack has a leaf, every leaf wires to every spine
  1 leaf     servers cable to the leaf at the top of their own rack
  2 hops     server to server across the row: leaf, spine, leaf, always three hops
  3 ECMP     traffic spreads over all four spines at once; losing one costs a quarter
  4 tiers    a third tier joins pods; switch and optic counts climb with every tier
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
import net_leaf_detail as NL  # noqa: E402
from sand_overview import F, show, empty  # noqa: E402
from power_vrm_detail import bx, wire, run, blink, present, frame, arc  # noqa: E402

SLUG = "TRM_SPINE_LEAF"
BEATS = [
    ("Spine-leaf: every rack gets a leaf, every leaf wires to every spine",
     "Spine-leaf is the standard layout of a data-center network. Each rack has a leaf (top-of-rack) switch, and each "
     "leaf has one uplink to every spine switch. There are no leaf-to-leaf or spine-to-spine links. The full mesh "
     "between the two tiers is what makes the network predictable."),
    ("The leaf collects the servers in its rack",
     "Every GPU server cables up to the leaf above it, short runs that can use cheap copper. Half the leaf's ports face "
     "down to servers and half face up to spines, so the leaf can carry all its servers' traffic upward without a bottleneck."),
    ("Any server to any other: leaf, spine, leaf",
     "A packet from a server in the first rack to one in the last climbs to its leaf, crosses one spine, and drops to the "
     "far leaf. Every pair of servers is the same three switch hops apart, so latency and bandwidth are the same wherever "
     "a job's GPUs land."),
    ("Traffic spreads across every spine at once",
     "Because each leaf has a path through every spine, flows are hashed across all of them (ECMP). Adding spines adds "
     "bandwidth, and losing one spine only removes a quarter of the capacity here instead of cutting racks off."),
    ("Bigger clusters add a tier, and every tier adds switches and optics",
     "One leaf-spine pair of tiers tops out at a few thousand GPUs; bigger AI clusters add a super-spine tier on top. "
     "Each tier multiplies the switches and the optical links between them, which is why GPU counts drive optics and "
     "switch demand. Related: Arista (ANET), Cisco (CSCO), Broadcom (AVGO), Nvidia (NVDA), Coherent (COHR)."),
]

XS = [-224.0 + 64.0 * i for i in range(8)]
SPZ = -200.0
SPX = [-72.0, -24.0, 24.0, 72.0]
SPY = 280.0
SUPY = 400.0


def build():
    m, root = C.setup(SLUG, len(BEATS))
    m.update(NL.materials())
    bx("floor", (-280.0, -2.0, -330.0), (280.0, 0.0, 80.0), m["tile"], empty("fl", root))
    leaves, srv = [], []
    for r, xc in enumerate(XS):
        g = empty(f"r{r}", root)
        NL.frame_rack(m, g, xc, 0.0, f"rk{r}")
        ports = []
        for t, y in enumerate(NL.TRAY_Y):
            ports += NL.server(m, g, xc, y, 0.0, 1, f"s{r}_{t}")
        lf = NL.switch(m, g, (xc, NL.LEAF_Y, 0.5), 1.0, detail=False, name=f"lf{r}")
        for i, p in enumerate(ports):
            q = lf["down"][4 + 3 * i]
            zc = 2.0 + 0.4 * i
            x = xc + 24.0 - 0.6 * i
            wire(f"d{r}_{i}", [p, (p[0], p[1], zc), (x, p[1], zc), (x, q[1] - 3.0, zc), (q[0], q[1] - 3.0, zc), q], 0.32,
                 m["dac"], g, 6)
        for gi, lg in enumerate(lf["leds"]):
            blink(lg, 1, [gi, gi + 4], n=8, on=0.6)
        leaves.append(lf)
        srv.append(ports)
    # spine rack
    sg = empty("spines", root)
    bx("sprk", (-100.0, 0.0, SPZ - 60.0), (100.0, 4.0, SPZ + 2.0), m["rack"], sg)
    for x in (-98.0, 98.0):
        bx(f"post{x}", (x - 2.0, 0.0, SPZ - 2.0), (x + 2.0, SPY + 30.0, SPZ + 2.0), m["rack"], sg)
    bx("sptop", (-100.0, SPY + 28.0, SPZ - 60.0), (100.0, SPY + 32.0, SPZ + 2.0), m["rack"], sg)
    spines = [NL.switch(m, sg, (x, SPY, SPZ), 0.8, detail=False, name=f"sp{j}") for j, x in enumerate(SPX)]
    for j, sp in enumerate(spines):
        for gi, lg in enumerate(sp["leds"]):
            blink(lg, 3, [gi, gi + 4], n=8, on=0.6)
    # fibre: every leaf to every spine
    fg = empty("fibre", root)
    routes = {}
    for r, lf in enumerate(leaves):
        for j, sp in enumerate(spines):
            a = lf["up"][6 + 6 * j]
            b = sp["down"][2 + 4 * r]
            pts = arc((a[0], a[1] + 4.0, a[2] + 1.0), (b[0], b[1] - 2.0, b[2] + 3.0), 25.0 + 4.0 * j, n=12)
            pts = [a] + pts + [b]
            routes[(r, j)] = pts
            wire(f"f{r}{j}", pts, 0.35, m["smf"], fg, 6)

    def down(r, i):
        p, q = srv[r][i], leaves[r]["down"][4 + 3 * i]
        x = XS[r] + 22.0
        return [p, (p[0], p[1], 3.0), (x, p[1], 3.0), (x, q[1] - 3.0, 3.0), q]

    # beat 0: a pulse on every fibre
    for (r, j), pts in routes.items():
        run(root, f"m{r}{j}", pts, 1, 0.9, m["up"], 0, 0.05 + 0.1 * j, 0.9, 40)
    # beat 1: servers to leaves
    for r in (2, 3, 4, 5):
        for i in (0, 2, 5, 7):
            run(root, f"s{r}{i}", down(r, i), 2, 0.9, m["pkt"], 1, 0.05 + 0.05 * i, 0.8, 40)
    # beat 2: rack 0 -> leaf0 -> spine 1 -> leaf7 -> rack 7
    hop = down(0, 2) + routes[(0, 1)] + list(reversed(routes[(7, 1)])) + list(reversed(down(7, 5)))
    run(root, "hop", hop, 5, 1.5, m["spine"], 2, 0.0, 0.35, 110)
    # beat 3: ECMP from leaf 1 across all four spines to leaf 6
    for j in range(4):
        path = routes[(1, j)] + list(reversed(routes[(6, j)]))
        run(root, f"ecmp{j}", path, 4, 1.1, m["pkt"], 3, 0.0 + 0.04 * j, 0.6, 70)
    # beat 4: super-spine tier
    sup = empty("super", root)
    sups = [NL.switch(m, sup, (x, SUPY, SPZ - 40.0), 0.8, detail=False, name=f"ss{k}") for k, x in enumerate((-48.0, 48.0))]
    for j, sp in enumerate(spines):
        for k, ss in enumerate(sups):
            a = sp["up"][10 + 10 * k]
            b = ss["down"][6 + 6 * j]
            wire(f"sf{j}{k}", [a, (a[0], a[1] + 30.0, a[2] + 2.0), (b[0], b[1] - 30.0, b[2] + 2.0), b], 0.4, m["aoc"], sup, 6)
            run(sup, f"sb{j}{k}", [a, (a[0], a[1] + 30.0, a[2] + 2.0), (b[0], b[1] - 30.0, b[2] + 2.0), b], 2, 1.1,
                m["up"], 4, 0.1 + 0.1 * j, 0.8, 40)
    # ghost pods beside: more leaf-spine blocks
    for k, x in enumerate((-420.0, 420.0)):
        bx(f"pod{k}", (x - 120.0, 0.0, -60.0), (x + 120.0, 220.0, 0.0), m["rackside"], sup)
        wire(f"podf{k}", [(x, 222.0, -30.0), (x * 0.5, SUPY + 30.0, SPZ - 30.0), (x * 0.12, SUPY + 8.0, SPZ - 40.0)], 0.8,
             m["aoc"], sup, 6)
    present(sup, [(F(4, 0.0), F(5, 0))])

    C.tags(root, {
        0: [("leaf on every rack", (XS[1], NL.LEAF_Y + 12.0, 0.0)), ("spine switches", (SPX[3], SPY + 12.0, SPZ)),
            ("every leaf to every spine", routes[(5, 2)][7])],
        1: [("leaf (top of rack)", (XS[3], NL.LEAF_Y + 12.0, 0.0)), ("servers cable up", (XS[3] + 24.0, 120.0, 2.0)),
            ("half ports down, half up", (XS[4], NL.LEAF_Y + 12.0, 0.0))],
        2: [("1: up to leaf", (XS[0], NL.LEAF_Y + 12.0, 0.0)), ("2: across a spine", (SPX[1], SPY + 12.0, SPZ)),
            ("3: down to far leaf", (XS[7], NL.LEAF_Y + 12.0, 0.0))],
        3: [("hashed over all 4 spines", (0.0, SPY + 14.0, SPZ)), ("lose one: -25% only", (SPX[0], SPY + 2.0, SPZ)),
            ("leaf 2", (XS[1], NL.LEAF_Y + 12.0, 0.0))],
        4: [("super-spine tier", (0.0, SUPY + 12.0, SPZ - 40.0)), ("more pods join", (-420.0, 222.0, -30.0)),
            ("more tiers = more optics", (SPX[2], SPY + 30.0, SPZ))],
    })
    C.done(SLUG, BEATS, [
        frame((0.0, 170.0, -100.0), 540.0, 0.25, 0.35, pad=1.0),
        frame((XS[3] + 30.0, 140.0, 0.0), 160.0, 0.30, 0.15),
        [(0.0, frame((0.0, 200.0, -100.0), 520.0, 0.10, 0.25)), (0.5, frame((80.0, 200.0, -100.0), 480.0, -0.10, 0.25))],
        frame((0.0, 240.0, -100.0), 400.0, 0.05, 0.30),
        frame((0.0, 230.0, -150.0), 950.0, 0.10, 0.25, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()

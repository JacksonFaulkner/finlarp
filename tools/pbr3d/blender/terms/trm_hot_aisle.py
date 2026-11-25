"""TRM_HOT_AISLE: the Terms-tab overview for hot/cold aisle containment.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_hot_aisle.py

Writes assets/term_TRM_HOT_AISLE.glb and specs/terms/TRM_HOT_AISLE.json. Units cm; racks come from
trm_rack_density's kit.

A slice of a data hall cut open at its front (z > 0 side faces the camera): a raised floor with its
under-floor plenum, two rows of air-cooled racks back to back round a hot aisle, cold aisles on the
outside with perforated tiles, a CRAH unit at the left end, a ceiling return plenum. The
containment (roof panels, chimney, end doors) appears in beat 1. Two racks at row A's right end
are liquid-cooled AI racks with a CDU for beat 4.

Beats:
  0 mixing     no containment: hot exhaust curls over the racks back into the cold aisle
  1 contain    roof and doors seal the hot aisle
  2 loop       CRAH -> floor -> tiles -> rack fronts -> hot aisle -> ceiling -> CRAH
  3 warmer     supply air can run warmer and fans slower: lower PUE
  4 AI hall    GPUs go liquid; containment still handles network and storage
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, present  # noqa: E402
import trm_rack_density as K  # noqa: E402

SLUG = "TRM_HOT_AISLE"
BEATS = [
    ("Servers breathe front to back, and the hall has to keep the air apart",
     "Air-cooled servers pull cool air in at the front and push hot air out the back. Racks are lined up in rows "
     "with fronts facing fronts (cold aisles) and backs facing backs (hot aisles). Left open, hot exhaust spills "
     "over the tops and round the row ends back into the server intakes, so the cooling plant has to over-chill "
     "everything to make up for it."),
    ("Containment seals one aisle with a roof and doors",
     "Aisle containment closes off either the hot or the cold aisle with roof panels and sliding end doors. Here the "
     "hot aisle is sealed and a chimney ducts it straight into the ceiling return plenum. Blanking panels in empty "
     "rack slots stop air sneaking through the racks themselves."),
    ("One clean loop: cold under the floor, hot through the ceiling",
     "The CRAH (computer room air handler) blows cold air into the raised floor; it rises through perforated tiles "
     "into the cold aisle, through the servers, into the sealed hot aisle, up to the ceiling and back to the CRAH's "
     "coils, which dump the heat into chilled water. No stream mixes with the other."),
    ("Kept apart, the air can run warmer and the fans slower",
     "Without mixing, supply air can be 24-27 C instead of 18 C and the return comes back hotter, which makes the "
     "chillers and economisers far more efficient and lets fans slow down. That trims PUE (total facility power "
     "over IT power) by a tenth or more, a large saving at tens of megawatts."),
    ("In AI halls, liquid takes the GPUs and air handles the rest",
     "An AI rack at 130 kW sends most of its heat to liquid through cold plates and a CDU, but some heat is still "
     "air-side, and network switches, storage and older servers stay air-cooled. So contained aisles remain, beside "
     "liquid loops. Related: Vertiv (VRT), Schneider Electric, nVent (NVT)."),
]

NX = 6  # racks per row
PX = 62.0
ZA, ZB = 105.0, -105.0  # row centres: A faces +z, B faces -z; hot aisle between |z| < 45
CRAH_X = -130.0
CEIL = 330.0
X0, X1 = -30.0 - 10.0, (NX - 1) * PX + 30.0 + 10.0  # contained aisle x span


def build():
    m, root = C.setup(SLUG, len(BEATS))
    K.mats(m)
    # raised floor: slab low, plenum, tiles at y = -6
    bx("slab", (-230, -70, -300), (X1 + 200, -62, 300), m["concrete"], root)
    for x in range(-220, int(X1 + 190), 60):
        for z in (-280, -220, -160, 160, 220, 280, -100, -40, 20, 80):
            K.fb(f"ped{x}_{z}", (x - 1.2, -62, z - 1.2), (x + 1.2, -6, z + 1.2), m["steel"], root)
    K.flush("ped")
    K.floor(m, root, -230, X1 + 200, -300, 300, True, "fl")
    # perforated tiles in the cold aisles
    for x in range(0, int(X1), 60):
        for zc in (190.0, -190.0):
            bx(f"perf{x}_{zc}", (x - 28, -5.9, zc - 28), (x + 28, -5.7, zc + 28), m["grill"], root)
    # ceiling plenum and return grilles over the hot aisle
    bx("ceil", (-230, CEIL, -300), (X1 + 200, CEIL + 6, 300), m["frame2"], root)
    bx("ceil_top", (-230, CEIL + 70, -300), (X1 + 200, CEIL + 76, 300), m["concrete"], root)
    for x in range(0, int(X1), 60):
        bx(f"ret{x}", (x - 25, CEIL - 0.5, -25), (x + 25, CEIL + 0.2, 25), m["grill"], root)
    # CRAH at the left end, ducted into floor and ceiling
    bx("crah", (CRAH_X - 40, -6, -150), (CRAH_X + 40, 230, 150), m["cdu"], root)
    bx("crah_coil", (CRAH_X - 41, 120, -130), (CRAH_X + 41, 220, 130), m["coldp"], root)
    for k in range(4):
        D.tube(f"crah_fan{k}", (CRAH_X + 40, 30, -105 + k * 70), (CRAH_X + 41.5, 30, -105 + k * 70), 26.0, m["grill"], root, 20)
    bx("crah_duct", (CRAH_X - 30, 230, -100), (CRAH_X + 30, CEIL, 100), m["busway"], root)
    for k in range(2):
        D.tube(f"chw{k}", (CRAH_X - 20 + 40 * k, 230, -140), (CRAH_X - 20 + 40 * k, CEIL + 70, -140), 4.0, m["hose_b" if k == 0 else "hose_r"], root, 12)

    # the two rows
    pa, pb = [], []
    for i in range(NX):
        x = i * PX
        if i >= NX - 2:
            _, p, _ = K.rack_ai(m, root, f"a{i}", (x, ZA), 1, cut=False, liquid=True)
        else:
            _, p, _ = K.rack_ent(m, root, f"a{i}", (x, ZA), 1, "srv" if i % 2 else "net")
        pa.append(p)
        _, p, _ = K.rack_ent(m, root, f"b{i}", (x, ZB), -1, "disk" if i % 3 == 0 else "srv")
        pb.append(p)
    cdp = K.cdu(m, root, "cdu", ((NX) * PX, ZA), 1)

    # containment: roof, chimney, end doors (presented from beat 1)
    cont = empty("contain", root)
    bx("roof", (X0, K.RH + 2, -45), (X1, K.RH + 4, 45), m["glass"], cont)
    for z in (-45, 45):
        bx(f"chim{z}", (X0, K.RH + 4, z - 1), (X1, CEIL, z + 1), m["frame2"], cont)
    for xe in (X0, X1):
        if xe == X0:  # the near (x1) end shows only its door frame so the camera sees in
            bx(f"door{xe}", (xe - 1, 0, -45), (xe + 1, K.RH + 4, 45), m["glass"], cont)
        bx(f"doorf{xe}", (xe - 1.5, 0, -46), (xe + 1.5, K.RH + 4, -43), m["frame"], cont)
        bx(f"doorg{xe}", (xe - 1.5, 0, 43), (xe + 1.5, K.RH + 4, 46), m["frame"], cont)
        bx(f"doorm{xe}", (xe - 1.5, 0, -1.5), (xe + 1.5, K.RH + 4, 1.5), m["frame"], cont)
    present(cont, [(F(1, 0.15), F(5, 0))])

    # beat 0: mixing. cold up through tiles, hot out the backs curling over tops into the cold aisle
    for k in range(4):
        x = 20 + k * 90
        run(root, f"m_cold{k}", [(x, -5, 190), (x, 60, 180), (x, 80 + k * 20, K.RD + ZA + 2)], 3, 2.0, m["cold_b"], [0], 0.0, 0.6, 40)
        run(root, f"m_hot{k}", [(x, 90, 0), (x, K.RH + 25, 10), (x, K.RH + 30, 140), (x, 150, 185), (x, 120, ZA + K.RD + 4)], 3, 2.0, m["hot_r"], [0], 0.1, 0.8, 50)
    run(root, "m_end", [(X1 - 20, 100, 0), (X1 + 40, 100, 30), (X1 + 40, 100, 180), (X1 - 30, 100, ZA + K.RD + 4)], 4, 2.0, m["hot_r"], [0], 0.2, 0.9, 50)

    # beat 2-4: the clean loop
    def loop(beats, scale=1.0):
        for k in range(3):
            zc = 190.0 if k != 1 else -190.0
            fl = [(CRAH_X + 42, -30, zc * 0.5), (60 + k * 120, -30, zc), (60 + k * 120, -5, zc), (60 + k * 120, 90, zc)]
            run(root, f"u{k}_{beats[0]}", fl, int(5 * scale), 2.0, m["cold_b"], beats, 0.0, 0.6, 45)
            zf = ZA + K.RD + 2 if zc > 0 else ZB - K.RD - 2
            zr = ZA - K.RD - 2 if zc > 0 else ZB + K.RD + 2
            run(root, f"t{k}_{beats[0]}", [(60 + k * 120, 90, zf), (60 + k * 120, 90, zr), (60 + k * 120, K.RH, 0), (60 + k * 120, CEIL + 30, 0), (CRAH_X, CEIL + 30, 0), (CRAH_X, 200, 0)],
                int(5 * scale), 2.0, m["hot_r"], beats, 0.2, 0.85, 60)
    loop([2, 3])
    loop([4], 0.6)

    # beat 4: liquid loop on the AI racks
    for i in (NX - 2, NX - 1):
        x = i * PX
        path = [cdp["out"], (cdp["out"][0], K.RH + 14, ZA - 40), (x - 20, K.RH + 14, ZA - 40), (x - 20, K.RH + 14, ZA - K.RD + 4), (x - 20, 20, ZA - K.RD + 4)]
        D.polyline(f"ls{i}", path[:4], 2.0, m["hose_b"], root)
        run(root, f"lq{i}", path, 8, 1.6, m["cold_b"], [4], 0.0, 0.7, 50)
        back = [(x + 20, 20, ZA - K.RD + 4), (x + 20, K.RH + 8, ZA - K.RD + 4), (x + 20, K.RH + 8, ZA - 30), (cdp["in"][0], K.RH + 8, ZA - 30), cdp["in"]]
        D.polyline(f"lr{i}", back[1:], 2.0, m["hose_r"], root)
        run(root, f"lh{i}", back, 8, 1.6, m["hot_r"], [4], 0.15, 0.85, 50)
    rise(root, "warm_return", (200, CEIL + 10, 0), 6, 2.0, m["heat"], [2], 0.2, 0.9, 40.0, 50, (150.0, 20.0))

    mid = ((NX - 1) * PX / 2, K.RH + 10, 0.0)
    C.tags(root, {
        0: [("cold aisle", (150, 30, 200)), ("hot exhaust spills over", (150, K.RH + 30, 60)),
            ("recirculates into intakes", (X1 + 40, 100, 150))],
        1: [("hot aisle sealed", mid), ("roof + chimney to ceiling", (150, K.RH + 60, 45)),
            ("sliding end doors", (X1, 140, 30))],
        2: [("CRAH: fans + chilled-water coil", (CRAH_X, 230, 150)), ("raised-floor plenum", (40, -40, 190)),
            ("perforated tiles", (120, -5, 190)), ("ceiling return", (250, CEIL + 30, 0))],
        3: [("supply 18 C -> 24-27 C", (100, 40, 190)), ("hotter return, slower fans", (CRAH_X, 230, 0)),
            ("lower PUE", mid)],
        4: [("AI racks: liquid via CDU", (cdp["top"][0], K.RH + 20, ZA)), ("network + storage stay on air", pb[1]["top"]),
            ("VRT, Schneider, NVT", (CRAH_X, 240, 150))],
    })
    C.done(SLUG, BEATS, [
        frame((200.0, 120.0, 0.0), 600.0, 1.15, 0.15, pad=1.0),
        frame((150.0, 150.0, 0.0), 800.0, 0.85, 0.30, pad=1.0),
        frame((150.0, 130.0, 0.0), 640.0, 1.45, 0.06, pad=1.0),
        frame((120.0, 120.0, 0.0), 600.0, 1.30, 0.20, pad=1.0),
        frame((300.0, 120.0, 40.0), 480.0, 0.70, 0.35, pad=1.0),
    ], root)


if __name__ == "__main__":
    build()

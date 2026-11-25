"""TRM_CONVERTIBLE_NOTES: the Terms-tab overview for convertible notes, at the POWER pages' detail.

    blender -b --factory-startup --python tools/pbr3d/blender/terms/trm_convertible_notes.py

A financing term, so the scene is its own: on the left a bond desk (the note holders' vault), in
the middle the issuer's HQ tower with a giant note certificate standing in front of it (seal,
coupon strip, conversion-price tag), on the right a stock price wall: price line climbing past a
glowing conversion-price line and a higher cap line, and a share stack that grows on conversion.

Beats:
  0 loan      cash flows from note buyers into the company; the note certificate
  1 coupon    small coupon coins drip back: low interest, because of the option
  2 strike    the price line climbs from issue price toward the conversion price
  3 convert   price above strike: the note turns into new shares, stack grows, holders dilute
  4 capped    a capped call cancels dilution between strike and cap
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.dirname(HERE)]
import term_common as C  # noqa: E402
from sand_overview import F, empty, show  # noqa: E402
import power_vrm_detail as D  # noqa: E402
from power_vrm_detail import bx, frame, run, rise, blink, mat  # noqa: E402

SLUG = "TRM_CONVERTIBLE_NOTES"
BEATS = [
    ("A convertible note is a bond that can turn into stock",
     "Investors lend the company cash today and get a note back: a bond with a maturity date, usually five to "
     "seven years out. Unlike a plain bond, the holder may swap it for a fixed number of shares instead of being "
     "repaid. Growth companies with heavy capex use them to raise large sums quickly without selling stock up front."),
    ("The coupon is low because the buyer gets an option",
     "Interest on a convertible is often 0% to 3%, well below what the same company would pay on straight debt. "
     "The difference is the price of the embedded call option on the stock. Cheap interest is why the structure "
     "appeals to cash-hungry issuers, but the bill can come later as dilution."),
    ("The conversion price is set well above today's stock price",
     "At issue the conversion price is typically 25% to 40% above the stock price, called the conversion premium. "
     "Conversion rate = principal divided by conversion price, for example $1,000 / $50 = 20 shares per note. "
     "Below that price the note behaves like debt; above it, it behaves like stock."),
    ("Above the conversion price, notes become new shares",
     "Once the stock trades above the conversion price, holders convert (or the company settles in shares), and new "
     "shares are added to the count. Existing shareholders own a smaller slice of the company. Analysts track "
     "diluted share counts with the if-converted method for exactly this reason."),
    ("A capped call buys back the dilution up to a cap",
     "Many issuers spend part of the proceeds on a capped call: an option that pays out shares or cash between the "
     "conversion price and a higher cap price, often 75% to 100% above issue. Dilution is offset in that band, and "
     "only returns if the stock flies past the cap. Related: Super Micro Computer (SMCI), CoreWeave (CRWV), Nebius "
     "(NBIS), Lumentum (LITE)."),
]

# price wall layout (x across, y up), standing at z = WZ
WX0, WX1, WY0, WY1, WZ = 60.0, 220.0, 0.0, 110.0, -40.0
ISSUE_Y, STRIKE_Y, CAP_Y = 30.0, 52.0, 84.0
HQ = (-40.0, -60.0)  # tower x, z
VAULT = (-190.0, -40.0)
NOTE = (-85.0, 10.0)  # note certificate centre x, z


def mats(m):
    m["ground"] = mat("cv_ground", (0.42, 0.44, 0.46), rough=0.8)
    m["paper"] = mat("cv_paper", (0.93, 0.90, 0.80), rough=0.7)
    m["seal"] = mat("cv_seal", (0.70, 0.12, 0.12), metal=0.3, rough=0.4)
    m["glass"] = mat("cv_glass", (0.30, 0.45, 0.60), metal=0.4, rough=0.15)
    m["concrete"] = mat("cv_concrete", (0.72, 0.72, 0.70), rough=0.8)
    m["wallbk"] = mat("cv_wall", (0.05, 0.06, 0.08), rough=0.5)
    m["axis"] = mat("cv_axis", (0.65, 0.68, 0.72), metal=0.6, rough=0.4)
    m["cash"] = mat("cv_cash", (0.35, 0.95, 0.45), emit=(0.30, 0.90, 0.40), strength=3.0)
    m["coin"] = mat("cv_coin", (1.0, 0.82, 0.30), emit=(1.0, 0.78, 0.25), strength=3.0)
    m["price"] = mat("cv_price", (0.35, 0.80, 1.0), emit=(0.30, 0.75, 1.0), strength=4.0)
    m["strike"] = mat("cv_strike", (1.0, 0.65, 0.20), emit=(1.0, 0.60, 0.15), strength=3.5)
    m["capl"] = mat("cv_cap", (0.80, 0.45, 1.0), emit=(0.75, 0.40, 1.0), strength=3.5)
    m["share_old"] = mat("cv_share_old", (0.25, 0.40, 0.75), metal=0.3, rough=0.4)
    m["share_new"] = mat("cv_share_new", (1.0, 0.55, 0.25), emit=(1.0, 0.50, 0.20), strength=0.6)
    m["band"] = mat("cv_band", (0.60, 0.40, 1.0), emit=(0.55, 0.35, 1.0), strength=0.3)


def tower(m, root):
    x, z = HQ
    g = empty("hq", root)
    bx("hq_core", (x - 22.0, 0.0, z - 22.0), (x + 22.0, 120.0, z + 22.0), m["glass"], g)
    for f in range(15):
        y = 6.0 + f * 7.8
        bx(f"hq_slab{f}", (x - 22.4, y, z - 22.4), (x + 22.4, y + 0.9, z + 22.4), m["concrete"], g)
    for k in range(5):
        xx = x - 22.0 + k * 11.0
        bx(f"hq_mul{k}", (xx - 0.5, 0.0, z + 22.0), (xx + 0.5, 120.0, z + 22.6), m["axis"], g)
    bx("hq_roof", (x - 18.0, 120.0, z - 18.0), (x + 18.0, 126.0, z + 18.0), m["dark"], g)
    bx("hq_door", (x - 6.0, 0.0, z + 22.0), (x + 6.0, 10.0, z + 23.0), m["dark"], g)
    lights = empty("hq_lights", root)
    for f in range(0, 15, 2):
        for k in range(4):
            xx = x - 19.0 + k * 11.0
            bx(f"hq_w{f}{k}", (xx, 8.0 + f * 7.8, z + 22.7), (xx + 5.0, 12.0 + f * 7.8, z + 23.0), m["coin"], lights)
    show(lights, [(F(0, 0.4), F(1, 0))])
    return (x, 60.0, z + 22.0)


def vault(m, root):
    x, z = VAULT
    g = empty("vault", root)
    bx("v_body", (x - 30.0, 0.0, z - 25.0), (x + 30.0, 45.0, z + 25.0), m["concrete"], g)
    bx("v_roof", (x - 33.0, 45.0, z - 28.0), (x + 33.0, 50.0, z + 28.0), m["concrete"], g)
    for k in range(5):
        D.tube(f"v_col{k}", (x - 24.0 + k * 12.0, 0.0, z + 27.0), (x - 24.0 + k * 12.0, 44.0, z + 27.0), 1.8, m["paper"], g, 12)
    D.tube("v_door", (x, 18.0, z + 25.0), (x, 18.0, z + 27.0), 11.0, m["steel"], g, 32)
    for k in range(6):  # door spokes
        import math
        a = k * math.pi / 3
        D.tube(f"v_spoke{k}", (x, 18.0, z + 27.2), (x + 8.0 * math.cos(a), 18.0 + 8.0 * math.sin(a), z + 27.2), 0.5, m["alu"], g, 6)
    return (x, 30.0, z + 28.0)


def note(m, root):
    """The giant note certificate standing upright in front of the tower."""
    x, z = NOTE
    g = empty("note", root)
    w, h = 54.0, 36.0
    y0 = 14.0
    bx("note_stand", (x - 4.0, 0.0, z - 3.0), (x + 4.0, y0, z), m["dark"], g)
    bx("note_base", (x - 14.0, 0.0, z - 6.0), (x + 14.0, 1.5, z + 3.0), m["dark"], g)
    bx("note_sheet", (x - w / 2, y0, z - 1.2), (x + w / 2, y0 + h, z), m["paper"], g)
    bx("note_border", (x - w / 2 + 2.0, y0 + 2.0, z), (x + w / 2 - 2.0, y0 + 2.6, z + 0.2), m["gold"], g)
    bx("note_border2", (x - w / 2 + 2.0, y0 + h - 2.6, z), (x + w / 2 - 2.0, y0 + h - 2.0, z + 0.2), m["gold"], g)
    for s in (-1, 1):
        bx(f"note_bs{s}", (x + s * (w / 2 - 2.6), y0 + 2.0, z), (x + s * (w / 2 - 2.0), y0 + h - 2.0, z + 0.2), m["gold"], g)
    for k in range(5):  # text lines
        bx(f"note_txt{k}", (x - 20.0, y0 + 20.0 + k * 2.6, z), (x + 6.0 - (k % 2) * 6.0, y0 + 21.0 + k * 2.6, z + 0.2), m["ink"], g)
    D.tube("note_seal", (x + 16.0, y0 + 10.0, z), (x + 16.0, y0 + 10.0, z + 0.8), 5.0, m["seal"], g, 24)
    # coupon strip along the bottom: perforated coupons
    coupons = []
    for k in range(7):
        cx = x - 22.0 + k * 6.2
        c = bx(f"note_cp{k}", (cx, y0 + 4.0, z), (cx + 5.2, y0 + 9.0, z + 0.3), m["paper"], g)
        bx(f"note_cpi{k}", (cx + 1.0, y0 + 6.0, z + 0.3), (cx + 4.2, y0 + 7.0, z + 0.4), m["ink"], g)
        coupons.append((cx + 2.6, y0 + 6.5, z + 0.5))
    # conversion price tag hanging from the corner
    tag = empty("note_tag", root)
    D.polyline("tag_string", [(x + w / 2 - 3.0, y0 + h - 3.0, z + 0.3), (x + w / 2 + 6.0, y0 + h - 12.0, z + 2.0)], 0.2, m["ink"], tag)
    bx("tag_card", (x + w / 2 + 2.0, y0 + h - 22.0, z + 1.6), (x + w / 2 + 12.0, y0 + h - 12.0, z + 2.2), m["strike"], tag)
    show(tag, [(F(2, 0.0), F(5, 0))])
    return {"sheet": (x, y0 + h - 4.0, z), "coupons": coupons, "seal": (x + 16.0, y0 + 10.0, z + 1.0),
            "tag": (x + w / 2 + 7.0, y0 + h - 17.0, z + 2.2), "c": (x, y0 + h / 2, z)}


def wall(m, root):
    """The stock price wall: axes, issue/strike/cap lines, a price line revealed piece by piece."""
    g = empty("wall", root)
    bx("wall_bk", (WX0 - 6.0, WY0, WZ - 3.0), (WX1 + 6.0, WY1 + 6.0, WZ), m["wallbk"], g)
    bx("wall_ax_y", (WX0, WY0 + 4.0, WZ), (WX0 + 1.0, WY1, WZ + 0.6), m["axis"], g)
    bx("wall_ax_x", (WX0, WY0 + 4.0, WZ), (WX1, WY0 + 5.0, WZ + 0.6), m["axis"], g)
    for k in range(1, 9):
        xx = WX0 + k * (WX1 - WX0) / 9
        bx(f"wall_tx{k}", (xx - 0.3, WY0 + 2.0, WZ), (xx + 0.3, WY0 + 5.0, WZ + 0.6), m["axis"], g)
        bx(f"wall_grid{k}", (xx - 0.15, WY0 + 5.0, WZ), (xx + 0.15, WY1, WZ + 0.2), m["grid"], g)
    bx("issue_line", (WX0, ISSUE_Y - 0.3, WZ), (WX1, ISSUE_Y + 0.3, WZ + 0.5), m["axis"], g)
    strike = empty("strike", root)
    bx("strike_line", (WX0, STRIKE_Y - 0.6, WZ), (WX1, STRIKE_Y + 0.6, WZ + 0.8), m["strike"], strike)
    show(strike, [(F(2, 0.0), F(5, 0))])
    cap = empty("cap", root)
    bx("cap_line", (WX0, CAP_Y - 0.6, WZ), (WX1, CAP_Y + 0.6, WZ + 0.8), m["capl"], cap)
    bx("cap_band", (WX0, STRIKE_Y + 0.6, WZ + 0.1), (WX1, CAP_Y - 0.6, WZ + 0.3), m["band"], cap)
    show(cap, [(F(4, 0.15), F(5, 0))])
    # the price path: quarters of noise climbing from issue to above cap
    ys = [30, 28, 33, 31, 36, 34, 40, 38, 45, 49, 47, 55, 60, 58, 66, 72, 70, 79, 88, 92]
    n = len(ys)
    pts = [(WX0 + 4.0 + (WX1 - WX0 - 8.0) * i / (n - 1), float(y), WZ + 1.2) for i, y in enumerate(ys)]
    # reveal schedule: up to index 4 in beat 0, 10 by the end of beat 2, 13 in beat 3, all in beat 4
    for i in range(n - 1):
        seg = empty(f"px_seg{i}", root)
        D.polyline(f"px{i}", [pts[i], pts[i + 1]], 0.7, m["price"], seg)
        if i < 4:
            f0 = F(0, 0.2 + 0.15 * i)
        elif i < 10:
            f0 = F(2, 0.1 + 0.13 * (i - 4))
        elif i < 13:
            f0 = F(3, 0.05 + 0.15 * (i - 10))
        else:
            f0 = F(4, 0.25 + 0.1 * (i - 13))
        show(seg, [(f0, F(5, 0))])
    # a "now" marker that rides with the reveal
    return {"pts": pts, "strike": (WX0 + 20.0, STRIKE_Y, WZ + 1.0), "cap": (WX0 + 20.0, CAP_Y, WZ + 1.0),
            "issue": (WX1 - 30.0, ISSUE_Y, WZ + 1.0), "c": ((WX0 + WX1) / 2, WY1 / 2, WZ)}


def shares(m, root):
    """Share-count stack beside the wall: old shares always, new conversion shares added in beat 3,
    plus an ownership bar (old holders' share) that shrinks."""
    g = empty("shares", root)
    sx, sz = 255.0, -20.0
    bx("sh_plinth", (sx - 14.0, 0.0, sz - 12.0), (sx + 14.0, 3.0, sz + 12.0), m["dark"], g)
    for k in range(10):
        y = 3.0 + k * 5.0
        bx(f"sh_old{k}", (sx - 10.0, y, sz - 8.0), (sx + 10.0, y + 4.4, sz + 8.0), m["share_old"], g)
    new = []
    for k in range(4):
        e = empty(f"sh_new{k}", root)
        y = 53.0 + k * 5.0
        bx(f"sh_newb{k}", (sx - 10.0, y, sz - 8.0), (sx + 10.0, y + 4.4, sz + 8.0), m["share_new"], e)
        show(e, [(F(3, 0.35 + 0.12 * k), F(4, 0.3) if k >= 2 else F(5, 0))])
        new.append(e)
    # capped call hands two blocks back: they fly off (shown as cancelled frames) in beat 4
    for k in range(2):
        e = empty(f"sh_back{k}", root)
        y = 63.0 + k * 5.0
        for s in (-1, 1):
            bx(f"sh_backf{k}{s}", (sx - 10.0, y + (2.0 if s > 0 else 0.0), sz + 8.2), (sx + 10.0, y + (2.4 if s > 0 else 0.4), sz + 8.6), m["capl"], e)
        bx(f"sh_backs{k}", (sx - 10.0, y, sz + 8.2), (sx - 9.6, y + 2.4, sz + 8.6), m["capl"], e)
        bx(f"sh_backt{k}", (sx + 9.6, y, sz + 8.2), (sx + 10.0, y + 2.4, sz + 8.6), m["capl"], e)
        show(e, [(F(4, 0.3), F(5, 0))])
    # ownership bar: old holders' share of the company
    ox = sx + 26.0
    full = empty("own_full", root)
    bx("own_full_b", (ox - 3.0, 3.0, sz - 3.0), (ox + 3.0, 53.0, sz + 3.0), m["share_old"], full)
    show(full, [(0, F(3, 0.6))])
    thin = empty("own_thin", root)
    bx("own_thin_b", (ox - 3.0, 3.0, sz - 3.0), (ox + 3.0, 39.0, sz + 3.0), m["share_old"], thin)
    bx("own_thin_n", (ox - 3.0, 39.0, sz - 3.0), (ox + 3.0, 53.0, sz + 3.0), m["share_new"], thin)
    show(thin, [(F(3, 0.6), F(4, 0.35))])
    mid = empty("own_mid", root)
    bx("own_mid_b", (ox - 3.0, 3.0, sz - 3.0), (ox + 3.0, 46.0, sz + 3.0), m["share_old"], mid)
    bx("own_mid_n", (ox - 3.0, 46.0, sz - 3.0), (ox + 3.0, 53.0, sz + 3.0), m["share_new"], mid)
    show(mid, [(F(4, 0.35), F(5, 0))])
    return {"old": (sx, 30.0, sz + 8.0), "new": (sx, 60.0, sz + 8.0), "own": (ox, 45.0, sz + 3.0),
            "back": (sx, 66.0, sz + 8.6), "c": (sx + 10.0, 35.0, sz)}


def build():
    m, root = C.setup(SLUG, len(BEATS))
    mats(m)
    bx("ground", (-240.0, -2.0, -110.0), (300.0, 0.0, 50.0), m["ground"], root)
    hq = tower(m, root)
    vp = vault(m, root)
    nt = note(m, root)
    wp = wall(m, root)
    sh = shares(m, root)

    # beat 0: cash from the vault (note buyers) to the HQ; the note goes back the other way
    for k in range(3):
        run(root, f"cash{k}", [(vp[0] + 30.0, 10.0 + 6.0 * k, VAULT[1] + 10.0), (HQ[0] - 24.0, 10.0 + 6.0 * k, HQ[1] + 30.0)],
            8, 1.6, m["cash"], 0, 0.05 + 0.1 * k, 0.7 + 0.1 * k, 45)
    run(root, "note_out", [(HQ[0] - 24.0, 3.0, HQ[1] + 36.0), (vp[0] + 30.0, 3.0, VAULT[1] + 20.0)], 3, 2.2, m["paper"], 0, 0.3, 0.8, 50)
    # beat 1: coupon coins drip from HQ to the vault, a few per year; also visible later
    for k in range(2):
        run(root, f"coupon{k}", [(HQ[0] - 22.0, 40.0 + 4.0 * k, HQ[1] + 10.0), (-120.0, 52.0 + 4.0 * k, -30.0), (vp[0] + 10.0, 50.0, VAULT[1])],
            5, 1.4, m["coin"], [1, 2], 0.05 + 0.1 * k, 0.85, 50)
    # the coupons on the certificate blink as each is "clipped"
    clip = empty("clip", root)
    for k, p in enumerate(nt["coupons"]):
        bx(f"clip{k}", (p[0] - 2.4, p[1] - 2.3, p[2]), (p[0] + 2.4, p[1] + 2.3, p[2] + 0.2), m["coin"], clip)
    blink(clip, 1, [0, 2, 4, 6], n=8, on=0.5)

    # beat 3: the note certificate's "shares" flow to the share stack; price burst above strike
    for k in range(3):
        run(root, f"conv{k}", [(nt["c"][0] + 20.0, 30.0 + 4.0 * k, NOTE[1] + 2.0), (40.0, 70.0, 10.0), (sh["new"][0], 58.0 + 3.0 * k, sh["new"][2])],
            6, 1.8, m["share_new"], 3, 0.1 + 0.08 * k, 0.75, 55)
    rise(root, "breakout", (wp["pts"][12][0], STRIKE_Y + 4.0, WZ + 2.0), 8, 1.0, m["price"], 3, 0.2, 0.8, 22.0, 35, (8.0, 0.5))
    # beat 4: capped call: HQ pays a premium to a dealer, shares come back
    run(root, "premium", [(HQ[0] + 24.0, 20.0, HQ[1] + 30.0), (sh["c"][0] - 30.0, 20.0, 10.0)], 5, 1.4, m["coin"], 4, 0.0, 0.4, 45)
    run(root, "hedge", [(sh["back"][0] - 14.0, 66.0, sh["back"][2] + 4.0), (120.0, 90.0, 20.0), (HQ[0] + 24.0, 90.0, HQ[1] + 30.0)],
        4, 1.6, m["capl"], 4, 0.4, 0.85, 50)

    C.magnify(m, root, (HQ[0], 1.0, HQ[1] + 30.0), (nt["c"][0], 30.0, NOTE[1]), r=3.0, name="mag")

    pts = wp["pts"]
    tags = {
        0: [("buyers lend cash", (vp[0] + 50.0, 28.0, VAULT[1] + 10.0)), ("note: bond, 5-7 yr maturity", nt["sheet"]),
            ("issuer gets the cash", hq), ("price at issue", wp["issue"])],
        1: [("coupon 0%-3%", nt["coupons"][3]), ("coupons paid to holders", (-120.0, 56.0, -30.0)),
            ("cheap vs straight debt", hq)],
        2: [("conversion price", wp["strike"]), ("25-40% premium at issue", (pts[6][0], 42.0, WZ + 1.0)),
            ("$1,000 / $50 = 20 shares", nt["tag"]), ("stock climbing", pts[9])],
        3: [("above strike: converts", pts[12]), ("new shares issued", sh["new"]),
            ("old holders' slice shrinks", sh["own"]), ("if-converted share count", sh["old"])],
        4: [("cap price", wp["cap"]), ("hedged band: no dilution", (pts[15][0], 68.0, WZ + 1.0)),
            ("capped call returns shares", sh["back"]), ("SMCI, CRWV, NBIS, LITE", (pts[18][0], 100.0, WZ + 1.0))],
    }
    C.tags(root, tags)
    C.done(SLUG, BEATS, [
        frame((-90.0, 40.0, -30.0), 250.0, 0.15, 0.30, pad=1.0),
        [(0.0, frame((-90.0, 35.0, -10.0), 150.0, -0.10, 0.25)), (0.6, frame((-110.0, 35.0, -20.0), 170.0, 0.15, 0.25))],
        frame((140.0, 55.0, WZ), 190.0, -0.15, 0.15),
        [(0.0, frame((120.0, 50.0, -20.0), 300.0, 0.10, 0.25, pad=1.0)), (0.6, frame((190.0, 50.0, -20.0), 200.0, -0.20, 0.20))],
        frame((160.0, 55.0, -25.0), 230.0, -0.10, 0.18),
    ], root)


if __name__ == "__main__":
    build()

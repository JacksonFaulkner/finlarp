"""Beat builders and computed callouts for custom stories. Callout text is always derived from the
numbers in the beat (shares, multiples, changes), so a tag never says more than the data does."""
from __future__ import annotations


def scene(name: str, beats: list) -> dict | None:
    """A scene of the beats that have data (a missing history or short series drops its beat)."""
    beats = [b for b in beats if b]
    # one colour per series name across the scene, so a segment keeps its colour beat to beat
    reg: dict[str, int] = {}
    for b in beats:
        if b["panel"] == "towers":
            b["colors"] = [reg.setdefault(n, len(reg)) for n, _ in b["series"]]
    return {"name": name, "beats": beats} if beats else None


def bars(title: str, unit: str, points: list[list], tags: list[dict] | None = None) -> dict | None:
    if len(points) < 3:
        return None
    b = {"panel": "bars", "title": title, "unit": unit, "points": points}
    if tags:
        b["tags"] = tags
    return b


def shaped(hist: dict | None, rename: dict | None = None, top: int = 6) -> dict | None:
    """`hist` with display names (`rename`: prefix -> name) and at most `top` series: the rest
    (smallest by the latest period) fold into "Other". Call before computing tags."""
    if not hist:
        return None
    n = len(hist["periods"])
    merged: dict[str, list] = {}  # series that end up with one display name are summed (e.g. two "Other"s)
    for name, vs in hist["series"]:
        name = next((v for k, v in (rename or {}).items() if name.startswith(k)), name)
        acc = merged.setdefault(name, [0.0] * n)
        merged[name] = [round(a + (b or 0), 1) for a, b in zip(acc, vs)]
    ser = [[k, v] for k, v in merged.items()]
    if len(ser) > top:
        ser.sort(key=lambda s: -s[1][-1])
        keep = [s for s in ser if s[0] != "Other"][:top - 1]
        rest = [s for s in ser if s not in keep]
        ser = keep + [["Other", [round(sum(s[1][i] for s in rest), 1) for i in range(n)]]]
    return {**hist, "series": ser}


def towers(title: str, hist: dict, pct: bool = False, tags: list[dict] | None = None) -> dict:
    tags = [fit(t) for t in (tags or []) if t]
    b = {"panel": "towers", "title": title, "unit": hist.get("unit", "$M"), "periods": hist["periods"], "series": hist["series"],
         "srcs": hist.get("srcs", [])}
    if pct:
        b["pct"] = True
    if tags:
        b["tags"], b["auto_tags"] = tags, False
    return b


def _find(hist: dict, prefix: str) -> int | None:
    return next((k for k, (n, _) in enumerate(hist["series"]) if n.startswith(prefix)), None)


def _money(v: float, unit: str = "$M") -> str:
    if v < 0:
        return "-" + _money(-v, unit)
    cur = unit[:-1].strip()
    cur = cur if cur.endswith("$") else cur + " "
    if abs(v) >= 1e6:
        return f"{cur}{v / 1e6:.2f}T"
    return f"{cur}{v / 1e3:.1f}B" if abs(v) >= 1e3 else f"{cur}{v:,.0f}M"


def share(hist: dict, prefix: str, u: float = 0.7) -> dict | None:
    """'<name> = n% of <total>' for the latest period (e.g. AWS's share of operating income)."""
    k = _find(hist, prefix)
    if k is None:
        return None
    tot = sum(max(0.0, vs[-1]) for _, vs in hist["series"]) or 1
    name, vs = hist["series"][k]
    cu = hist.get("unit", "$M")
    return {"i": -1, "s": k, "u": u, "text": f"{name} {_money(vs[-1], cu)}, {vs[-1] / tot * 100:.0f}% of the total"}


def growth(hist: dict, prefix: str, u: float = 0.7) -> dict | None:
    """'<name> $a -> $b (k.kx)' pinned on the latest tower."""
    k = _find(hist, prefix)
    if k is None:
        return None
    name, vs = hist["series"][k]
    a, b = vs[0], vs[-1]
    mult = "" if a <= 0 else (f" ({b / a:.1f}x)" if b / a >= 2 else f" ({(b / a - 1) * 100:+.0f}%)")
    cu = hist.get("unit", "$M")
    return {"i": -1, "s": k, "text": f"{name} {_money(a, cu)} -> {_money(b, cu)}{mult}", "u": u}


def seg_tags(hist: dict, prefixes: list[str]) -> list[dict]:
    return [t for j, p in enumerate(prefixes) if (t := growth(hist, p, u=0.55 + 0.15 * j))]


def pct_tags(hist: dict, prefixes: list[str]) -> list[dict]:
    """'<name> a% -> b% of revenue' pinned on the latest tower of a share (pct) beat."""
    out = []
    tot = [sum(vs[i] for _, vs in hist["series"]) or 1 for i in range(len(hist["periods"]))]
    for j, p in enumerate(prefixes):
        k = _find(hist, p)
        if k is None:
            continue
        name, vs = hist["series"][k]
        a, b = vs[0] / tot[0] * 100, vs[-1] / tot[-1] * 100
        out.append({"i": -1, "s": k, "u": 0.55 + 0.15 * j,
                    "text": f"{name} {a:.0f}% -> {b:.0f}% ({hist['periods'][0]} -> {hist['periods'][-1]})"})
    return out


def series_bars(title: str, hist: dict | None, prefix: str, tags: list[dict] | None = None) -> dict | None:
    """One series of a history as bars (e.g. a segment's operating loss, which towers cannot show)."""
    k = _find(hist, prefix) if hist else None
    if k is None:
        return None
    pts = [[p, v] for p, v in zip(hist["periods"], hist["series"][k][1])]
    b = {"panel": "bars", "title": title, "unit": hist.get("unit", "$M"), "points": pts}
    if tags:
        b["tags"] = tags
    return b


def of_total(hist: dict, prefix: str, total: float, what: str, u: float = 0.7) -> dict | None:
    """'<name> <money>, n% of <what>' against an outside total (e.g. one customer vs revenue)."""
    k = _find(hist, prefix)
    if k is None or not total:
        return None
    name, vs = hist["series"][k]
    return {"i": -1, "s": k, "u": u,
            "text": f"{name} {_money(vs[-1], hist.get('unit', '$M'))}, {vs[-1] / total * 100:.0f}% of {what}"}


def total_of(hist: dict, i: int = -1) -> float:
    return sum(vs[i] for _, vs in hist["series"])


def without(hist: dict | None, *prefixes: str) -> dict | None:
    """`hist` minus the series whose names start with any of `prefixes` (e.g. a contra line)."""
    if not hist:
        return None
    ser = [s for s in hist["series"] if not any(s[0].startswith(p) for p in prefixes)]
    return {**hist, "series": ser} if ser else None


def with_unit(hist: dict | None, unit: str) -> dict | None:
    return {**hist, "unit": unit} if hist else None


def peak_share(hist: dict, prefix: str, u: float = 0.7) -> dict | None:
    """'<name> peaked at n% in <period>' for a share (pct) beat whose share rose then fell."""
    k = _find(hist, prefix)
    if k is None:
        return None
    tot = [sum(vs[i] for _, vs in hist["series"]) or 1 for i in range(len(hist["periods"]))]
    sh = [v / t * 100 for v, t in zip(hist["series"][k][1], tot)]
    i = max(range(len(sh)), key=lambda j: sh[j])
    return {"i": i, "s": k, "u": u, "text": f"{hist['series'][k][0]} peaked at {sh[i]:.0f}% in {hist['periods'][i]}"}


def total_swing(hist: dict, u: float = 0.75) -> dict | None:
    """'Total <first period> <loss/profit> -> <last period> <...>' over all series, losses kept as
    losses (towers draw negatives as 0, so the tag says what the towers cannot)."""
    a = sum(vs[0] for _, vs in hist["series"])
    b = sum(vs[-1] for _, vs in hist["series"])
    cu = hist.get("unit", "$M")
    word = lambda v: ("loss " if v < 0 else "") + _money(abs(v), cu)  # noqa: E731
    k = max(range(len(hist["series"])), key=lambda j: hist["series"][j][1][-1])
    return {"i": -1, "s": k, "u": u,
            "text": f"Total {hist['periods'][0]} {word(a)} -> {hist['periods'][-1]} {word(b)}"}


def drop(hist: dict | None, *names: str) -> dict | None:
    """`hist` minus the series named exactly `names` (`without` matches prefixes)."""
    if not hist:
        return None
    ser = [s for s in hist["series"] if s[0] not in names]
    return {**hist, "series": ser} if ser else None


def yoy(hist: dict, prefix: str, u: float = 0.7) -> dict | None:
    """Short growth tag without money: '<name> +n%' (or k.kx), first -> last period."""
    k = _find(hist, prefix)
    if k is None:
        return None
    name, vs = hist["series"][k]
    a, b = vs[0], vs[-1]
    if a <= 0:
        return None
    ch = f"{b / a:.1f}x" if b / a >= 2 else f"{(b / a - 1) * 100:+.0f}%"
    return {"i": -1, "s": k, "u": u, "text": f"{name} {ch}"}


def bars_year_ago(points: list[list], unit: str = "$M", u: float = 0.75) -> dict | None:
    """Bars tag on the latest point vs the point 4 back (same quarter a year earlier)."""
    import re as _re
    pb, b = points[-1]
    m = _re.match(r"^(Q[1-4]')(\d\d)$", str(pb))
    if m:  # "Q3'26" -> the "Q3'25" point, wherever it sits (series can skip quarters)
        want = f"{m.group(1)}{int(m.group(2)) - 1:02d}"
        prev = [p for p in points if p[0] == want]
        if not prev:
            return None
        pa, a = prev[-1]
    elif len(points) >= 5:
        pa, a = points[-5]
    else:
        return None
    if unit == "%":
        txt = f"{pb} {b:.1f}% vs {pa} {a:.1f}%"
    else:
        ch = f"{b / a:.1f}x" if a > 0 and b / a >= 2 else (f"{(b / a - 1) * 100:+.0f}%" if a > 0 else "")
        txt = f"{pb} vs {pa}: {ch}" if ch else f"{pb} vs {pa}"
    return {"i": -1, "text": txt, "u": u}


def bars_swing(points: list[list], unit: str = "%", u: float = 0.75) -> dict | None:
    """Bars tag for a min -> latest swing (e.g. a loss turning into a profit)."""
    if len(points) < 2:
        return None
    lo = min(range(len(points)), key=lambda i: points[i][1])
    if lo == len(points) - 1:
        return None
    f = (lambda v: f"{v:.1f}%") if unit == "%" else (lambda v: _money(v, unit))  # noqa: E731
    return {"i": -1, "u": u, "text": f"{points[lo][0]} {f(points[lo][1])} -> {points[-1][0]} {f(points[-1][1])}"}


def fit(tag: dict | None, limit: int = 45) -> dict | None:
    """Shorten a tag that would run off the frame: drop a trailing '(...)' then money spans."""
    import re as _re
    if not tag or len(tag["text"]) <= limit:
        return tag
    t = _re.sub(r"\s*\([^)]*\)\s*$", "", tag["text"])
    if len(t) > limit:
        t = _re.sub(r"\s[A-Z]*\$?[\d.,]+[KMBT]?\s->\s[A-Z]*\$?[\d.,]+[KMBT]?", "", t)
    return {**tag, "text": t[: limit]}


def short(tags: list, names: dict[str, str]) -> list:
    """Tags with long series names swapped for short ones in the text only (the legend keeps
    the full name): short(pct_tags(h, [...]), {"Test and Measurement and Electronics": "T&M"})."""
    out = []
    for t in tags:
        if t:
            txt = t["text"]
            for full, sh in names.items():
                txt = txt.replace(full, sh)
            t = {**t, "text": txt}
        out.append(t)
    return out


def tagged(beat: dict | None, *tags: dict | None) -> dict | None:
    """A bars beat with these custom tags in place of the default first / last / peak ones."""
    if not beat:
        return None
    tags = [t for t in tags if t]
    return {**beat, "tags": tags, "auto_tags": False} if tags else beat


def money(v: float, unit: str = "$M") -> str:
    """A value in millions of `unit` as a short string: 1520 -> $1.5B, -57 -> -$57M."""
    return _money(v, unit)


def _fmt_point(v: float, unit: str) -> str:
    return f"{v:.1f}%" if unit == "%" else _money(v, unit)


def bars_peak_to_last(points: list[list], unit: str = "%", u: float = 0.75) -> dict | None:
    """Bars tag for a series that came off its high: '<peak period> <v> -> <last period> <v>'."""
    if len(points) < 2:
        return None
    hi = max(range(len(points)), key=lambda i: points[i][1])
    if hi == len(points) - 1:
        return None
    return {"i": -1, "u": u, "text": f"{points[hi][0]} {_fmt_point(points[hi][1], unit)} -> "
                                     f"{points[-1][0]} {_fmt_point(points[-1][1], unit)}"}


def bars_first_to_last(points: list[list], unit: str = "$M", u: float = 0.75) -> dict | None:
    """Bars tag over the whole span: '<first> -> <last> (k.kx / +n% / +n pts)'."""
    if len(points) < 2:
        return None
    (pa, a), (pb, b) = points[0], points[-1]
    if unit == "%":
        ch = f"{b - a:+.1f} pts"
    elif a > 0 and b > 0:
        ch = f"{b / a:.1f}x" if b / a >= 2 else f"{(b / a - 1) * 100:+.0f}%"
    else:
        ch = ""
    tail = f" ({ch})" if ch else ""
    return {"i": -1, "u": u, "text": f"{pa} {_fmt_point(a, unit)} -> {pb} {_fmt_point(b, unit)}{tail}"}


def find(hist: dict, prefix: str) -> int | None:
    """Index of the first series whose name starts with `prefix`."""
    return _find(hist, prefix)


def bars_total(points: list[list], unit: str = "$M", u: float = 0.75) -> dict | None:
    """Bars tag summing the whole span: '<first>-<last> total <money>' (e.g. 5 years of FCF)."""
    if len(points) < 2:
        return None
    return {"i": -1, "u": u, "text": f"{points[0][0]}-{points[-1][0]} total {_money(sum(v for _, v in points), unit)}"}


def last_step(hist: dict, prefix: str, u: float = 0.7) -> dict | None:
    """'<name> +n% in <last period>' for the change from the last-but-one period to the last."""
    k = _find(hist, prefix)
    if k is None or len(hist["periods"]) < 2:
        return None
    name, vs = hist["series"][k]
    a, b = vs[-2], vs[-1]
    if a <= 0:
        return None
    return {"i": -1, "s": k, "u": u, "text": f"{name} {(b / a - 1) * 100:+.0f}% in {hist['periods'][-1]}"}


def bars_low(points: list[list], unit: str = "%", u: float = 0.6) -> dict | None:
    """Bars tag pinned on the lowest bar: 'low <period> <value>'."""
    if not points:
        return None
    i = min(range(len(points)), key=lambda j: points[j][1])
    return {"i": i, "u": u, "text": f"low {points[i][0]} {_fmt_point(points[i][1], unit)}"}

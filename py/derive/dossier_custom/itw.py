"""Illinois Tool Works: seven steady segments; in the latest quarter against a year earlier Test &
Measurement and Electronics and Welding grow fastest in revenue and income, and the operating margin
holds in a narrow mid-20s band."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import shaped

TICKER = "ITW"
NAMES = {"Testand Measurementand Electronics": "Test & Measurement and Electronics"}


def _band(b: dict | None) -> dict | None:
    """Replace the default tags with the margin's range over the quarters shown."""
    if not b:
        return None
    ys = [y for _, y in b["points"]]
    b["tags"] = [{"i": -1, "u": 0.8, "text": f"{min(ys):.1f}% to {max(ys):.1f}% over {len(ys)} quarters"}]
    b["auto_tags"] = False
    return b


def _yoy(hist: dict, prefixes: list[str]) -> list[dict]:
    """Short '<name> +n% year on year' tags (the long segment names overflow the money tags)."""
    out = []
    for j, p in enumerate(prefixes):
        k = next((k for k, (n, _) in enumerate(hist["series"]) if n.startswith(p)), None)
        if k is None or not hist["series"][k][1][0]:
            continue
        name, vs = hist["series"][k]
        out.append({"i": -1, "s": k, "u": 0.55 + 0.15 * j, "text": f"{name} {(vs[-1] / vs[0] - 1) * 100:+.0f}% y/y"})
    return out


def specs(d: Data) -> list[dict]:
    # quarterly segments: the annual segment facts list one member twice and miss Specialty Products
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    oi_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2, oi=True), NAMES)
    beats = [
        seg_q and story.towers("Revenue by segment, same quarter a year apart", seg_q,
                               tags=_yoy(seg_q, ["Test", "Welding"])),
        oi_q and story.towers("Segment operating income, a year apart", oi_q, tags=_yoy(oi_q, ["Test", "Welding"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        _band(story.bars("Operating margin", "%", d.points("Operating margin, quarterly"))),
    ]
    return [story.scene(d.name("financials"), beats)]

"""AES: revenue holds near $12B as electricity generation revenue shrinks and electric distribution
grows, the US rises to about 41% of revenue, gross margin slips every year, and free cash flow is
negative in every one of the five years. Segment revenue is left out: its members do not add up to
reported revenue (a new AES Andes segment appears only in FY2025, eliminations are missing)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, growth, money, pct_tags, seg_tags, shaped, tagged

TICKER = "AES"
NAMES = {"Nonregulatedrevenue": "Non-regulated revenue", "CL": "Chile", "DO": "Dominican Republic",
         "SV": "El Salvador", "MX": "Mexico", "BG": "Bulgaria", "PA": "Panama", "CO": "Colombia",
         "AR": "Argentina", "VN": "Vietnam", "JO": "Jordan"}


def _first_to_last(pts: list[list], u: float = 0.75) -> dict | None:
    if len(pts) < 2:
        return None
    return {"i": -1, "u": u, "text": f"{pts[0][0]} {pts[0][1]:.1f}% -> {pts[-1][0]} {pts[-1][1]:.1f}%"}


def _total(pts: list[list], u: float = 0.75) -> dict | None:
    if len(pts) < 2:
        return None
    return {"i": -1, "u": u, "text": f"{pts[0][0]}-{pts[-1][0]} total {money(sum(v for _, v in pts))}"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Electricity Generation", "Electric Distribution"])),
        geo and story.towers("Revenue share by country", geo, pct=True, tags=pct_tags(geo, ["US", "Chile"])),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=[growth(prod_q, "Non-regulated")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Gross margin, annual", "%", gm), _first_to_last(gm)),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), _total(fcf)),
    ]
    return [story.scene(d.name("financials"), beats)]

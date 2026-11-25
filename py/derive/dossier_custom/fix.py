"""Comfort Systems USA: Electrical nearly doubles and segment operating income grows faster than
revenue, new construction drives the latest quarter, technology customers about double a year
apart, and the operating margin rises."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "FIX"
NAMES = {"Service Calls Maintenance and Monitoring": "Service calls, maintenance and monitoring",
         "Technology Customer": "Technology", "Manufacturing Customer": "Manufacturing",
         "Healthcare Customer": "Healthcare", "Government Customer": "Government",
         "Office Building Customer": "Office buildings", "Retail Restaurants and Entertainment": "Retail, restaurants and entertainment",
         "Multi Family and Residential": "Multi-family and residential", "Other Customer": "Other"}


def specs(d: Data) -> list[dict]:
    # the Annual and Quarterly revenue blocks carry a bad FY2025 / Q4'25 point, so revenue is told from segments
    seg = shaped(d.history(("ProductOrServiceAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    kind_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    cust_q = shaped(d.history(("MajorCustomersAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Electrical", "Mechanical"])),
        oi and story.towers("Segment operating income", oi, tags=seg_tags(oi, ["Electrical", "Mechanical"])),
        kind_q and story.towers("Same quarter a year apart", kind_q, tags=[growth(kind_q, "New Construction")]),
        cust_q and story.towers("By customer sector, same quarter a year apart", cust_q, tags=[growth(cust_q, "Technology")]),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]

"""POC: pull every USPTO application where Marvell (or an acquired co) is applicant or assignee.

Needs USPTO_API_KEY (plugin .env). Writes raw/patents.jsonl, one slim row per application.
Pre-AIA (<2014) filings list inventors as applicants, hence the assignee clause.
"""
import json, os, time, requests
from pathlib import Path

RAW = Path(__file__).parent / "raw"
ENV = Path(__file__).resolve().parents[2] / ".env"
NAMES = ["Marvell*", "Cavium*", "Inphi*", "Aquantia*", "Innovium*", "\"Celestial AI\"", "XConn*", "Polariton*"]
URL = "https://api.uspto.gov/api/v1/patent/applications/search"
PAGE = 100


def api_key() -> str:
    if k := os.environ.get("USPTO_API_KEY"):
        return k
    for line in ENV.read_text().splitlines():
        if line.startswith("USPTO_API_KEY="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("USPTO_API_KEY missing")


S = requests.Session(); S.headers["X-API-Key"] = api_key()


def get(offset: int) -> dict:
    n = "(" + " OR ".join(NAMES) + ")"
    q = f"applicationMetaData.firstApplicantName:{n} OR assignmentBag.assigneeBag.assigneeNameText:{n}"
    for _ in range(5):
        r = S.get(URL, params={"q": q, "offset": offset, "limit": PAGE}, timeout=60)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", 5))); continue
        r.raise_for_status(); return r.json()
    raise RuntimeError(f"gave up at offset {offset}")


def slim(x: dict) -> dict:
    m = x.get("applicationMetaData", {})
    return {
        "app": x.get("applicationNumberText"),
        "filed": m.get("filingDate"),
        "effective": m.get("effectiveFilingDate"),
        "title": m.get("inventionTitle"),
        "applicant": m.get("firstApplicantName"),
        "status": m.get("applicationStatusDescriptionText"),
        "type": m.get("applicationTypeLabelName"),
        "pub": m.get("earliestPublicationNumber"),
        "cpc": [c.replace(" ", "") for c in m.get("cpcClassificationBag") or []],
        "inventors": [i.get("inventorNameText") for i in m.get("inventorBag") or []],
        "parents": len(x.get("parentContinuityBag") or []),
    }


out = RAW / "patents.jsonl"
first = get(0); total = first["count"]; rows = [slim(x) for x in first["patentFileWrapperDataBag"]]
for off in range(PAGE, total, PAGE):
    time.sleep(0.2)
    rows += [slim(x) for x in get(off).get("patentFileWrapperDataBag", [])]
    print(f"{len(rows)}/{total}", end="\r")
out.write_text("\n".join(json.dumps(r) for r in rows))
print(f"\nwrote {len(rows)} rows -> {out}")

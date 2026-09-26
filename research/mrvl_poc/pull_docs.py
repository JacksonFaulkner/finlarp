"""POC: fetch latest 10-K (+exhibits index) and last-12mo Form 4 XMLs for MRVL."""
import json, time, requests
from pathlib import Path
RAW = Path(__file__).parent / "raw"
S = requests.Session(); S.headers["User-Agent"] = "security_spread (personal nvim tool) contact: jackson.faulkner1@gmail.com"
def get(url):
    time.sleep(0.12); r = S.get(url, timeout=30); r.raise_for_status(); return r
rows = json.load(open(RAW / "filings_index.json"))
def base(x): return f"https://www.sec.gov/Archives/edgar/data/{x['cik']}/{x['accessionNumber'].replace('-','')}"
tk = max((x for x in rows if x["form"] == "10-K"), key=lambda x: x["filingDate"])
idx = get(base(tk) + "/index.json").json()
(RAW / "10k/index.json").write_text(json.dumps(idx))
for it in idx["directory"]["item"]:
    n = it["name"]
    if n == tk["primaryDocument"] or "ex21" in n.lower() or n.lower().endswith("ex-21.htm"):
        (RAW / "10k" / n).write_bytes(get(base(tk) + "/" + n).content); print("got", n)
for x in rows:
    if x["form"] == "4" and x["filingDate"] >= "2025-09-26":
        doc = x["primaryDocument"].split("/")[-1]
        out = RAW / "form4" / f"{x['accessionNumber']}.xml"
        if not out.exists(): out.write_bytes(get(base(x) + "/" + doc).content)
print("form4 files:", len(list((RAW / "form4").glob("*.xml"))))

"""POC: bucket raw/patents.jsonl into Marvell revenue streams by CPC code; print yearly counts + recent titles.

Bucket = first CPC on the application that matches a pattern (CPC order ~ primary class first).
Last ~2 filing years are undercounted: applications publish 18 months after filing.
"""
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

RAW = Path(__file__).parent / "raw"

# tech bucket -> (revenue stream, CPC regex)
BUCKETS = {
    "optics":      ("Interconnect", r"^(G02B6|G02F|H01S|H04B10|H04J14|H01L31|H10F)"),
    "serdes_dsp":  ("Interconnect", r"^(H04L25|H04L27|H04L1/|H04L7|H03M13|H04B3|H04B1/)"),
    "analog":      ("Interconnect", r"^(H03K|H03L|H03F|H03H|H03G|H03M1|H02M|G05F|H03D)"),
    "switch_net":  ("Switching", r"^(H04L45|H04L47|H04L49|H04L12|H04L41|H04L43|H04L61|H04L67|H04L69|H04L65)"),
    "compute_mem": ("Custom/compute", r"^(G06F9|G06F15|G06F12|G06F13|G06F7|G06F8|G06F11|G06F16|G06F17|G06N|G06F5|G06F1/)"),
    "packaging":   ("Custom/compute", r"^(H01L23|H01L25|H01L21|H10W|H10P|H10D|H05K|H01L24)"),
    "test":        ("Custom/compute", r"^(G01R|G06F30)"),
    "storage":     ("Storage", r"^(G11B|G11C|G06F3/)"),
    "security":    ("Comms & other", r"^(H04L9|G06F21|H04L63)"),
    "wireless":    ("Comms & other", r"^(H04W|H04B7|H04B17|H04L5)"),
    "auto":        ("Comms & other", r"^(B60|G01S|G08G)"),
}
_RX = [(b, re.compile(p)) for b, (_, p) in BUCKETS.items()]
# wildcard name matches that aren't Marvell (XConn* -> XConnect oilfield, Marvell* -> Marvellous Day)
JUNK = re.compile(r"XCONNECT|PERFX|MARVELLOUS|INPHILIGHT|FIRQUEST", re.I)


def bucket(cpcs: list[str]) -> str:
    for c in cpcs:
        for b, rx in _RX:
            if rx.match(c):
                return b
    return "other" if cpcs else "no_cpc"


def main(since: str = "2016"):
    rows = [json.loads(l) for l in (RAW / "patents.jsonl").read_text().splitlines()]
    rows = [r for r in rows if not JUNK.search(r["applicant"] or "")]
    by_year: dict[str, Counter] = defaultdict(Counter)
    recent: dict[str, list] = defaultdict(list)
    acq = Counter()
    for r in rows:
        b = bucket(r["cpc"]); y = (r["filed"] or "0000")[:4]
        by_year[y][b] += 1
        if y >= "2023":
            recent[b].append(r)
        a = (r["applicant"] or "").upper()
        for n in ("CELESTIAL", "XCONN", "POLARITON", "INPHI", "CAVIUM", "INNOVIUM", "AQUANTIA"):
            if n in a:
                acq[n] += 1
    names = list(BUCKETS) + ["other", "no_cpc"]
    print(f"{len(rows)} applications; acquired-co applicant counts: {dict(acq)}\n")
    print("| year | " + " | ".join(names) + " | all |")
    print("|" + "---|" * (len(names) + 2))
    for y in sorted(k for k in by_year if k >= since):
        c = by_year[y]
        print(f"| {y} | " + " | ".join(str(c[n]) for n in names) + f" | {sum(c.values())} |")
    streams = Counter()
    for y in by_year:
        if y >= "2021":
            for b, n in by_year[y].items():
                streams[BUCKETS.get(b, ("unmapped",))[0]] += n
    print("\nfiled 2021+ by stream:", dict(streams.most_common()))
    for b in names:
        rs = sorted(recent[b], key=lambda r: r["filed"], reverse=True)[:8]
        if rs:
            print(f"\n## {b} (2023+: {len(recent[b])})")
            for r in rs:
                print(f"- {r['filed']} {r['title'].title()} [{r['applicant']}]")


if __name__ == "__main__":
    main(*sys.argv[1:])

"""Bot-likeness signals for $CASHTAG tweet pulls (jobs/pull_cashtags.py), per ticker window.

    uv run python -m derive.botcheck             # table of signals per cashtags/<TICKER>_<since>.jsonl
    uv run python -m derive.botcheck --authors QUBT_2024-11-12   # the most suspicious accounts in one window

None of these proves automation; each is a pattern bot networks and paid shills tend to share, so read the table
as "which windows look unlike organic chatter" and compare spike windows with the recent baseline of the same ticker.

  young      share of tweets from accounts under 90 days old at tweet time
  tiny       share from accounts with under 50 followers
  heavy      share from accounts averaging over 100 tweets/day for life
  dup        share of tweets whose normalised text appears 3+ times (copy-paste)
  dup_auth   distinct authors inside the largest copy-paste group
  top1       share of tweets from the single most active author
  spam_tags  share carrying 4+ cashtags
  burst      busiest minute / median minute (tweets per minute), over minutes with any tweet
  noeng      share with zero likes, retweets and replies
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics as st
from collections import Counter, defaultdict
from datetime import timezone
from email.utils import parsedate_to_datetime

from sources import universe

DIR = universe.data_dir("cashtags")


def _ts(s: str):
    return parsedate_to_datetime(s).astimezone(timezone.utc)


def norm(text: str) -> str:
    t = re.sub(r"https?://\S+|@\w+", "", text.lower())
    return re.sub(r"[^a-z$ ]+", "", re.sub(r"\d+", "", t)).strip()


def load(f) -> list[dict]:
    rows = []
    for line in f.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        a = r.get("author") or {}
        try:
            when, born = _ts(r["createdAt"]), _ts(a["createdAt"])
        except (KeyError, ValueError, TypeError):
            continue
        age = (when - born).days
        rows.append({
            "id": r["id"], "user": (a.get("username") or "").lower(), "when": when, "age": age,
            "fol": a.get("followers") or 0, "fing": a.get("following") or 0, "sts": a.get("statusesCount") or 0,
            "per_day": (a.get("statusesCount") or 0) / max(age, 1), "text": r.get("text") or "",
            "likes": r.get("likeCount") or 0, "rt": r.get("retweetCount") or 0, "rep": r.get("replyCount") or 0,
            "is_reply": bool(r.get("isReply")), "verified": bool(a.get("isBlueVerified") or a.get("isVerified")),
            "ntags": len((r.get("entities") or {}).get("symbols") or []),
        })
    return rows


def signals(rows: list[dict]) -> dict:
    n = len(rows)
    if not n:
        return {}
    dup = Counter(hashlib.md5(norm(r["text"]).encode()).hexdigest() for r in rows if len(norm(r["text"])) > 12)
    big = {h for h, c in dup.items() if c >= 3}
    groups = defaultdict(set)
    for r in rows:
        h = hashlib.md5(norm(r["text"]).encode()).hexdigest()
        if h in big:
            groups[h].add(r["user"])
    per_min = Counter(r["when"].strftime("%Y%m%d%H%M") for r in rows)
    users = Counter(r["user"] for r in rows)
    return {
        "n": n, "authors": len(users),
        "young": sum(r["age"] < 90 for r in rows) / n,
        "tiny": sum(r["fol"] < 50 for r in rows) / n,
        "heavy": sum(r["per_day"] > 100 for r in rows) / n,
        "dup": sum(dup[hashlib.md5(norm(r["text"]).encode()).hexdigest()] >= 3 for r in rows) / n,
        "dup_auth": max((len(v) for v in groups.values()), default=0),
        "top1": users.most_common(1)[0][1] / n,
        "spam_tags": sum(r["ntags"] >= 4 for r in rows) / n,
        "burst": max(per_min.values()) / max(st.median(per_min.values()), 1),
        "noeng": sum(r["likes"] + r["rt"] + r["rep"] == 0 for r in rows) / n,
        "median_age_d": st.median(r["age"] for r in rows),
    }


def authors(rows: list[dict], top: int = 15) -> None:
    by = defaultdict(list)
    for r in rows:
        by[r["user"]].append(r)
    scored = []
    for u, rs in by.items():
        r0 = rs[0]
        score = (r0["age"] < 90) + (r0["fol"] < 50) + (r0["per_day"] > 100) + (r0["fing"] > 10 * max(r0["fol"], 1)) + (len(rs) >= 5)
        scored.append((score, len(rs), u, r0))
    for score, n, u, r0 in sorted(scored, reverse=True)[:top]:
        print(f"  score {score} @{u:<18} tweets {n:>3} age {r0['age']:>5}d followers {r0['fol']:>6} following {r0['fing']:>6} posts/day {r0['per_day']:.0f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--authors", help="window stem like QUBT_2024-11-12: list its most suspicious accounts")
    a = ap.parse_args()
    if a.authors:
        authors(load(DIR / f"{a.authors}.jsonl"))
        return
    cols = ["n", "authors", "young", "tiny", "heavy", "dup", "dup_auth", "top1", "spam_tags", "burst", "noeng"]
    print(f"{'window':<18}" + "".join(f"{c:>10}" for c in cols) + f"{'med_age_d':>11}")
    for f in sorted(DIR.glob("*.jsonl")):
        s = signals(load(f))
        if not s:
            continue
        cells = "".join(f"{s[c]:>10.0f}" if c in ("n", "authors", "dup_auth", "burst") else f"{s[c]:>10.0%}" for c in cols)
        print(f"{f.stem:<18}{cells}{s['median_age_d']:>11.0f}")


if __name__ == "__main__":
    main()

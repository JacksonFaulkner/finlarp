"""Score the tweet labeller against a hand-checked gold set (sentiment/gold.json) and print every failure.

    uv run python -m jobs.eval_sentiment

Expectations are pydantic types, so the direction of a stance is checked with built-in constraints, not hand-written
comparisons: bullish = PositiveInt, bearish = NegativeInt, neutral = Literal[0], not_bearish = NonNegativeInt,
not_bullish = NonPositiveInt. Each gold check may also pin view_holder, claim, or require a price target. +1 versus +2 is
never scored: only the sign is, because intensity is not a stable distinction between runs.
"""
from __future__ import annotations

import json
import argparse
from typing import Literal

from pydantic import NegativeInt, NonNegativeInt, NonPositiveInt, PositiveInt, TypeAdapter, ValidationError

from core.schemas.sentiment import Claim, ViewHolder
from sources import tweet_sentiment as ts

STANCE = {
    "bullish": TypeAdapter(PositiveInt), "bearish": TypeAdapter(NegativeInt), "neutral": TypeAdapter(Literal[0]),
    "not_bearish": TypeAdapter(NonNegativeInt), "not_bullish": TypeAdapter(NonPositiveInt),
}
VIEW_HOLDER, CLAIM = TypeAdapter(ViewHolder), TypeAdapter(Claim)
PRICE_TARGET = TypeAdapter(float)


def problems(lab: dict, c: dict) -> list[str]:
    bad = []
    for name, adapter, expect, value in (
        ("stance", STANCE.get(c.get("stance", "")), c.get("stance"), lab["stance"]),
        ("view_holder", TypeAdapter(Literal[c["view_holder"]]) if c.get("view_holder") else None, c.get("view_holder"), lab["view_holder"]),
        ("claim", TypeAdapter(Literal[c["claim"]]) if c.get("claim") else None, c.get("claim"), lab["claim"]),
        ("price_target", PRICE_TARGET if c.get("price_target") else None, "a number", lab["price_target"]),
    ):
        if adapter is None:
            continue
        try:
            adapter.validate_python(value)
        except ValidationError:
            bad.append(f"{name} {value!r} is not {expect}")
    return bad


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--votes", type=int, default=1, help="labelling passes per tweet (median is scored)")
    votes = ap.parse_args().votes
    gold = json.loads((ts.DIR / "gold.json").read_text())
    batch = [{"id": g["id"], "handle": g["handle"], "text": g["text"], "cashtags": g["cashtags"]} for g in gold]
    _, items, spent = ts.label_voted(batch, votes)
    by = {i["id"]: i for i in items}
    total = passed = 0
    for g in gold:
        it = by.get(g["id"])
        labs = {lab["ticker"].upper().lstrip("$"): lab for lab in (it or {}).get("labels", [])}
        for c in g["checks"]:
            total += 1
            lab = labs.get(c["ticker"])
            bad = ["no label"] if lab is None else problems(lab, c)
            if g["sarcasm"] and it and not it["is_sarcastic"]:
                bad.append("is_sarcastic is false")
            if bad:
                print(f"FAIL #{g['idx']:>2} {c['ticker']:<5} {'; '.join(bad)} | evidence {lab['evidence'] if lab else ''!r}")
                print(f"       {g['text'].replace(chr(10), ' ')[:120]!r}")
            else:
                passed += 1
    labels = [lab for it in items for lab in it["labels"]]
    inconsistent = sum(lab["view_holder"] == "none" and lab["stance"] != 0 for lab in labels)
    print(f"consistency: {inconsistent}/{len(labels)} labels with view_holder none but a non-zero stance")
    print(f"{passed}/{total} checks pass ({passed / max(total, 1):.0%}); {len(gold)} tweets, {votes} pass(es); about ${spent:.3f}")
    (ts.DIR / "gold_last_run.json").write_text(json.dumps(items, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Per-ticker stance labels and tweet metadata for finance tweets, from an OpenAI model with structured outputs.

    raw/<run>.jsonl  ->  tweet_sentiment.parquet   one row per (tweet, ticker): stance, focus, whose view, claim, ...
                         tweet_meta.parquet        one row per tweet: type, themes, keywords, entities, sarcasm, ...

The output contract is the pydantic models in core/schemas/sentiment.py: the JSON Schema sent to the Responses API is
generated from them (field descriptions carry the labelling rules) and every reply is validated against them. Tweets go in
15 per request so the instructions are paid for once per batch. PROMPT_VERSION is written into every raw row, so a rerun
after a schema or prompt change never mixes versions.

Each tweet can be labelled several times (--votes 3). The raw file keeps every pass; ingest takes the median stance across
passes, copies the other fields from the pass that matches it, and records how many passes agreed.

CLI:  uv run python sources/tweet_sentiment.py run --n 300 --votes 3     # random pilot, originals with a universe cashtag
      uv run python sources/tweet_sentiment.py run --all --votes 3       # every tweet still short of 3 passes
      uv run python sources/tweet_sentiment.py ingest
      uv run python sources/tweet_sentiment.py show 20
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import threading
import time
from collections import Counter, defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import duckdb
import requests
from pydantic import ValidationError

from core.schemas.sentiment import TweetBatch, TweetItem, TweetLabel, strict_schema
from sources import keys, pq, tweets, universe

MODEL = os.environ.get("SENTIMENT_MODEL", "gpt-6-luna")
EFFORT = os.environ.get("SENTIMENT_EFFORT", "none")  # reasoning effort; none is cheapest and fastest
PROMPT_VERSION = 13
PRICE_IN, PRICE_OUT, PRICE_CACHED = 0.10, 0.50, 0.01  # USD per million tokens, standard (OpenAI model page; Batch is half)
DIR = universe.data_dir("sentiment")
RAW = DIR / "raw"
OUT = DIR / "tweet_sentiment.parquet"
META = DIR / "tweet_meta.parquet"
BATCH = 15
URL = "https://api.openai.com/v1/responses"
SCHEMA = strict_schema(TweetBatch)
FLAGGED_FILE = DIR / "flagged_ids.json"  # tweets OpenAI's content filter refused; never sent again
_flag_lock = threading.Lock()
FLAGGED: set[str] = set(json.loads(FLAGGED_FILE.read_text())) if FLAGGED_FILE.exists() else set()


def _flag(tweet_id: str) -> None:
    with _flag_lock:
        FLAGGED.add(tweet_id)
        FLAGGED_FILE.write_text(json.dumps(sorted(FLAGGED)))


def _add_usage(*us: dict) -> dict:
    out = {"input_tokens": 0, "output_tokens": 0, "input_tokens_details": {"cached_tokens": 0}}
    for u in us:
        out["input_tokens"] += u.get("input_tokens", 0)
        out["output_tokens"] += u.get("output_tokens", 0)
        out["input_tokens_details"]["cached_tokens"] += (u.get("input_tokens_details") or {}).get("cached_tokens", 0)
    return out

SYSTEM = """You label finance tweets for a research database. Each input tweet comes with its id, author handle, text and the
cashtags it carries. Return one item per tweet, with one label per cashtag listed for that tweet and no others. Follow each
field's description exactly. Judge every ticker on its own: one tweet can be bullish on one stock and bearish on another.
Price moves are not views. Never invent facts that are not in the tweet."""


def vote_counts(version: int = PROMPT_VERSION) -> Counter:
    return Counter(r["id"] for f in RAW.glob("*.jsonl") for line in f.read_text().splitlines() if line.strip()
                   if (r := json.loads(line)).get("v") == version)


def pending(n: int | None, votes: int = 1, originals_only: bool = True, tickers: set[str] | None = None) -> list[dict]:
    """Tweets with a universe cashtag that have fewer than `votes` labelling passes at this prompt version
    (only those naming one of `tickers`, when given)."""
    have = vote_counts()
    rows = duckdb.connect().execute(
        f"SELECT w.id, w.handle, w.text, list(DISTINCT t.ticker) tickers FROM read_parquet('{tweets.TWEETS}') w "
        f"JOIN read_parquet('{tweets.TICKERS}') t ON t.tweet_id = w.id AND t.in_universe "
        f"WHERE NOT w.is_retweet {'AND NOT w.is_reply' if originals_only else ''} GROUP BY 1, 2, 3").fetchall()
    todo = [{"id": i, "handle": h, "text": x[:900], "cashtags": sorted(t)} for i, h, x, t in rows if have[i] < votes and i not in FLAGGED and (not tickers or tickers & set(t))]
    if n:
        random.Random(7).shuffle(todo)
        todo = todo[:n]
    return todo


def _texts(d: dict) -> list[str]:
    """Every output_text of a Responses API reply (usually one; the model sometimes adds a second message)."""
    if d.get("status") == "incomplete":
        return []
    return [part["text"] for item in d.get("output", []) if item.get("type") == "message"
            for part in item.get("content", []) if part.get("type") == "output_text"]


def _parse(text: str) -> TweetBatch | None:
    """The first complete JSON object in the text, validated; trailing junk after it is ignored (seen with gpt-6-luna)."""
    start = text.find("{")
    if start < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
        return TweetBatch.model_validate(obj)
    except (ValueError, ValidationError):
        return None


def label_batch(batch: list[dict], retries: int = 4) -> tuple[list[dict], dict]:
    batch = [b for b in batch if b["id"] not in FLAGGED]
    if not batch:
        return [], {}
    body = {
        "model": MODEL, "instructions": SYSTEM, "reasoning": {"effort": EFFORT},
        "input": [{"role": "user", "content": json.dumps(batch, ensure_ascii=False)}],
        "text": {"format": {"type": "json_schema", "name": "tweet_labels", "strict": True, "schema": SCHEMA}},
    }
    usage_total: dict = {}
    for attempt in range(retries):
        try:
            r = requests.post(URL, json=body, timeout=180, headers={"Authorization": f"Bearer {keys.require('OPENAI_API_KEY')}"})
        except requests.RequestException:
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code in (429, 500, 502, 503):
            time.sleep(10 * (attempt + 1))
            continue
        if r.status_code != 200:
            msg = r.json().get("error", {}).get("message", r.text)
            if r.status_code == 400 and "usage policy" in msg:  # the content filter refused something in this batch
                if len(batch) == 1:
                    _flag(batch[0]["id"])
                    return [], usage_total
                mid = len(batch) // 2
                (a, ua), (b2, ub) = label_batch(batch[:mid]), label_batch(batch[mid:])
                return a + b2, _add_usage(usage_total, ua, ub)
            raise SystemExit(f"{r.status_code}: {msg[:400]}")
        d = r.json()
        for k in ("input_tokens", "output_tokens"):  # failed attempts are billed too
            usage_total[k] = usage_total.get(k, 0) + d.get("usage", {}).get(k, 0)
        usage_total.setdefault("input_tokens_details", {"cached_tokens": 0})["cached_tokens"] += \
            (d.get("usage", {}).get("input_tokens_details") or {}).get("cached_tokens", 0)
        parsed = next((p for t in _texts(d) if (p := _parse(t))), None)
        if parsed is None:
            print("  reply had no valid JSON object, retrying", file=sys.stderr)
            continue
        want = {b["id"]: set(b["cashtags"]) for b in batch}
        kept = []
        for it in parsed.items:
            if it.id in want:  # drop invented ids and tickers the tweet does not carry
                row = it.model_dump(mode="json")
                row["labels"] = [lab for lab in row["labels"] if lab["ticker"].upper().lstrip("$") in want[it.id]]
                row["v"] = PROMPT_VERSION
                kept.append(row)
        return kept, usage_total
    return [], usage_total


def cost(u: dict) -> float:
    cached = (u.get("input_tokens_details") or {}).get("cached_tokens", 0)
    return ((u.get("input_tokens", 0) - cached) * PRICE_IN + cached * PRICE_CACHED + u.get("output_tokens", 0) * PRICE_OUT) / 1e6


WORKERS = 16  # requests in flight; well inside the Build tier's 5,000 requests and 2M tokens per minute


def label_passes(todos: list[list[dict]], workers: int = WORKERS,
                 sink: Callable[[int, list[dict]], None] | None = None) -> tuple[list[list[dict]], float]:
    """Several labelling passes at once: every batch of every pass shares one pool. Each pass shuffles its tweets with its own
    seed, so a tweet has different batch neighbours in each pass."""
    jobs = []
    for r, todo in enumerate(todos):
        shuffled = random.Random(r).sample(todo, len(todo))
        jobs += [(r, shuffled[i:i + BATCH]) for i in range(0, len(shuffled), BATCH)]
    out: list[list[dict]] = [[] for _ in todos]
    spent, done = 0.0, 0
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(label_batch, batch): r for r, batch in jobs}
        for fut in as_completed(futs):
            items, usage = fut.result()
            out[futs[fut]] += items
            if sink and items:
                sink(futs[fut], items)  # saved as each batch lands, so a crash cannot lose paid work
            spent += cost(usage)
            done += 1
            if done % 25 == 0:
                print(f"  {done}/{len(jobs)} requests, about ${spent:.3f}", file=sys.stderr, flush=True)
    return out, spent


def label_many(todo: list[dict], workers: int = WORKERS) -> tuple[list[dict], float]:
    """One labelling pass."""
    out, spent = label_passes([todo], workers)
    return out[0], spent


def aggregate(passes: list[dict]) -> dict:
    """Merge several labelling passes of one tweet. Per ticker: median stance, the other fields from the highest-confidence
    pass that has that stance (so the label is always one the model actually produced), plus votes and agreement."""
    n = len(passes)
    need = (n + 1) // 2
    by = defaultdict(list)
    for p in passes:
        for lab in p["labels"]:
            by[lab["ticker"].upper().lstrip("$")].append(lab)
    sign = lambda x: (x > 0) - (x < 0)  # noqa: E731
    labels = []
    for ticker, labs in by.items():
        if len(labs) < need:
            continue
        stances = sorted(lab["stance"] for lab in labs)
        final = stances[(len(stances) - 1) // 2]
        rep = max((lab for lab in labs if lab["stance"] == final), key=lambda lab: lab["confidence"])
        labels.append({**rep, "ticker": ticker, "confidence": round(statistics.mean(lab["confidence"] for lab in labs), 3),
                       "votes": len(labs), "agreement": round(sum(sign(lab["stance"]) == sign(final) for lab in labs) / len(labs), 3)})

    def common(field: str, cap: int, lower: bool = False) -> list[str]:
        c = Counter(x.lower() if lower else x for p in passes for x in set(map(str.lower if lower else str, p[field])))
        return [x for x, k in c.most_common() if k >= need][:cap]

    return {"id": passes[0]["id"], "v": passes[0]["v"], "labels": labels,
            "tweet_type": Counter(p["tweet_type"] for p in passes).most_common(1)[0][0],
            "themes": common("themes", 3), "keywords": common("keywords", 6, lower=True), "entities": common("entities", 8),
            "is_repost": sum(p["is_repost"] for p in passes) * 2 > n, "is_sarcastic": sum(p["is_sarcastic"] for p in passes) * 2 > n}


def label_voted(todo: list[dict], votes: int, workers: int = WORKERS) -> tuple[list[dict], list[dict], float]:
    """`votes` passes over the tweets, run together. Returns (the passes, the aggregated items, the cost)."""
    by_pass, spent = label_passes([todo] * votes, workers)
    passes = [{**it, "vote": r} for r, items in enumerate(by_pass) for it in items]
    by = defaultdict(list)
    for p in passes:
        by[p["id"]].append(p)
    return passes, [aggregate(v) for v in by.values()], spent


def run(n: int | None, workers: int, include_replies: bool, votes: int, tickers: set[str] | None = None) -> None:
    todo = pending(n, votes, originals_only=not include_replies, tickers=tickers)
    have = vote_counts()
    print(f"{len(todo)} tweets, up to {votes} passes each, {workers} workers, model {MODEL}, prompt v{PROMPT_VERSION}", flush=True)
    RAW.mkdir(parents=True, exist_ok=True)
    stamp, started, written = f"{datetime.now(timezone.utc):%Y%m%d_%H%M%S}", time.monotonic(), Counter()

    def sink(r: int, items: list[dict]) -> None:
        with (RAW / f"{stamp}_pass{r}.jsonl").open("a") as fh:
            fh.write("".join(json.dumps({**i, "vote": r}, ensure_ascii=False) + "\n" for i in items))
        written[r] += len(items)

    _, spent = label_passes([[t for t in todo if have[t["id"]] <= r] for r in range(votes)], workers, sink)
    for r in range(votes):
        print(f"  pass {r + 1}: {written[r]} tweets labelled", flush=True)
    print(f"{len(FLAGGED)} tweets refused by the content filter and skipped (sentiment/flagged_ids.json)")
    print(f"total about ${spent:.3f} in {time.monotonic() - started:.0f}s")


LABEL_TYPES = {"id": "VARCHAR", "ticker": "VARCHAR", "focus": "VARCHAR", "stance": "INTEGER", "view_holder": "VARCHAR",
               "claim": "VARCHAR", "horizon": "VARCHAR", "has_numbers": "BOOLEAN", "price_target": "DOUBLE",
               "catalyst": "VARCHAR", "evidence": "VARCHAR", "confidence": "DOUBLE", "votes": "INTEGER", "agreement": "DOUBLE"}
META_TYPES = {"id": "VARCHAR", "tweet_type": "VARCHAR", "themes": "VARCHAR[]", "keywords": "VARCHAR[]",
              "entities": "VARCHAR[]", "is_repost": "BOOLEAN", "is_sarcastic": "BOOLEAN"}
assert set(LABEL_TYPES) == set(TweetLabel.model_fields) | {"id", "votes", "agreement"}, "parquet columns drifted from the pydantic model"
assert set(META_TYPES) == set(TweetItem.model_fields) - {"labels"}, "parquet columns drifted from the pydantic model"


def _write(rows: list[dict], dest, types: dict[str, str]) -> None:
    tmp = dest.with_name(dest.name + ".ndjson")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    try:
        cols = ", ".join(f"'{k}': '{v}'" for k, v in types.items())
        pq.copy_atomic(duckdb.connect(), f"SELECT * FROM read_json('{tmp}', format='newline_delimited', columns={{{cols}}})", dest)
    finally:
        tmp.unlink(missing_ok=True)


def ingest(version: int = PROMPT_VERSION) -> dict:
    by = defaultdict(list)
    for f in sorted(RAW.glob("*.jsonl")):
        for line in f.read_text().splitlines():
            if line.strip() and (it := json.loads(line)).get("v") == version:
                by[it["id"]].append(it)
    items = [aggregate(v) for v in by.values()]
    labels = [{**{k: lab[k] for k in LABEL_TYPES if k != "id"}, "id": it["id"]} for it in items for lab in it["labels"]]
    if not labels:
        raise SystemExit(f"no v{version} labels in {RAW}")
    _write(labels, OUT, LABEL_TYPES)
    _write([{k: it[k] for k in META_TYPES} for it in items], META, META_TYPES)
    return {"labels": len(labels), "tweets": len(items), "avg_passes": round(sum(len(v) for v in by.values()) / len(by), 2)}


def show(n: int) -> None:
    for tk, fo, st, vh, cl, ag, ev, text in duckdb.connect().execute(
            f"SELECT s.ticker, s.focus, s.stance, s.view_holder, s.claim, s.agreement, s.evidence, w.text "
            f"FROM read_parquet('{OUT}') s JOIN read_parquet('{tweets.TWEETS}') w ON w.id = s.id ORDER BY random() LIMIT {n}").fetchall():
        print(f"{tk:<6} {fo:<15} {st:+d} {vh:<14} {cl:<16} agree {ag:.2f} | {ev!r} <- {text.replace(chr(10), ' ')[:90]!r}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--n", type=int, default=300)
    r.add_argument("--all", action="store_true")
    r.add_argument("--workers", type=int, default=WORKERS)
    r.add_argument("--votes", type=int, default=3)
    r.add_argument("--include-replies", action="store_true")
    r.add_argument("--tickers", help="only tweets naming one of these, comma separated (e.g. MU,NVDA)")
    sub.add_parser("ingest")
    s = sub.add_parser("show")
    s.add_argument("n", nargs="?", type=int, default=20)
    a = ap.parse_args()
    if a.cmd == "run":
        run(None if a.all else a.n, a.workers, a.include_replies, a.votes,
            {x.strip().upper() for x in a.tickers.split(',') if x.strip()} if a.tickers else None)
        print(json.dumps(ingest()))
    elif a.cmd == "ingest":
        print(json.dumps(ingest()))
    else:
        show(a.n)


if __name__ == "__main__":
    sys.exit(main())

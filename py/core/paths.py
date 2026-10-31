"""On-disk layout of the finlarp data dir. Every script reads and writes through these names.

DATA_ROOT defaults to <repo>/data and can be moved with the FINLARP_DATA env var. Each name
below is the path of one file or dir that finlarp owns; the rebuildable SEC/market caches and
the user's own notes (mind.duckdb) all live under it.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("FINLARP_DATA", ROOT / "data"))

# Top-level files
DB_PATH = DATA_ROOT / "finlarp.duckdb"  # historical price cache + portfolio caches (core.db)
MIND_DB_PATH = DATA_ROOT / "mind.duckdb"  # the user's own notes (mind.store)
ETRADE_TOKEN_PATH = DATA_ROOT / "etrade_token.json"  # cached E*TRADE OAuth token (sources.etrade)
YAHOO_CRUMB_PATH = DATA_ROOT / "yahoo_crumb.json"  # cached Yahoo cookie+crumb (sources.yahoo)
SEARCH_HISTORY_PATH = DATA_ROOT / "search_history"

# 13F holdings dataset (sources.sec_13f)
SEC_13F_DIR = DATA_ROOT / "sec_13f"

# One dir per puller / derived dataset
ACCOUNT_DIR = DATA_ROOT / "account"
ARXIV_DIR = DATA_ROOT / "arxiv"
BULK_DIR = DATA_ROOT / "bulk"
CASHTAGS_DIR = DATA_ROOT / "cashtags"
DEBUG_DIR = DATA_ROOT / "debug"
DOCS_DIR = DATA_ROOT / "docs"
EARNINGS_DIR = DATA_ROOT / "earnings"
EVENTS_DIR = DATA_ROOT / "events"
FILING_TEXT_DIR = DATA_ROOT / "filing_text"
FILINGS_DIR = DATA_ROOT / "filings"
FINANCIALS_DIR = DATA_ROOT / "financials"
FOLLOWING_DIR = DATA_ROOT / "following"
GODEL_DIR = DATA_ROOT / "godel"
INSIDERS_DIR = DATA_ROOT / "insiders"
LOCKS_DIR = DATA_ROOT / "locks"
LOGS_DIR = DATA_ROOT / "logs"
MARKET_DIR = DATA_ROOT / "market"
NEWS_DIR = DATA_ROOT / "news"
OPTIONS_DIR = DATA_ROOT / "options"
PATENTS_DIR = DATA_ROOT / "patents"
PROFILES_DIR = DATA_ROOT / "profiles"
SCRATCH_DIR = DATA_ROOT / "scratch"
SEARCH_DIR = DATA_ROOT / "search"
SEGMENTS_DIR = DATA_ROOT / "segments"
SENTIMENT_DIR = DATA_ROOT / "sentiment"
SHORT_DIR = DATA_ROOT / "short"
SQUEEZE_DIR = DATA_ROOT / "squeeze"
SUBMISSIONS_DIR = DATA_ROOT / "submissions"
TWEET_CALENDAR_DIR = DATA_ROOT / "tweet_calendar"
TWEETS_DIR = DATA_ROOT / "tweets"

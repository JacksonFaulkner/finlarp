"""The one way to talk to sec.gov: a declared User-Agent (SEC 403s without
contact info) and a process-wide throttle with backoff.

SEC allows 10 requests/second per IP across *all* processes. Pullers may
run concurrently, so each process defaults to SEC_RPS=1.5; raise it via
the env var when running a single puller alone.
"""
from __future__ import annotations

import os
import threading
import time

import requests

UA = "finlarp (personal nvim tool) contact: jackson.faulkner1@gmail.com"
RPS = float(os.environ.get("SEC_RPS", "1.5"))

_lock = threading.Lock()
_last = 0.0
_session = requests.Session()
_session.headers["User-Agent"] = UA


def _throttle() -> None:
    global _last
    with _lock:
        wait = _last + 1.0 / RPS - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last = time.monotonic()


def get(url: str, timeout: int = 60) -> requests.Response:
    """Throttled GET with backoff on 429/5xx and dropped connections.
    Returns the response (404 is returned, not raised)."""
    for attempt in range(5):
        _throttle()
        try:
            resp = _session.get(url, timeout=timeout)
        except requests.exceptions.RequestException:
            # Read timeouts / dropped connections are transient on sec.gov.
            if attempt == 4:
                raise
            time.sleep(2 ** attempt * 5)
            continue
        # SEC signals its rate limit with a 403 "Request Rate Threshold
        # Exceeded" page as often as with a 429; callers cache a failed
        # fetch as permanent, so back off and retry it like a 429.
        throttled = resp.status_code == 403 and "Rate Threshold" in resp.text
        if throttled or resp.status_code == 429 or resp.status_code >= 500:
            time.sleep(2 ** attempt * 5)
            continue
        return resp
    resp.raise_for_status()
    return resp


def stream(url: str, timeout: int = 600) -> requests.Response:
    """Throttled streaming GET for bulk zips; one request, no retry.
    Use as a context manager and iter_content() the body."""
    _throttle()
    return _session.get(url, timeout=timeout, stream=True)

"""Apify: run an actor and read back its dataset items.

Needs APIFY_TOKEN (see sources/keys.py). Actor ids use the `user~name` form
(`user/name` is accepted and converted).
"""
from __future__ import annotations

import requests

from sources import keys

BASE = "https://api.apify.com/v2"


def _actor_id(actor: str) -> str:
    return actor.replace("/", "~")


def _headers() -> dict:
    return {"Authorization": f"Bearer {keys.require('APIFY_TOKEN')}"}


def run_actor(actor: str, run_input: dict | None = None, timeout: int = 300) -> list[dict]:
    """Run an actor synchronously and return its dataset items.

    Apify holds the request open until the run finishes (cap ~300s); for longer
    runs use start_run + wait_run + dataset_items.
    """
    resp = requests.post(
        f"{BASE}/acts/{_actor_id(actor)}/run-sync-get-dataset-items",
        headers=_headers(),
        json=run_input or {},
        timeout=timeout + 10,
    )
    resp.raise_for_status()
    return resp.json()


def start_run(actor: str, run_input: dict | None = None) -> dict:
    """Start an actor run without waiting. Returns the run object (id, defaultDatasetId, status)."""
    resp = requests.post(
        f"{BASE}/acts/{_actor_id(actor)}/runs", headers=_headers(), json=run_input or {}, timeout=30
    )
    resp.raise_for_status()
    return resp.json()["data"]


def wait_run(run_id: str, wait_secs: int = 60) -> dict:
    """Block up to wait_secs for a run to finish. Check status in the result."""
    resp = requests.get(
        f"{BASE}/actor-runs/{run_id}",
        headers=_headers(),
        params={"waitForFinish": wait_secs},
        timeout=wait_secs + 10,
    )
    resp.raise_for_status()
    return resp.json()["data"]


def dataset_items(dataset_id: str, limit: int = 1000, offset: int = 0) -> list[dict]:
    resp = requests.get(
        f"{BASE}/datasets/{dataset_id}/items",
        headers=_headers(),
        params={"format": "json", "clean": "true", "limit": limit, "offset": offset},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()

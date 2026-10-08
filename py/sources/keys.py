"""API keys: the process env first, then the plugin's gitignored .env
(nvim's `run` passes it via `uv run --env-file`; scripts run by hand
fall back to reading it here)."""
from __future__ import annotations

import os
from functools import cache
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


@cache
def _dotenv() -> dict[str, str]:
    out = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip("\"'")
    return out


def get(name: str) -> str | None:
    return os.environ.get(name) or _dotenv().get(name)


def require(name: str) -> str:
    if v := get(name):
        return v
    raise SystemExit(f"{name} missing (env or {ENV_FILE})")

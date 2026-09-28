"""Parquet output helpers."""
from __future__ import annotations

from pathlib import Path

import duckdb


def copy_atomic(con: duckdb.DuckDBPyConnection, select: str, dest: Path | str,
                options: str = "FORMAT parquet") -> None:
    """COPY (select) to dest via a .part file + rename, so the MCP server,
    dossier builds and the Rust screens (which read these files while
    pullers run) never see a truncated file, and a crash keeps the old one."""
    dest = Path(dest)
    part = dest.with_name(dest.name + ".part")
    con.execute(f"COPY ({select}) TO '{part}' ({options})")
    part.replace(dest)

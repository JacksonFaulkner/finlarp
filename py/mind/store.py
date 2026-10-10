"""mind.duckdb: the user's own notes, kept apart from the rebuildable SEC cache.

Objects (entities) are shared vocabulary with the world data: `ticker:MRVL`,
`patent:11234567`, `accn:0001628280-25-012345`. Notes link to them through
note_links, so "everything I ever asked about MRVL" is one join.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

import duckdb

from core import db

MIND_PATH = Path(db.DB_PATH.parent / "finlarp" / "mind.duckdb")

_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS entities (
        id VARCHAR PRIMARY KEY,   -- kind:key
        kind VARCHAR NOT NULL,    -- ticker | patent | filing | theme | person
        key VARCHAR NOT NULL,
        first_seen TIMESTAMP DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS notes (
        id VARCHAR PRIMARY KEY,
        ts TIMESTAMP DEFAULT now(),
        kind VARCHAR DEFAULT 'question',  -- question | claim | observation | rationale
        body VARCHAR NOT NULL,
        anchor_entity VARCHAR,            -- entity id the note was written on
        anchor_screen VARCHAR,            -- dossier | search | file path ...
        anchor_context VARCHAR,           -- text/number under the cursor
        status VARCHAR DEFAULT 'pending'  -- pending | answered | failed
    )
    """,
    "ALTER TABLE notes ADD COLUMN IF NOT EXISTS session_id VARCHAR",  # claude session that answered
    "ALTER TABLE notes ADD COLUMN IF NOT EXISTS cwd VARCHAR",         # cwd that session ran in
    "ALTER TABLE answers ADD COLUMN IF NOT EXISTS structured VARCHAR",  # JSON: summary, key_points, themes, follow_ups, learn
    """
    CREATE TABLE IF NOT EXISTS note_themes (
        note_id VARCHAR NOT NULL,
        theme VARCHAR NOT NULL,
        PRIMARY KEY (note_id, theme)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS note_links (
        note_id VARCHAR NOT NULL,
        entity_id VARCHAR NOT NULL,
        role VARCHAR NOT NULL,            -- anchor | mention
        PRIMARY KEY (note_id, entity_id, role)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS answers (
        note_id VARCHAR PRIMARY KEY,
        ts TIMESTAMP DEFAULT now(),
        body VARCHAR,
        model VARCHAR,
        error VARCHAR
    )
    """,
]


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    MIND_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(MIND_PATH), read_only=read_only)
    if not read_only:
        for stmt in _SCHEMA:
            con.execute(stmt)
    return con


def _ensure_entity(con, entity_id: str) -> None:
    kind, _, key = entity_id.partition(":")
    con.execute("INSERT OR IGNORE INTO entities (id, kind, key) VALUES (?, ?, ?)", [entity_id, kind, key])


def add_note(
    body: str,
    *,
    kind: str = "question",
    anchor_entity: str | None = None,
    anchor_screen: str | None = None,
    anchor_context: str | None = None,
    mentions: list[str] = (),
) -> str:
    note_id = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    with connect() as con:
        con.execute(
            "INSERT INTO notes (id, kind, body, anchor_entity, anchor_screen, anchor_context) VALUES (?,?,?,?,?,?)",
            [note_id, kind, body, anchor_entity, anchor_screen, anchor_context],
        )
        links = {(e, "mention") for e in mentions}
        if anchor_entity:
            links.add((anchor_entity, "anchor"))
        for entity_id, role in links:
            _ensure_entity(con, entity_id)
            con.execute("INSERT OR IGNORE INTO note_links VALUES (?,?,?)", [note_id, entity_id, role])
    return note_id


def get_note(note_id: str) -> dict:
    with connect(read_only=True) as con:
        row = con.execute(
            "SELECT id, kind, body, anchor_entity, anchor_screen, anchor_context FROM notes WHERE id = ?", [note_id]
        ).fetchone()
    if row is None:
        raise KeyError(note_id)
    return dict(zip(["id", "kind", "body", "anchor_entity", "anchor_screen", "anchor_context"], row))


def save_answer(
    note_id: str,
    structured: dict | None,
    model: str,
    error: str | None = None,
    session_id: str | None = None,
    cwd: str | None = None,
) -> None:
    body = structured.get("summary") if structured else None
    with connect() as con:
        con.execute(
            "INSERT OR REPLACE INTO answers (note_id, body, model, error, structured) VALUES (?,?,?,?,?)",
            [note_id, body, model, error, json.dumps(structured) if structured else None],
        )
        con.execute(
            "UPDATE notes SET status = ?, session_id = ?, cwd = ? WHERE id = ?",
            ["failed" if error else "answered", session_id, cwd, note_id],
        )
        for theme in (structured or {}).get("themes", []):
            con.execute("INSERT OR IGNORE INTO note_themes VALUES (?,?)", [note_id, theme.strip().lower()])


def index_rows() -> list[dict]:
    """Every note with its answer, links and themes, newest first (feeds the nvim picker)."""
    with connect(read_only=True) as con:
        rows = con.execute(
            """
            SELECT n.id, n.ts, n.kind, n.body, n.status, n.anchor_entity, n.anchor_screen, n.anchor_context,
                   n.session_id, n.cwd, a.structured, a.error,
                   (SELECT list(entity_id) FROM note_links WHERE note_id = n.id),
                   (SELECT list(theme) FROM note_themes WHERE note_id = n.id)
            FROM notes n LEFT JOIN answers a ON a.note_id = n.id ORDER BY n.ts DESC
            """
        ).fetchall()
    keys = ["id", "ts", "kind", "body", "status", "anchor", "screen", "context", "session_id", "cwd",
            "structured", "error", "entities", "themes"]
    out = []
    for r in rows:
        d = dict(zip(keys, r))
        d["structured"] = json.loads(d["structured"]) if d["structured"] else None
        d["entities"] = d["entities"] or []
        d["themes"] = d["themes"] or []
        out.append(d)
    return out


def notes_for(entity_id: str, limit: int = 50) -> list[dict]:
    """Every note linked to an entity (anchor or mention), newest first, with its answer."""
    with connect(read_only=True) as con:
        rows = con.execute(
            """
            SELECT n.id, n.ts, n.kind, n.body, n.status, a.body
            FROM notes n JOIN note_links l ON l.note_id = n.id
            LEFT JOIN answers a ON a.note_id = n.id
            WHERE l.entity_id = ? GROUP BY ALL ORDER BY n.ts DESC LIMIT ?
            """,
            [entity_id, limit],
        ).fetchall()
    return [
        {"id": r[0], "ts": str(r[1]), "kind": r[2], "body": r[3], "status": r[4], "answer": r[5]} for r in rows
    ]


def dump(obj) -> str:
    return json.dumps(obj, default=str)

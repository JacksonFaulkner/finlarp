"""Answer a note by running headless Claude Code against the finlarp MCP tools.

The answer is structured (summary, key points, themes, follow-up questions,
what to learn) so it can be filtered on later. The run gets its own Claude
session id, so the note viewer can reopen the full chat with --resume.
"""
from __future__ import annotations

import json
import re
import subprocess
import uuid
from datetime import date
from pathlib import Path

from mind import store

MODEL = "sonnet"
ROOT = Path(__file__).resolve().parents[2]

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "specific title for the question, max 60 chars, ticker first, e.g. 'NBIS: volume vs 20-day average', not a restatement of the question"},
        "summary": {"type": "string", "description": "the answer, leading with the conclusion"},
        "key_points": {"type": "array", "items": {"type": "string"}, "description": "the important evidence, each with its source"},
        "themes": {"type": "array", "items": {"type": "string"}, "description": "1-3 short reusable theme tags, lowercase, e.g. 'hbm supply', 'customer concentration'"},
        "assumption": {"type": "string", "description": "the assumption hidden in how the question was framed"},
        "follow_ups": {"type": "array", "items": {"type": "string"}, "description": "deeper questions worth asking next"},
        "learn": {"type": "array", "items": {"type": "string"}, "description": "concepts the user should understand to ask better questions here"},
        "depth": {"type": "string", "enum": ["definitional", "causal", "counterfactual"]},
    },
    "required": ["title", "summary", "key_points", "themes", "assumption", "follow_ups", "learn", "depth"],
}

PROMPT = """You are the analyst inside a personal research desk. The user wrote a note while reading.
Today is {today}. Answer with the mcp__finlarp__* tools: SEC/patent/price data via company, search,
financials and sql (check `schema` before SQL), and anything about today, premarket, a recent move
or news via live_quote, live_history and live_news (the local price data lags by a session or more;
never say the data can't answer a question about today without trying the live tools). Cite what
you used (table, filing accession, patent id, or "Yahoo live"). Say plainly if the data cannot answer it.
The user cares more about whether their understanding is improving than about the answer itself.

Reply in two parts:
1. A readable markdown answer for the user: conclusion first, then evidence, then the assumption
   hidden in how they framed the question, then questions worth asking next, then concepts to learn.
2. Finish with ONE fenced ```json block (nothing after it) matching this JSON schema, for indexing:
{schema}

Where the note was written: {anchor}
Text under the cursor: {context}

Note ({kind}):
{body}
"""

_JSON_BLOCK = re.compile(r"```json\s*(\{.*\})\s*```", re.DOTALL)


def parse(text: str) -> dict:
    m = _JSON_BLOCK.search(text)
    if not m:
        raise ValueError("answer had no json block")
    return json.loads(m.group(1))


def run(note_id: str) -> dict:
    note = store.get_note(note_id)
    session_id = str(uuid.uuid4())
    prompt = PROMPT.format(
        anchor=note["anchor_entity"] or note["anchor_screen"] or "unknown",
        context=note["anchor_context"] or "none",
        kind=note["kind"],
        body=note["body"],
        today=date.today().isoformat(),
        schema=json.dumps(SCHEMA),
    )
    try:
        proc = subprocess.run(
            ["claude", "-p", prompt, "--model", MODEL, "--output-format", "json",
             "--session-id", session_id,
             "--allowedTools", "mcp__finlarp__*"],
            capture_output=True, text=True, timeout=600, cwd=ROOT,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or f"claude exited {proc.returncode}")
        out = json.loads(proc.stdout)
        structured = parse(out["result"])
    except Exception as e:  # noqa: BLE001 - recorded on the note, surfaced to the user
        store.save_answer(note_id, None, MODEL, error=str(e), session_id=session_id, cwd=str(ROOT))
        raise
    store.save_answer(note_id, structured, MODEL, session_id=session_id, cwd=str(ROOT))
    return structured

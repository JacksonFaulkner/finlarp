"""CLI for the mind layer; every command prints one JSON document.

    uv run py/mind/cli.py add --body "why is MRVL capex up" --anchor ticker:MRVL --screen dossier
    uv run py/mind/cli.py answer <note_id>
    uv run py/mind/cli.py notes ticker:MRVL
"""
from __future__ import annotations

import argparse
import sys

from mind import answer, extract, store


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--body", required=True)
    a.add_argument("--kind", default="question")
    a.add_argument("--anchor")
    a.add_argument("--screen")
    a.add_argument("--context")
    r = sub.add_parser("answer")
    r.add_argument("note_id")
    sub.add_parser("index")
    n = sub.add_parser("notes")
    n.add_argument("entity")
    args = p.parse_args()

    if args.cmd == "add":
        mentions = extract.entities(args.body + " " + (args.context or ""))
        anchor = args.anchor or next(iter(extract.entities(args.context or "")), None)
        note_id = store.add_note(
            args.body,
            kind=args.kind,
            anchor_entity=anchor,
            anchor_screen=args.screen,
            anchor_context=args.context,
            mentions=mentions,
        )
        print(store.dump({"id": note_id, "mentions": mentions}))
    elif args.cmd == "answer":
        structured = answer.run(args.note_id)
        print(store.dump({"id": args.note_id, "answer": structured}))
    elif args.cmd == "index":
        print(store.dump(store.index_rows()))
    else:
        print(store.dump(store.notes_for(args.entity)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

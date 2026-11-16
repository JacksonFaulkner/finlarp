#!/usr/bin/env python3
"""Run one command and append a record of it to a JSON-lines log, so runs can be compared later.

    python3 tools/pbr3d/observe.py --label bake:logic_die --out assets/logic_die_overview.glb \
        --meta scene=logic_die_overview -- blender -b --python tools/pbr3d/blender/logic_die_overview.py

Each record has: run_id, label, where (PBR3D_WHERE, e.g. "local" or "worker"), started/ended (UTC),
wall_s, user_s, sys_s (the child's CPU time), max_rss (raw ru_maxrss: bytes on macOS, KiB on Linux),
exit code, the command, git sha (and whether the tree was dirty), host shape (os, arch, cpus, RAM
if readable), any --meta key=value pairs, and each --out file's bytes and sha256.

The log is PBR3D_RUNLOG, default tools/pbr3d/runs.jsonl. Child stdout/stderr pass through unchanged.
Standard library only, so it runs on the Mac and on the worker with no install.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOG = os.path.join(HERE, "runs.jsonl")


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def git_state():
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"], cwd=HERE, capture_output=True, text=True, check=True
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"], cwd=HERE, capture_output=True, text=True, check=True
            ).stdout.strip()
        )
        return {"sha": sha, "dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"sha": None, "dirty": None}


def ram_bytes():
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError):
        return None


def host_shape():
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "arch": platform.machine(),
        "cpus": os.cpu_count(),
        "ram_bytes": ram_bytes(),
        "python": platform.python_version(),
    }


def file_record(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return {"path": path, "bytes": os.path.getsize(path), "sha256": h.hexdigest()}


def main(argv):
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--label", required=True, help="what ran, e.g. bake:logic_die_overview")
    ap.add_argument("--out", action="append", default=[], help="output file to hash (repeatable)")
    ap.add_argument("--meta", action="append", default=[], help="key=value to record (repeatable)")
    ap.add_argument("--log", default=os.environ.get("PBR3D_RUNLOG", DEFAULT_LOG))
    ap.add_argument("cmd", nargs=argparse.REMAINDER, help="the command, after --")
    args = ap.parse_args(argv)
    cmd = args.cmd[1:] if args.cmd and args.cmd[0] == "--" else args.cmd
    if not cmd:
        ap.error("no command given after --")

    meta = {}
    for kv in args.meta:
        k, _, v = kv.partition("=")
        meta[k] = v

    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = utc_now()
    t0 = time.monotonic()
    proc = subprocess.run(cmd)
    wall = time.monotonic() - t0
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    ended = utc_now()

    outputs = []
    for p in args.out:
        if os.path.exists(p):
            outputs.append(file_record(p))
        else:
            outputs.append({"path": p, "missing": True})

    record = {
        "run_id": uuid.uuid4().hex[:12],
        "label": args.label,
        "where": os.environ.get("PBR3D_WHERE", "unset"),
        "started": started,
        "ended": ended,
        "wall_s": round(wall, 3),
        "user_s": round(after.ru_utime - before.ru_utime, 3),
        "sys_s": round(after.ru_stime - before.ru_stime, 3),
        "max_rss": after.ru_maxrss,
        "exit": proc.returncode,
        "cmd": cmd,
        "git": git_state(),
        "host": host_shape(),
        "meta": meta,
        "outputs": outputs,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.log)), exist_ok=True)
    with open(args.log, "a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
    print(
        f"[observe] {args.label}: {record['wall_s']}s wall, {record['user_s']}s user, "
        f"exit {proc.returncode} -> {args.log} ({record['run_id']})",
        file=sys.stderr,
    )
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

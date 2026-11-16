"""Bake queue for the FIBER pages: runs Blender scene scripts locally or on the cloud worker, with
caps on how many run at once, so agents queue instead of stacking up on the machine.

    python3 tools/pbr3d/bake_queue.py sync                 # push the shared Blender modules to the worker
    python3 tools/pbr3d/bake_queue.py bake <script.py> <name> [--where auto|local|worker] [-- args...]

Args after `--` reach the script as sys.argv after its own `--` (for zooms that take a letter, etc.).

`bake` blocks until the bake finishes, then prints `OK <where> <glb path>` or `FAIL <where> <log path>`.
The script must call finish(NAME, page=...) like the other overviews: it writes assets/<page>_<name>.glb.

Caps: LOCAL_SLOTS (Blender bakes at once on this Mac, 16 GB RAM) and WORKER_SLOTS (on the m7i worker,
16 vCPU / 61 GB). `auto` takes a local slot if one is free, else a worker slot, else waits.
Transport: the worker reads and writes the context bucket (s3://finlarp-context-<acct>/fiber/).
"""

import json
import os
import shutil
import subprocess
import sys
import tarfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.join(HERE, "blender")
ASSETS = os.path.join(HERE, "assets")
BLENDER = "/opt/homebrew/bin/blender"
REGION = "us-east-1"
INSTANCE = "i-0ea804856aa7ba4fe"
WORKER_DIR = "/home/ubuntu/fiber_bake"
WORKER_BLENDER = "/snap/bin/blender"
ACCT = "762185908994"
BUCKET = f"finlarp-context-{ACCT}"
PREFIX = "fiber"
LOCAL_SLOTS = 3
WORKER_SLOTS = 8
SLOT_DIR = os.path.join("/private/tmp", "fiber_bake_slots")
SHARED = ["fiber_kit.py", "sand_overview.py", "sand_zooms.py", "pbr_kit.py", "fiber_overview.py"]


def sh(cmd, check=False):
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def acquire(kind, n):
    """Take a free slot (a directory). Returns the slot path, or None if all are busy. Slots left by a
    dead process are reclaimed."""
    os.makedirs(SLOT_DIR, exist_ok=True)
    for i in range(n):
        path = os.path.join(SLOT_DIR, f"{kind}{i}")
        pid_file = os.path.join(path, "pid")
        if os.path.isdir(path):
            try:
                pid = int(open(pid_file).read())
                os.kill(pid, 0)
                continue  # alive, busy
            except (OSError, ValueError):
                shutil.rmtree(path, ignore_errors=True)
        try:
            os.mkdir(path)
        except FileExistsError:
            continue
        with open(pid_file, "w") as f:
            f.write(str(os.getpid()))
        return path
    return None


def release(path):
    shutil.rmtree(path, ignore_errors=True)


def wait_slot(prefer):
    """Block until a slot frees. `prefer` is the order to try: ['local', 'worker'] or a single kind."""
    while True:
        for kind in prefer:
            if kind == "local":
                s = acquire("local", LOCAL_SLOTS)
                if s:
                    return "local", s
            else:
                s = acquire("worker", WORKER_SLOTS)
                if s:
                    return "worker", s
        time.sleep(2)


def sync():
    """Pack the shared modules and put them on the worker (and make sure the worker has Blender)."""
    tgz = os.path.join("/private/tmp", "fiber_bake_sync.tgz")
    with tarfile.open(tgz, "w:gz") as t:
        for name in SHARED:
            t.add(os.path.join(BLENDER_DIR, name), arcname=name)
    key = f"s3://{BUCKET}/{PREFIX}/sync/blender.tgz"
    subprocess.run(["aws", "s3", "cp", tgz, key, "--region", REGION], check=True, capture_output=True)
    r = ssm(
        f"mkdir -p {WORKER_DIR}/tools/pbr3d/blender {WORKER_DIR}/tools/pbr3d/assets && cd {WORKER_DIR}/tools/pbr3d/blender "
        f"&& aws s3 cp s3://{BUCKET}/{PREFIX}/sync/blender.tgz - --region {REGION} | tar xz && echo synced"
    )
    print("sync:", r.splitlines()[-1] if r else r)


def ssm(command):
    """Run one shell command on the worker over SSM; returns its stdout (or raises)."""
    params = json.dumps({"commands": [command]})
    cid = sh(["aws", "ssm", "send-command", "--instance-ids", INSTANCE, "--region", REGION,
              "--document-name", "AWS-RunShellScript", "--parameters", params,
              "--query", "Command.CommandId", "--output", "text"], check=True).stdout.strip()
    sh(["aws", "ssm", "wait", "command-executed", "--command-id", cid, "--instance-id", INSTANCE,
        "--region", REGION])
    out = sh(["aws", "ssm", "get-command-invocation", "--command-id", cid, "--instance-id", INSTANCE,
              "--region", REGION, "--query", "StandardOutputContent", "--output", "text"]).stdout
    return out.rstrip("\n")


def bake_local(script, name, log, args):
    cmd = [BLENDER, "-b", "--factory-startup", "--python", script]
    if args:
        cmd += ["--"] + args
    r = sh(cmd)
    with open(log, "w") as f:
        f.write(r.stdout + r.stderr)
    # Only the files this bake itself exported (finish() prints `exported <path>`).
    exported = [l.split(None, 1)[1].strip() for l in (r.stdout + r.stderr).splitlines() if l.startswith("exported ")]
    with open(log, "a") as f:
        f.write("\n".join(exported) + "\n")
    return r.returncode if r.returncode != 0 or exported else 1


def pack_job(name):
    """Every fiber_*.py and the shared modules, so the job's imports are all on the worker."""
    tgz = os.path.join("/private/tmp", f"fiber_job_{name}_{os.getpid()}.tgz")
    names = sorted(f for f in os.listdir(BLENDER_DIR) if f.startswith("fiber_") and f.endswith(".py"))
    with tarfile.open(tgz, "w:gz") as t:
        for n in sorted(set(names + SHARED)):
            if os.path.exists(os.path.join(BLENDER_DIR, n)):
                t.add(os.path.join(BLENDER_DIR, n), arcname=n)
    key = f"{PREFIX}/jobs/{name}-{os.getpid()}.tgz"
    subprocess.run(["aws", "s3", "cp", tgz, f"s3://{BUCKET}/{key}", "--region", REGION],
                   check=True, capture_output=True)
    os.remove(tgz)
    return key


def bake_worker(script, name, log, args):
    """Runs one bake in its own folder on the worker, so its GLBs can't mix with another job's."""
    key = pack_job(name)
    extra = (" " + " ".join(args)) if args else ""
    job = f"{WORKER_DIR}/jobs/{name}-{os.getpid()}"
    cmd = (
        f"mkdir -p {job}/tools/pbr3d/blender {job}/tools/pbr3d/assets && "
        f"cd {job}/tools/pbr3d/blender && aws s3 cp s3://{BUCKET}/{key} - --region {REGION} | tar xz && "
        f"{WORKER_BLENDER} -b --factory-startup --python {os.path.basename(script)} -- {extra} "
        f"> {job}/bake.log 2>&1; rc=$?; "
        f"find {job}/tools/pbr3d/assets -name '*.glb'; echo; echo rc=$rc"
    )
    out = ssm(cmd)
    with open(log, "w") as f:
        f.write(out)
    rc, glbs = 1, []
    for line in out.splitlines():
        if line.startswith("rc="):
            rc = int(line[3:])
        elif line.startswith("/") and line.strip().endswith(".glb"):
            glbs.append(line.strip())
    if rc != 0 or not glbs:
        ssm(f"rm -rf {job}")
        return rc or 1
    os.makedirs(ASSETS, exist_ok=True)
    for g in glbs:
        key_out = f"{PREFIX}/out/{os.path.basename(g)}"
        ssm(f"aws s3 cp {g} s3://{BUCKET}/{key_out} --region {REGION}")
        sh(["aws", "s3", "cp", f"s3://{BUCKET}/{key_out}", os.path.join(ASSETS, os.path.basename(g)),
            "--region", REGION], check=True)
    ssm(f"rm -rf {job}")
    with open(log, "a") as f:
        f.write("\n".join(os.path.join(ASSETS, os.path.basename(g)) for g in glbs) + "\n")
    return 0


def rc_ok(log):
    """True when the bake's log has at least one exported GLB (set by bake_local / bake_worker)."""
    return any(l.strip().endswith(".glb") for l in open(log).read().splitlines())


def bake(script, name, where="auto", args=()):
    script = os.path.abspath(script)
    os.makedirs(os.path.join(SLOT_DIR, "logs"), exist_ok=True)
    prefer = {"auto": ["local", "worker"], "local": ["local"], "worker": ["worker"]}[where]
    kind, slot = wait_slot(prefer)
    log = os.path.join(SLOT_DIR, "logs", f"{name}.{kind}.{os.getpid()}.log")
    try:
        t0 = time.time()
        rc = bake_local(script, name, log, list(args)) if kind == "local" else bake_worker(script, name, log, list(args))
        secs = time.time() - t0
    finally:
        release(slot)
    if rc == 0:
        wrote = [l.strip() for l in open(log).read().splitlines() if l.strip().endswith(".glb")]
        print(f"OK {kind} {secs:.0f}s {' '.join(os.path.relpath(w, HERE) for w in wrote) or '(no glb found)'}")
    else:
        print(f"FAIL {kind} {secs:.0f}s {log}")
    return rc


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "sync":
        sync()
    elif len(sys.argv) >= 4 and sys.argv[1] == "bake":
        rest = sys.argv[4:]
        args = []
        if "--" in rest:
            i = rest.index("--")
            args, rest = rest[i + 1:], rest[:i]
        where = "auto"
        if "--where" in rest:
            where = rest[rest.index("--where") + 1]
        sys.exit(bake(sys.argv[2], sys.argv[3], where, args))
    else:
        print(__doc__)
        sys.exit(2)

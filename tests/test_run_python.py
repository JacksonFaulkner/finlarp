import json
import shutil
import time

import pytest

pytestmark = [pytest.mark.integration,
              pytest.mark.skipif(shutil.which("sandbox-exec") is None, reason="needs sandbox-exec")]


def run(s, code, **k):
    return json.loads(s.run_python(code, **k))


def test_oneshot(s, has_data):
    r = run(s, "print('hello')")
    assert r["returncode"] == 0 and "hello" in r["output"]


def test_sandbox_denials(s, has_data):
    code = '''
import socket, pathlib, os
def t(name, f):
    try:
        f(); print(name, "ALLOWED")
    except Exception as e:
        print(name, "DENIED", type(e).__name__)
t("env", lambda: len(open(%r).read()))
t("ssh", lambda: os.listdir(os.path.expanduser(%r)))
t("write", lambda: open(%r, "w"))
t("net", lambda: socket.create_connection(("1.1.1.1", 80), timeout=3))
''' % (str(s._REPO / ".env"), str(s._HOME / ".ssh"), str(s._HOME / "pytest_should_not_exist.txt"))
    out = run(s, code)["output"]
    for name in ("env", "ssh", "write", "net"):
        assert f"{name} DENIED" in out, out
    assert not (s._HOME / "pytest_should_not_exist.txt").exists()


def test_session_persist_reset(s, has_data):
    run(s, "x = 41", session="pytest1")
    assert "42" in run(s, "print(x + 1)", session="pytest1")["output"]
    run(s, "", session="pytest1", reset_session=True)
    r = run(s, "print(x)", session="pytest1")
    assert "NameError" in r["output"]
    run(s, "", session="pytest1", reset_session=True)


@pytest.mark.slow
def test_timeout(s, has_data):
    t = time.time()
    r = run(s, "import time; time.sleep(30)", timeout_s=2)
    assert "timed out" in r["output"] and time.time() - t < 15


def test_flood(s, has_data):
    r = run(s, "print('x' * 100 + '\\n') if False else None\nfor _ in range(5000): print('y' * 50)")
    assert len(r["output"]) <= s._PY_OUT_MAX and "truncated" in r


def test_fl_in_child(s, has_data):
    r = run(s, "print(round(fl.tstat([1,2,3,4,5]), 3))")
    assert r["returncode"] == 0 and "4.243" in r["output"], r

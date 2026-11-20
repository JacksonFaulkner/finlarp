"""show_screen: validation and the control-socket path, against a real unix socket."""
import json
import socket
import threading

import pytest


@pytest.fixture
def server():
    from agent import server
    return server


@pytest.fixture
def tmpdir_short(monkeypatch, tmp_path):
    """Unix socket paths are short; keep the temp dir under /private/tmp."""
    import tempfile
    import shutil
    d = tempfile.mkdtemp(prefix="flc", dir="/private/tmp")
    monkeypatch.setattr(tempfile, "gettempdir", lambda: d)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def fake_fl(path, reply, got):
    """A listener that records each request line and answers with `reply`."""
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(str(path))
    srv.listen(1)

    def run():
        conn, _ = srv.accept()
        with conn:
            got.append(json.loads(conn.makefile().readline()))
            conn.sendall((json.dumps(reply) + "\n").encode())
        srv.close()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t


def test_screens_come_from_main_rs(server):
    screens = server._fl_screens()
    assert "diagrams" in screens and "home" in screens


def test_unknown_screen_refused_without_sending(server, tmpdir_short):
    assert "unknown screen" in server.show_screen("bogus")


def test_bad_arg_refused_without_sending(server, tmpdir_short):
    assert "not allowed" in server.show_screen("diagrams", "x;rm -rf ~")


def test_no_listener_says_so(server, tmpdir_short):
    assert "no running fl" in server.show_screen("diagrams", "memory")


def test_sends_screen_and_arg_and_reports_ok(server, tmpdir_short):
    got = []
    t = fake_fl(f"{tmpdir_short}/fl-control-1.sock", {"ok": True}, got)
    out = server.show_screen("diagrams", "memory")
    t.join(5)
    assert got == [{"screen": "diagrams", "arg": "memory"}]
    assert out == "showing diagrams memory in the running fl window."


def test_relays_refusal(server, tmpdir_short):
    got = []
    t = fake_fl(f"{tmpdir_short}/fl-control-1.sock", {"ok": False, "error": "nope"}, got)
    out = server.show_screen("home")
    t.join(5)
    assert "refused" in out and "nope" in out


def test_stale_socket_is_skipped(server, tmpdir_short):
    # A socket file with nothing listening: its fl has exited.
    stale = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    stale.bind(f"{tmpdir_short}/fl-control-9.sock")
    stale.close()
    assert "no running fl" in server.show_screen("home")


def test_open_node_sends_tool_call(server, tmpdir_short):
    got = []
    t = fake_fl(f"{tmpdir_short}/fl-control-1.sock", {"ok": True, "node": "HBM STACK"}, got)
    out = server.open_node("HBM STACK")
    t.join(5)
    assert got == [{"tool": "open_node", "args": {"node": "HBM STACK"}}]
    assert "opened node" in out


def test_open_node_relays_error(server, tmpdir_short):
    got = []
    t = fake_fl(f"{tmpdir_short}/fl-control-1.sock", {"ok": False, "error": "no node NOPE"}, got)
    out = server.open_node("NOPE")
    t.join(5)
    assert "refused" in out and "no node NOPE" in out

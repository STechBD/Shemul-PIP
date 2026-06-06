from __future__ import annotations

import sys
import tempfile
import uuid
from pathlib import Path

from shemul import alias


class FakeUI:
    def __init__(self):
        self.msgs = []

    def info(self, m):
        self.msgs.append(("info", m))

    def warn(self, m):
        self.msgs.append(("warn", m))

    def success(self, m):
        self.msgs.append(("success", m))

    def error(self, m):
        self.msgs.append(("error", m))


def _bin_env(monkeypatch):
    base = Path(tempfile.mkdtemp(prefix=f"aliasbin_{uuid.uuid4().hex}_"))
    monkeypatch.setenv("SHEMUL_BIN_DIR", str(base))
    return base


def test_detect_free(monkeypatch):
    _bin_env(monkeypatch)
    status = alias.detect(which=lambda n: None)
    assert status.state == "free"


def test_detect_conflict(monkeypatch):
    _bin_env(monkeypatch)
    status = alias.detect(which=lambda n: "/usr/bin/s")
    assert status.state == "conflict"
    assert status.path == Path("/usr/bin/s")


def test_install_free_creates_shim(monkeypatch):
    _bin_env(monkeypatch)
    ui = FakeUI()
    rc = alias.install(ui, which=lambda n: None)
    assert rc == 0
    target = alias.shim_path()
    assert target.exists()
    assert alias.shim_is_ours(target)
    if not sys.platform.startswith("win"):
        import os

        assert os.access(target, os.X_OK)


def test_install_conflict_refuses(monkeypatch):
    _bin_env(monkeypatch)
    ui = FakeUI()
    rc = alias.install(ui, which=lambda n: "/usr/bin/s")
    assert rc == 1
    assert not alias.shim_path().exists()
    assert any(kind == "warn" for kind, _ in ui.msgs)


def test_install_ours_is_noop(monkeypatch):
    _bin_env(monkeypatch)
    # Pre-create our shim, then simulate `which` finding it.
    created = alias._write_shim()
    ui = FakeUI()
    rc = alias.install(ui, which=lambda n: str(created))
    assert rc == 0
    assert any("already points to Shemul" in m for _, m in ui.msgs)


def test_remove_only_removes_ours(monkeypatch):
    _bin_env(monkeypatch)
    created = alias._write_shim()
    ui = FakeUI()
    rc = alias.remove(ui)
    assert rc == 0
    assert not created.exists()


def test_remove_leaves_foreign(monkeypatch):
    base = _bin_env(monkeypatch)
    foreign = alias.shim_path()
    foreign.parent.mkdir(parents=True, exist_ok=True)
    foreign.write_text("echo not ours\n", encoding="utf-8")
    ui = FakeUI()
    rc = alias.remove(ui)
    assert rc == 1
    assert foreign.exists()


def test_handle_unknown_action(monkeypatch):
    _bin_env(monkeypatch)
    ui = FakeUI()
    rc = alias.handle(ui, "frobnicate")
    assert rc == 1
    assert any(kind == "error" for kind, _ in ui.msgs)

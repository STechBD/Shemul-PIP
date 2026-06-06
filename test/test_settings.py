from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from shemul import settings


class FakeUI:
    def __init__(self):
        self.msgs = []
        self.tables = []

    def info(self, m):
        self.msgs.append(("info", m))

    def warn(self, m):
        self.msgs.append(("warn", m))

    def success(self, m):
        self.msgs.append(("success", m))

    def error(self, m):
        self.msgs.append(("error", m))

    def table(self, title, columns, rows):
        self.tables.append((title, columns, rows))


def _tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix=f"settings_{uuid.uuid4().hex}_")) / "settings.json"


def test_defaults():
    assert settings.load(_tmp()) == {"auto_update": False}


def test_set_get_roundtrip():
    p = _tmp()
    settings.set_value("auto_update", True, p)
    assert settings.get("auto_update", path=p) is True
    assert settings.load(p)["auto_update"] is True


def test_key_aliases():
    p = _tmp()
    settings.set_value("auto-update", True, p)
    assert settings.get("autoupdate", path=p) is True


def test_unknown_keys_are_not_persisted():
    p = _tmp()
    settings.save({"auto_update": True, "bogus": 1}, p)
    assert "bogus" not in settings.load(p)


def test_handle_toggle(monkeypatch):
    p = _tmp()
    monkeypatch.setenv("SHEMUL_SETTINGS_PATH", str(p))
    ui = FakeUI()
    assert settings.handle(ui, ["auto-update", "on"]) == 0
    assert settings.load(p)["auto_update"] is True
    assert settings.handle(ui, ["auto-update", "off"]) == 0
    assert settings.load(p)["auto_update"] is False


def test_handle_invalid_value(monkeypatch):
    monkeypatch.setenv("SHEMUL_SETTINGS_PATH", str(_tmp()))
    ui = FakeUI()
    assert settings.handle(ui, ["auto-update", "maybe"]) == 1
    assert any(kind == "error" for kind, _ in ui.msgs)


def test_handle_unknown_key(monkeypatch):
    monkeypatch.setenv("SHEMUL_SETTINGS_PATH", str(_tmp()))
    ui = FakeUI()
    assert settings.handle(ui, ["bogus", "on"]) == 1


def test_handle_show_lists_settings(monkeypatch):
    monkeypatch.setenv("SHEMUL_SETTINGS_PATH", str(_tmp()))
    ui = FakeUI()
    assert settings.handle(ui, []) == 0
    assert ui.tables and ui.tables[0][0] == "Settings"


def test_handle_reset(monkeypatch):
    p = _tmp()
    monkeypatch.setenv("SHEMUL_SETTINGS_PATH", str(p))
    settings.set_value("auto_update", True, p)
    ui = FakeUI()
    assert settings.handle(ui, ["reset"]) == 0
    assert settings.load(p)["auto_update"] is False


def test_global_settings_path_override(monkeypatch):
    p = _tmp()
    monkeypatch.setenv("SHEMUL_SETTINGS_PATH", str(p))
    from shemul.util import global_settings_path

    assert global_settings_path() == p

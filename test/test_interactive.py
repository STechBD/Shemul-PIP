from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from shemul import interactive, settings


# ---- Fakes -----------------------------------------------------------------

class _Ask:
    def __init__(self, value):
        self._value = value

    def ask(self):
        return self._value


class FakeQuestionary:
    """Minimal stand-in: select() -> 'Yes', checkbox() -> ['auto_update']."""

    def __init__(self, select_value="Yes", checkbox_value=None):
        self._select_value = select_value
        self._checkbox_value = checkbox_value if checkbox_value is not None else ["auto_update"]

    def select(self, *a, **k):
        return _Ask(self._select_value)

    def checkbox(self, *a, **k):
        return _Ask(self._checkbox_value)

    class Choice:
        def __init__(self, title=None, checked=False):
            self.title = title
            self.checked = checked


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


def _force_interactive(monkeypatch, q=None):
    monkeypatch.setattr(interactive, "interactive_enabled", lambda: True)
    monkeypatch.setattr(interactive, "questionary", q or FakeQuestionary())


# ---- interactive_enabled ---------------------------------------------------

def test_disabled_by_env(monkeypatch):
    monkeypatch.setenv("SHEMUL_NO_INTERACTIVE", "1")
    assert interactive.interactive_enabled() is False


def test_disabled_when_no_questionary(monkeypatch):
    monkeypatch.setattr(interactive, "questionary", None)
    monkeypatch.delenv("SHEMUL_NO_INTERACTIVE", raising=False)
    assert interactive.interactive_enabled() is False


# ---- confirm ---------------------------------------------------------------

def test_confirm_fallback_returns_default(monkeypatch):
    monkeypatch.setattr(interactive, "interactive_enabled", lambda: False)
    monkeypatch.setattr("rich.prompt.Confirm.ask", lambda *a, **k: k.get("default", False))
    assert interactive.confirm("ok?", default=True) is True
    assert interactive.confirm("ok?", default=False) is False


def test_confirm_interactive_yes(monkeypatch):
    _force_interactive(monkeypatch, FakeQuestionary(select_value="Yes"))
    assert interactive.confirm("ok?", default=False) is True


def test_confirm_interactive_no(monkeypatch):
    _force_interactive(monkeypatch, FakeQuestionary(select_value="No"))
    assert interactive.confirm("ok?", default=True) is False


def test_confirm_interactive_cancel_returns_default(monkeypatch):
    _force_interactive(monkeypatch, FakeQuestionary(select_value=None))
    assert interactive.confirm("ok?", default=True) is True


# ---- select_one ------------------------------------------------------------

def test_select_one_fallback_default(monkeypatch):
    monkeypatch.setattr(interactive, "interactive_enabled", lambda: False)
    assert interactive.select_one("pick", ["a", "b"], default="b") == "b"


def test_select_one_fallback_first_when_no_default(monkeypatch):
    monkeypatch.setattr(interactive, "interactive_enabled", lambda: False)
    assert interactive.select_one("pick", ["a", "b"]) == "a"


def test_select_one_empty():
    assert interactive.select_one("pick", []) is None


def test_select_one_interactive(monkeypatch):
    _force_interactive(monkeypatch, FakeQuestionary(select_value="b"))
    assert interactive.select_one("pick", ["a", "b"]) == "b"


# ---- toggle_settings -------------------------------------------------------

def test_toggle_settings_noninteractive_returns_none(monkeypatch):
    monkeypatch.setattr(interactive, "interactive_enabled", lambda: False)
    assert interactive.toggle_settings("m", {"auto_update": False}) is None


def test_toggle_settings_interactive(monkeypatch):
    _force_interactive(monkeypatch, FakeQuestionary(checkbox_value=["auto_update"]))
    result = interactive.toggle_settings("m", {"auto_update": False})
    assert result == {"auto_update": True}


# ---- settings command interactive path -------------------------------------

def _tmp_settings() -> Path:
    return Path(tempfile.mkdtemp(prefix=f"isettings_{uuid.uuid4().hex}_")) / "settings.json"


def test_settings_no_args_interactive_saves(monkeypatch):
    path = _tmp_settings()
    monkeypatch.setenv("SHEMUL_SETTINGS_PATH", str(path))
    monkeypatch.setattr(interactive, "interactive_enabled", lambda: True)
    monkeypatch.setattr(interactive, "toggle_settings", lambda msg, items: {"auto_update": True})

    ui = FakeUI()
    code = settings.handle(ui, [])

    assert code == 0
    assert settings.load(path)["auto_update"] is True
    assert ui.tables  # still shows the resulting table


def test_settings_no_args_noninteractive_just_shows(monkeypatch):
    path = _tmp_settings()
    monkeypatch.setenv("SHEMUL_SETTINGS_PATH", str(path))
    monkeypatch.setattr(interactive, "interactive_enabled", lambda: False)

    ui = FakeUI()
    code = settings.handle(ui, [])

    assert code == 0
    assert ui.tables


# ---- guard delegates to the interactive layer ------------------------------

def test_guard_uses_interactive_confirm(monkeypatch):
    from shemul.guard import Guard

    monkeypatch.setattr(interactive, "confirm", lambda message, default=False: True)
    assert Guard().confirm("proceed?") is True
    monkeypatch.setattr(interactive, "confirm", lambda message, default=False: False)
    assert Guard().confirm("proceed?") is False

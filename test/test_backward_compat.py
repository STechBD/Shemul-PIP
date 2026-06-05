from __future__ import annotations

from pathlib import Path

from shemul.app import App
from shemul.config import ShemulConfig


class _Result:
    def __init__(self, code=0):
        self.return_code = code


def _mute(app):
    app.ui.success = lambda m: None
    app.ui.error = lambda m: None
    app.ui.info = lambda m: None
    app.ui.warn = lambda m: None


def test_resolve_identical_to_legacy():
    app = App()
    config = ShemulConfig(
        raw={"commands": {"hi": {"run": "echo {{NAME}}"}}, "vars": {"NAME": "world"}},
        path=Path("x"),
    )
    resolved = app.resolve(config, "hi")
    assert resolved.command == "echo world"
    assert resolved.shell is True
    assert resolved.exec_argv is None
    assert resolved.runner == ""


def test_legacy_run_command_single_executor_call(monkeypatch):
    app = App()
    _mute(app)
    calls = []
    monkeypatch.setattr(app.executor, "run", lambda *a, **k: calls.append((a, k)) or _Result(0))

    config = ShemulConfig(raw={"commands": {"hi": {"run": "echo hi"}}}, path=Path("x"))
    code = app.run_command(config, "hi", dry=False, trace=False, extra_args=[])

    assert code == 0
    assert len(calls) == 1  # planner/plugin gates stay inert for a plain command


def test_env_templating_unchanged():
    app = App()
    config = ShemulConfig(
        raw={
            "commands": {"up": {"run": "compose -f {{env.compose}} up", "env": "local"}},
            "env": {"local": {"compose": "docker-compose.yml"}},
        },
        path=Path("x"),
    )
    resolved = app.resolve(config, "up")
    assert resolved.command == "compose -f docker-compose.yml up"

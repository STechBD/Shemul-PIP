from __future__ import annotations

from pathlib import Path

from shemul.app import App
from shemul.config import ShemulConfig
from shemul.plugins import PluginRegistry, discover


class _Result:
    def __init__(self, code=0):
        self.return_code = code


def _mute(app):
    app.ui.success = lambda m: None
    app.ui.error = lambda m: None
    app.ui.info = lambda m: None
    app.ui.warn = lambda m: None


def test_discover_empty_registry():
    reg = discover()
    assert isinstance(reg, PluginRegistry)
    # No shemul.plugins entry points installed in the test environment.
    assert reg.runners == {}


def test_register_runner_and_resolver():
    reg = PluginRegistry()
    reg.register_runner("docker", lambda r: 0)
    reg.register_resolver("tmpl", lambda r: r)
    assert "docker" in reg.runners
    assert "tmpl" in reg.resolvers


def test_runner_dispatched_on_hot_path():
    app = App()
    _mute(app)
    calls = []
    app.plugins.register_runner("docker", lambda resolved: calls.append(resolved.name) or 0)

    config = ShemulConfig(raw={"commands": {"c": {"run": "echo hi", "runner": "docker"}}}, path=Path("x"))
    code = app.run_command(config, "c", dry=False, trace=False, extra_args=[])

    assert code == 0
    assert calls == ["c"]


def test_unknown_runner_falls_back_to_executor(monkeypatch):
    app = App()
    _mute(app)
    exec_calls = []
    monkeypatch.setattr(app.executor, "run", lambda *a, **k: exec_calls.append(1) or _Result(0))

    config = ShemulConfig(raw={"commands": {"c": {"run": "echo hi", "runner": "missing"}}}, path=Path("x"))
    app.run_command(config, "c", dry=False, trace=False, extra_args=[])

    assert len(exec_calls) == 1


def test_failing_runner_falls_back(monkeypatch):
    app = App()
    _mute(app)
    exec_calls = []
    monkeypatch.setattr(app.executor, "run", lambda *a, **k: exec_calls.append(1) or _Result(0))

    def boom(resolved):
        raise RuntimeError("plugin broke")

    app.plugins.register_runner("docker", boom)
    config = ShemulConfig(raw={"commands": {"c": {"run": "echo hi", "runner": "docker"}}}, path=Path("x"))
    code = app.run_command(config, "c", dry=False, trace=False, extra_args=[])

    assert code == 0
    assert len(exec_calls) == 1  # fell back to default execution
